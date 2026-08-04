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
import time

import pandas as pd

from . import bus, config
from .bar_buffer import LiveBarBuffer
from .symbols import classify_symbol, yfinance_to_oanda_instrument

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

# yfinance-style native interval -> OANDA candle granularity. Only intervals OANDA's
# /candles endpoint natively serves; anything else (90m, 5d, 3mo, ...) has no entry
# and get_historical_candles declines it, same "not covered" fallback as everywhere
# else in this module. app.py's own _RESAMPLE_INTERVALS resolves synthetic intervals
# (2h, 4h, 10m, 45m, ...) down to one of these native ones before calling in here, and
# resamples the result the same way it already does for the yfinance-sourced leg.
_OANDA_GRANULARITY = {
    "1m": "M1", "2m": "M2", "5m": "M5", "15m": "M15", "30m": "M30",
    "60m": "H1", "1h": "H1", "1d": "D", "1wk": "W", "1mo": "M",
}
_OANDA_GRANULARITY_MINUTES = {
    "M1": 1, "M2": 2, "M5": 5, "M15": 15, "M30": 30,
    "H1": 60, "D": 1440, "W": 10080, "M": 43800,
}
# Rough days-of-history each yfinance period implies — only used to size the OANDA
# "count" request, so approximate is fine; OANDA just returns whatever it actually
# has, capped at its own 5000-candle-per-request ceiling.
_PERIOD_DAYS = {
    "1d": 1, "5d": 5, "60d": 60, "1mo": 31, "3mo": 93, "6mo": 186,
    "1y": 366, "2y": 732, "5y": 1830, "10y": 3660, "ytd": 366, "max": 3660,
}
_OANDA_MAX_CANDLES = 5000


def _estimate_candle_count(period: str, granularity: str) -> int:
    days = _PERIOD_DAYS.get(period, 90)
    minutes_per_candle = _OANDA_GRANULARITY_MINUTES.get(granularity, 1440)
    return max(2, min(_OANDA_MAX_CANDLES, days * 1440 // minutes_per_candle + 2))


def get_historical_candles(symbol: str, interval: str, period: str) -> "pd.DataFrame | None":
    """Real historical OHLC candles for a forex/metal-fx pair straight from OANDA's
    REST API, when OANDA is configured and lists this exact pair — or None on any
    non-coverage/failure (not configured, pair not listed, interval OANDA can't
    serve, request error), so callers fall straight back to their existing
    yfinance-based path exactly like get_live_tail already does. Unlike
    get_live_tail (always the single current still-forming bar, sourced from our
    own streamed tick buffer), this covers the full requested history and returns
    a DataFrame shaped like a yfinance-sourced one: OHLCV columns, UTC
    DatetimeIndex — a drop-in replacement for that leg of _fetch_ohlcv.

    This is what fixes metal-fx symbols (XAU*/XAG*) specifically: Yahoo Finance has
    delisted the real spot quotes for those, so app.py falls back to a COMEX
    futures proxy (GC=F/SI=F) which trades at a basis/contango premium to true spot
    — confirmed live, GC=F ran ~$50-60 above real XAU/USD spot on 2026-07-29. OANDA
    quotes the real cross directly (XAU_USD, XAU_GBP, ...), so using it here
    whenever it's available sidesteps that premium entirely instead of only
    patching the most-recent bar the way get_live_tail's stitch does."""
    try:
        if classify_symbol(symbol) not in ("forex", "metal-fx"):
            return None
        granularity = _OANDA_GRANULARITY.get(interval)
        if granularity is None:
            return None
        instrument = yfinance_to_oanda_instrument(symbol)
        if instrument is None:
            return None
        from .oanda_client import fetch_candles
        count = _estimate_candle_count(period, granularity)
        return fetch_candles(instrument, granularity, count)
    except Exception:
        log.exception("get_historical_candles failed for %s", symbol)
        return None


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
            # subset=["Close"]: resampling to daily-or-coarser buckets can span a gap
            # (e.g. a weekend, or any period with no ticks) and produce an empty
            # calendar-day row — Volume sums to 0 (not NaN) for those, so dropna's
            # default how="all" doesn't remove them, and a resulting empty row landing
            # last (picked by iloc[[-1]] below) sent a literal NaN Close into the chart
            # JSON, which isn't valid strict JSON and broke chart loading client-side.
            df = df.resample(_RESAMPLE_RULES[interval]).agg(_RESAMPLE_AGG).dropna(subset=["Close"])
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


# Symbols currently watched because marketdata.bus's Redis-backed refcount
# (see get_desired_symbols) asked for them — tracked separately from
# ensure_symbol_watched's older call sites so sync_watched_symbols() only
# ever unwatches a symbol *it* watched, never one requested through the
# permanent-once-watched legacy path. Purely additive: with REDIS_URL unset,
# get_desired_symbols() returns None, sync_watched_symbols() no-ops, and
# nothing here is ever touched.
_refcount_watched: set[str] = set()
_SYNC_INTERVAL_SECONDS = 5


def sync_watched_symbols() -> None:
    """Reconciles the streamers' watch sets against Redis's 'watch:desired'
    set — the realtime/ service's live count of which symbols have >=1
    connected SSE viewer. Runs on a timer rather than reacting to Redis
    events: a few seconds of staleness costs nothing (both providers already
    tolerate a "not yet watching" gap right after watch() — see
    start_background_streams' own seed-symbol handling), and a poll loop is
    far simpler to reason about than mutating two long-lived streaming
    connections from an event callback."""
    global _refcount_watched
    desired = bus.get_desired_symbols()
    if desired is None:
        return
    for symbol in desired - _refcount_watched:
        category = classify_symbol(symbol)
        if category in ("forex", "metal-fx") and _oanda_streamer is not None:
            _oanda_streamer.watch(symbol)
        elif category == "stock" and _alpaca_streamer is not None:
            _alpaca_streamer.watch(symbol)
    for symbol in _refcount_watched - desired:
        category = classify_symbol(symbol)
        if category in ("forex", "metal-fx") and _oanda_streamer is not None:
            _oanda_streamer.unwatch(symbol)
        elif category == "stock" and _alpaca_streamer is not None:
            _alpaca_streamer.unwatch(symbol)
    _refcount_watched = desired


def _sync_watched_symbols_loop() -> None:
    while True:
        try:
            sync_watched_symbols()
        except Exception:
            log.exception("sync_watched_symbols failed")
        time.sleep(_SYNC_INTERVAL_SECONDS)


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

    if config.REDIS_URL and (_oanda_streamer is not None or _alpaca_streamer is not None):
        threading.Thread(target=_sync_watched_symbols_loop, name="watch-sync", daemon=True).start()
        log.info("Redis-backed watch-symbol sync started")
