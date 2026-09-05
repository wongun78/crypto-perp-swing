from __future__ import annotations

import pandas as pd

from .config import StrategyConfig
from .features import atr, bollinger_zscore, donchian, rsi
from .regime import Regime


class RegimeAdaptiveStrategy:
    """Trend breakout in directional regimes; mean reversion only in ranges."""

    def __init__(self, config: StrategyConfig = StrategyConfig()) -> None:
        self.config = config

    def generate(self, bars: pd.DataFrame, regime: pd.Series) -> pd.DataFrame:
        output = pd.DataFrame(index=bars.index)
        output["regime"] = regime.reindex(bars.index).fillna(Regime.RANGE.value)
        output = output.join(donchian(bars, self.config.donchian_period))
        output["atr"] = atr(bars, self.config.atr_period)
        output["rsi"] = rsi(bars["close"], self.config.rsi_period)
        output = output.join(bollinger_zscore(bars["close"], self.config.bollinger_period))
        output["entry_signal"] = 0
        output["exit_signal"] = False
        output["stop_price"] = float("nan")

        long_breakout = (output["regime"] == Regime.TREND_UP.value) & (bars["close"] > output["donchian_high"])
        short_breakout = (output["regime"] == Regime.TREND_DOWN.value) & (bars["close"] < output["donchian_low"])
        long_reversion = (
            (output["regime"] == Regime.RANGE.value)
            & (output["zscore"] <= -self.config.entry_zscore)
            & (output["rsi"] < 35)
        )
        short_reversion = (
            (output["regime"] == Regime.RANGE.value)
            & (output["zscore"] >= self.config.entry_zscore)
            & (output["rsi"] > 65)
        )

        output.loc[long_breakout | long_reversion, "entry_signal"] = 1
        output.loc[short_breakout | short_reversion, "entry_signal"] = -1
        output.loc[output["entry_signal"] == 1, "stop_price"] = (
            bars["close"] - self.config.stop_atr_multiple * output["atr"]
        )
        output.loc[output["entry_signal"] == -1, "stop_price"] = (
            bars["close"] + self.config.stop_atr_multiple * output["atr"]
        )

        range_exit = (output["regime"] == Regime.RANGE.value) & (
            output["zscore"].abs() <= self.config.exit_zscore
        )
        trend_exit = ((output["regime"] == Regime.TREND_UP.value) & (bars["close"] < output["donchian_low"])) | (
            (output["regime"] == Regime.TREND_DOWN.value) & (bars["close"] > output["donchian_high"])
        )
        output.loc[range_exit | trend_exit, "exit_signal"] = True
        return output

