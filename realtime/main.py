"""Workstream 1/2 spike (docs/scaling-plan.md): an async streaming service that
proves the async-transport + Redis-fan-out pattern for the price chart's SSE
feed. Deliberately narrow — only /stream/prices exists so far, nothing else
has been moved off the main Flask app, and nothing in the main app depends on
this service being up (marketdata/bus.py's publish is a no-op if this
service, or Redis, isn't there).

Requires the main app's OANDA/Alpaca streamers to be publishing ticks to
Redis (REDIS_URL set on the main app — see marketdata/bus.py) and SECRET_KEY
to match the main app's, so this service can validate the same session
cookie. See README.md for local run + deployment notes.
"""

import asyncio
import json
import logging
import time

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


@app.get("/stream/prices")
async def stream_prices(request: Request, symbol: str = Query(...)):
    user_id = user_id_from_session_cookie(request.cookies.get("session"))
    if not user_id:
        return JSONResponse({"error": "unauthorized"}, status_code=401)

    channel = f"prices:{symbol.upper()}"

    async def generate():
        client = redis_bus.get_client()
        pubsub = client.pubsub()
        await pubsub.subscribe(channel)
        deadline = time.monotonic() + STREAM_MAX_SECONDS
        yield "retry: 2000\n\n"
        try:
            while time.monotonic() < deadline:
                try:
                    msg = await pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=HEARTBEAT_SECONDS
                    )
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

    resp = StreamingResponse(generate(), media_type="text/event-stream")
    resp.headers["Cache-Control"] = "no-cache"
    resp.headers["X-Accel-Buffering"] = "no"
    return resp
