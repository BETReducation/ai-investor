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

from . import config
from .symbols import yfinance_to_alpaca_symbol

log = logging.getLogger(__name__)

_INITIAL_BACKOFF = 1.0
_MAX_BACKOFF = 60.0


class AlpacaStreamer:
    def __init__(self, get_buffer):
        """`get_buffer(symbol)` returns (creating if needed) the LiveBarBuffer for a
        display symbol (e.g. 'AAPL') — injected from router.py so this module never
        needs to import router (which imports this module)."""
        self._get_buffer = get_buffer
        self._alpaca_to_symbol: dict[str, str] = {}
        self._stream = None
        self._thread: threading.Thread | None = None

    # -- public API -----------------------------------------------------------

    def watch(self, symbol: str) -> None:
        alpaca_symbol = yfinance_to_alpaca_symbol(symbol)
        if alpaca_symbol in self._alpaca_to_symbol:
            return
        self._alpaca_to_symbol[alpaca_symbol] = symbol
        if self._stream is not None:
            self._stream.subscribe_trades(self._on_trade, alpaca_symbol)

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
            self._get_buffer(symbol).on_tick(trade.timestamp, float(trade.price), float(trade.size or 0))
        except Exception:
            log.exception("Alpaca trade handler failed for %s", getattr(trade, "symbol", "?"))

    def _run(self) -> None:
        from alpaca.data.enums import DataFeed
        from alpaca.data.live import StockDataStream

        feed = DataFeed.SIP if config.ALPACA_FEED == "sip" else DataFeed.IEX
        backoff = _INITIAL_BACKOFF
        while True:
            if not self._alpaca_to_symbol:
                # Nothing to watch yet — avoid connecting with zero subscriptions;
                # wait for watch() to add something.
                time.sleep(5)
                continue
            try:
                self._stream = StockDataStream(config.ALPACA_API_KEY, config.ALPACA_API_SECRET, feed=feed)
                for alpaca_symbol in list(self._alpaca_to_symbol.keys()):
                    self._stream.subscribe_trades(self._on_trade, alpaca_symbol)
                self._stream.run()  # blocks until the connection drops or .stop() is called
                backoff = _INITIAL_BACKOFF  # reset after any clean-ish exit
            except Exception as e:
                log.warning("Alpaca stream error, reconnecting in %.0fs: %s", backoff, e)
            finally:
                self._stream = None
            time.sleep(backoff)
            backoff = min(backoff * 2, _MAX_BACKOFF)
