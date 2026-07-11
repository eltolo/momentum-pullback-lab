from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .data_loader import PriceDataBundle
from .mep import FXSeriesBundle

ROOT = Path(__file__).resolve().parents[2]
MAX_INVALID_OHLC_BARS = 5  # tolerate a few corrupt bars from yfinance


@dataclass(frozen=True)
class AuditArtifacts:
    ok: bool
    analysis_start: str | None
    analysis_end: str | None
    included_tickers: list[str]
    excluded_tickers: list[dict[str, Any]]
    critical_failures: list[str]
    warnings: list[str]
    report_path: str
    summary_path: str
    panel_path: str
    tradable_path: str


def _as_date(value: pd.Timestamp | None) -> str | None:
    if value is None or pd.isna(value):
        return None
    return pd.Timestamp(value).strftime("%Y-%m-%d")


def _markdown_table(rows: list[dict[str, Any]], columns: list[tuple[str, str]]) -> list[str]:
    if not rows:
        return ["_none_"]
    header = "| " + " | ".join(label for _, label in columns) + " |"
    divider = "| " + " | ".join("---" for _ in columns) + " |"
    lines = [header, divider]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(key, "")) for key, _ in columns) + " |")
    return lines


def _format_date_list(values: list[pd.Timestamp], limit: int = 5) -> str:
    if not values:
        return ""
    shown = [pd.Timestamp(value).strftime("%Y-%m-%d") for value in values[:limit]]
    suffix = "" if len(values) <= limit else f" (+{len(values) - limit} more)"
    return ", ".join(shown) + suffix


def _build_adjusted_panel(prices: pd.DataFrame, fx_series: pd.DataFrame) -> pd.DataFrame:
    panel = prices.copy()
    close_for_factor = panel["close_ars_raw"].replace(0, pd.NA)
    adj_factor = (panel["adj_close_ars"] / close_for_factor).fillna(1.0)
    adj_factor = adj_factor.replace([pd.NA, pd.NaT], 1.0)
    panel["adjustment_factor"] = pd.to_numeric(adj_factor, errors="coerce").fillna(1.0)

    for raw_col, adj_col in [
        ("open_ars_raw", "open_ars_adj"),
        ("high_ars_raw", "high_ars_adj"),
        ("low_ars_raw", "low_ars_adj"),
        ("close_ars_raw", "close_ars_adj"),
    ]:
        panel[adj_col] = pd.to_numeric(panel[raw_col], errors="coerce") * panel["adjustment_factor"]

    panel = panel.merge(fx_series, left_on="Date", right_on="fx_date", how="left")
    panel["close_usd_mep_raw"] = panel["close_ars_raw"] / panel["mep"]
    panel["close_usd_mep_adj"] = panel["close_ars_adj"] / panel["mep"]
    panel["dollar_volume_ars"] = panel["close_ars_raw"] * panel["volume"]
    panel["dollar_volume_usd_mep"] = panel["dollar_volume_ars"] / panel["mep"]
    panel["date"] = panel["Date"].dt.strftime("%Y-%m-%d")
    return panel


def _rolling_tradable_panel(panel: pd.DataFrame, config: dict[str, Any]) -> pd.DataFrame:
    liquidity = config.get("liquidity", {})
    risk = config.get("risk", {})
    scales = liquidity.get("capital_scales_usd_mep", [5000, 10000, 15000])
    max_positions = int(risk.get("max_positions", 3))
    participation = float(liquidity.get("max_participation_of_daily_volume", 0.01))
    window = int(liquidity.get("avg_dollar_volume_window", 20))

    work = panel[["date", "ticker", "dollar_volume_usd_mep"]].copy()
    work["date"] = pd.to_datetime(work["date"], utc=False)
    work = work.sort_values(["ticker", "date"]).reset_index(drop=True)
    work["avg_dollar_volume_20d_usd_mep"] = (
        work.groupby("ticker")["dollar_volume_usd_mep"]
        .transform(lambda s: s.rolling(window=window, min_periods=window).mean())
    )

    frames: list[pd.DataFrame] = []
    for scale in scales:
        position_size = float(scale) / max_positions
        scale_frame = work[["date", "ticker", "avg_dollar_volume_20d_usd_mep"]].copy()
        scale_frame["scale_usd_mep"] = float(scale)
        scale_frame["position_size_usd_mep"] = position_size
        scale_frame["max_participation"] = participation
        scale_frame["is_tradable"] = scale_frame["avg_dollar_volume_20d_usd_mep"] * participation >= position_size
        frames.append(scale_frame)

    tradable = pd.concat(frames, ignore_index=True)
    tradable["date"] = tradable["date"].dt.strftime("%Y-%m-%d")
    return tradable


