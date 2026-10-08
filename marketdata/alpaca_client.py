"""Alpaca real-time trade stream client — live tail for US equities/ETFs.

Wraps alpaca.data.live.StockDataStream, whose run() manages its own asyncio event
loop internally (asyncio.run(...) — confirmed via the installed SDK's source), so
it's safe to drive from a plain daemon thread with no extra asyncio setup here.
Subscribing after the stream is already running is explicitly thread-safe on
alpaca-py's side (it schedules the subscribe message onto the stream's own loop via
asyncio.run_coroutine_threadsafe once self._running is True — confirmed via the
installed SDK's _subscribe() source), so watch() can be called directly from
request-handling code with no extra synchronization needed here.
"""

import logging
import threading
import time

import requests

from . import bus, config
from .symbols import yfinance_to_alpaca_symbol

log = logging.getLogger(__name__)

_INITIAL_BACKOFF = 1.0
_MAX_BACKOFF = 60.0

# alpaca-py's StockDataStream.run() manages its own reconnect loop internally and
# swallows/retries an auth failure without ever raising back out to us — so on bad
# credentials it hammers reconnect attempts in a tight loop (no backoff of its own),
# flooding the logs with thousands of "auth failed" tracebacks. A bad key/secret pair
# can't fix itself on the next attempt, so we check auth cheaply via one REST call
# before ever handing control to run()'s internal loop, and back off for a long time
# (not our usual exponential 1-60s) if it's rejected.
_AUTH_CHECK_URL = "https://data.alpaca.markets/v2/stocks/bars"
_AUTH_RECHECK_INTERVAL = 1800.0  # 30 min — no point hammering a dead credential faster

# Separately, "connection limit exceeded" (another connection — e.g. an overlapping
# deploy, or a second environment — already holds this API key's single free-tier
# stream slot) raises the *same* ValueError shape but from inside _run_forever()'s
# main loop, not before it, so the pre-flight REST check above never sees it. Per
# the vendored SDK's _run_forever() (alpaca/data/live/websocket.py — see the
# `except ValueError` branch), only "insufficient subscription" gets treated as
# fatal; every other ValueError, including this one, is logged and retried with
# `await asyncio.sleep(0)` — i.e. no backoff at all, hammering reconnects several
# times a second until whatever's holding the slot lets go. _ConnLimitWatcher below
# taps the SDK's own logger to notice that pattern and forces the stream to stop
# (via the public, thread-safe stop() — confirmed safe to call from another thread)
# so control returns to our _run() loop, which then applies its own real backoff.
_CONN_LIMIT_MSG = "connection limit exceeded"
_CONN_LIMIT_HIT_THRESHOLD = 3   # this many hits inside the window = a real conflict, not a blip
_CONN_LIMIT_WINDOW = 10.0       # seconds
_CONN_LIMIT_BACKOFF = 45.0      # cool-down once detected, so we're not hammering too


class _ConnLimitWatcher(logging.Handler):
    def __init__(self, on_detected):
        super().__init__()
        self._on_detected = on_detected
        self._hits: list[float] = []

    def emit(self, record: logging.LogRecord) -> None:
        try:
            msg = record.getMessage()
        except Exception:
            return
        if _CONN_LIMIT_MSG not in msg:
            return
        now = time.monotonic()
        self._hits = [t for t in self._hits if now - t < _CONN_LIMIT_WINDOW] + [now]
        if len(self._hits) >= _CONN_LIMIT_HIT_THRESHOLD:
            self._hits = []
            self._on_detected()


def _credentials_valid() -> bool:
    try:
        resp = requests.get(
            _AUTH_CHECK_URL,
            params={"symbols": "AAPL", "timeframe": "1Day", "limit": 1},
            headers={
                "APCA-API-KEY-ID": config.ALPACA_API_KEY,
                "APCA-API-SECRET-KEY": config.ALPACA_API_SECRET,
            },
            timeout=10,
        )
        return resp.status_code != 401
    except Exception:
        # A network hiccup on the check itself isn't evidence the credentials are
        # bad — let the normal stream connect attempt (with its own backoff) decide.
        return True


