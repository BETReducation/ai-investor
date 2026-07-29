# Scaling to 1000 simultaneous streaming users

Goal: 1000 users can each hold an open live-streaming session (price chart, and
eventually the strategy engine) without thread exhaustion on the main app,
degraded latency on unrelated routes, or 502s — verified by load test, not
assumed.

## Why the current design can't get there

`/api/prices/stream` (app.py) is a per-connection loop that holds one gunicorn
thread for the life of the connection (~55s, then the client reconnects). The
Procfile runs `gunicorn --worker-class gthread --threads 16 --timeout 120`,
i.e. one worker × 16 threads. A handful of concurrent streams is fine; anywhere
near 1000 concurrent streams is not — every other route (login, backtester,
signals) shares that same limited thread pool, so the site degrades and
eventually times out for everyone, not just streaming users.

## The two problems, and why they need different fixes

1. **Connection-holding at scale** (I/O-bound): holding thousands of long-lived
   connections cheaply needs an async runtime (coroutines, not OS threads) —
   this is what Workstream 1 addresses.
2. **Fan-out across instances** (once you horizontally scale the streaming
   service): every replica shouldn't independently open its own OANDA/Alpaca
   connection for the same symbols — this is what the Redis pub/sub layer in
   Workstream 2 addresses.
3. **Compute at scale** (CPU-bound, relevant once the strategy engine is wired
   in): indicator recomputation should scale with the number of *distinct
   symbols* being watched, not the number of *users* watching them — this is a
   separate concern from 1 and 2, addressed in Workstream 5.

## Workstreams

1. **Async streaming service.** A small, separate async service (FastAPI/
   uvicorn) that owns only the real-time endpoints. Everything else (pages,
   auth, backtester, REST routes) stays on the existing Flask/gunicorn app,
   untouched. The async service validates the existing Flask session cookie
   rather than duplicating auth. Deployed as its own Railway service, not a
   second process bolted onto the existing one.

2. **Redis pub/sub fan-out.** The OANDA/Alpaca streamers keep their current
   single-connection-per-provider design unchanged, but also publish ticks to
   Redis channels. The async service subscribes and fans out to connected
   clients. This is what lets the async service run multiple replicas without
   each one opening a duplicate upstream provider connection.

3. **Symbol-subscription budgeting.** Open question, potentially blocking:
   Alpaca/OANDA's per-connection symbol and rate limits need verifying. Build
   reference-counted watch/unwatch — a symbol stays subscribed only while ≥1
   active user is watching it.

4. **Horizontal scaling + load balancing.** Multiple replicas of the async
   service behind a load balancer that correctly holds long-lived SSE/
   WebSocket connections — needs verifying on Railway specifically.

5. **Wire the strategy engine onto the stream.** Move engine evaluation off
   the polling loop onto the live-tick pipeline. Indicator computation stays
   server-side Python. Throttle recompute per-symbol (e.g. on bar-close, not
   every tick) so CPU cost scales with distinct symbols, not user count.

6. **Load testing.** Synthetic test opening ~1000 concurrent SSE connections,
   measuring connection-hold overhead, memory, and latency. Nothing above is
   considered done until this confirms it holds.

## Sequencing

1. Spike: async service + Redis pub/sub for chart SSE only, single instance,
   no load balancer — prove the pattern end to end. **(this branch)**
2. Symbol-subscription budgeting.
3. Horizontal scaling + LB, load test toward 1000.
4. Wire the engine onto the same pipeline, add compute throttling.
5. Re-run the load test with the engine active.

## Status

All code below is written, unit-tested against mocks/fakes, and merged to
`main` — **none of it is deployed**. `REDIS_URL` and `REALTIME_BASE_URL` are
unset in every environment today, and every piece of this is designed to be
a no-op until they're set (same presence-as-flag pattern as the rest of
`marketdata/config.py`), so nothing about the live app has changed yet.

- [x] Workstream 1/2: `realtime/` async service + Redis-bridged chart SSE.
      See `realtime/README.md`.
- [x] Workstream 3: symbol-subscription budgeting. Reference-counted
      watch/unwatch (`OandaStreamer.unwatch`/`AlpacaStreamer.unwatch`,
      `router.sync_watched_symbols`) driven by realtime/'s per-connection
      refcount in Redis (`watch:desired`). Verified against fake streamers —
      watches new symbols, unwatches dropped ones, no-ops with no Redis.
- [x] Workstream 5: strategy engine wired onto the live pipeline. A
      background worker in app.py (`_engine_worker_loop`) recomputes
      `calculate_all()` once per (symbol, period, interval, calc_params) —
      deduped/throttled across every viewer sharing those params — then runs
      `score_signals()` per-viewer's own thresholds and publishes to Redis.
      `realtime/main.py`'s `/stream/signals` relays it. Frontend
      (`static/signal_config.html`) uses SSE when `REALTIME_BASE_URL` is set,
      falls back to the existing 10s poll otherwise. Verified the dedup/
      throttle/per-user-threshold logic against mocks; **not** tested against
      a real Alpaca/OANDA feed or a real browser, since nothing's deployed.
      Known gap: streams open once per symbol at engine-start; toggling the
      watchlist mid-run doesn't add/drop streams the way polling does.
- [x] Workstream 6: `realtime/loadtest.py` — concurrent-SSE-connection load
      tester. Smoke-tested against a local fake server (20 connections);
      **not yet run against the real service**, since nothing's deployed.
- [ ] Verify Alpaca/OANDA per-connection symbol and rate limits.
- [ ] Confirm Railway's load balancer holds long-lived SSE connections
      cleanly across replicas.
- [ ] Workstream 4: horizontal scaling + load balancing — not started.
- [ ] Deploy: provision a Redis addon and a second Railway service for
      `realtime/`, set `REDIS_URL`/`REALTIME_BASE_URL`/`SECRET_KEY` on both
      services. **Costs real money and touches shared production
      infrastructure — holding off on doing this without explicit
      confirmation on cost, even though the rest of this project was done
      without waiting for review.**
- [ ] Run `realtime/loadtest.py` against the real deployed service and
      confirm it holds at meaningfully-high concurrency before calling any
      of this validated.

## Open questions (still open — not blocking the code above, but blocking deployment)

- Alpaca/OANDA per-connection symbol/rate limits — unverified.
- Railway Redis addon: cost and connection limits at the scale this implies.
- Whether the async service should eventually also serve the frontend for
  streaming-adjacent routes, or stay narrowly scoped to just the stream
  endpoints indefinitely.
