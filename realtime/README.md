# realtime/ — async streaming service (Workstream 1/2 spike)

Part of the scaling plan in `../docs/scaling-plan.md`. This is a **spike**,
not production infrastructure yet:

- Only proves the pattern (async transport + Redis fan-out) for the price
  chart's live feed.
- Not wired into the frontend (`static/signal_config.html` still talks to
  the main app's `/api/prices/stream`).
- Not deployed anywhere.
- Doesn't touch the strategy engine, symbol-subscription budgeting, load
  balancing, or load testing — those are separate, later workstreams.

## How it fits together

1. The main app's OANDA/Alpaca streamers (`marketdata/oanda_client.py`,
   `marketdata/alpaca_client.py`) publish every tick to Redis via
   `marketdata/bus.py`, on channel `prices:{SYMBOL}` — but only if `REDIS_URL`
   is set on the main app. If it isn't, this is a total no-op and the main
   app behaves exactly as it does today.
2. This service subscribes to that same Redis channel per active
   `/stream/prices?symbol=...` connection and relays messages to the client
   as SSE — no polling loop, no dependency on the main app's gunicorn thread
   pool.

## Running locally

```
cd realtime
pip install -r requirements.txt
export SECRET_KEY=<same value as the main app's SECRET_KEY>
export REDIS_URL=redis://localhost:6379/0
uvicorn main:app --reload --port 8001
```

You'll also need the main app running with the same `REDIS_URL` and
`SECRET_KEY`, and at least one OANDA/Alpaca-covered symbol actively
streaming, for `/stream/prices` to receive anything.

Auth: this service validates the *same* Flask session cookie the main app
issues (via `flask.sessions.SecureCookieSessionInterface`, same
`SECRET_KEY`) — no separate login exists here. `SECRET_KEY` must match
across both services in every environment, including Railway.

## Deploying (not yet done)

Intended as its own Railway service pointed at this repo with **root
directory set to `realtime/`**, sharing the same `SECRET_KEY` and `REDIS_URL`
env vars as the main app, plus a Railway Redis addon provisioned and shared
between both services. Not provisioned yet — needs a decision on Redis addon
cost/limits before doing this for real (see open questions in
`../docs/scaling-plan.md`).