class AlpacaStreamer:
    def __init__(self, get_buffer):
        """`get_buffer(symbol)` returns (creating if needed) the LiveBarBuffer for a
        display symbol (e.g. 'AAPL') — injected from router.py so this module never
        needs to import router (which imports this module)."""
        self._get_buffer = get_buffer
        self._alpaca_to_symbol: dict[str, str] = {}
        self._stream = None
        self._thread: threading.Thread | None = None
        self._conn_limit_hit = threading.Event()

    # -- public API -----------------------------------------------------------

    def watch(self, symbol: str) -> None:
        alpaca_symbol = yfinance_to_alpaca_symbol(symbol)
        if alpaca_symbol in self._alpaca_to_symbol:
            return
        self._alpaca_to_symbol[alpaca_symbol] = symbol
        if self._stream is not None:
            self._stream.subscribe_trades(self._on_trade, alpaca_symbol)

    def unwatch(self, symbol: str) -> None:
        """Removes a display symbol from the watched set (see
        marketdata/router.py's sync_watched_symbols — this is only ever called
        for symbols that mechanism itself watched). unsubscribe_trades() uses
        the same asyncio.run_coroutine_threadsafe pattern subscribe_trades()
        does internally (confirmed via the installed SDK's websocket.py
        _unsubscribe), so this is just as safe to call from a plain thread."""
        alpaca_symbol = next(
            (a for a, s in self._alpaca_to_symbol.items() if s == symbol), None
        )
        if alpaca_symbol is None:
            return
        del self._alpaca_to_symbol[alpaca_symbol]
        if self._stream is not None:
            try:
                self._stream.unsubscribe_trades(alpaca_symbol)
            except Exception:
                log.exception("Alpaca unsubscribe_trades failed for %s", alpaca_symbol)

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="alpaca-streamer", daemon=True)
        self._thread.start()

    # -- internals ------------------------------------------------------------

    async def _on_trade(self, trade) -> None:
        # alpaca-py handlers must be coroutines; this is invoked on the stream's
        # own event loop, never the request-handling thread.
        try:
            symbol = self._alpaca_to_symbol.get(trade.symbol)
            if not symbol:
                return
            price = float(trade.price)
            self._get_buffer(symbol).on_tick(trade.timestamp, price, float(trade.size or 0))
            bus.publish_tick(symbol, trade.timestamp, price)
        except Exception:
            log.exception("Alpaca trade handler failed for %s", getattr(trade, "symbol", "?"))

    def _watch_for_conn_limit(self, stream, done: threading.Event) -> None:
        """Runs on its own thread (never the stream's event-loop thread — stop()'s
        run_coroutine_threadsafe(...).result() would deadlock if called from there)
        for the lifetime of one self._stream.run() call. Forces that stream to stop
        as soon as _ConnLimitWatcher flags repeated "connection limit exceeded"
        hits, so _run()'s own backoff gets a chance to run instead of the SDK's
        internal no-backoff retry."""
        while not done.is_set():
            if self._conn_limit_hit.wait(timeout=1):
                try:
                    stream.stop()
                except Exception:
                    log.exception("Failed to force-stop Alpaca stream after connection-limit hits")
                return

    def _run(self) -> None:
        from alpaca.data.enums import DataFeed
        from alpaca.data.live import StockDataStream

        feed = DataFeed.SIP if config.ALPACA_FEED == "sip" else DataFeed.IEX
        watcher_logger = logging.getLogger("alpaca.data.live.websocket")
        conn_limit_watcher = _ConnLimitWatcher(self._conn_limit_hit.set)
        watcher_logger.addHandler(conn_limit_watcher)
        backoff = _INITIAL_BACKOFF
        try:
            while True:
                if not self._alpaca_to_symbol:
                    # Nothing to watch yet — avoid connecting with zero subscriptions;
                    # wait for watch() to add something.
                    time.sleep(5)
                    continue
                if not _credentials_valid():
                    log.error(
                        "Alpaca API credentials rejected (401) — check ALPACA_API_KEY/"
                        "ALPACA_API_SECRET. Not starting the stream; rechecking in %.0f min.",
                        _AUTH_RECHECK_INTERVAL / 60,
                    )
                    time.sleep(_AUTH_RECHECK_INTERVAL)
                    continue
                self._conn_limit_hit.clear()
                watchdog_done = threading.Event()
                try:
                    self._stream = StockDataStream(config.ALPACA_API_KEY, config.ALPACA_API_SECRET, feed=feed)
                    watchdog = threading.Thread(
                        target=self._watch_for_conn_limit, args=(self._stream, watchdog_done), daemon=True
                    )
                    watchdog.start()
                    for alpaca_symbol in list(self._alpaca_to_symbol.keys()):
                        self._stream.subscribe_trades(self._on_trade, alpaca_symbol)
                    self._stream.run()  # blocks until the connection drops or .stop() is called
                    if self._conn_limit_hit.is_set():
                        log.warning(
                            "Alpaca reported '%s' repeatedly — another connection is likely "
                            "holding this API key's single free-tier stream slot. Backing off "
                            "%.0fs instead of the SDK's own no-backoff retry.",
                            _CONN_LIMIT_MSG, _CONN_LIMIT_BACKOFF,
                        )
                        backoff = max(backoff, _CONN_LIMIT_BACKOFF)
                    else:
                        backoff = _INITIAL_BACKOFF  # reset after any clean-ish exit
                except Exception as e:
                    log.warning("Alpaca stream error, reconnecting in %.0fs: %s", backoff, e)
                finally:
                    self._stream = None
                    watchdog_done.set()
                time.sleep(backoff)
                backoff = min(backoff * 2, _MAX_BACKOFF)
        finally:
            watcher_logger.removeHandler(conn_limit_watcher)


