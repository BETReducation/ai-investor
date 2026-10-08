"""Historical crypto candles from Coinbase Exchange's public REST API — no key,
no account, no stream connection, so nothing here can conflict with another
machine. Same contract as oanda_client.fetch_candles: UTC-indexed OHLCV frame, or
None on any failure so the caller falls back to yfinance."""

import logging
import time

import pandas as pd
import requests

log = logging.getLogger(__name__)

_HOST = "https://api.exchange.coinbase.com"
_MAX_PER_REQUEST = 300  # Coinbase's hard cap per /candles call
# yfinance-style interval -> Coinbase granularity in seconds (only the natively supported ones).
GRANULARITY = {"1m": 60, "5m": 300, "15m": 900, "60m": 3600, "1h": 3600, "1d": 86400}


def fetch_candles(symbol: str, interval: str, count: int) -> "pd.DataFrame | None":
    gran = GRANULARITY.get(interval)
    if gran is None or not symbol.upper().endswith("-USD"):
        return None
    product = symbol.upper()
    end = int(time.time())
    rows = {}
    try:
        remaining = count
        while remaining > 0:
            n = min(remaining, _MAX_PER_REQUEST)
            start = end - n * gran
            resp = requests.get(
                f"{_HOST}/products/{product}/candles",
                params={"granularity": gran, "start": pd.Timestamp(start, unit="s").isoformat(),
                        "end": pd.Timestamp(end, unit="s").isoformat()},
                headers={"User-Agent": "gcg-signals"}, timeout=10,
            )
            resp.raise_for_status()
            batch = resp.json()
            if not batch:
                break
            for t, low, high, open_, close, vol in batch:
                rows[t] = {"Open": open_, "High": high, "Low": low, "Close": close, "Volume": vol}
            end = start
            remaining -= n
    except Exception:
        log.exception("Coinbase candles fetch failed for %s/%s", product, interval)
        return None
    if not rows:
        return None
    df = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    df.index = pd.DatetimeIndex(pd.to_datetime(df.index, unit="s", utc=True))
    return df.astype(float)
