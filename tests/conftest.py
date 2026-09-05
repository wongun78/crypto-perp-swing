import numpy as np
import pandas as pd
import pytest


@pytest.fixture
def bars() -> pd.DataFrame:
    index = pd.date_range("2024-01-01", periods=300, freq="4h")
    close = pd.Series(100 + np.linspace(0, 30, len(index)) + np.sin(np.arange(len(index)) / 4), index=index)
    return pd.DataFrame(
        {
            "open": close.shift(1).fillna(close.iloc[0]),
            "high": close + 1.5,
            "low": close - 1.5,
            "close": close,
            "volume": 1000.0,
            "funding_rate": 0.0,
        },
        index=index,
    )

