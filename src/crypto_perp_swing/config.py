from dataclasses import dataclass


@dataclass(frozen=True)
class CostConfig:
    """Execution assumptions expressed in basis points."""

    taker_fee_bps: float = 5.0
    slippage_bps: float = 3.0

    @property
    def fee_rate(self) -> float:
        return self.taker_fee_bps / 10_000

    @property
    def slippage_rate(self) -> float:
        return self.slippage_bps / 10_000


@dataclass(frozen=True)
class RiskConfig:
    risk_per_trade: float = 0.01
    max_leverage: float = 3.0
    max_margin_fraction: float = 0.80
    min_notional: float = 25.0


@dataclass(frozen=True)
class StrategyConfig:
    ema_fast: int = 50
    ema_slow: int = 200
    adx_period: int = 14
    trend_adx: float = 20.0
    atr_period: int = 14
    donchian_period: int = 20
    rsi_period: int = 14
    bollinger_period: int = 20
    bollinger_std: float = 2.0
    entry_zscore: float = 2.0
    exit_zscore: float = 0.25
    stop_atr_multiple: float = 2.0


@dataclass(frozen=True)
class BacktestConfig:
    initial_equity: float = 10_000.0
    bars_per_year: int = 6 * 365  # 4H bars

