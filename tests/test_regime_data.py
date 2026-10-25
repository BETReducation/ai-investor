import json
import pathlib

import pandas as pd

from marketdata.build_regime_data import bond_returns

DATA = pathlib.Path(__file__).resolve().parent.parent / "static/explainers/oil-inflation-regimes/data.js"


def test_bond_flat_yield_returns_one_month_of_coupon():
    y = pd.Series([6.0, 6.0, 6.0])
    r = bond_returns(y)
    assert abs(r.iloc[1] - 0.06 / 12) < 1e-3


def test_bond_loses_when_yields_rise_and_gains_when_they_fall():
    r = bond_returns(pd.Series([5.0, 7.0, 4.0]))
    assert r.iloc[1] < 0 < r.iloc[2]


def test_built_data_is_complete_and_rebased():
    d = json.loads(DATA.read_text()[len("window.REGIME_DATA="):-2])
    for p in d.values():
        n = len(p["months"])
        assert n == 24
        for mode in ("nominal", "real"):
            for series in p[mode].values():
                assert len(series) == n and series[0] == 100
        assert len(p["oil"]) == len(p["cpiYoy"]) == len(p["deflator"]) == n