def execute_data_audit(price_bundle: PriceDataBundle, fx_bundle: FXSeriesBundle) -> AuditArtifacts:
    config = price_bundle.config
    output_report = ROOT / "results" / "01_data_quality_report.md"
    summary_path = ROOT / "data" / "quality_reports" / "t267_data_quality_summary.json"
    panel_path = ROOT / "data" / "processed" / "t267_argentina_panel.csv"
    tradable_path = ROOT / "data" / "processed" / "t267_argentina_tradable_by_scale.csv"

    prices = price_bundle.prices.copy()
    fx_series = fx_bundle.series.copy()
    critical_failures: list[str] = []
    warnings = list(fx_bundle.notes)
    excluded_tickers: list[dict[str, Any]] = []
    included_tickers: list[str] = []

    if prices.empty:
        critical_failures.append("No BYMA daily rows found for the desired universe.")
    if fx_series.empty:
        critical_failures.append("No canonical FX series rows found.")

    if price_bundle.missing_desired_tickers:
        critical_failures.append(
            "Desired tickers missing from historico_diario: " + ", ".join(sorted(price_bundle.missing_desired_tickers))
        )

    analysis_start = None
    analysis_end = None
    panel = pd.DataFrame()
    tradable = pd.DataFrame()

    if not prices.empty and not fx_series.empty:
        prices = prices.sort_values(["ticker", "Date"]).reset_index(drop=True)
        fx_series = fx_series.sort_values("fx_date").reset_index(drop=True)

        max_price_date = prices["Date"].max()
        max_fx_date = fx_series["fx_date"].max()
        if max_fx_date < max_price_date:
            critical_failures.append(
                f"FX coverage ends at {_as_date(max_fx_date)} but price data continues to {_as_date(max_price_date)}; forward-fill is forbidden."
            )

        analysis_start = max(prices["Date"].min(), fx_series["fx_date"].min())
        analysis_end = min(max_price_date, max_fx_date)
        calendar_dates = fx_series.loc[
            (fx_series["fx_date"] >= analysis_start) & (fx_series["fx_date"] <= analysis_end), "fx_date"
        ].drop_duplicates().sort_values()
        base_window_prices = prices.loc[
            (prices["Date"] >= analysis_start) & (prices["Date"] <= analysis_end)
        ].copy()

        invalid_mask = (
            (base_window_prices["open_ars_raw"] <= 0)
            | (base_window_prices["high_ars_raw"] <= 0)
            | (base_window_prices["low_ars_raw"] <= 0)
            | (base_window_prices["close_ars_raw"] <= 0)
            | (base_window_prices["high_ars_raw"] < base_window_prices["low_ars_raw"])
            | (base_window_prices["high_ars_raw"] < base_window_prices["open_ars_raw"])
            | (base_window_prices["high_ars_raw"] < base_window_prices["close_ars_raw"])
            | (base_window_prices["low_ars_raw"] > base_window_prices["open_ars_raw"])
            | (base_window_prices["low_ars_raw"] > base_window_prices["close_ars_raw"])
            | (base_window_prices["volume"] < 0)
        )
        invalid_rows = base_window_prices.loc[
            invalid_mask,
            ["ticker", "Date", "open_ars_raw", "high_ars_raw", "low_ars_raw", "close_ars_raw", "volume"],
        ]
        zero_volume = base_window_prices.loc[base_window_prices["volume"] == 0, ["ticker", "Date"]]
        if not zero_volume.empty:
            warnings.append(f"Zero-volume rows detected: {len(zero_volume)}")

        excluded_lookup: dict[str, set[str]] = {}
        missing_date_lookup: dict[str, list[pd.Timestamp]] = {}
        invalid_date_lookup: dict[str, list[pd.Timestamp]] = {}
        invalid_count_lookup: dict[str, int] = {}
        for row in invalid_rows.itertuples(index=False):
            excluded_lookup.setdefault(row.ticker, set()).add(
                f"invalid_ohlc_on_{pd.Timestamp(row.Date).strftime('%Y-%m-%d')}"
            )
            invalid_date_lookup.setdefault(row.ticker, []).append(pd.Timestamp(row.Date))
            invalid_count_lookup[row.ticker] = invalid_count_lookup.get(row.ticker, 0) + 1

        for ticker, ticker_rows in base_window_prices.groupby("ticker"):
            ticker_dates = set(ticker_rows["Date"])
            missing_dates = sorted(set(calendar_dates) - ticker_dates)
            if missing_dates:
                excluded_lookup.setdefault(ticker, set()).add(f"missing_{len(missing_dates)}_dates_in_base_window")
                missing_date_lookup[ticker] = missing_dates

        for ticker in sorted({*prices["ticker"].unique(), *excluded_lookup.keys()}):
            reasons = sorted(excluded_lookup.get(ticker, set()))
            inv_count = invalid_count_lookup.get(ticker, 0)
            missing = missing_date_lookup.get(ticker, [])
            invalid_dates = sorted(invalid_date_lookup.get(ticker, []))
            if missing:
                # Missing dates always exclude
                excluded_tickers.append({
                    "ticker": ticker,
                    "reasons": "; ".join(reasons),
                    "missing_dates_count": len(missing),
                    "missing_dates_sample": _format_date_list(missing),
                    "invalid_dates": _format_date_list(invalid_dates),
                })
            elif inv_count > MAX_INVALID_OHLC_BARS:
                # Too many invalid bars → exclude
                excluded_tickers.append({
                    "ticker": ticker,
                    "reasons": "; ".join(reasons),
                    "missing_dates_count": 0,
                    "missing_dates_sample": "",
                    "invalid_dates": _format_date_list(invalid_dates),
                })
            else:
                # Tolerate minor invalid OHLC
                if inv_count > 0:
                    warnings.append(f"{ticker}: {inv_count} invalid OHLC row(s) tolerated")
                included_tickers.append(ticker)

        base_panel = prices.loc[
            (prices["Date"] >= analysis_start)
            & (prices["Date"] <= analysis_end)
            & (prices["ticker"].isin(included_tickers))
        ].copy()
        base_fx = fx_series.loc[(fx_series["fx_date"] >= analysis_start) & (fx_series["fx_date"] <= analysis_end)].copy()
        panel = _build_adjusted_panel(base_panel, base_fx)
        panel["included_in_base"] = True
        panel["quality_status"] = "included"
        tradable = _rolling_tradable_panel(panel, config) if not panel.empty else pd.DataFrame()

    panel.to_csv(panel_path, index=False)
    tradable.to_csv(tradable_path, index=False)

    summary_payload = {
        "ok": not critical_failures,
        "analysis_start": _as_date(analysis_start),
        "analysis_end": _as_date(analysis_end),
        "price_db_path": str(price_bundle.db_path),
        "price_table": price_bundle.price_table,
        "fx_db_path": str(fx_bundle.db_path),
        "fx_source_table": fx_bundle.source_table,
        "fx_source_kind": fx_bundle.source_kind,
        "desired_tickers": price_bundle.desired_tickers,
        "included_tickers": included_tickers,
        "excluded_tickers": excluded_tickers,
        "critical_failures": critical_failures,
        "warnings": warnings,
        "panel_rows": int(len(panel)),
        "tradable_rows": int(len(tradable)),
        "panel_path": str(panel_path),
        "tradable_path": str(tradable_path),
    }
    summary_path.write_text(json.dumps(summary_payload, indent=2, ensure_ascii=False), encoding="utf-8")

    report_lines = [
        "# 01 Data Quality Report",
        "",
        f"- Gate status: {'PASS' if not critical_failures else 'FAIL'}",
        f"- Price source: `{price_bundle.db_path}` / `{price_bundle.price_table}`",
        f"- FX source: `{fx_bundle.db_path}` / `{fx_bundle.source_table}` ({fx_bundle.source_kind})",
        f"- Base overlap window: `{_as_date(analysis_start)}` → `{_as_date(analysis_end)}`",
        f"- Curated panel: `{panel_path}`",
        f"- Tradable universe by scale: `{tradable_path}`",
        f"- JSON summary: `{summary_path}`",
        "",
        "## Critical failures",
    ]
    report_lines.extend(f"- {item}" for item in critical_failures) if critical_failures else report_lines.append("- none")
    report_lines.extend([
        "",
        "## Warnings",
    ])
    report_lines.extend(f"- {item}" for item in warnings) if warnings else report_lines.append("- none")
    report_lines.extend([
        "",
        "## Included tickers",
        ", ".join(included_tickers) if included_tickers else "_none_",
        "",
        "## Excluded tickers",
    ])
    report_lines.extend(
        _markdown_table(
            excluded_tickers,
            [
                ("ticker", "Ticker"),
                ("reasons", "Reasons"),
                ("missing_dates_count", "Missing dates"),
                ("missing_dates_sample", "Missing date sample"),
                ("invalid_dates", "Invalid dates"),
            ],
        )
    )
    report_lines.extend([
        "",
        "## Deliverables",
        f"- Curated panel rows: `{len(panel)}`",
        f"- Tradable rows: `{len(tradable)}`",
        f"- Universe precalculated by scale: `{sorted(panel['ticker'].unique().tolist()) if not panel.empty else []}`",
    ])
    output_report.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    return AuditArtifacts(
        ok=not critical_failures,
        analysis_start=_as_date(analysis_start),
        analysis_end=_as_date(analysis_end),
        included_tickers=included_tickers,
        excluded_tickers=excluded_tickers,
        critical_failures=critical_failures,
        warnings=warnings,
        report_path=str(output_report),
        summary_path=str(summary_path),
        panel_path=str(panel_path),
        tradable_path=str(tradable_path),
    )
