"""OANDA v20 streaming pricing client — live tail for forex/metal-fx symbols.

Plain requests-based chunked-transfer HTTP stream (see the plan doc for why this
isn't built on oandapyV20: the streaming endpoint is ~30 lines of newline-delimited
JSON over `requests.get(..., stream=True)`, and hand-rolling it keeps full control
over the reconnect/heartbeat-timeout behavior this needs anyway). Runs in its own
daemon thread; never lets an exception escape past the thread — any failure here
just means forex/metals silently keep using yfinance, exactly like before this
integration existed.
"""

import json
import logging
import threading
import time

import pandas as pd
import requests

from . import config
from .symbols import yfinance_to_oanda_instrument

log = logging.getLogger(__name__)

_INITIAL_BACKOFF = 1.0
_MAX_BACKOFF = 60.0
_HEARTBEAT_TIMEOUT = 30.0  # OANDA sends a heartbeat roughly every 5s on an open stream


class OandaStreamer:
    def __init__(self, get_buffer):
        """`get_buffer(symbol)` returns (creating if needed) the LiveBarBuffer for a
        display symbol (e.g. 'EURUSD=X', 'XAUGBP=X') — injected from router.py so
        this module never needs to import router (which imports this module)."""
        self._get_buffer = get_buffer
        self._lock = threading.Lock()
        self._watched: set[str] = set()  # display symbols currently being streamed
        self._instrument_to_symbol: dict[str, str] = {}  # 'EUR_USD' -> 'EURUSD=X'
        self._known_instruments: set[str] | None = None
        self._reconnect_event = threading.Event()
        self._thread: threading.Thread | None = None

    # -- public API ---------------------------------------------------------

    def watch(self, symbol: str) -> None:
        """Adds a display symbol to the watched set. OANDA's pricing stream takes
        its full instrument list at connection-open time (no dynamic subscribe on
        this endpoint), so this forces a reconnect to pick it up promptly rather
        than waiting for the next natural reconnect."""
        instrument = yfinance_to_oanda_instrument(symbol, self._known_instruments)
        if instrument is None:
            return  # not a forex/metal-shaped pair, or not one OANDA actually lists
        with self._lock:
            if symbol in self._watched:
                return
            self._watched.add(symbol)
            self._instrument_to_symbol[instrument] = symbol
        self._reconnect_event.set()

    def start(self) -> None:
        self._thread = threading.Thread(target=self._run, name="oanda-streamer", daemon=True)
        self._thread.start()

    # -- internals ------------------------------------------------------------

    def _rest_host(self) -> str:
        return config.OANDA_REST_HOSTS.get(config.OANDA_ENVIRONMENT, config.OANDA_REST_HOSTS["practice"])

    def _stream_host(self) -> str:
        return config.OANDA_STREAM_HOSTS.get(config.OANDA_ENVIRONMENT, config.OANDA_STREAM_HOSTS["practice"])

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {config.OANDA_API_TOKEN}"}

    def _refresh_known_instruments(self) -> None:
        """Fetched once per process lifetime (an account's tradable-instrument list
        essentially never changes), not on every reconnect — re-fetching on every
        flaky-network reconnect would be a lot of extra REST calls for no real
        benefit. Re-validates the current watch set against the real list, so any
        symbol the app's yfinance-derived guess assumed OANDA covers (but doesn't —
        see symbols.py's docstring) quietly drops back to yfinance instead of being
        requested from a stream that will just reject it."""
        url = f"https://{self._rest_host()}/v3/accounts/{config.OANDA_ACCOUNT_ID}/instruments"
        resp = requests.get(url, headers=self._auth_headers(), timeout=10)
        resp.raise_for_status()
        data = resp.json()
        self._known_instruments = {i["name"] for i in data.get("instruments", [])}
        with self._lock:
            for symbol in list(self._watched):
                instrument = yfinance_to_oanda_instrument(symbol, self._known_instruments)
                if instrument is None:
                    self._watched.discard(symbol)
                    self._instrument_to_symbol = {
                        i: s for i, s in self._instrument_to_symbol.items() if s != symbol
                    }

    def _run(self) -> None:
        backoff = _INITIAL_BACKOFF
        while True:
            try:
                if self._known_instruments is None:
                    self._refresh_known_instruments()
                with self._lock:
                    instruments = list(self._instrument_to_symbol.keys())
                if not instruments:
                    # Nothing to watch yet — wait for watch() rather than opening a
                    # stream with an empty instrument list.
                    self._reconnect_event.wait(timeout=5)
                    self._reconnect_event.clear()
                    continue
                self._reconnect_event.clear()
                self._stream_once(instruments)
                backoff = _INITIAL_BACKOFF  # reset after any clean-ish exit
            except Exception as e:
                log.warning("OANDA stream error, reconnecting in %.0fs: %s", backoff, e)
                self._reconnect_event.wait(timeout=backoff)
                self._reconnect_event.clear()
                backoff = min(backoff * 2, _MAX_BACKOFF)

    def _stream_once(self, instruments: list[str]) -> None:
        url = f"https://{self._stream_host()}/v3/accounts/{config.OANDA_ACCOUNT_ID}/pricing/stream"
        params = {"instruments": ",".join(instruments)}
        last_heartbeat = time.monotonic()
        with requests.get(
            url, headers=self._auth_headers(), params=params, stream=True,
            timeout=(10, _HEARTBEAT_TIMEOUT),
        ) as resp:
            resp.raise_for_status()
            for line in resp.iter_lines():
                if self._reconnect_event.is_set():
                    return  # watch() added a new instrument — reconnect with the fuller list
                if time.monotonic() - last_heartbeat > _HEARTBEAT_TIMEOUT:
                    raise TimeoutError("no OANDA heartbeat received")
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                msg_type = msg.get("type")
                if msg_type == "HEARTBEAT":
                    last_heartbeat = time.monotonic()
                elif msg_type == "PRICE":
                    last_heartbeat = time.monotonic()
                    self._on_price(msg)

    def _on_price(self, msg: dict) -> None:
        symbol = self._instrument_to_symbol.get(msg.get("instrument"))
        if not symbol:
            return
        bids, asks = msg.get("bids") or [], msg.get("asks") or []
        if not bids or not asks:
            return
        try:
            bid = float(bids[0]["price"])
            ask = float(asks[0]["price"])
            ts = pd.Timestamp(msg["time"])  # OANDA sends RFC3339 UTC timestamps
        except (KeyError, ValueError, IndexError, TypeError):
            return
        self._get_buffer(symbol).on_tick(ts, (bid + ask) / 2.0)
