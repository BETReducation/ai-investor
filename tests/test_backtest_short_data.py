import numpy as np
import pandas as pd
import pytest

from api.backtest import run_backtest


def test_too_few_candles_raises_clear_error():
    idx = pd.date_range("2026-01-01", periods=20, freq="4h")
    close = np.linspace(100, 110, 20)
    df = pd.DataFrame({"Open": close, "High": close + 1, "Low": close - 1, "Close": close, "Volume": 1000}, index=idx)
    with pytest.raises(ValueError, match="Not enough data"):
        run_backtest(df)
