"""Builds static/explainers/oil-inflation-regimes/data.js.

Monthly data for two oil-shock / high-inflation windows (1973-74 and 2008-09):
stocks, bonds and gold rebased to 100 at the start (nominal and CPI-adjusted),
plus WTI oil and CPI inflation. One-off historical build, not a live feed.

Needs pandas, curl and xlrd (Shiller's file is a legacy .xls):
    python marketdata/build_regime_data.py
"""
import io
import json
import pathlib
import subprocess

import pandas as pd

OUT = pathlib.Path(__file__).resolve().parent.parent / "static/explainers/oil-inflation-regimes/data.js"
FRED = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
SHILLER = "http://www.econ.yale.edu/~shiller/data/ie_data.xls"
GOLD = "https://raw.githubusercontent.com/datasets/gold-prices/main/data/monthly.csv"

WINDOWS = {
    "1973": ("1973-01", "1974-12"),
    "2008": ("2008-01", "2009-12"),
}


def get(url):
    # curl rather than requests: FRED's server reliably stalls python-requests connections here
    return subprocess.run(["curl", "-sfL", "--retry", "3", "-m", "60", url], check=True, capture_output=True).stdout


def fred(series):
    df = pd.read_csv(io.BytesIO(get(FRED.format(series))), na_values=".")
    df.index = pd.PeriodIndex(df.iloc[:, 0], freq="M")
    return pd.to_numeric(df.iloc[:, 1], errors="coerce")


def shiller_stocks():
    raw = pd.read_excel(io.BytesIO(get(SHILLER)), sheet_name="Data", header=None, skiprows=8, engine="xlrd")
    raw = raw.iloc[:, :3]
    raw.columns = ["date", "price", "div"]
    raw = raw[pd.to_numeric(raw["date"], errors="coerce").notna()]
    # dates arrive as floats like 1973.1 for October, so rebuild from the string with 2-digit months
    raw["date"] = raw["date"].map(lambda d: f"{d:.2f}")
    raw.index = pd.PeriodIndex(raw["date"].str.replace(".", "-", regex=False), freq="M")
    price = pd.to_numeric(raw["price"])
    div = pd.to_numeric(raw["div"])
    # monthly total return: price change plus one twelfth of the annual dividend, reinvested
    ret = (price + div / 12) / price.shift(1) - 1
    return ret


def bond_returns(y):
    """Total return on a constant-maturity 10-year par bond bought each month at the prior month's yield."""
    n = 10 - 1 / 12
    c = y.shift(1) / 100
    y1 = y / 100
    price = c * (1 - (1 + y1) ** -n) / y1 + (1 + y1) ** -n
    return price - 1 + c / 12


def gold_series():
    df = pd.read_csv(io.BytesIO(get(GOLD)))
    df.index = pd.PeriodIndex(df["Date"], freq="M")
    return df["Price"]


def rebase(ret, months):
    r = ret.reindex(months).copy()
    r.iloc[0] = 0.0
    return 100 * (1 + r).cumprod()


def rd(s, n=2):
    return [None if pd.isna(v) else round(float(v), n) for v in s]


def main():
    oil, cpi, gs10, gold = fred("WTISPLC"), fred("CPIAUCSL"), fred("GS10"), gold_series()
    stock_ret = shiller_stocks()
    bond_ret = bond_returns(gs10)
    yoy = cpi.pct_change(12) * 100

    out = {}
    for key, (a, b) in WINDOWS.items():
        months = pd.period_range(a, b, freq="M")
        deflator = cpi.reindex(months) / cpi.reindex(months).iloc[0]
        nominal = {
            "stocks": rebase(stock_ret, months),
            "bonds": rebase(bond_ret, months),
            "gold": 100 * gold.reindex(months) / gold.reindex(months).iloc[0],
        }
        out[key] = {
            "months": [str(m) for m in months],
            "nominal": {k: rd(v) for k, v in nominal.items()},
            "real": {k: rd(v / deflator) for k, v in nominal.items()},
            "deflator": rd(deflator, 4),
            "oil": rd(oil.reindex(months)),
            "cpiYoy": rd(yoy.reindex(months), 1),
        }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text("window.REGIME_DATA=" + json.dumps(out, separators=(",", ":")) + ";\n")
    print("wrote", OUT)


if __name__ == "__main__":
    main()
