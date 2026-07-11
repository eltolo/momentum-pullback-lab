from __future__ import annotations

from typing import Any

import pandas as pd

from .indicators import sma


def compute_exits(
    entry_log: pd.DataFrame,
    price_panel: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """For each entry, find the exit date and reason.

    entry_log: columns [date, ticker, entry_price, entry_close_usd]
    price_panel: daily prices with ticker, date, close_usd_mep_adj, sma columns

    Returns: same rows with exit_date, exit_price, exit_reason, holding_days added.
    """
    exit_cfg = config.get("exit", {})
    exit_type = str(exit_cfg.get("type", "close_above_sma"))
    sma_period = int(exit_cfg.get("sma_period", 5))
    max_hold = int(exit_cfg.get("max_holding_days", 15))

    prices = price_panel.copy().sort_values(["ticker", "date"])

    # Precompute exit SMA per ticker
    prices["exit_sma"] = prices.groupby("ticker")["close_usd_mep_adj"].transform(
        lambda s: sma(s, sma_period)
    )

    results = []
    for _, entry in entry_log.iterrows():
        ticker = entry["ticker"]
        entry_date = entry["date"]
        ticker_prices = prices.loc[
            (prices["ticker"] == ticker)
            & (prices["date"] > entry_date)
        ].sort_values("date")

        exit_date = None
        exit_price = None
        exit_reason = None
        holding_days = 0

        for _, row in ticker_prices.iterrows():
            holding_days += 1
            current_date = row["date"]
            current_close = row["close_usd_mep_adj"]

            # Exit condition 1: close_above_sma(5)
            if exit_type == "close_above_sma" and row["exit_sma"] is not None and not pd.isna(row["exit_sma"]):
                if current_close > row["exit_sma"]:
                    exit_date = current_date
                    exit_price = current_close
                    exit_reason = "close_above_sma5"
                    break

            # Exit condition 2: max holding days
            if holding_days >= max_hold:
                exit_date = current_date
                exit_price = current_close
                exit_reason = "max_holding_days"
                break

        if exit_date is None:
            # Use last available price
            if not ticker_prices.empty:
                last = ticker_prices.iloc[-1]
                exit_date = last["date"]
                exit_price = last["close_usd_mep_adj"]
                exit_reason = "end_of_data"
                holding_days = len(ticker_prices)

        results.append({
            "date": entry_date,
            "ticker": ticker,
            "entry_price": entry["entry_price"],
            "entry_close_usd": entry.get("entry_close_usd", entry["entry_price"]),
            "exit_date": exit_date,
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "holding_days": holding_days,
        })

    return pd.DataFrame(results)
