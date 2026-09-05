import pandas as pd
import pytest

from crypto_perp_swing.data import validate_bars


def test_validate_bars_rejects_missing_columns() -> None:
    frame = pd.DataFrame({"close": [1]}, index=pd.date_range("2024-01-01", periods=1))
    with pytest.raises(ValueError, match="Missing"):
        validate_bars(frame)


def test_validate_bars_sorts_index(bars) -> None:
    result = validate_bars(bars.iloc[::-1])
    assert result.index.is_monotonic_increasing

