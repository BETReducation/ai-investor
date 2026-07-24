"""Routes /api/prices' live-tail lookups to whichever provider (if any) covers a
symbol, and owns the background streaming threads' lifecycle.

Every public function here is designed to never raise past this module's boundary —
any failure (misconfiguration, provider SDK missing, stream down) is treated
identically to "not covered", and the caller (app.py's _fetch_ohlcv) falls straight
back to its existing pure-yfinance behavior. Nothing here is load-bearing for
correctness; it's a pure optimization layer on top of what already works.
"""

import logging
import threading

import pandas as pd

from . import config
from .bar_buffer import LiveBarBuffer
from .symbols import classify_symbol

log = logging.getLogger(__name__)

_buffers: dict[str, LiveBarBuffer] = {}
_buffers_lock = threading.Lock()

_oanda_streamer = None
_alpaca_streamer = None
_started = False
_started_lock = threading.Lock()

# A handful of resample rules beyond '1m' bars — kept as a small local copy rather
# than importing app.py's _RESAMPLE_RULES, since app.py imports *from* marketdata
# (not the other way around) and importing back would be circular. This table only
# needs to cover intervals a live tail could plausibly be asked for; anything else
# is returned as raw 1-minute bars and left for the caller to handle.
_RESAMPLE_RULES = {
    "2h": "2h", "4h": "4h", "10m": "10min", "45m": "45min", "1h": "1h",
}
_RESAMPLE_AGG = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}


def _get_buffer(symbol: str) -> LiveBarBuffer:
    with _buffers_lock:
        buf = _buffers.get(symbol)
        if buf is None:
            buf = LiveBarBuffer()
            _buffers[symbol] = buf
        return buf


def _resample_for_interval(df: pd.DataFrame, interval: str) -> pd.DataFrame:
    if interval == "1m" or interval not in _RESAMPLE_RULES:
        return df
    return df.resample(_RESAMPLE_RULES[interval]).agg(_RESAMPLE_AGG).dropna(how="all")


def get_live_tail(symbol: str, interval: str) -> "pd.DataFrame | None":
    """A small OHLCV DataFrame of the most recent live bar(s) for `symbol` at
    `interval`, or None if not covered / not yet streaming / stale. Deliberately a
    no-op (always None) whenever OANDA/Alpaca aren't configured, since `_buffers`
    only ever gets populated by a running streamer."""
    try:
        category = classify_symbol(symbol)
        if category not in ("forex", "metal-fx", "stock"):
            return None
        buf = _buffers.get(symbol)
        if buf is None or buf.is_stale():
            return None
        df = buf.snapshot_df()
        if df is None or df.empty:
            return None
        return _resample_for_interval(df, interval)
    except Exception:
        log.exception("get_live_tail failed for %s — falling back to yfinance", symbol)
        return None


def ensure_symbol_watched(symbol: str) -> None:
    """Called after a symbol is added to a watchlist so its stream starts (if a
    covering provider is running) without waiting for the next full restart."""
    try:
        category = classify_symbol(symbol)
        if category in ("forex", "metal-fx") and _oanda_streamer is not None:
            _oanda_streamer.watch(symbol)
        elif category == "stock" and _alpaca_streamer is not None:
            _alpaca_streamer.watch(symbol)
    except Exception:
        log.exception("ensure_symbol_watched failed for %s", symbol)


def start_background_streams(seed_symbols: list[str] | None = None) -> None:
    """Starts each configured provider's background streaming thread. Safe to call
    multiple times (idempotent) and safe to call with neither provider configured
    (does nothing). Must be called once at module load in app.py — see the
    _should_start_background_streams() guard there for why it's not simply called
    unconditionally at import time."""
    global _oanda_streamer, _alpaca_streamer, _started
    with _started_lock:
        if _started:
            return
        _started = True

    seed_symbols = seed_symbols or []

    if config.OANDA_ENABLED:
        try:
            from .oanda_client import OandaStreamer
            _oanda_streamer = OandaStreamer(_get_buffer)
            for sym in seed_symbols:
                if classify_symbol(sym) in ("forex", "metal-fx"):
                    _oanda_streamer.watch(sym)
            _oanda_streamer.start()
            log.info("OANDA streamer started")
        except Exception:
            log.exception("Failed to start OANDA streamer — forex/metals will use yfinance only")

    if config.ALPACA_ENABLED:
        try:
            from .alpaca_client import AlpacaStreamer
            _alpaca_streamer = AlpacaStreamer(_get_buffer)
            for sym in seed_symbols:
                if classify_symbol(sym) == "stock":
                    _alpaca_streamer.watch(sym)
            _alpaca_streamer.start()
            log.info("Alpaca streamer started")
        except Exception:
            log.exception("Failed to start Alpaca streamer — equities will use yfinance only")
