from __future__ import annotations

from dataclasses import asdict, dataclass

import pandas as pd

from .config import BacktestConfig, CostConfig, RiskConfig
from .risk import RiskManager


@dataclass
class OpenPosition:
    direction: int
    quantity: float
    entry_price: float
    stop_price: float
    entry_time: pd.Timestamp
    entry_cost: float
    high_water: float
    low_water: float


@dataclass
class BacktestResult:
    equity_curve: pd.DataFrame
    trades: pd.DataFrame


class EventDrivenBacktester:
    """Single-instrument perpetual simulator with next-bar execution and intrabar stops."""

    def __init__(
        self,
        backtest: BacktestConfig = BacktestConfig(),
        risk: RiskConfig = RiskConfig(),
        costs: CostConfig = CostConfig(),
    ) -> None:
        self.backtest = backtest
        self.costs = costs
        self.risk_manager = RiskManager(risk, costs)

    def run(self, bars: pd.DataFrame, signals: pd.DataFrame) -> BacktestResult:
        required = {"entry_signal", "exit_signal", "stop_price"}
        missing = required - set(signals.columns)
        if missing:
            raise ValueError(f"Signals missing columns: {sorted(missing)}")
        signals = signals.reindex(bars.index).copy()
        cash = self.backtest.initial_equity
        position: OpenPosition | None = None
        records: list[dict] = []
        trades: list[dict] = []

        def execution_price(raw_price: float, direction: int, is_entry: bool) -> float:
            """Apply adverse slippage: buys pay more; sells receive less."""
            sign = direction if is_entry else -direction
            return raw_price * (1 + sign * self.costs.slippage_rate)

        def equity_at(mark: float) -> float:
            if position is None:
                return cash
            return cash + position.direction * position.quantity * (mark - position.entry_price)

        def close_position(timestamp: pd.Timestamp, raw_price: float, reason: str) -> None:
            nonlocal cash, position
            if position is None:
                return
            price = execution_price(raw_price, position.direction, is_entry=False)
            exit_cost = position.quantity * price * self.costs.fee_rate
            gross_pnl = position.direction * position.quantity * (price - position.entry_price)
            cash += gross_pnl - exit_cost
            trades.append(
                {
                    "entry_time": position.entry_time,
                    "exit_time": timestamp,
                    "direction": position.direction,
                    "entry_price": position.entry_price,
                    "exit_price": price,
                    "quantity": position.quantity,
                    "gross_pnl": gross_pnl,
                    "fees": position.entry_cost + exit_cost,
                    "net_pnl": gross_pnl - position.entry_cost - exit_cost,
                    "exit_reason": reason,
                }
            )
            position = None

        for i, (timestamp, bar) in enumerate(bars.iterrows()):
            # Signals are known only after the prior bar has closed.
            prior = signals.iloc[i - 1] if i else None
            if position is not None and prior is not None and bool(prior["exit_signal"]):
                close_position(timestamp, float(bar["open"]), "signal_exit")

            if prior is not None and int(prior["entry_signal"]) in {-1, 1}:
                desired_direction = int(prior["entry_signal"])
                if position is not None and position.direction != desired_direction:
                    close_position(timestamp, float(bar["open"]), "reverse")
                if position is None:
                    stop = float(prior["stop_price"])
                    entry = execution_price(float(bar["open"]), desired_direction, is_entry=True)
                    plan = self.risk_manager.plan(equity_at(entry), entry, stop, desired_direction)
                    if plan is not None:
                        entry_cost = plan.notional * self.costs.fee_rate
                        cash -= entry_cost
                        position = OpenPosition(
                            direction=plan.direction,
                            quantity=plan.quantity,
                            entry_price=plan.entry_price,
                            stop_price=plan.stop_price,
                            entry_time=timestamp,
                            entry_cost=entry_cost,
                            high_water=float(bar["high"]),
                            low_water=float(bar["low"]),
                        )

            if position is not None:
                if position.direction == 1 and float(bar["low"]) <= position.stop_price:
                    close_position(timestamp, position.stop_price, "stop_loss")
                elif position.direction == -1 and float(bar["high"]) >= position.stop_price:
                    close_position(timestamp, position.stop_price, "stop_loss")

            if position is not None and "funding_rate" in bars.columns:
                funding = float(bar["funding_rate"])
                cash -= position.direction * position.quantity * float(bar["close"]) * funding

            if position is not None:
                position.high_water = max(position.high_water, float(bar["high"]))
                position.low_water = min(position.low_water, float(bar["low"]))
            records.append(
                {
                    "timestamp": timestamp,
                    "equity": equity_at(float(bar["close"])),
                    "cash": cash,
                    "position": 0 if position is None else position.direction,
                    "stop_price": float("nan") if position is None else position.stop_price,
                }
            )

        if position is not None:
            close_position(bars.index[-1], float(bars.iloc[-1]["close"]), "end_of_test")
            records[-1]["equity"] = cash
            records[-1]["cash"] = cash
            records[-1]["position"] = 0

        curve = pd.DataFrame(records).set_index("timestamp")
        return BacktestResult(equity_curve=curve, trades=pd.DataFrame([asdict_trade for asdict_trade in trades]))
