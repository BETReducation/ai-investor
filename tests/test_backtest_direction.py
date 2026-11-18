import numpy as np
import pandas as pd
import pytest

from api.backtest import run_backtest


def _df(n=400, seed=3):
    rng = np.random.default_rng(seed)
    close = 100 + np.cumsum(rng.normal(0, 1.2, n)) + 8 * np.sin(np.arange(n) / 12)
    idx = pd.date_range("2024-01-01", periods=n, freq="D")
    return pd.DataFrame({"Open": close, "High": close + 1, "Low": close - 1, "Close": close, "Volume": 1000}, index=idx)


def _run(mode, **kw):
    return run_backtest(_df(), direction_mode=mode, min_confidence=50, stop_loss_pct=8, take_profit_pct=8, **kw)[0]


def test_long_mode_has_only_longs():
    trades = _run("long")
    assert trades and {t["side"] for t in trades} == {"long"}


def test_short_mode_has_only_shorts_and_signed_returns():
    trades = _run("short")
    assert trades and {t["side"] for t in trades} == {"short"}
    for t in trades:
        expected = (t["entry_price"] - t["exit_price"]) / t["entry_price"] * 100
        assert t["return_pct"] == pytest.approx(expected, abs=0.02)


def test_both_mode_reverses_and_never_overlaps():
    trades = _run("both")
    assert {t["side"] for t in trades} == {"long", "short"}
    for a, b in zip(trades, trades[1:]):
        assert a["exit_date"] <= b["entry_date"]


def test_short_stops_sit_on_the_right_side():
    for t in _run("short"):
        if t["exit_reason"] == "Stop Loss":
            assert t["exit_price"] > t["entry_price"]
        if t["exit_reason"] == "Take Profit":
            assert t["exit_price"] < t["entry_price"]
