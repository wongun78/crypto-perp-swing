from __future__ import annotations

from enum import StrEnum

import pandas as pd

from .config import StrategyConfig
from .features import adx, atr, ema


class Regime(StrEnum):
    TREND_UP = "trend_up"
    TREND_DOWN = "trend_down"
    RANGE = "range"
    HIGH_VOLATILITY = "high_volatility"


class DailyRegimeDetector:
    def __init__(self, config: StrategyConfig = StrategyConfig()) -> None:
        self.config = config

    def predict(self, daily: pd.DataFrame) -> pd.DataFrame:
        indicators = adx(daily, self.config.adx_period)
        result = daily[["close"]].copy()
        result["ema_fast"] = ema(daily["close"], self.config.ema_fast)
        result["ema_slow"] = ema(daily["close"], self.config.ema_slow)
        result["atr"] = atr(daily, self.config.atr_period)
        result = result.join(indicators)
        result["atr_pct"] = result["atr"] / result["close"]
        high_volatility = result["atr_pct"] > result["atr_pct"].rolling(120, min_periods=60).quantile(0.80)
        uptrend = (result["ema_fast"] > result["ema_slow"]) & (result["adx"] >= self.config.trend_adx)
        downtrend = (result["ema_fast"] < result["ema_slow"]) & (result["adx"] >= self.config.trend_adx)
        result["regime"] = Regime.RANGE.value
        result.loc[uptrend, "regime"] = Regime.TREND_UP.value
        result.loc[downtrend, "regime"] = Regime.TREND_DOWN.value
        result.loc[high_volatility & ~(uptrend | downtrend), "regime"] = Regime.HIGH_VOLATILITY.value
        return result


def align_completed_daily_regime(regimes: pd.DataFrame, intraday_index: pd.DatetimeIndex) -> pd.Series:
    """Expose only the previous completed daily decision to intraday bars."""
    completed = regimes["regime"].shift(1)
    return completed.reindex(intraday_index, method="ffill").fillna(Regime.RANGE.value).rename("regime")

