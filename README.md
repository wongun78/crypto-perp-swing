# crypto-perp-swing

Research and paper-trading engine for **BTC/ETH perpetual futures** on a 4H swing horizon.

The first version deliberately favors transparent, testable rules over opaque prediction:

- Daily market regime: trend up, trend down, or range.
- 4H entries: Donchian breakout in trends; Bollinger/RSI mean reversion in ranges.
- Perpetual-aware costs: taker fee, slippage, and funding.
- Risk-first sizing: fixed equity risk, ATR/structure stop, capped effective leverage.
- No live order routing in v0.1.

## Architecture

```text
CSV / exchange adapter
        |
    data validation
        |
Daily regime ------> 4H signal engine
        |                  |
        +--------------> risk sizing
                              |
                  event-driven backtest
                              |
                     metrics + trade log
```

`signal` modules decide *when* to trade. `risk` decides *how large* the trade may be. The
backtester models execution on the following bar, so a signal never trades on information from
the same bar.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
pytest
```

Your CSV must have a timestamp index/column plus `open`, `high`, `low`, `close`, `volume`.
An optional `funding_rate` column is interpreted as the funding rate charged at each 4H bar
(positive funding means longs pay shorts).

```bash
crypto-perp-swing --csv data/BTCUSDT_4h.csv --initial-equity 10000
```

## Risk model

For each entry, position notional is bounded by the smaller of the risk budget and effective
leverage limit:

```text
risk budget = equity × risk_per_trade
loss fraction = |entry - stop| / entry + estimated slippage
risk-based notional = risk budget / loss fraction
max notional = equity × max_leverage × max_margin_fraction
```

Default risk is 1% per trade. A 3x--5x exchange setting is treated as a margin constraint, not
permission to risk 3x--5x more capital.

## Roadmap

1. Validate BTC/ETH historical data and cost assumptions.
2. Walk-forward and parameter-sensitivity tests.
3. Paper-trading adapter and weekly journal.
4. Only after the above: optional order-routing integration.

