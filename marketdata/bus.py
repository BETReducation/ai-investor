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


def get_set_members(key: str) -> "set[str] | None":
    """None means 'Redis unavailable, don't touch anything' — distinct from an
    empty set, which legitimately means 'nothing is currently desired'. Used
    for both "watch:desired" (router.py's sync_watched_symbols, Workstream 3)
    and "engine:desired" (app.py's engine worker, Workstream 5) — both are
    realtime/'s refcounted view of what's currently being actively viewed,
    just for two different downstream consumers."""
    client = _get_client()
    if client is None:
        return None
    try:
        members = client.smembers(key)
        return {m.decode() if isinstance(m, bytes) else m for m in members}
    except Exception:
        log.warning("Redis read of %s failed", key, exc_info=True)
        return None


def get_desired_symbols() -> "set[str] | None":
    """"watch:desired" specifically — see get_set_members. router.py's
    sync_watched_symbols() polls this to decide what the OANDA/Alpaca
    streamers should be watching."""
    return get_set_members("watch:desired")


def publish(channel: str, payload: dict) -> None:
    client = _get_client()
    if client is None:
        return
    try:
        client.publish(channel, json.dumps(payload))
    except Exception:
        log.warning("Redis publish to %s failed", channel, exc_info=True)
