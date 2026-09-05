from __future__ import annotations

import numpy as np
import pandas as pd


def ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False, min_periods=period).mean()


def atr(bars: pd.DataFrame, period: int = 14) -> pd.Series:
    previous_close = bars["close"].shift(1)
    true_range = pd.concat(
        [
            bars["high"] - bars["low"],
            (bars["high"] - previous_close).abs(),
            (bars["low"] - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)
    return true_range.ewm(alpha=1 / period, adjust=False, min_periods=period).mean().rename("atr")


def adx(bars: pd.DataFrame, period: int = 14) -> pd.DataFrame:
    """Wilder-style ADX and directional indicators."""
    up_move = bars["high"].diff()
    down_move = -bars["low"].diff()
    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    smoothed_atr = atr(bars, period)
    plus_di = 100 * plus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / smoothed_atr
    minus_di = 100 * minus_dm.ewm(alpha=1 / period, adjust=False, min_periods=period).mean() / smoothed_atr
    denominator = (plus_di + minus_di).replace(0, np.nan)
    dx = 100 * (plus_di - minus_di).abs() / denominator
    adx_value = dx.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    return pd.DataFrame({"adx": adx_value, "+di": plus_di, "-di": minus_di})


def rsi(close: pd.Series, period: int = 14) -> pd.Series:
    change = close.diff()
    gains = change.clip(lower=0)
    losses = -change.clip(upper=0)
    average_gain = gains.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    average_loss = losses.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    rs = average_gain / average_loss.replace(0, np.nan)
    return (100 - (100 / (1 + rs))).rename("rsi")


def bollinger_zscore(close: pd.Series, period: int = 20) -> pd.DataFrame:
    mean = close.rolling(period, min_periods=period).mean()
    std = close.rolling(period, min_periods=period).std(ddof=0).replace(0, np.nan)
    return pd.DataFrame({"bb_mid": mean, "zscore": (close - mean) / std})


def donchian(bars: pd.DataFrame, period: int = 20) -> pd.DataFrame:
    """Prior-window channel: current bar is excluded to prevent a look-ahead signal."""
    return pd.DataFrame(
        {
            "donchian_high": bars["high"].rolling(period, min_periods=period).max().shift(1),
            "donchian_low": bars["low"].rolling(period, min_periods=period).min().shift(1),
        }
    )

