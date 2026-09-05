from __future__ import annotations

import argparse

from .config import BacktestConfig
from .data import read_csv
from .pipeline import run_research


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the crypto perpetual swing research pipeline.")
    parser.add_argument("--csv", required=True, help="Path to 4H OHLCV CSV.")
    parser.add_argument("--initial-equity", type=float, default=10_000.0)
    args = parser.parse_args()

    bars = read_csv(args.csv)
    result, _, metrics = run_research(bars, backtest=BacktestConfig(initial_equity=args.initial_equity))
    print("Performance metrics")
    for key, value in metrics.items():
        print(f"{key}: {value:.2%}" if "return" in key or "drawdown" in key or "volatility" in key or "cagr" in key else f"{key}: {value:.2f}")
    print(f"trades: {len(result.trades)}")


if __name__ == "__main__":
    main()

