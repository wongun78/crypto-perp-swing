from crypto_perp_swing.config import CostConfig, RiskConfig
from crypto_perp_swing.risk import RiskManager


def test_position_risk_is_bounded() -> None:
    manager = RiskManager(RiskConfig(risk_per_trade=0.01, max_leverage=3), CostConfig(slippage_bps=3))
    plan = manager.plan(equity=10_000, entry_price=100, stop_price=98, direction=1)
    assert plan is not None
    assert plan.notional <= 10_000 * 3 * 0.80
    assert plan.expected_loss <= plan.risk_budget * 1.000001


def test_invalid_stop_is_rejected() -> None:
    manager = RiskManager()
    assert manager.plan(10_000, 100, 101, 1) is None

