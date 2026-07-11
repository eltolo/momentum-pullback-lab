from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .data_loader import DEFAULT_DB_PATH, load_market_config


CCL_PROXY_PAIRS = {
    "GGAL.BA": "GGALD",
    "PAMP.BA": "PAMPD",
    "YPFD.BA": "YPFDD",
    "BBAR.BA": "BBARD",
    "CEPU.BA": "CEPUD",
}


@dataclass(frozen=True)
class FXSeriesBundle:
    db_path: Path
    source_table: str
    source_kind: str
    notes: list[str]
    series: pd.DataFrame


def _table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table_name,),
    ).fetchone()
    return bool(row)


def _extend_ccl_with_especie_d_proxy(
    conn: sqlite3.Connection,
    series: pd.DataFrame,
    start_date: str,
) -> tuple[pd.DataFrame, list[str]]:
    if series.empty or not _table_exists(conn, "historico_especie_d"):
        return series, []

    lookback_start = (pd.Timestamp(start_date) - pd.Timedelta(days=30)).strftime("%Y-%m-%d")
    ars_tickers = tuple(CCL_PROXY_PAIRS.keys())
    usd_tickers = tuple(CCL_PROXY_PAIRS.values())
    ars_placeholders = ", ".join("?" for _ in ars_tickers)
    usd_placeholders = ", ".join("?" for _ in usd_tickers)

    ars = pd.read_sql_query(
        f"SELECT Ticker, Date, Close FROM historico_diario WHERE Date >= ? AND Ticker IN ({ars_placeholders})",
        conn,
        params=(lookback_start, *ars_tickers),
    )
    usd = pd.read_sql_query(
        f"SELECT Ticker, Date, Close FROM historico_especie_d WHERE Date >= ? AND Ticker IN ({usd_placeholders})",
        conn,
        params=(lookback_start, *usd_tickers),
    )
    if ars.empty or usd.empty:
        return series, []

    ars["proxy_ticker"] = ars["Ticker"].map(CCL_PROXY_PAIRS)
    merged = ars.merge(
        usd,
        left_on=["proxy_ticker", "Date"],
        right_on=["Ticker", "Date"],
        suffixes=("_ars", "_usd"),
    )
    if merged.empty:
        return series, []

    merged["ratio"] = pd.to_numeric(merged["Close_ars"], errors="coerce") / pd.to_numeric(merged["Close_usd"], errors="coerce")
    daily_proxy = (
        merged.dropna(subset=["ratio"])
        .groupby("Date")
        .agg(proxy_mep=("ratio", "median"), proxy_pairs=("ratio", "count"))
        .reset_index()
    )
    if daily_proxy.empty:
        return series, []

    series_for_overlap = series[["fx_date", "mep"]].copy()
    series_for_overlap["fx_date"] = pd.to_datetime(series_for_overlap["fx_date"], utc=False)
    series_for_overlap["Date"] = series_for_overlap["fx_date"].dt.strftime("%Y-%m-%d")
    overlap = daily_proxy.merge(series_for_overlap, on="Date", how="inner")
    if overlap.empty:
        return series, []

    overlap["scale_factor"] = pd.to_numeric(overlap["mep"], errors="coerce") / pd.to_numeric(overlap["proxy_mep"], errors="coerce")
    overlap = overlap.dropna(subset=["scale_factor"])
    if overlap.empty:
        return series, []

    scale_factor = float(overlap["scale_factor"].median())
    last_fx_date = series["fx_date"].max()
    extension = daily_proxy.loc[pd.to_datetime(daily_proxy["Date"], utc=False) > last_fx_date].copy()
    if extension.empty:
        return series, []

    extension["fx_date"] = pd.to_datetime(extension["Date"], utc=False)
    extension["mep"] = pd.to_numeric(extension["proxy_mep"], errors="coerce") * scale_factor
    extension = extension.dropna(subset=["mep"])
    extension["fx_source_table"] = "historico_especie_d"
    extension["fx_source_kind"] = "ccl_proxy_extended_with_especie_d"

    base_series = series.copy()
    base_series["fx_date"] = pd.to_datetime(base_series["fx_date"], utc=False)
    combined = pd.concat(
        [base_series, extension[["fx_date", "mep", "fx_source_table", "fx_source_kind"]]],
        ignore_index=True,
    )
    combined = combined.drop_duplicates(subset=["fx_date"], keep="last").sort_values("fx_date").reset_index(drop=True)
    notes = [
        (
            "Extended ccl_diario with calibrated especie D proxy "
            f"from {extension['Date'].min()} to {extension['Date'].max()} "
            f"using median scale factor {scale_factor:.6f} over {len(overlap)} overlap days."
        )
    ]
    return combined, notes


def load_canonical_mep(market: str = "argentina") -> FXSeriesBundle:
    config = load_market_config(market)
    data_config = config.get("data", {})
    db_path = Path(data_config.get("fx_db_path", data_config.get("price_db_path", DEFAULT_DB_PATH)))
    start_date = data_config.get("start_date", "2021-03-29")
    hierarchy = data_config.get("fx_source_hierarchy", ["mep_diario", "bullmarket_resumen", "ccl_diario"])

    notes: list[str] = []
    with sqlite3.connect(db_path) as conn:
        source_table = ""
        source_kind = ""
        sql = ""
        for candidate in hierarchy:
            if candidate == "mep_diario" and _table_exists(conn, "mep_diario"):
                source_table = "mep_diario"
                source_kind = "mep_direct"
                sql = "SELECT date AS fx_date, mep AS mep FROM mep_diario WHERE date >= ? ORDER BY date"
                break
            if candidate == "bullmarket_resumen" and _table_exists(conn, "bullmarket_resumen"):
                source_table = "bullmarket_resumen"
                source_kind = "mep_mid"
                sql = "SELECT fecha AS fx_date, (mep_bid + mep_ask) / 2.0 AS mep FROM bullmarket_resumen WHERE fecha >= ? AND mep_bid IS NOT NULL AND mep_ask IS NOT NULL ORDER BY fecha"
                break
            if candidate == "ccl_diario" and _table_exists(conn, "ccl_diario"):
                source_table = "ccl_diario"
                source_kind = "ccl_proxy_for_mep"
                sql = "SELECT date AS fx_date, ccl AS mep FROM ccl_diario WHERE date >= ? AND ccl IS NOT NULL ORDER BY date"
                notes.append("No dedicated historical MEP table found; using ccl_diario as the current canonical USD conversion proxy.")
                break

        if not sql:
            raise RuntimeError(f"No canonical FX source found in {db_path}")

        series = pd.read_sql_query(sql, conn, params=(start_date,))
        if source_table == "ccl_diario" and not series.empty:
            series, extension_notes = _extend_ccl_with_especie_d_proxy(conn, series, start_date)
            notes.extend(extension_notes)

    if not series.empty:
        series["fx_date"] = pd.to_datetime(series["fx_date"], utc=False)
        series["mep"] = pd.to_numeric(series["mep"], errors="coerce")
        series = series.dropna(subset=["mep"]).drop_duplicates(subset=["fx_date"], keep="last")
        series = series.sort_values("fx_date").reset_index(drop=True)
        series["fx_source_table"] = source_table
        series["fx_source_kind"] = source_kind

    return FXSeriesBundle(
        db_path=db_path,
        source_table=source_table,
        source_kind=source_kind,
        notes=notes,
        series=series,
    )
