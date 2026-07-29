"""Optional Redis publish bridge for the realtime/ scaling spike (see
docs/scaling-plan.md, Workstreams 1-2).

Presence of REDIS_URL is the on/off switch, same pattern as every other
optional integration in this package (config.py). Publishing here is a pure
side channel on top of the existing OANDA/Alpaca -> LiveBarBuffer tick path —
it never affects /api/prices or /api/prices/stream, and any failure here
(no REDIS_URL, Redis unreachable, publish error) is swallowed so it can never
take down the streamers it's attached to.
"""

import json
import logging

from . import config

log = logging.getLogger(__name__)

_client = None
_client_checked = False


def _get_client():
    global _client, _client_checked
    if _client_checked:
        return _client
    _client_checked = True
    if not config.REDIS_URL:
        return None
    try:
        import redis
        client = redis.from_url(config.REDIS_URL, socket_connect_timeout=5)
        client.ping()
        _client = client
    except Exception:
        log.exception("Failed to connect to Redis — tick publishing disabled")
        _client = None
    return _client


def publish_tick(symbol: str, ts, price: float) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        payload = json.dumps({"symbol": symbol.upper(), "time": str(ts), "price": price})
        client.publish(f"prices:{symbol.upper()}", payload)
    except Exception:
        log.warning("Redis publish failed for %s", symbol, exc_info=True)
