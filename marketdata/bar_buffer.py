"""Aggregates a stream of ticks into 1-minute OHLCV bars, per symbol.

OANDA/Alpaca's streams deliver ticks, not bars — this bridges that into the same
bar shape /api/prices already returns, so nothing downstream needs to change.
"""

import collections
import threading
import time

import pandas as pd


class LiveBarBuffer:
    """One instance per symbol. Thread-safe via a per-instance lock; hold times are
    microseconds (dict mutation only), so a lock per symbol (rather than one global
    lock shared across every symbol) costs essentially nothing while avoiding any
    chance of unrelated symbols blocking each other."""

    def __init__(self, maxlen_minutes: int = 1440):  # ~24h of 1-minute bars
        self._lock = threading.Lock()
        self._completed = collections.deque(maxlen=maxlen_minutes)
        self._current_bucket_ts = None
        self._current_bar = None
        self.last_tick_at: float | None = None  # time.monotonic(), for staleness checks

    def on_tick(self, ts, price: float, size: float = 0.0) -> None:
        bucket = pd.Timestamp(ts).floor("min")
        with self._lock:
            self.last_tick_at = time.monotonic()
            if bucket != self._current_bucket_ts:
                if self._current_bar is not None:
                    self._completed.append((self._current_bucket_ts, self._current_bar))
                self._current_bucket_ts = bucket
                self._current_bar = {"Open": price, "High": price, "Low": price, "Close": price, "Volume": size}
            else:
                bar = self._current_bar
                if price > bar["High"]:
                    bar["High"] = price
                if price < bar["Low"]:
                    bar["Low"] = price
                bar["Close"] = price
                bar["Volume"] += size

    def snapshot_df(self) -> "pd.DataFrame | None":
        """Completed bars plus the still-forming current bar as the trailing row —
        the same 'always partial' semantics the yfinance-sourced trailing bar already
        has today (today's daily bar, or the current 1m/5m bar, is never finalized)."""
        with self._lock:
            if self._current_bar is None and not self._completed:
                return None
            rows = list(self._completed)
            if self._current_bar is not None:
                rows.append((self._current_bucket_ts, dict(self._current_bar)))
        idx = pd.DatetimeIndex([r[0] for r in rows])
        return pd.DataFrame([r[1] for r in rows], index=idx)

    def is_stale(self, max_age_seconds: float = 60.0) -> bool:
        return self.last_tick_at is None or (time.monotonic() - self.last_tick_at) > max_age_seconds
