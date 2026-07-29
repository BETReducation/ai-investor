"""Workstream 1/2/5 spike (docs/scaling-plan.md): an async streaming service
that proves the async-transport + Redis-fan-out pattern for the price chart's
live feed (/stream/prices) and the strategy engine's live signal feed
(/stream/signals). Deliberately narrow — nothing else has been moved off the
main Flask app, and nothing in the main app depends on this service being up
(marketdata/bus.py's publish calls are no-ops if this service, or Redis,
isn't there).

Requires the main app to be publishing to Redis (REDIS_URL set on the main
app — see marketdata/bus.py and app.py's engine worker) and SECRET_KEY to
match the main app's, so this service can validate the same session cookie.
See README.md for local run + deployment notes.
"""

import asyncio
import hashlib
import json
import logging
import time
from typing import AsyncIterator

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, StreamingResponse

import redis_bus
from auth import user_id_from_session_cookie

log = logging.getLogger(__name__)
app = FastAPI(title="ai-investor realtime (spike)")

# Mirrors /api/prices/stream's own rationale in app.py: short-lived streams
# plus the client's EventSource auto-reconnect, so no single connection is
# held indefinitely and deploys/restarts drain quickly.
STREAM_MAX_SECONDS = 55
HEARTBEAT_SECONDS = 15


@app.get("/healthz")
async def healthz():
    return {"ok": True}


async def _sse_relay(channel: str, desired_set: str, desired_value: str) -> AsyncIterator[str]:
    """Shared body for every refcounted SSE stream this service serves:
    subscribe to `channel`, mark `desired_value` wanted in `desired_set` (see
    redis_bus.mark_wanted) for the life of the connection, relay messages,
    heartbeat when idle, and unmark on disconnect regardless of how it ends."""
    client = redis_bus.get_client()
    pubsub = client.pubsub()
    await pubsub.subscribe(channel)
    await redis_bus.mark_wanted(desired_set, desired_value)
    deadline = time.monotonic() + STREAM_MAX_SECONDS
    yield "retry: 2000\n\n"
    try:
        while time.monotonic() < deadline:
            try:
                msg = await pubsub.get_message(ignore_subscribe_messages=True, timeout=HEARTBEAT_SECONDS)
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("pubsub.get_message failed for %s", channel)
                yield ": err\n\n"
                await asyncio.sleep(1)
                continue
            if msg is None:
                yield ": hb\n\n"
                continue
            yield f"data: {msg['data']}\n\n"
    finally:
        await pubsub.unsubscribe(channel)
        await pubsub.close()
        try:
            await redis_bus.mark_unwanted(desired_set, desired_value)
        except Exception:
            log.exception("mark_unwanted(%s, %s) failed", desired_set, desired_value)


def _sse_response(generator: AsyncIterator[str]) -> StreamingResponse:
    resp = StreamingResponse(generator, media_type="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"
    return resp


@app.get("/stream/prices")
async def stream_prices(request: Request, symbol: str = Query(...)):
    if not user_id_from_session_cookie(request.cookies.get("session")):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    upper_symbol = symbol.upper()
    return _sse_response(_sse_relay(f"prices:{upper_symbol}", "watch:desired", upper_symbol))


@app.get("/stream/signals")
async def stream_signals(
    request: Request,
    symbol: str = Query(...),
    period: str = Query("6mo"),
    interval: str = Query("1d"),
):
    """Mirrors /api/signals' query params exactly, but pushes updates instead
    of being polled. Every param besides symbol/period/interval (calc params,
    scoring thresholds — see app.py's _extract_calc_params/
    _extract_signal_thresholds) is forwarded verbatim as an opaque params
    blob; this service never needs to know which keys mean what, only the
    main app's engine worker does, so the two can never drift on that list.
    """
    if not user_id_from_session_cookie(request.cookies.get("session")):
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    extra_params = {
        k: v for k, v in request.query_params.items() if k not in ("symbol", "period", "interval")
    }
    job = {"symbol": symbol.upper(), "period": period, "interval": interval}
    if extra_params:
        job["params"] = extra_params
    job_json = json.dumps(job, sort_keys=True, separators=(",", ":"))
    # Must match app.py's _engine_job_channel() exactly — that's the other
    # half of this contract.
    channel = "signals:" + hashlib.sha1(job_json.encode()).hexdigest()

    return _sse_response(_sse_relay(channel, "engine:desired", job_json))
