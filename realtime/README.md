# realtime/ — async streaming service (Workstreams 1/2/3/5/6)

Part of the scaling plan in `../docs/scaling-plan.md`. All code below is
written and unit-tested against mocks/fakes — **none of it is deployed
anywhere yet.** Deploying it means provisioning a paid Railway service and
Redis addon; see `../docs/scaling-plan.md`'s Status section for why that's
being held back pending an explicit cost decision, separate from the code
itself being done.

## Endpoints

- `GET /stream/prices?symbol=...` — live price chart feed. Relays
  `prices:{SYMBOL}` from Redis, published by the main app's OANDA/Alpaca
  streamers (`marketdata/bus.py`) whenever `REDIS_URL` is set there.
- `GET /stream/signals?symbol=...&period=...&interval=...&<scoring/calc params>`
  — live strategy-engine feed, mirrors `/api/signals`' query params exactly.
  Relays a Redis channel published by the main app's `_engine_worker_loop`
  (app.py), which recomputes indicators once per distinct (symbol, period,
  interval, calc_params) — shared across every viewer using those params —
  and scores each viewer's own thresholds individually, so per-user strategy
  customization is preserved even though the expensive part is shared.
- `GET /healthz`

Both streaming endpoints require the same Flask-Login session cookie the
main app issues (`SECRET_KEY` must match across both services) and both use
a Redis-backed refcount (`redis_bus.mark_wanted`/`mark_unwanted`) so the main
app only keeps a symbol/job "hot" while at least one viewer is actually
watching it — see `marketdata/router.py`'s `sync_watched_symbols()` and
app.py's `_engine_worker_tick()` for the two consumers of that signal.

## Running locally

```
cd realtime
pip install -r requirements.txt
export SECRET_KEY=<same value as the main app's SECRET_KEY>
export REDIS_URL=redis://localhost:6379/0
uvicorn main:app --reload --port 8001
```

You'll also need the main app running with the same `REDIS_URL` and
`SECRET_KEY` (`python app.py`), and at least one OANDA/Alpaca-covered symbol
actively streaming, for `/stream/prices` to receive anything — or a running
strategy engine for `/stream/signals`.

Auth: this service validates the *same* Flask session cookie the main app
issues (via `flask.sessions.SecureCookieSessionInterface`, same
`SECRET_KEY`) — no separate login exists here.

## Load testing

`loadtest.py` opens N concurrent SSE connections and reports connect
latency, time-to-first-message, and error counts (client-side only — watch
the server's own CPU/memory separately). Needs a real session cookie and
`pip install aiohttp` (deliberately not in requirements.txt — dev-only
tool). See the script's own docstring for usage. Smoke-tested against a
local fake server; not yet run against this service for real.

## Deploying (not yet done — costs money, needs explicit go-ahead)

Intended as its own Railway service pointed at this repo with **root
directory set to `realtime/`**, sharing `SECRET_KEY` and `REDIS_URL` with the
main app, plus a Railway Redis addon provisioned and shared between both
services. The main app also needs `REALTIME_BASE_URL` set to this service's
public URL once it exists (see app.py's `/api/me` and
`static/signal_config.html`'s `checkTier()` — that's what flips the frontend
from polling to SSE). Not provisioned yet — needs a decision on Redis addon
cost/limits and the second Railway service's cost before doing this for real
(see open questions in `../docs/scaling-plan.md`).
