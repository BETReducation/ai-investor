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

## Phase 2 UX audit — 2026-09-02

Everything above was correctness/completeness. This pass is about what it actually
feels like to use these two pages, especially for someone who isn't already fluent in
technical indicators — which is most of the target audience for an education platform.

### Signals is well taught; Backtester isn't

`signal_config.html` explains itself. Every strategy chip carries a plain-English
`title` tooltip ("BUY when RSI is oversold and price is near the lower Bollinger Band —
a mean-reversion bounce setup"), and the confidence slider, chart-type picker, and data
source are all tooltipped too (24 tooltips total).

`strategy-lab.html` (Backtester) has 6 tooltips, and none of them are about trading —
they're all UI chrome ("Toggle light/dark mode", "Delete selected strategy"). Switch to
Detailed mode and you get 25+ indicators (ADX, PSAR, Ichimoku, Supertrend, HMA, Stoch,
StochRSI, CCI, Williams %R, ROC, MFI, TSI, Awesome Oscillator, Keltner, StDev, Chaikin
Volatility, Historical Volatility, OBV, VWAP, A/D, CMF, Volume Profile, Fibonacci,
inverse H&S) and ~90 numeric parameters between them, with zero explanation of what any
of them do or what a sane value looks like. A beginner who came from a Learn lesson has
no way to connect "RSI Length: 14" back to what they just read.

This is a bigger miss than it looks, because the site already has 42 lessons covering
exactly this material (`LESSON_PAGES` in app.py) and zero of them are linked from the
tool. Nothing on the Backtester page points at `/learn` for a specific indicator — the
only link is the generic nav dropdown.

**Fix:** at minimum, port the tooltip pattern from Signals onto the Backtester's
indicator toggles/labels. Better: link each indicator name to its Learn lesson anchor
if one exists (some indicators — e.g. ADX, Ichimoku — may not have a lesson yet, which
is its own gap worth flagging back to the content side).

### Results dumped in the same jargon

`renderResults()` labels the headline metrics as "Sharpe Ratio", "Profit Factor", "Max
Drawdown %" with no tooltip or plain-English gloss (strategy-lab.html:3383-3487) — the
exact moment a first-time user most needs "this number is good/bad because...". Signals
doesn't have this problem because its outputs are BUY/SELL/WAIT, not statistics.

**Fix:** short tooltip per metric (Signals already proves the pattern works well and is
cheap to add — same `title="..."` attribute).

### Backtester mobile: sidebar-before-results, no shortcut to Run

Confirmed still unfixed from Phase 1 (item 6): at ≤768px the sidebar just stacks above
the results (`strategy-lab.html:691-701`, `flex-direction: column`). The sidebar HTML
runs ~1,250 lines (807-2058) — symbol search, period, both indicator modes, risk
management — all of it between the top of the page and the Run button. A phone user
scrolls through the entire config before they can even press Run, and past it again to
see results. There's no sticky/floating Run button to shortcut this.

Signals solved the equivalent problem with a purpose-built mobile tab UI; Backtester
still hasn't adopted it. This is the single highest-impact mobile fix available.

### Everything else checked and fine

Loading/error/idle states are all present and clearly worded on both pages (no bare
`alert()` dialogs anywhere in either file). Switching Basic ⇄ Detailed mode on the
Backtester preserves both panels' state independently — no silent data loss. Signal
condition builder's confidence-threshold tooltip is a good model of explaining a
non-obvious control in one sentence; worth reusing that voice anywhere else jargon
shows up.

### Updated punch list (adds to Phase 1's, in priority order)

8. Add plain-English tooltips to Backtester's indicator toggles/params, matching the
   Signals pattern. (strategy-lab.html, `detailedIndicators` block)
9. Add a one-line gloss/tooltip to each results metric (Sharpe, Profit Factor, Max
   Drawdown, Sortino, etc.). (strategy-lab.html:3383-3487)
10. Link indicator names to their Learn lesson where one exists. (strategy-lab.html,
    app.py `LESSON_PAGES`)
11. Ship the mobile tab UI for Backtester (still open from item 6) — now the top
    mobile-UX priority across both pages.
