from __future__ import annotations

from typing import Any

import pandas as pd

from .indicators import close_above_sma, rsi2, rolling_return


def compute_signals(
    panel: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Compute signal layers on a panel of daily ticker data.

    Layers applied in order:
    1. Trend filter (price > SMA(slow_sma))
    2. Momentum percentile filter (126d return, rank, keep >= min_percentile)
    3. Pullback (RSI2 < threshold)
    4. Entry confirmation (close > previous high)
    """
    work = panel.copy()
    trend = config.get("trend", {})
    momentum = config.get("momentum", {})
    pullback = config.get("pullback", {})
    confirmation = config.get("confirmation", {})

    slow_period = int(trend.get("slow_sma", 200))
    fast_period = int(trend.get("fast_sma", 50))
    mom_lookback = int(momentum.get("lookback", 126))
    min_percentile = float(momentum.get("min_percentile", 60))
    min_abs_return = float(momentum.get("min_absolute_return", 0.0))
    pb_type = str(pullback.get("type", "RSI2"))
    pb_threshold = float(pullback.get("threshold", 10))
    confirm_type = str(confirmation.get("type", "close_above_previous_high"))

    work = work.sort_values(["ticker", "date"]).reset_index(drop=True)

    # 1. Trend filter
    work["sma_slow"] = work.groupby("ticker")["close_usd_mep_adj"].transform(
        lambda s: s.rolling(window=slow_period, min_periods=slow_period).mean()
    )
    work["sma_fast"] = work.groupby("ticker")["close_usd_mep_adj"].transform(
        lambda s: s.rolling(window=fast_period, min_periods=fast_period).mean()
    )
    work["in_uptrend"] = (work["close_usd_mep_adj"] > work["sma_slow"]).astype(int)

    # 2. Momentum percentile filter
    work["momentum_126d"] = work.groupby("ticker")["close_usd_mep_adj"].transform(
        lambda s: s / s.shift(mom_lookback) - 1.0
    )
    work["mom_rank_pct"] = work.groupby("date")["momentum_126d"].rank(pct=True)
    work["high_momentum"] = (
        (work["mom_rank_pct"] >= min_percentile / 100.0)
        & (work["momentum_126d"] >= min_abs_return)
    ).astype(int)

    # 3. Pullback detection
    if pb_type.upper() == "RSI2":
        work["rsi2"] = work.groupby("ticker")["close_usd_mep_adj"].transform(rsi2)
        work["in_pullback"] = (work["rsi2"] < pb_threshold).astype(int)
    else:
        work["in_pullback"] = 0

    # 4. Entry confirmation
    if confirm_type == "close_above_previous_high":
        work["prev_high"] = work.groupby("ticker")["close_usd_mep_adj"].shift(1)
        work["entry_signal"] = (
            (work["in_uptrend"] == 1)
            & (work["high_momentum"] == 1)
            & (work["in_pullback"] == 1)
            & (work["close_usd_mep_adj"] > work["prev_high"])
        ).astype(int)
    else:
        # Fallback: signal on pullback alone
        work["entry_signal"] = (
            (work["in_uptrend"] == 1)
            & (work["high_momentum"] == 1)
            & (work["in_pullback"] == 1)
        ).astype(int)

    return work


def compute_benchmarks(
    panel: pd.DataFrame,
    config: dict[str, Any],
) -> pd.DataFrame:
    """Compute buy-and-hold benchmark returns.

    Returns a daily DataFrame with:
      - close_ars_raw, close_usd_mep_adj per ticker
      - equal_weight_portfolio_ars, equal_weight_portfolio_usd
    """
    work = panel.copy()
    # Daily returns per ticker
    for col, ret_col in [
        ("close_ars_raw", "ret_ars"),
        ("close_usd_mep_adj", "ret_usd"),
    ]:
        work[ret_col] = work.groupby("ticker")[col].transform(
            lambda s: s.pct_change(fill_method=None)
        )

    # Equal-weight portfolio: average return across tickers per day
    daily = work.groupby("date").agg(
        ret_ars=("ret_ars", "mean"),
        ret_usd=("ret_usd", "mean"),
    )
    daily["cum_ret_ars"] = (1.0 + daily["ret_ars"]).cumprod()
    daily["cum_ret_usd"] = (1.0 + daily["ret_usd"]).cumprod()
    daily["benchmark_type"] = "equal_weight_buy_and_hold"
    return daily.reset_index()
