from __future__ import annotations

import pandas as pd

from .backtest import BacktestResult, EventDrivenBacktester
from .config import BacktestConfig, CostConfig, RiskConfig, StrategyConfig
from .data import to_daily, validate_bars
from .metrics import performance_metrics
from .regime import DailyRegimeDetector, align_completed_daily_regime
from .signals import RegimeAdaptiveStrategy


def run_research(
    bars: pd.DataFrame,
    strategy: StrategyConfig = StrategyConfig(),
    risk: RiskConfig = RiskConfig(),
    costs: CostConfig = CostConfig(),
    backtest: BacktestConfig = BacktestConfig(),
) -> tuple[BacktestResult, pd.DataFrame, dict[str, float]]:
    clean = validate_bars(bars)
    daily_regime = DailyRegimeDetector(strategy).predict(to_daily(clean))
    aligned_regime = align_completed_daily_regime(daily_regime, clean.index)
    signals = RegimeAdaptiveStrategy(strategy).generate(clean, aligned_regime)
    result = EventDrivenBacktester(backtest, risk, costs).run(clean, signals)
    metrics = performance_metrics(result.equity_curve["equity"], backtest.bars_per_year)
    return result, signals, metrics

