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

# Resample rules for every interval a live tail can plausibly serve — kept as a
# small local copy rather than importing app.py's _RESAMPLE_RULES, since app.py
# imports *from* marketdata (not the other way around) and importing back would be
# circular. Deliberately stops at '1d': LiveBarBuffer only holds ~24h of 1-minute
# bars (bar_buffer.py's maxlen), so anything coarser (5d, 1wk, 1mo, ...) can't be
# built correctly from it — get_live_tail declines those rather than serving a bar
# that's silently missing most of its own period.
_RESAMPLE_RULES = {
    "2m": "2min", "5m": "5min", "10m": "10min", "15m": "15min", "30m": "30min",
    "45m": "45min", "60m": "60min", "90m": "90min", "1h": "1h", "2h": "2h", "4h": "4h",
    "1d": "1D",
}
_RESAMPLE_AGG = {"Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"}


def _get_buffer(symbol: str) -> LiveBarBuffer:
    with _buffers_lock:
        buf = _buffers.get(symbol)
        if buf is None:
            buf = LiveBarBuffer()
            _buffers[symbol] = buf
        return buf


def get_live_tail(symbol: str, interval: str, tz=None) -> "pd.DataFrame | None":
    """A single-row OHLCV DataFrame — the current still-forming bar at `interval`
    for `symbol` — or None if not covered / not yet streaming / stale / an interval
    coarser than the buffer can represent. Deliberately a no-op (always None)
    whenever OANDA/Alpaca aren't configured, since `_buffers` only ever gets
    populated by a running streamer.

    `tz` should be the historical series' own tz (e.g. America/New_York for a
    yfinance-sourced df) — only matters for '1d', where bucket *boundaries* are
    meaningful (a day starts at that tz's midnight, not UTC's); resampling in raw
    UTC would label "today's" bar with the wrong calendar date once converted for
    display, landing it as a spurious extra row instead of replacing yfinance's
    stale "today" row. Sub-daily buckets are short enough that this doesn't matter
    — any reasonable tz choice for those just shifts bucket edges by a fixed
    offset, not which day a bar belongs to.

    Only ever returns the single latest bar, never a multi-row tail: the caller
    (app.py's _stitch_live_tail) replaces every historical row from that bar's
    timestamp onward with it, so returning more than one row here would leak
    raw, wrongly-grained bars into a coarser series — e.g. a handful of 1-minute
    rows tacked onto what should be one bar per day. One properly-aggregated
    "current bar so far" is exactly what a live tail should ever contribute; the
    historical fetch already covers everything before it."""
    try:
        category = classify_symbol(symbol)
        if category not in ("forex", "metal-fx", "stock"):
            return None
        if interval != "1m" and interval not in _RESAMPLE_RULES:
            return None
        buf = _buffers.get(symbol)
        if buf is None or buf.is_stale():
            return None
        df = buf.snapshot_df()
        if df is None or df.empty:
            return None
        if interval != "1m":
            if interval == "1d" and tz is not None:
                df = df.tz_convert(tz)
            df = df.resample(_RESAMPLE_RULES[interval]).agg(_RESAMPLE_AGG).dropna(how="all")
            if df.empty:
                return None
        return df.iloc[[-1]]
    except Exception:
        log.exception("get_live_tail failed for %s — falling back to yfinance", symbol)
        return None


def is_symbol_live(symbol: str) -> bool:
    """Whether get_live_tail(symbol, ...) would currently serve a genuine live bar
    for this symbol — i.e. the same condition it already checks, exposed on its own
    so callers (the /api/prices route) can tell users "this is really live" without
    misleadingly badging delayed yfinance data as live. Never raises."""
    try:
        buf = _buffers.get(symbol)
        return buf is not None and not buf.is_stale()
    except Exception:
        return False


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
