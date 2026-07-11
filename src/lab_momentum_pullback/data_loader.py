from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from .config_loader import load_yaml

ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = Path("/home/tato/proyectos/MPC_Conexar/historico_merval.db")


@dataclass(frozen=True)
class PriceDataBundle:
    config: dict[str, Any]
    db_path: Path
    price_table: str
    desired_tickers: list[str]
    desired_store_tickers: list[str]
    available_store_tickers: list[str]
    missing_desired_tickers: list[str]
    prices: pd.DataFrame


def load_market_config(market: str = "argentina") -> dict[str, Any]:
    return load_yaml(ROOT / "config" / f"{market}.yaml")


def plain_to_store_ticker(ticker: str) -> str:
    ticker = ticker.strip().upper()
    return ticker if "." in ticker else f"{ticker}.BA"


def store_to_plain_ticker(ticker: str) -> str:
    return ticker.split(".")[0].upper()


def _query_dataframe(db_path: Path, sql: str, params: tuple[Any, ...] = ()) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        return pd.read_sql_query(sql, conn, params=params)


def _available_cols(db_path: Path, table: str) -> set[str]:
    with sqlite3.connect(db_path) as conn:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return {row[1] for row in cur.fetchall()}


def load_price_data(market: str = "argentina") -> PriceDataBundle:
    config = load_market_config(market)
    data_config = config.get("data", {})
    db_path = Path(data_config.get("price_db_path", DEFAULT_DB_PATH))
    price_table = data_config.get("price_table", "historico_diario")
    start_date = data_config.get("start_date", "2021-03-29")

    desired_tickers = [str(ticker).upper() for ticker in config.get("universe", [])]
    desired_store_tickers = [plain_to_store_ticker(ticker) for ticker in desired_tickers]

    available = _query_dataframe(
        db_path,
        f"SELECT DISTINCT Ticker FROM {price_table} WHERE Date >= ? ORDER BY Ticker",
        (start_date,),
    )
    available_store_tickers = available["Ticker"].astype(str).tolist()
    available_set = set(available_store_tickers)
    selected_store_tickers = [ticker for ticker in desired_store_tickers if ticker in available_set]
    missing_desired_tickers = [store_to_plain_ticker(ticker) for ticker in desired_store_tickers if ticker not in available_set]

    placeholders = ", ".join("?" for _ in selected_store_tickers) or "''"
    cols_in_table = _available_cols(db_path, price_table)
    select_cols = ["Ticker", "Date", "Open", "High", "Low", "Close", "Adj_Close", "Volume"]
    for extra in ("_source", "_captured_at"):
        if extra in cols_in_table:
            select_cols.append(extra)
    select_expr = ",\n            ".join(select_cols)
    prices = _query_dataframe(
        db_path,
        f"""
        SELECT
            {select_expr}
        FROM {price_table}
        WHERE Date >= ?
          AND Ticker IN ({placeholders})
        ORDER BY Ticker, Date
        """,
        (start_date, *selected_store_tickers),
    )

    if not prices.empty:
        prices["Date"] = pd.to_datetime(prices["Date"], utc=False)
        prices["ticker"] = prices["Ticker"].map(store_to_plain_ticker)
        prices["source_ticker"] = prices["Ticker"]
        prices = prices.rename(
            columns={
                "Open": "open_ars_raw",
                "High": "high_ars_raw",
                "Low": "low_ars_raw",
                "Close": "close_ars_raw",
                "Adj_Close": "adj_close_ars",
                "Volume": "volume",
            }
        )

    return PriceDataBundle(
        config=config,
        db_path=db_path,
        price_table=price_table,
        desired_tickers=desired_tickers,
        desired_store_tickers=desired_store_tickers,
        available_store_tickers=available_store_tickers,
        missing_desired_tickers=missing_desired_tickers,
        prices=prices,
    )
