from __future__ import annotations

import numpy as np
import pandas as pd


def performance_metrics(equity_curve: pd.Series, bars_per_year: int = 6 * 365) -> dict[str, float]:
    """Metrics based on a marked-to-market 4H equity curve."""
    returns = equity_curve.pct_change().dropna()
    total_return = equity_curve.iloc[-1] / equity_curve.iloc[0] - 1
    years = max(len(returns) / bars_per_year, 1 / bars_per_year)
    cagr = (equity_curve.iloc[-1] / equity_curve.iloc[0]) ** (1 / years) - 1
    running_peak = equity_curve.cummax()
    drawdown = equity_curve / running_peak - 1
    volatility = returns.std(ddof=0) * np.sqrt(bars_per_year)
    sharpe = np.nan if returns.std(ddof=0) == 0 else returns.mean() / returns.std(ddof=0) * np.sqrt(bars_per_year)
    return {
        "total_return": float(total_return),
        "cagr": float(cagr),
        "max_drawdown": float(drawdown.min()),
        "annualized_volatility": float(volatility),
        "sharpe": float(sharpe),
    }

