# Backtester / Signals / Portfolio audit — Phase 1 output

Audit date: 2026-09-02. Covers `static/signal_config.html`, `static/strategy-lab.html`,
`static/strategy-lab-forex.html`, `static/portfolio-balancer.html`, and the backend
routes in `app.py` they call.

## Signals (`signal_config.html` → `/api/signals`, `/api/prices`, `/api/prices/stream`, `/api/indicators`, `/api/custom-symbols`, `/api/symbol-search`)

**Works end-to-end:** symbol select → chart render, live tail via SSE, strategy engine
scan, custom symbol add/remove, symbol autocomplete, save/load preferences, and a
purpose-built mobile tab UI (not just a squeezed desktop layout).

**Half-built / broken:**
- Fired condition-alerts (`alerts` array, signal_config.html:834) are in-memory only —
  never persisted to localStorage or included in `savePreferences()`. Refresh the page
  and the alert history silently disappears.
- Price alerts only save if the user manually clicks "SAVE MY DEFAULTS"
  (signal_config.html:2754-2773) — set one and navigate away without saving, it's gone.
- **Tier paywall is client-side only.** `/api/signals` (app.py:4372-4374) only checks
  `@login_required`, no tier check. Any logged-in `basic`-tier user can call it directly
  and get full signal output the UI claims requires an upgrade.

## Backtester — Stocks/ETFs/Futures & Forex (`strategy-lab.html`, `strategy-lab-forex.html` → `/api/backtest`)

**Works end-to-end:** full config → results (equity curve, trade log, metrics), CSV
export, save/load strategy configs incl. deep-link from profile page, shared custom
symbols/search with Signals. Frontend/backend param names checked across ~90
indicator/threshold keys — no mismatches found. Intentionally public, no login gate,
consistent front and back.

**Half-built / broken:**
- No dedicated mobile layout — sidebar just stacks above the main panel at 768px
  (strategy-lab.html:691-701), so configuring on a phone means scrolling a long list of
  toggles/sliders before reaching Run. Signals already solved this; Backtester hasn't.
- Sector/peer trade enrichment (app.py:4678-4685) is wrapped in bare `try/except: pass`
  — a failure silently drops that field from the trade log with no error anywhere.

## Portfolio Balancer (`portfolio-balancer.html`)

**Works end-to-end:** fully self-contained manual investment tracker (add/update/remove,
pie chart, allocation table, event log), localStorage always + debounced sync to
`/api/save-preferences` for signed-in users with visible sync status.

**Half-built / broken:**
- `/api/portfolio-prices` and its `_PB_TICKERS` map (app.py:2734-2795, ~60 lines) are
  dead code — leftover from a superseded "live-priced predefined asset classes" design,
  nothing in any frontend file calls it.
- `seedDemo()` auto-populates fake investments (ISA, Crypto Wallet, Cash Savings) for
  any first-time visitor with no stored data (portfolio-balancer.html:833), with no
  "this is sample data" label — a new user could mistake it for real saved data.

## Prioritised punch list (most painful first)

1. Enforce `signal_tester+` tier server-side on `/api/signals` — paywall is currently
   UI-only and trivially bypassed. (app.py:4372)
2. Persist fired strategy alerts so they survive a refresh. (signal_config.html:834)
3. Auto-save price alerts on add/remove instead of requiring a manual save click.
   (signal_config.html:2754-2773)
4. Label Portfolio Balancer's auto-seeded demo data as sample data.
   (portfolio-balancer.html:833)
5. Delete the dead `/api/portfolio-prices` route and `_PB_TICKERS` map. (app.py:2734-2795)
6. Build a mobile tab layout for the Backtester sidebar, matching Signals.
   (strategy-lab.html:691-701)
7. Surface (log or banner) when sector/peer trade enrichment silently fails.
   (app.py:4678-4685)
