/* The Armoury: shared maths, chart helpers and the saved-results store.
   Used by /tools/armoury and /tools/armoury/cot. Only dependency is Plotly (loaded by the page). */
(function (global) {
  'use strict';
  const A = {};

  // ── Normal distribution ──────────────────────────────────────────────────
  function erfc(x) {
    const z = Math.abs(x), t = 1 / (1 + 0.5 * z);
    const r = t * Math.exp(-z * z - 1.26551223 + t * (1.00002368 + t * (0.37409196 + t * (0.09678418 +
      t * (-0.18628806 + t * (0.27886807 + t * (-1.13520398 + t * (1.48851587 + t * (-0.82215223 + t * 0.17087277)))))))));
    return x >= 0 ? r : 2 - r;
  }
  A.pdf = x => Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
  A.cdf = x => 0.5 * erfc(-x / Math.SQRT2);

  // ── Black-Scholes-Merton (continuous dividend yield q) ───────────────────
  A.bs = function (S, K, T, r, q, v, call) {
    if (T <= 0 || v <= 0) return Math.max(0, call ? S - K : K - S);
    const sq = v * Math.sqrt(T);
    const d1 = (Math.log(S / K) + (r - q + 0.5 * v * v) * T) / sq, d2 = d1 - sq;
    const eq = Math.exp(-q * T), er = Math.exp(-r * T);
    return call ? S * eq * A.cdf(d1) - K * er * A.cdf(d2) : K * er * A.cdf(-d2) - S * eq * A.cdf(-d1);
  };
  // delta, gamma, theta (per day), vega (per 1 vol point), rho (per 1 rate point)
  A.greeks = function (S, K, T, r, q, v, call) {
    if (T <= 0 || v <= 0) {
      const itm = call ? S > K : S < K;
      return { delta: itm ? (call ? 1 : -1) : 0, gamma: 0, theta: 0, vega: 0, rho: 0 };
    }
    const sq = v * Math.sqrt(T);
    const d1 = (Math.log(S / K) + (r - q + 0.5 * v * v) * T) / sq, d2 = d1 - sq;
    const eq = Math.exp(-q * T), er = Math.exp(-r * T), pd = A.pdf(d1);
    const common = -S * eq * pd * v / (2 * Math.sqrt(T));
    return {
      delta: call ? eq * A.cdf(d1) : eq * (A.cdf(d1) - 1),
      gamma: eq * pd / (S * sq),
      theta: (call ? common - r * K * er * A.cdf(d2) + q * S * eq * A.cdf(d1)
                   : common + r * K * er * A.cdf(-d2) - q * S * eq * A.cdf(-d1)) / 365,
      vega: S * eq * pd * Math.sqrt(T) / 100,
      rho: (call ? K * T * er * A.cdf(d2) : -K * T * er * A.cdf(-d2)) / 100
    };
  };
  // Implied volatility by bisection; NaN when the price sits outside no-arbitrage bounds.
  A.impliedVol = function (price, S, K, T, r, q, call) {
    if (!(price > 0) || T <= 0) return NaN;
    let lo = 1e-4, hi = 5;
    if (price < A.bs(S, K, T, r, q, lo, call) - 1e-9 || price > A.bs(S, K, T, r, q, hi, call)) return NaN;
    for (let i = 0; i < 80; i++) {
      const mid = 0.5 * (lo + hi);
      if (A.bs(S, K, T, r, q, mid, call) > price) hi = mid; else lo = mid;
    }
    return 0.5 * (lo + hi);
  };

  // ── Cox-Ross-Rubinstein binomial tree ────────────────────────────────────
  // keep=true returns every node (use only for small N). Early exercise is flagged where it beats holding.
  A.binomial = function (S, K, T, r, q, v, call, N, american, keep) {
    const dt = T / N, u = Math.exp(v * Math.sqrt(dt)), d = 1 / u;
    const p = (Math.exp((r - q) * dt) - d) / (u - d), disc = Math.exp(-r * dt);
    const payoff = s => Math.max(0, call ? s - K : K - s);
    let vals = [];
    const nodes = [];
    for (let j = 0; j <= N; j++) vals.push(payoff(S * Math.pow(u, N - j) * Math.pow(d, j)));
    if (keep) for (let j = 0; j <= N; j++) nodes.push({ i: N, j, S: S * Math.pow(u, N - j) * Math.pow(d, j), V: vals[j], ex: false });
    for (let i = N - 1; i >= 0; i--) {
      const next = new Array(i + 1);
      for (let j = 0; j <= i; j++) {
        const s = S * Math.pow(u, i - j) * Math.pow(d, j);
        let hold = disc * (p * vals[j] + (1 - p) * vals[j + 1]), ex = false;
        if (american) { const e = payoff(s); if (e > hold + 1e-12) { hold = e; ex = true; } }
        next[j] = hold;
        if (keep) nodes.push({ i, j, S: s, V: hold, ex });
      }
      vals = next;
    }
    return { price: vals[0], nodes };
  };

  // ── Basic statistics and matrices ────────────────────────────────────────
  A.mean = a => a.reduce((s, x) => s + x, 0) / (a.length || 1);
  A.std = a => { const m = A.mean(a); return Math.sqrt(a.reduce((s, x) => s + (x - m) * (x - m), 0) / Math.max(1, a.length - 1)); };
  A.cov = (a, b) => { const ma = A.mean(a), mb = A.mean(b); let s = 0; for (let i = 0; i < a.length; i++) s += (a[i] - ma) * (b[i] - mb); return s / Math.max(1, a.length - 1); };
  A.returns = c => { const o = []; for (let i = 1; i < c.length; i++) o.push(c[i] / c[i - 1] - 1); return o; };
  A.percentile = (arr, p) => { const s = arr.slice().sort((a, b) => a - b); const k = (s.length - 1) * p, f = Math.floor(k), c = Math.ceil(k); return s[f] + (s[c] - s[f]) * (k - f); };
  A.rankOf = (arr, x) => { let n = 0; arr.forEach(v => { if (v < x) n++; }); return 100 * n / Math.max(1, arr.length); };
  A.mulMV = (M, v) => M.map(row => row.reduce((s, x, j) => s + x * v[j], 0));
  A.dot = (a, b) => a.reduce((s, x, i) => s + x * b[i], 0);
  A.inv = function (M) { // Gauss-Jordan
    const n = M.length, a = M.map((r, i) => r.concat(Array.from({ length: n }, (_, j) => i === j ? 1 : 0)));
    for (let c = 0; c < n; c++) {
      let piv = c;
      for (let r = c + 1; r < n; r++) if (Math.abs(a[r][c]) > Math.abs(a[piv][c])) piv = r;
      if (Math.abs(a[piv][c]) < 1e-14) return null;
      [a[c], a[piv]] = [a[piv], a[c]];
      const pv = a[c][c];
      for (let j = 0; j < 2 * n; j++) a[c][j] /= pv;
      for (let r = 0; r < n; r++) if (r !== c) { const f = a[r][c]; if (f) for (let j = 0; j < 2 * n; j++) a[r][j] -= f * a[c][j]; }
    }
    return a.map(r => r.slice(n));
  };
  A.covMatrix = R => { // R: array of return series, one per asset
    const n = R.length; return Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => A.cov(R[i], R[j])));
  };
  // seeded generator so demo data is repeatable
  A.rng = function (seed) { let s = seed >>> 0; return () => { s = (s * 1664525 + 1013904223) >>> 0; return s / 4294967296; }; };
  A.gauss = rng => Math.sqrt(-2 * Math.log(rng() + 1e-12)) * Math.cos(2 * Math.PI * rng());
  A.demoCloses = function (symbols, days) {
    const out = { dates: [], closes: {} }, d0 = new Date();
    for (let i = days; i > 0; i--) { const d = new Date(d0.getTime() - i * 86400000); if (d.getDay() % 6) out.dates.push(d.toISOString().slice(0, 10)); }
    const n = out.dates.length, rng = A.rng(42), mkt = Array.from({ length: n }, () => A.gauss(rng));
    symbols.forEach((s, k) => {
      const r2 = A.rng(100 + k * 7), beta = 0.6 + 0.15 * k, vol = 0.012 + 0.002 * (k % 4), drift = 0.0003;
      let p = 100; out.closes[s] = [];
      for (let i = 0; i < n; i++) { p *= 1 + drift + vol * (beta * mkt[i] + (1 - 0.5 * beta) * A.gauss(r2)) * 0.9; out.closes[s].push(+p.toFixed(4)); }
    });
    return out;
  };

  // ── Portfolio optimisation (long-only) ───────────────────────────────────
  function projectSimplex(v) {
    const n = v.length, u = v.slice().sort((a, b) => b - a);
    let css = 0, rho = 0, theta = 0;
    for (let i = 0; i < n; i++) { css += u[i]; const t = (css - 1) / (i + 1); if (u[i] - t > 0) { rho = i; theta = t; } }
    return v.map(x => Math.max(0, x - theta));
  }
  const portVar = (w, S) => A.dot(w, A.mulMV(S, w));
  A.minVariance = function (S) {
    const n = S.length, L = Math.max(...S.map(r => r.reduce((s, x) => s + Math.abs(x), 0)));
    let w = Array(n).fill(1 / n);
    for (let it = 0; it < 2500; it++) w = projectSimplex(w.map((x, i) => x - (1 / (2 * L)) * 2 * A.dot(S[i], w)));
    return w;
  };
  A.maxSharpe = function (mu, S, rf) {
    const n = mu.length, rng = A.rng(7), sharpe = w => (A.dot(mu, w) - rf) / Math.sqrt(Math.max(1e-12, portVar(w, S)));
    let best = Array(n).fill(1 / n), bs = sharpe(best);
    for (let k = 0; k < 3000; k++) {
      const x = Array.from({ length: n }, () => -Math.log(rng() + 1e-12)); const t = x.reduce((a, b) => a + b, 0), w = x.map(v => v / t);
      const s = sharpe(w); if (s > bs) { bs = s; best = w; }
    }
    let w = best;
    for (let it = 0; it < 800; it++) {
      const sg = Math.sqrt(Math.max(1e-12, portVar(w, S))), ex = A.dot(mu, w) - rf, Sw = A.mulMV(S, w);
      const g = mu.map((m, i) => m / sg - ex * Sw[i] / (sg * sg * sg));
      const step = 0.05 / (1 + it / 80), cand = projectSimplex(w.map((x, i) => x + step * g[i]));
      if (sharpe(cand) >= sharpe(w)) w = cand;
    }
    return w;
  };
  A.riskParity = function (S) {
    const n = S.length; let w = S.map((r, i) => 1 / Math.sqrt(Math.max(1e-12, r[i])));
    let t = w.reduce((a, b) => a + b, 0); w = w.map(x => x / t);
    for (let it = 0; it < 800; it++) {
      const m = A.mulMV(S, w), rc = w.map((x, i) => x * m[i]), avg = A.mean(rc);
      w = w.map((x, i) => x * Math.pow(avg / Math.max(1e-14, rc[i]), 0.5)); t = w.reduce((a, b) => a + b, 0); w = w.map(x => x / t);
    }
    return w;
  };
  // Black-Litterman: equal-weight market prior, absolute views {index: annual return}, confidence 0-1.
  A.blackLitterman = function (S, views, conf, delta, tau) {
    const n = S.length, wm = Array(n).fill(1 / n), pi = A.mulMV(S, wm).map(x => delta * x);
    const idx = Object.keys(views).map(Number); if (!idx.length) return pi;
    const k = idx.length, tS = S.map(r => r.map(x => tau * x));
    const M = Array.from({ length: k }, (_, a) => Array.from({ length: k }, (_, b) => tS[idx[a]][idx[b]] + (a === b ? tS[idx[a]][idx[a]] * (1 - conf) / Math.max(0.01, conf) : 0)));
    const Mi = A.inv(M); if (!Mi) return pi;
    const diff = idx.map(i => views[i] - pi[i]), y = A.mulMV(Mi, diff);
    return pi.map((p, i) => p + idx.reduce((s, j, a) => s + tS[i][j] * y[a], 0));
  };
  // Metrics for a weight vector over daily return series R[asset][t]; bench is a daily return series.
  A.portfolioMetrics = function (w, R, bench, rf) {
    const n = R[0].length, pr = [];
    for (let t = 0; t < n; t++) { let s = 0; for (let i = 0; i < w.length; i++) s += w[i] * R[i][t]; pr.push(s); }
    let eq = 1, peak = 1, mdd = 0; const curve = [], dd = [];
    pr.forEach(x => { eq *= 1 + x; peak = Math.max(peak, eq); const d = eq / peak - 1; mdd = Math.min(mdd, d); curve.push(eq); dd.push(d); });
    const ann = Math.pow(eq, 252 / n) - 1, vol = A.std(pr) * Math.sqrt(252), rfd = rf / 252;
    const down = Math.sqrt(A.mean(pr.map(x => Math.min(0, x - rfd) ** 2))) * Math.sqrt(252);
    let beta = NaN; if (bench && bench.length === n) { const vb = A.cov(bench, bench); beta = vb > 0 ? A.cov(pr, bench) / vb : NaN; }
    const var95 = -A.percentile(pr, 0.05), tail = pr.filter(x => x <= -var95);
    return { ann, vol, sharpe: vol ? (ann - rf) / vol : NaN, sortino: down ? (ann - rf) / down : NaN, maxDD: mdd,
             calmar: mdd ? ann / Math.abs(mdd) : NaN, treynor: beta ? (ann - rf) / beta : NaN, beta,
             var95, cvar95: tail.length ? -A.mean(tail) : var95, curve, dd };
  };

  // ── Kalman filters ───────────────────────────────────────────────────────
  // Dynamic hedge ratio: y_t = b_t . x_t + noise, with b_t a random walk (x_t includes an intercept).
  A.kalmanRegression = function (y, X, delta, ve) {
    const k = X[0].length + 1, T = y.length; let b = Array(k).fill(0);
    let P = Array.from({ length: k }, (_, i) => Array.from({ length: k }, (_, j) => i === j ? 1 : 0));
    const Qd = delta / (1 - delta), betas = [], z = [], spread = [];
    for (let t = 0; t < T; t++) {
      const x = X[t].concat([1]);
      P = P.map((r, i) => r.map((v, j) => v + (i === j ? Qd : 0)));
      const Px = A.mulMV(P, x), S = A.dot(x, Px) + ve, e = y[t] - A.dot(x, b), K = Px.map(v => v / S);
      b = b.map((v, i) => v + K[i] * e);
      P = P.map((r, i) => r.map((v, j) => v - K[i] * Px[j]));
      betas.push(b.slice()); spread.push(e); z.push(e / Math.sqrt(S));
    }
    return { betas, spread, z };
  };
  // Local linear trend on log prices: returns filtered level and per-day slope.
  A.kalmanTrend = function (series, q1, q2, rv) {
    let lv = series[0], sl = 0, P = [[1, 0], [0, 1]]; const level = [], slope = [];
    series.forEach(y => {
      lv += sl; // predict
      P = [[P[0][0] + P[0][1] + P[1][0] + P[1][1] + q1, P[0][1] + P[1][1]], [P[1][0] + P[1][1], P[1][1] + q2]];
      const S = P[0][0] + rv, k0 = P[0][0] / S, k1 = P[1][0] / S, e = y - lv;
      lv += k0 * e; sl += k1 * e;
      P = [[(1 - k0) * P[0][0], (1 - k0) * P[0][1]], [P[1][0] - k1 * P[0][0], P[1][1] - k1 * P[0][1]]];
      level.push(lv); slope.push(sl);
    });
    return { level, slope };
  };

  // ── Formatting and small helpers ─────────────────────────────────────────
  A.esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  A.fmt = (x, d) => (x == null || !isFinite(x)) ? '–' : Number(x).toLocaleString('en-US', { minimumFractionDigits: d == null ? 2 : d, maximumFractionDigits: d == null ? 2 : d });
  A.pct = (x, d) => (x == null || !isFinite(x)) ? '–' : (x * 100).toFixed(d == null ? 1 : d) + '%';
  A.COLORS = { good: '#00d4aa', warn: '#ff9f43', bad: '#ff4757', neutral: '#a855f7' };
  A.VERDICT_WORD = { good: 'Good', warn: 'Caution', bad: 'Poor', neutral: 'Info' };

  // ── Plotly helpers (theme-aware) ─────────────────────────────────────────
  function themeVars() {
    const dark = (document.documentElement.getAttribute('data-theme') || 'light') === 'dark';
    return { dark, text: dark ? '#e6e9f2' : '#1a1d2b', grid: dark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.08)' };
  }
  A.layout = function (o) {
    const t = themeVars(), ax = { gridcolor: t.grid, zerolinecolor: t.grid, color: t.text };
    const lay = Object.assign({
      paper_bgcolor: 'rgba(0,0,0,0)', plot_bgcolor: 'rgba(0,0,0,0)', font: { color: t.text, family: 'Space Grotesk, sans-serif', size: 12 },
      margin: { l: 56, r: 20, t: 36, b: 48 }, legend: { orientation: 'h', y: -0.2 }, xaxis: ax, yaxis: ax, autosize: true
    }, o || {});
    lay.xaxis = Object.assign({}, ax, lay.xaxis); lay.yaxis = Object.assign({}, ax, lay.yaxis);
    if (lay.scene) ['xaxis', 'yaxis', 'zaxis'].forEach(k => { lay.scene[k] = Object.assign({ gridcolor: t.grid, color: t.text, backgroundcolor: 'rgba(0,0,0,0)' }, lay.scene[k] || {}); });
    return lay;
  };
  A.plot = function (el, traces, layout) {
    if (typeof el === 'string') el = document.getElementById(el);
    if (!el) return;
    if (!global.Plotly) { el.innerHTML = '<div class="arm-empty">Charts need Plotly, which has not loaded. Check your connection and refresh.</div>'; return; }
    global.Plotly.react(el, traces, A.layout(layout), { responsive: true, displaylogo: false });
  };

  // ── Saved results store (browser + account) ──────────────────────────────
  // Shape: { results: { <calcKey>: {...} }, plans: [ {...} ] }
  const LS = 'armoury_saved_v1';
  let store = { results: {}, plans: [] };
  const listeners = [];
  function persistLocal() { try { localStorage.setItem(LS, JSON.stringify(store)); } catch (e) {} }
  let pushTimer = null;
  function persistRemote() {
    clearTimeout(pushTimer);
    pushTimer = setTimeout(() => {
      fetch('/api/save-preferences', { method: 'POST', credentials: 'include', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ armoury_saved: store }) }).catch(() => {});
    }, 800);
  }
  function emit() { listeners.forEach(f => { try { f(store); } catch (e) { console.error(e); } }); }
  A.store = {
    get: () => store,
    onChange: f => listeners.push(f),
    setResult(key, data) { store.results[key] = data; persistLocal(); persistRemote(); emit(); },
    removeResult(key) { delete store.results[key]; persistLocal(); persistRemote(); emit(); },
    has: key => !!store.results[key],
    addPlan(plan) { store.plans = store.plans.filter(p => p.name !== plan.name).concat([plan]); persistLocal(); persistRemote(); emit(); },
    removePlan(name) { store.plans = store.plans.filter(p => p.name !== name); persistLocal(); persistRemote(); emit(); },
    async load() {
      try { const l = JSON.parse(localStorage.getItem(LS) || 'null'); if (l && l.results) store = { results: l.results, plans: l.plans || [] }; } catch (e) {}
      try {
        const r = await fetch('/api/load-preferences', { credentials: 'include' });
        if (r.ok) { const d = await r.json(), s = d.preferences && d.preferences.armoury_saved; if (s && s.results) { store = { results: s.results, plans: s.plans || [] }; persistLocal(); } A.savedBacktests = (d.preferences && d.preferences.saved_backtests) || []; }
      } catch (e) {}
      emit();
    }
  };
  A.savedBacktests = [];

  // fetch helper that surfaces the server's error message
  A.getJSON = async function (url) {
    const r = await fetch(url, { credentials: 'include' });
    let d = {}; try { d = await r.json(); } catch (e) {}
    if (!r.ok) throw new Error(d.error || ('Request failed (' + r.status + ')'));
    return d;
  };

  global.Armoury = A;
})(window);
