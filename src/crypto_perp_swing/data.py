from __future__ import annotations

import pandas as pd


REQUIRED_COLUMNS = ("open", "high", "low", "close", "volume")


def validate_bars(bars: pd.DataFrame) -> pd.DataFrame:
    """Return a clean OHLCV frame or raise a useful validation error."""
    frame = bars.copy()
    frame.columns = [str(column).lower() for column in frame.columns]
    missing = set(REQUIRED_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing required OHLCV columns: {sorted(missing)}")
    if not isinstance(frame.index, pd.DatetimeIndex):
        raise TypeError("Bars must use a DatetimeIndex.")
    if frame.index.tz is not None:
        frame.index = frame.index.tz_convert("UTC").tz_localize(None)
    frame = frame[~frame.index.duplicated(keep="last")].sort_index()
    if frame.empty:
        raise ValueError("Bars are empty.")
    if frame[list(REQUIRED_COLUMNS)].isna().any().any():
        raise ValueError("OHLCV data contains missing values.")
    if (frame["high"] < frame[["open", "close", "low"]].max(axis=1)).any():
        raise ValueError("High must be at least open, close, and low.")
    if (frame["low"] > frame[["open", "close", "high"]].min(axis=1)).any():
        raise ValueError("Low must be at most open, close, and high.")
    if (frame["volume"] < 0).any():
        raise ValueError("Volume cannot be negative.")
    return frame.astype(float)


def to_daily(bars: pd.DataFrame) -> pd.DataFrame:
    """Resample an already-validated intraday frame to completed daily OHLCV bars."""
    aggregation = {
        "open": "first",
        "high": "max",
        "low": "min",
        "close": "last",
        "volume": "sum",
    }
    if "funding_rate" in bars:
        aggregation["funding_rate"] = "sum"
    daily = bars.resample("1D", label="right", closed="right").agg(aggregation).dropna()
    return validate_bars(daily)


def read_csv(path: str) -> pd.DataFrame:
    """Read a standard OHLCV CSV with `timestamp` or a first-column datetime index."""
    raw = pd.read_csv(path)
    timestamp = "timestamp" if "timestamp" in raw.columns else raw.columns[0]
    raw[timestamp] = pd.to_datetime(raw[timestamp], utc=True)
    raw = raw.set_index(timestamp)
    return validate_bars(raw)