_ALPACA_TIMEFRAME = {"1m": "1Min", "5m": "5Min", "15m": "15Min", "30m": "30Min",
                     "60m": "1Hour", "1h": "1Hour", "1d": "1Day", "1wk": "1Week", "1mo": "1Month"}


def fetch_bars(symbol: str, interval: str, days: int) -> "pd.DataFrame | None":
    """REST history for a US stock/ETF, so the same provider owns both the history and
    the live tail. Split-adjusted only (matches the yfinance auto_adjust=False path).
    UTC-indexed OHLCV frame, or None on any failure/non-coverage so the caller falls
    back to yfinance. Note the free 'iex' feed carries IEX-venue volume only."""
    import pandas as pd
    tf = _ALPACA_TIMEFRAME.get(interval)
    if tf is None or not (config.ALPACA_API_KEY and config.ALPACA_API_SECRET):
        return None
    headers = {"APCA-API-KEY-ID": config.ALPACA_API_KEY, "APCA-API-SECRET-KEY": config.ALPACA_API_SECRET}
    params = {
        "timeframe": tf, "feed": config.ALPACA_FEED, "adjustment": "split", "limit": 10000,
        "start": (pd.Timestamp.now(tz="UTC") - pd.Timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    url = f"https://data.alpaca.markets/v2/stocks/{yfinance_to_alpaca_symbol(symbol)}/bars"
    rows = []
    try:
        for _ in range(10):  # page cap
            resp = requests.get(url, headers=headers, params=params, timeout=10)
            resp.raise_for_status()
            body = resp.json()
            rows.extend(body.get("bars") or [])
            token = body.get("next_page_token")
            if not token:
                break
            params["page_token"] = token
    except Exception:
        log.exception("Alpaca bars fetch failed for %s/%s", symbol, interval)
        return None
    if not rows:
        return None
    df = pd.DataFrame(
        {"Open": [r["o"] for r in rows], "High": [r["h"] for r in rows], "Low": [r["l"] for r in rows],
         "Close": [r["c"] for r in rows], "Volume": [float(r["v"]) for r in rows]},
        index=pd.DatetimeIndex(pd.to_datetime([r["t"] for r in rows], utc=True)),
    )
    # Match yfinance's stock convention (America/New_York; daily bars stamped at local
    # midnight) so _stitch_live_tail's per-tz day buckets line up with these rows.
    df.index = df.index.tz_convert("America/New_York")
    if interval in ("1d", "1wk", "1mo"):
        df.index = df.index.normalize()
    return df
