import pandas as pd

from crypto_perp_swing.backtest import EventDrivenBacktester


def test_backtest_uses_next_bar_execution(bars) -> None:
    signals = pd.DataFrame(
        {"entry_signal": 0, "exit_signal": False, "stop_price": float("nan")}, index=bars.index
    )
    signals.iloc[20, signals.columns.get_loc("entry_signal")] = 1
    signals.iloc[20, signals.columns.get_loc("stop_price")] = bars.iloc[20]["close"] - 5
    result = EventDrivenBacktester().run(bars, signals)
    assert len(result.trades) == 1
    assert result.trades.iloc[0]["entry_time"] == bars.index[21]
    assert result.trades.iloc[0]["exit_reason"] == "end_of_test"

