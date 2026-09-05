from __future__ import annotations

from dataclasses import dataclass

from .config import CostConfig, RiskConfig


@dataclass(frozen=True)
class PositionPlan:
    direction: int
    entry_price: float
    stop_price: float
    quantity: float
    notional: float
    initial_margin: float
    risk_budget: float
    expected_loss: float


class RiskManager:
    def __init__(self, risk: RiskConfig = RiskConfig(), costs: CostConfig = CostConfig()) -> None:
        self.risk = risk
        self.costs = costs

    def plan(self, equity: float, entry_price: float, stop_price: float, direction: int) -> PositionPlan | None:
        if equity <= 0 or entry_price <= 0 or direction not in {-1, 1}:
            return None
        stop_distance = (entry_price - stop_price) * direction
        if stop_distance <= 0:
            return None
        risk_budget = equity * self.risk.risk_per_trade
        loss_fraction = (stop_distance / entry_price) + self.costs.slippage_rate
        risk_based_notional = risk_budget / loss_fraction
        leverage_cap_notional = equity * self.risk.max_leverage * self.risk.max_margin_fraction
        notional = min(risk_based_notional, leverage_cap_notional)
        if notional < self.risk.min_notional:
            return None
        quantity = notional / entry_price
        expected_loss = quantity * stop_distance + notional * self.costs.slippage_rate
        return PositionPlan(
            direction=direction,
            entry_price=entry_price,
            stop_price=stop_price,
            quantity=quantity,
            notional=notional,
            initial_margin=notional / self.risk.max_leverage,
            risk_budget=risk_budget,
            expected_loss=expected_loss,
        )

