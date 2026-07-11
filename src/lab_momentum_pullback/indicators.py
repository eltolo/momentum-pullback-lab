from __future__ import annotations

import numpy as np
import pandas as pd


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple moving average."""
    return series.rolling(window=period, min_periods=period).mean()


def rsi2(series: pd.Series) -> pd.Series:
    """2-period RSI used for pullback detection."""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.rolling(window=2, min_periods=2).mean()
    avg_loss = loss.rolling(window=2, min_periods=2).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    rsi = 100.0 - (100.0 / (1.0 + rs))
    return rsi


def rolling_return(series: pd.Series, lookback: int) -> pd.Series:
    """Rolling total return over lookback periods."""
    return series / series.shift(lookback) - 1.0


def high_since(series: pd.Series, lookback: int) -> pd.Series:
    """Highest value over lookback periods."""
    return series.rolling(window=lookback, min_periods=1).max()


def close_above_sma(close: pd.Series, period: int) -> pd.Series:
    """Binary: 1 when close > SMA(period)."""
    return (close > sma(close, period)).astype(int)


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range."""
    prev_close = close.shift(1)
    tr = pd.concat([
        (high - low).abs(),
        (high - prev_close).abs(),
        (low - prev_close).abs(),
    ], axis=1).max(axis=1)
    return tr.rolling(window=period, min_periods=period).mean()
