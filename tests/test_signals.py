from crypto_perp_swing.regime import Regime
from crypto_perp_swing.signals import RegimeAdaptiveStrategy


def test_signal_engine_has_required_contract(bars) -> None:
    regime = bars["close"].map(lambda _: Regime.TREND_UP.value)
    signals = RegimeAdaptiveStrategy().generate(bars, regime)
    assert {"entry_signal", "exit_signal", "stop_price"}.issubset(signals.columns)
    assert set(signals["entry_signal"].dropna().unique()).issubset({-1, 0, 1})

