from __future__ import annotations

from typing import Any

import pandas as pd

from .indicators import atr, sma


def compute_exits(
    entry_log: pd.DataFrame,
    price_panel: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """For each entry, find the exit date and reason.

    Supports exit types:
    - close_above_sma: exit when close > SMA(period)
    - fixed_days: exit after N holding days
    - trailing_stop_atr: trailing stop at N x ATR from highest close since entry
    """
    exit_cfg = config.get("exit", {})
    exit_type = str(exit_cfg.get("type", "close_above_sma"))
    sma_period = int(exit_cfg.get("sma_period", 5))
    max_hold = int(exit_cfg.get("max_holding_days", 15))
    min_hold = int(exit_cfg.get("min_holding_days", 0))
    atr_multiple = float(exit_cfg.get("trailing_stop_atr", 2.5))
    atr_period = int(exit_cfg.get("atr_period", 14))

    prices = price_panel.copy().sort_values(["ticker", "date"])

    # Precompute indicators
    prices["exit_sma"] = prices.groupby("ticker")["close_usd_mep_adj"].transform(
        lambda s: sma(s, sma_period)
    )
    if exit_type == "trailing_stop_atr":
        prices["atr_14"] = 0.0
        for ticker, grp in prices.groupby("ticker"):
            idx = grp.index
            prices.loc[idx, "atr_14"] = atr(
                grp["high_ars_raw"], grp["low_ars_raw"], grp["close_ars_raw"], atr_period
            ).values

    results = []
    for _, entry in entry_log.iterrows():
        ticker = entry["ticker"]
        entry_date = entry["date"]
        ticker_prices = prices.loc[
            (prices["ticker"] == ticker) & (prices["date"] > entry_date)
        ].sort_values("date")
        entry_price = float(entry["entry_price"])

        exit_date = None
        exit_price = None
        exit_reason = None
        holding_days = 0
        peak = entry_price

        for _, row in ticker_prices.iterrows():
            holding_days += 1
            current_close = float(row["close_usd_mep_adj"])
            close_ars = float(row["close_ars_raw"])
            ratio = current_close / close_ars if close_ars > 0 else 1.0
            # Convert high to USD terms for peak tracking
            current_high = float(row.get("high_ars_raw", close_ars)) * ratio

            # Min holding days barrier
            if holding_days < min_hold:
                continue

            # Exit: close_above_sma(5)
            if exit_type == "close_above_sma" and not pd.isna(row.get("exit_sma")):
                if current_close > float(row["exit_sma"]):
                    exit_date = row["date"]
                    exit_price = current_close
                    exit_reason = "close_above_sma5"
                    break

            # Exit: fixed_days
            if exit_type == "fixed_days" and holding_days >= max_hold:
                exit_date = row["date"]
                exit_price = current_close
                exit_reason = "fixed_days"
                break

            # Exit: trailing_stop_atr
            if exit_type == "trailing_stop_atr" and not pd.isna(row.get("atr_14")):
                atr_usd = float(row["atr_14"]) * ratio
                peak = max(peak, current_high)
                stop_level = peak - atr_usd * atr_multiple
                if current_close < stop_level:
                    exit_date = row["date"]
                    exit_price = current_close
                    exit_reason = "trailing_stop_atr"
                    break

            # Exit: max holding days (universal fallback)
            if holding_days >= max_hold:
                exit_date = row["date"]
                exit_price = current_close
                exit_reason = f"max_holding_{max_hold}d"
                break

        if exit_date is None:
            if not ticker_prices.empty:
                last = ticker_prices.iloc[-1]
                exit_date = last["date"]
                exit_price = float(last["close_usd_mep_adj"])
                exit_reason = "end_of_data"
                holding_days = len(ticker_prices)

        results.append({
            "date": entry_date,
            "ticker": ticker,
            "entry_price": entry_price,
            "entry_close_usd": float(entry.get("entry_close_usd", entry_price)),
            "exit_date": exit_date,
            "exit_price": exit_price,
            "exit_reason": exit_reason,
            "holding_days": holding_days,
        })

    return pd.DataFrame(results)
