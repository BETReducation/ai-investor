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


def test_price_level_cross_below_opens_short_at_the_cross_bar():
    df = _df()
    level = float(df["Close"].median())
    trades = run_backtest(df, direction_mode="short", level_price=level, level_cross="below",
                          min_confidence=101, stop_loss_pct=50, take_profit_pct=50)[0]
    assert trades and all(t["side"] == "short" for t in trades)
    closes = df["Close"]
    first = trades[0]["entry_date"]
    i = list(map(str, closes.index)).index(first)
    assert closes.iloc[i - 1] > level >= closes.iloc[i]


def test_price_level_cross_above_opens_long():
    df = _df()
    level = float(df["Close"].median())
    trades = run_backtest(df, direction_mode="long", level_price=level, level_cross="above",
                          min_confidence=101, stop_loss_pct=50, take_profit_pct=50)[0]
    assert trades and all(t["side"] == "long" for t in trades)


def test_reverse_on_stop_flips_into_opposite_side_at_stop_price():
    trades = _run("both", reverse_on_stop=True)
    flips = [(a, b) for a, b in zip(trades, trades[1:])
             if a["exit_reason"] in ("Stop Loss", "Trailing Stop") and b["entry_date"] == a["exit_date"]]
    assert flips
    for a, b in flips:
        assert a["side"] != b["side"] and b["entry_price"] == a["exit_price"]


def test_reverse_on_stop_off_by_default_changes_nothing():
    assert _run("both") == _run("both", reverse_on_stop=False)


_OFF = {"macd_on": 0, "bb_on": 0, "ma_on": 0, "vol_on": 0}
_LONG_SET = {**_OFF, "rsi_trigger": "oversold", "rsi_oversold": 42}
_SHORT_SET = {**_OFF, "rsi_trigger": "overbought", "rsi_overbought": 58}


def _split(**kw):
    return run_backtest(_df(), direction_mode="both", thresholds=_LONG_SET, short_thresholds=_SHORT_SET,
                        min_confidence=50, stop_loss_pct=10, take_profit_pct=10, **kw)[0]


def test_split_rules_longs_only_from_long_set_and_shorts_only_from_short_set():
    trades = _split()
    assert {t["side"] for t in trades} == {"long", "short"}
    for t in trades:
        assert "oversold" in str(t["entry_signals"]) if t["side"] == "long" else "overbought" in str(t["entry_signals"])
    for a, b in zip(trades, trades[1:]):
        assert a["exit_date"] <= b["entry_date"]


def test_split_rules_reverse_into_each_other():
    trades = _split()
    flips = [(a, b) for a, b in zip(trades, trades[1:])
             if a["exit_reason"] == "Signal" and b["entry_date"] == a["exit_date"]]
    assert flips and all(a["side"] != b["side"] for a, b in flips)


def test_split_rules_off_matches_single_set():
    one = run_backtest(_df(), direction_mode="both", thresholds=_LONG_SET, min_confidence=50)[0]
    same = run_backtest(_df(), direction_mode="both", thresholds=_LONG_SET, min_confidence=50, short_match="all")[0]
    assert one == same


def test_costs_default_off_and_reduce_returns_when_set():
    base = _run("both")
    assert all(t["cost_pct"] == 0 for t in base)
    costly = _run("both", fee_pct=0.1, borrow_pct=5.0)
    assert len(costly) == len(base)
    for a, b in zip(base, costly):
        assert b["cost_pct"] >= 0.2 - 1e-9
        assert b["return_pct"] <= a["return_pct"] - 0.19
        if b["side"] == "long":
            assert b["cost_pct"] == pytest.approx(0.2, abs=0.01)
        else:
            assert b["cost_pct"] > 0.2 - 1e-9
