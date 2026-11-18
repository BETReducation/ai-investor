/* The Armoury: the nine calculators and the Strategy Builder. Everything here is educational: it shows what
   models say about the numbers entered, never what to trade. */
(function () {
  'use strict';
  const A = window.Armoury, esc = A.esc, fmt = A.fmt;
  const $ = id => document.getElementById(id);
  const N = id => parseFloat($(id).value);
  const MODE = {};            // per-calculator chart mode: '2d' | '3d'
  const LAST = {};            // latest result per calculator (for the Save toggle)
  const CACHE = {};           // fetched market data kept between re-renders
  let active = 'bs';

  // ── Small UI helpers ─────────────────────────────────────────────────────
  const F = (id, label, val, o) => { o = o || {};
    const inner = o.options
      ? '<select id="' + id + '">' + o.options.map(x => '<option value="' + x[0] + '"' + (String(x[0]) === String(val) ? ' selected' : '') + '>' + x[1] + '</option>').join('') + '</select>'
      : '<input id="' + id + '" type="' + (o.type || 'number') + '" value="' + esc(val) + '" step="' + (o.step || 'any') + '"' + (o.min != null ? ' min="' + o.min + '"' : '') + (o.nolive ? ' data-nolive="1"' : '') + '>';
    return '<div class="arm-f"><label for="' + id + '">' + label + '</label>' + inner + (o.hint ? '<div class="hint">' + o.hint + '</div>' : '') + '</div>'; };
  const kpis = items => '<div class="arm-kpis">' + items.map(i => '<div class="arm-kpi ' + (i.c || '') + '"><span>' + i.l + '</span><b>' + i.v + '</b></div>').join('') + '</div>';
  const verdict = (c, head, text) => '<div class="arm-verdict ' + c + '"><strong>' + head + '</strong>' + text + '</div>';
  const chartBox = (id, cls) => '<div class="arm-chart ' + (cls || '') + '" id="' + id + '"></div>';
  const worst = list => list.includes('bad') ? 'bad' : list.includes('warn') ? 'warn' : 'good';
  const mode = k => MODE[k] || '2d';
  const range = (a, b, n) => Array.from({ length: n }, (_, i) => a + (b - a) * i / (n - 1));
  const T = id => N(id) / 365;
  const common = (p, o) => { o = o || {};
    return F(p + 'S', 'Stock price', o.S || 100) + F(p + 'K', 'Strike', o.K || 100) + F(p + 'T', 'Days to expiry', o.T || 90, { min: 1 }) +
      F(p + 'R', 'Interest rate %', o.R || 4.5) + F(p + 'Q', 'Dividend yield %', o.Q || 0) + F(p + 'V', 'Volatility %', o.V || 25) +
      F(p + 'Type', 'Type', o.type || 'call', { options: [['call', 'Call'], ['put', 'Put']] }); };
  const readCommon = p => ({ S: N(p + 'S'), K: N(p + 'K'), T: T(p + 'T'), r: N(p + 'R') / 100, q: N(p + 'Q') / 100, v: N(p + 'V') / 100, call: $(p + 'Type').value === 'call' });
  const okNums = (...x) => x.every(v => isFinite(v) && v > 0);

  // ── Market data ──────────────────────────────────────────────────────────
  async function getHistory(symbols, period, demo) {
    if (demo) { const d = A.demoCloses(symbols, { '6mo': 190, '1y': 370, '2y': 740, '5y': 1850 }[period] || 370); return { symbols, dates: d.dates, closes: d.closes, demo: true }; }
    return A.getJSON('/api/armoury/history?symbols=' + encodeURIComponent(symbols.join(',')) + '&period=' + period);
  }
  function demoChain() {
    const S = 100, r = 0.04, exps = [7, 30, 60, 120, 240].map(days => {
      const T = days / 365, strikes = range(70, 130, 13).map(x => Math.round(x / 2.5) * 2.5), row = { expiry: 'demo+' + days + 'd', days, calls: [], puts: [] };
      strikes.forEach(K => { const x = Math.log(K / S), v = 0.2 + 0.04 * Math.exp(-days / 90) - 0.25 * x + 1.2 * x * x;
        [true, false].forEach(c => { const m = A.bs(S, K, T, r, 0, v, c), o = { strike: K, bid: +(m * 0.98).toFixed(2), ask: +(m * 1.02).toFixed(2), last: +m.toFixed(2), oi: 100, yf_iv: v };
          (c ? row.calls : row.puts).push(o); }); });
      return row; });
    return { symbol: 'DEMO', spot: S, expiries: exps, demo: true };
  }
  async function getChain(symbol, demo) {
    if (demo) return demoChain();
    return A.getJSON('/api/armoury/chain?symbol=' + encodeURIComponent(symbol) + '&expiries=6');
  }
  const mid = o => (o.bid > 0 && o.ask > 0) ? (o.bid + o.ask) / 2 : (o.last || 0);

  // ── 1. Black-Scholes ─────────────────────────────────────────────────────
  const bs = {
    key: 'bs', title: 'Black-Scholes', blurb: 'Price a European call or put and see if the market looks cheap or rich.', modes: true,
    body: () => '<div class="arm-grid">' + common('bs') + F('bsMkt', 'Market price (optional)', '', { hint: 'Compare with the model' }) + '</div><div id="bsOut"></div>',
    run() {
      const p = readCommon('bs'); if (!okNums(p.S, p.K, p.T, p.v)) { $('bsOut').innerHTML = '<div class="arm-empty">Enter positive numbers to price.</div>'; return; }
      const price = A.bs(p.S, p.K, p.T, p.r, p.q, p.v, p.call), g = A.greeks(p.S, p.K, p.T, p.r, p.q, p.v, p.call), mkt = parseFloat($('bsMkt').value);
      let c = 'neutral', msg = 'Add a market price to see whether the option looks cheap or expensive against the model.', vol = null, diff = NaN;
      if (mkt > 0) { diff = (mkt - price) / price;
        if (diff < -0.05) { c = 'good'; vol = 'cheap'; msg = 'The market price is ' + A.pct(-diff) + ' below the model price, so the option looks cheap on these inputs.'; }
        else if (diff > 0.05) { c = 'bad'; vol = 'rich'; msg = 'The market price is ' + A.pct(diff) + ' above the model price, so the option looks expensive on these inputs.'; }
        else { c = 'warn'; vol = 'fair'; msg = 'The market price is within 5% of the model price, which is close to fair value on these inputs.'; } }
      $('bsOut').innerHTML = kpis([{ l: 'Model price', v: fmt(price, 4), c: c === 'neutral' ? '' : c }, { l: 'Delta', v: fmt(g.delta, 3) }, { l: 'Gamma', v: fmt(g.gamma, 4) },
        { l: 'Theta / day', v: fmt(g.theta, 4) }, { l: 'Vega / 1 pt', v: fmt(g.vega, 4) }, { l: 'Rho / 1 pt', v: fmt(g.rho, 4) }]) +
        verdict(c === 'neutral' ? '' : c, A.VERDICT_WORD[c] + ': ', msg) + chartBox('bsChart', mode('bs') === '3d' ? 'tall' : '');
      const col = A.COLORS[c];
      if (mode('bs') === '2d') {
        const xs = range(p.S * 0.6, p.S * 1.4, 60);
        const tr = [{ x: xs, y: xs.map(s => A.bs(s, p.K, p.T, p.r, p.q, p.v, p.call)), name: 'Model price today', line: { color: '#a855f7', width: 3 } },
          { x: xs, y: xs.map(s => Math.max(0, p.call ? s - p.K : p.K - s)), name: 'Value at expiry', line: { color: '#8892b0', dash: 'dot' } },
          { x: [p.S], y: [price], mode: 'markers', name: 'Model at current price', marker: { size: 12, color: col } }];
        if (mkt > 0) tr.push({ x: [p.S], y: [mkt], mode: 'markers', name: 'Market price', marker: { size: 14, color: col, symbol: 'diamond', line: { color: '#fff', width: 1 } } });
        A.plot('bsChart', tr, { xaxis: { title: 'Stock price' }, yaxis: { title: 'Option price' } });
      } else {
        const xs = range(p.S * 0.6, p.S * 1.4, 36), ys = range(Math.max(1, N('bsT') * 0.02), N('bsT'), 30);
        A.plot('bsChart', [{ type: 'surface', x: xs, y: ys, z: ys.map(d => xs.map(s => A.bs(s, p.K, d / 365, p.r, p.q, p.v, p.call))), colorscale: 'Viridis', showscale: false, opacity: 0.95 },
          { type: 'scatter3d', mode: 'markers', x: [p.S], y: [N('bsT')], z: [price], marker: { size: 6, color: col }, name: 'You are here' }],
          { scene: { xaxis: { title: 'Stock price' }, yaxis: { title: 'Days to expiry' }, zaxis: { title: 'Option price' } }, margin: { l: 0, r: 0, t: 10, b: 0 } });
      }
      return { verdict: c === 'neutral' ? 'neutral' : c, summary: (p.call ? 'Call' : 'Put') + ' K' + p.K + ', ' + N('bsT') + 'd: model ' + fmt(price, 2) + (mkt > 0 ? ' vs market ' + fmt(mkt, 2) : ''),
        metrics: { 'Model price': fmt(price, 4), Delta: fmt(g.delta, 3), Vega: fmt(g.vega, 3) }, vol };
    }
  };

  // ── 2. American options (binomial tree) ──────────────────────────────────
  const amer = {
    key: 'amer', title: 'American options', blurb: 'Binomial tree that prices early exercise.', modes: true,
    body: () => '<div class="arm-grid">' + common('am', { type: 'put', K: 105 }) + F('amN', 'Tree steps', 100, { min: 5, hint: '5 to 500' }) + '</div><div id="amOut"></div>',
    run() {
      const p = readCommon('am'); let n = Math.round(N('amN')); n = Math.max(5, Math.min(500, n || 100));
      if (!okNums(p.S, p.K, p.T, p.v)) { $('amOut').innerHTML = '<div class="arm-empty">Enter positive numbers to price.</div>'; return; }
      const am = A.binomial(p.S, p.K, p.T, p.r, p.q, p.v, p.call, n, true).price, eu = A.binomial(p.S, p.K, p.T, p.r, p.q, p.v, p.call, n, false).price, bsP = A.bs(p.S, p.K, p.T, p.r, p.q, p.v, p.call);
      const conv = Math.abs(eu - bsP) / Math.max(0.01, bsP), c = conv < 0.002 ? 'good' : conv < 0.01 ? 'warn' : 'bad', prem = am - bsP;
      $('amOut').innerHTML = kpis([{ l: 'American price', v: fmt(am, 4) }, { l: 'European (tree)', v: fmt(eu, 4) }, { l: 'Black-Scholes', v: fmt(bsP, 4) },
        { l: 'Early-exercise value', v: fmt(prem, 4), c: prem > 0.005 * Math.max(1, bsP) ? 'warn' : '' }, { l: 'Tree vs BS gap', v: A.pct(conv, 3), c }]) +
        verdict(c, c === 'good' ? 'Converged: ' : c === 'warn' ? 'Close: ' : 'Not converged: ', 'With ' + n + ' steps the European tree is ' + A.pct(conv, 3) + ' away from Black-Scholes. ' + (c === 'bad' ? 'Add more steps.' : 'The tree is a sound approximation.')) +
        '<div id="amWrap">' + chartBox('amChart', mode('am') === '3d' ? 'tall' : '') + (mode('am') === '2d' ? chartBox('amChart2', 'short') : '') + '</div>';
      if (mode('am') === '2d') {
        const ns = Math.min(7, n), tree = A.binomial(p.S, p.K, p.T, p.r, p.q, p.v, p.call, ns, true, true).nodes, yes = tree.filter(x => x.ex), no = tree.filter(x => !x.ex);
        const mk = (arr, col, nm) => ({ x: arr.map(x => x.i), y: arr.map(x => x.S), mode: 'markers+text', text: arr.map(x => x.V.toFixed(2)), textposition: 'top center', textfont: { size: 9 }, name: nm, marker: { size: 13, color: col } });
        A.plot('amChart', [mk(no, '#a855f7', 'Hold'), mk(yes, '#00d4aa', 'Exercise early')], { title: { text: 'Price tree (' + ns + ' steps shown; option value on each node)', font: { size: 13 } }, xaxis: { title: 'Step', dtick: 1 }, yaxis: { title: 'Stock price' } });
        const steps = [5, 10, 20, 40, 80, 160].filter(s => s <= 500);
        A.plot('amChart2', [{ x: steps, y: steps.map(s => A.binomial(p.S, p.K, p.T, p.r, p.q, p.v, p.call, s, false).price), name: 'European tree', line: { color: '#a855f7' } },
          { x: steps, y: steps.map(s => A.binomial(p.S, p.K, p.T, p.r, p.q, p.v, p.call, s, true).price), name: 'American tree', line: { color: '#00d4aa' } },
          { x: [steps[0], steps[steps.length - 1]], y: [bsP, bsP], name: 'Black-Scholes', line: { color: '#8892b0', dash: 'dot' } }], { title: { text: 'Convergence as steps increase', font: { size: 13 } }, xaxis: { title: 'Steps', type: 'log' }, yaxis: { title: 'Price' } });
      } else {
        const xs = range(p.S * 0.6, p.S * 1.4, 22), ys = range(Math.max(2, N('amT') * 0.05), N('amT'), 16);
        A.plot('amChart', [{ type: 'surface', x: xs, y: ys, z: ys.map(d => xs.map(s => Math.max(0, A.binomial(s, p.K, d / 365, p.r, p.q, p.v, p.call, 50, true).price - A.bs(s, p.K, d / 365, p.r, p.q, p.v, p.call)))), colorscale: [[0, '#1b2a41'], [0.5, '#ff9f43'], [1, '#00d4aa']], showscale: true, colorbar: { title: 'Premium', len: 0.6 } }],
          { scene: { xaxis: { title: 'Stock price' }, yaxis: { title: 'Days to expiry' }, zaxis: { title: 'Early-exercise value' } }, margin: { l: 0, r: 0, t: 10, b: 0 } });
      }
      return { verdict: c, summary: (p.call ? 'Call' : 'Put') + ' K' + p.K + ': American ' + fmt(am, 2) + ', early-exercise value ' + fmt(prem, 3), metrics: { American: fmt(am, 4), 'Early-exercise value': fmt(prem, 4) } };
    }
  };

  // ── 3. Implied volatility and the smile ──────────────────────────────────
  function ivPoints(chain, r, q) {
    return chain.expiries.map(e => { const Tt = e.days / 365, pts = [];
      const strikes = Array.from(new Set(e.calls.map(x => x.strike).concat(e.puts.map(x => x.strike)))).sort((a, b) => a - b);
      let tried = 0;
      strikes.forEach(K => { if (K < chain.spot * 0.6 || K > chain.spot * 1.4) return;
        const call = K >= chain.spot, o = (call ? e.calls : e.puts).find(x => x.strike === K); if (!o) return; tried++;
        const m = mid(o), v = A.impliedVol(m, chain.spot, K, Tt, r, q, call); if (isFinite(v) && v > 0.02 && v < 3) pts.push({ K, iv: v }); });
      return { days: e.days, expiry: e.expiry, pts, tried }; });
  }
  const iv = {
    key: 'iv', title: 'Implied volatility', blurb: 'Invert Black-Scholes over a live chain to see the volatility smile.', modes: true,
    body: () => '<div class="arm-grid">' + F('ivSym', 'Ticker', 'SPY', { type: 'text', nolive: true }) + F('ivR', 'Interest rate %', 4.5, { nolive: true }) + F('ivQ', 'Dividend yield %', 1.3, { nolive: true }) + '</div>' +
      '<div class="arm-row"><button class="arm-btn" id="ivGo">Load option chain</button><label class="arm-check"><input type="checkbox" id="ivDemo" data-nolive="1"> Use demo data</label></div><div class="arm-err" id="ivErr"></div><div id="ivOut"><div class="arm-empty">Load a chain to see its smile and volatility surface.</div></div>',
    init() { $('ivGo').onclick = async () => { $('ivErr').textContent = ''; $('ivGo').disabled = true;
      try { CACHE.chain = await getChain($('ivSym').value.trim().toUpperCase(), $('ivDemo').checked); CACHE.chainR = N('ivR') / 100; CACHE.chainQ = N('ivQ') / 100; this.run(); } catch (e) { $('ivErr').textContent = e.message; } $('ivGo').disabled = false; }; },
    run() {
      const ch = CACHE.chain; if (!ch) return;
      const r = CACHE.chainR, q = CACHE.chainQ, sets = ivPoints(ch, r, q), tried = sets.reduce((s, x) => s + x.tried, 0), got = sets.reduce((s, x) => s + x.pts.length, 0), ok = tried ? got / tried : 0;
      const c = ok >= 0.8 ? 'good' : ok >= 0.5 ? 'warn' : 'bad', first = sets.find(s => s.pts.length > 3) || sets[0];
      const atm = s => { if (!s || !s.pts.length) return NaN; return s.pts.reduce((b, x) => Math.abs(x.K - ch.spot) < Math.abs(b.K - ch.spot) ? x : b).iv; };
      const at = (s, k) => { if (!s || s.pts.length < 2) return NaN; const t = ch.spot * k; return s.pts.reduce((b, x) => Math.abs(x.K - t) < Math.abs(b.K - t) ? x : b).iv; };
      const skew = at(first, 0.9) - at(first, 1.1), last = sets[sets.length - 1];
      $('ivOut').innerHTML = (ch.demo ? '<div class="arm-note">Demo data: a synthetic chain priced with a skewed volatility curve.</div>' : '') +
        kpis([{ l: 'Spot', v: fmt(ch.spot, 2) }, { l: 'ATM IV (near term)', v: A.pct(atm(first)) }, { l: 'Skew (90% minus 110%)', v: A.pct(skew) }, { l: 'Term slope', v: A.pct(atm(last) - atm(sets[0])) }, { l: 'Strikes inverted', v: A.pct(ok, 0), c }]) +
        verdict(c, A.VERDICT_WORD[c] + ': ', got + ' of ' + tried + ' option prices inverted to a valid implied volatility. ' + (c === 'good' ? 'The surface below is built on solid data.' : c === 'warn' ? 'Some quotes are stale or outside no-arbitrage bounds, so treat gaps with care.' : 'Too many quotes failed (market closed or thin chain); the smile is not reliable.')) +
        '<p class="hint" style="font-size:12px;color:var(--muted)">Puts are used below the spot price and calls above it, the usual convention for a clean smile. Skew is positive when downside strikes carry higher IV.</p>' + chartBox('ivChart', mode('iv') === '3d' ? 'tall' : '');
      if (mode('iv') === '2d') {
        const cols = ['#a855f7', '#00d4aa', '#ff9f43', '#38bdf8', '#ff4757', '#f472b6', '#facc15', '#94a3b8'];
        A.plot('ivChart', sets.filter(s => s.pts.length).map((s, i) => ({ x: s.pts.map(x => x.K), y: s.pts.map(x => x.iv * 100), mode: 'lines+markers', name: s.days + 'd', line: { color: cols[i % cols.length] } })).concat([{ x: [ch.spot, ch.spot], y: [0, 100], mode: 'lines', name: 'Spot', line: { color: '#8892b0', dash: 'dot' }, hoverinfo: 'skip' }]),
          { xaxis: { title: 'Strike' }, yaxis: { title: 'Implied volatility %', rangemode: 'tozero' } });
      } else {
        const ks = range(ch.spot * 0.75, ch.spot * 1.25, 30), interp = (pts, k) => { if (pts.length < 2 || k < pts[0].K || k > pts[pts.length - 1].K) return null; for (let i = 1; i < pts.length; i++) if (k <= pts[i].K) { const a = pts[i - 1], b = pts[i]; return (a.iv + (b.iv - a.iv) * (k - a.K) / (b.K - a.K)) * 100; } return null; };
        const live = sets.filter(s => s.pts.length > 3);
        A.plot('ivChart', [{ type: 'surface', x: ks, y: live.map(s => s.days), z: live.map(s => ks.map(k => interp(s.pts, k))), colorscale: 'RdBu', reversescale: true, colorbar: { title: 'IV %', len: 0.6 } }],
          { scene: { xaxis: { title: 'Strike' }, yaxis: { title: 'Days to expiry' }, zaxis: { title: 'Implied vol %' } }, margin: { l: 0, r: 0, t: 10, b: 0 } });
      }
      return { verdict: c, summary: (ch.symbol || 'Chain') + ': ATM IV ' + A.pct(atm(first)) + ', skew ' + A.pct(skew), metrics: { 'ATM IV': A.pct(atm(first)), Skew: A.pct(skew) }, symbol: ch.symbol === 'DEMO' ? null : ch.symbol };
    }
  };

  // ── 4. Greeks and portfolio risk ─────────────────────────────────────────
  let posRows = [{ call: true, K: 100, d: 60, qty: 5, iv: 25 }, { call: false, K: 95, d: 60, qty: -3, iv: 27 }];
  const greeks = {
    key: 'greeks', title: 'Greeks and portfolio risk', blurb: 'Single-option Greeks, plus limits and stress tests across positions.', modes: true,
    body: () => '<h3 style="font-size:14px;margin:6px 0">Single option</h3><div class="arm-grid">' + common('gk') + F('gkWhich', 'Greek to chart', 'gamma', { options: [['delta', 'Delta'], ['gamma', 'Gamma'], ['theta', 'Theta'], ['vega', 'Vega'], ['rho', 'Rho']] }) + '</div>' +
      '<h3 style="font-size:14px;margin:18px 0 6px">Portfolio (same underlying price as above; quantity is contracts, negative = short)</h3><div class="arm-scroll"><table class="arm-table" id="gkPos"></table></div>' +
      '<div class="arm-row"><button class="arm-btn ghost" id="gkAdd">Add position</button></div>' +
      '<div class="arm-grid">' + F('gkLd', 'Delta limit (shares)', 400) + F('gkLg', 'Gamma limit', 40) + F('gkLv', 'Vega limit ($ per vol pt)', 2000) + F('gkLt', 'Theta limit ($ per day)', 400) + F('gkLoss', 'Max acceptable loss $', 8000) + '</div><div id="gkOut"></div>',
    init() { const draw = () => { $('gkPos').innerHTML = '<tr><th>Type</th><th>Strike</th><th>Days</th><th>Contracts</th><th>IV %</th><th></th></tr>' + posRows.map((r, i) =>
        '<tr><td><select data-i="' + i + '" data-k="call"><option value="1"' + (r.call ? ' selected' : '') + '>Call</option><option value="0"' + (r.call ? '' : ' selected') + '>Put</option></select></td>' +
        ['K', 'd', 'qty', 'iv'].map(k => '<td><input type="number" step="any" data-i="' + i + '" data-k="' + k + '" value="' + r[k] + '"></td>').join('') + '<td><button class="arm-btn ghost" data-del="' + i + '">×</button></td></tr>').join(''); };
      draw();
      $('gkPos').addEventListener('input', e => { const t = e.target, i = t.dataset.i; if (i == null) return; posRows[i][t.dataset.k] = t.dataset.k === 'call' ? t.value === '1' : parseFloat(t.value); });
      $('gkPos').addEventListener('click', e => { if (e.target.dataset.del != null) { posRows.splice(+e.target.dataset.del, 1); draw(); this.run(); } });
      $('gkAdd').onclick = () => { posRows.push({ call: true, K: 105, d: 60, qty: 1, iv: 25 }); draw(); this.run(); }; },
    run() {
      const p = readCommon('gk'); if (!okNums(p.S, p.K, p.T, p.v)) { $('gkOut').innerHTML = ''; return; }
      const r = p.r, q = p.q, S = p.S, rows = posRows.filter(x => isFinite(x.K) && x.d > 0 && isFinite(x.qty) && x.iv > 0);
      const val = (s, dShift, vShift) => rows.reduce((t, x) => t + x.qty * 100 * A.bs(s, x.K, Math.max(1e-6, (x.d - dShift) / 365), r, q, Math.max(0.01, x.iv / 100 + vShift), x.call), 0);
      const tot = { delta: 0, gamma: 0, theta: 0, vega: 0, rho: 0 };
      rows.forEach(x => { const g = A.greeks(S, x.K, x.d / 365, r, q, x.iv / 100, x.call); Object.keys(tot).forEach(k => { tot[k] += g[k] * x.qty * 100; }); });
      const lim = { delta: N('gkLd'), gamma: N('gkLg'), vega: N('gkLv'), theta: N('gkLt') };
      const util = k => lim[k] > 0 ? Math.abs(tot[k]) / lim[k] : 0, uc = u => u > 1 ? 'bad' : u > 0.7 ? 'warn' : 'good';
      const base = val(S, 0, 0), shocks = [-0.10, -0.05, 0, 0.05, 0.10], vs = [-0.05, 0, 0.05];
      const grid = vs.map(v => shocks.map(sh => val(S * (1 + sh), 0, v) - base)), maxLoss = Math.max(...grid.flat().map(x => -x), 0), cap = N('gkLoss') || 1;
      const sig = A.mean(rows.map(x => x.iv / 100)) / Math.sqrt(252) || 0.01, v95 = Math.max(0, -Math.min(val(S * (1 + 1.645 * sig), 1, 0) - base, val(S * (1 - 1.645 * sig), 1, 0) - base));
      const stressC = maxLoss > cap ? 'bad' : maxLoss > 0.5 * cap ? 'warn' : 'good', overall = worst(['delta', 'gamma', 'vega', 'theta'].map(k => uc(util(k))).concat([stressC]));
      const bar = k => '<tr><td>' + k[0].toUpperCase() + k.slice(1) + '</td><td>' + fmt(tot[k], 2) + '</td><td>' + fmt(lim[k], 0) + '</td><td style="width:35%"><div class="arm-bar"><i style="width:' + Math.min(100, util(k) * 100) + '%;background:' + A.COLORS[uc(util(k))] + '"></i></div></td><td><span class="arm-tag ' + uc(util(k)) + '">' + A.pct(util(k), 0) + '</span></td></tr>';
      const heat = '<table class="arm-table"><tr><th>IV shock</th>' + shocks.map(s => '<th>' + (s > 0 ? '+' : '') + s * 100 + '%</th>').join('') + '</tr>' + grid.map((row, i) => '<tr><td>' + (vs[i] > 0 ? '+' : '') + vs[i] * 100 + ' pts</td>' + row.map(x => { const l = -x, c = l > cap ? 'bad' : l > 0.5 * cap ? 'warn' : x >= 0 ? 'good' : 'neutral';
        return '<td style="background:' + (c === 'neutral' ? 'transparent' : A.COLORS[c] + '33') + '">' + fmt(x, 0) + '</td>'; }).join('') + '</tr>').join('') + '</table>';
      $('gkOut').innerHTML = verdict(overall, A.VERDICT_WORD[overall] + ': ', overall === 'good' ? 'All exposures sit inside your limits and the worst stress loss is within half your loss budget.' : overall === 'warn' ? 'At least one exposure is above 70% of its limit, or the worst stress loss is over half your budget.' : 'A limit is breached or the worst stress loss exceeds your budget.') +
        '<div class="arm-scroll"><table class="arm-table"><tr><th>Portfolio Greek</th><th>Value</th><th>Limit</th><th>Usage</th><th></th></tr>' + ['delta', 'gamma', 'vega', 'theta'].map(bar).join('') + '</table></div>' +
        kpis([{ l: 'Worst stress loss', v: '$' + fmt(maxLoss, 0), c: stressC }, { l: '1-day VaR (95%)', v: '$' + fmt(v95, 0) }, { l: 'Portfolio value', v: '$' + fmt(base, 0) }, { l: 'Rho', v: fmt(tot.rho, 1) }]) +
        '<h3 style="font-size:14px;margin:8px 0">Stress test: P&L by price and volatility shock</h3><div class="arm-scroll">' + heat + '</div>' + chartBox('gkChart', mode('greeks') === '3d' ? 'tall' : '') + (mode('greeks') === '2d' ? chartBox('gkChart2', 'short') : '');
      const w = $('gkWhich').value;
      if (mode('greeks') === '2d') {
        const xs = range(S * 0.6, S * 1.4, 70);
        A.plot('gkChart', [{ x: xs, y: xs.map(s => A.greeks(s, p.K, p.T, r, q, p.v, p.call)[w]), name: w, line: { color: '#a855f7', width: 3 } }, { x: [S], y: [A.greeks(S, p.K, p.T, r, q, p.v, p.call)[w]], mode: 'markers', name: 'Now', marker: { size: 12, color: '#00d4aa' } }], { title: { text: w + ' against stock price (single option)', font: { size: 13 } }, xaxis: { title: 'Stock price' } });
        const pxs = range(S * 0.7, S * 1.3, 60), minD = Math.min(...rows.map(x => x.d), 1) || 1;
        A.plot('gkChart2', [{ x: pxs, y: pxs.map(s => val(s, 0, 0) - base), name: 'Today', line: { color: '#a855f7', width: 3 } }, { x: pxs, y: pxs.map(s => val(s, Math.min(...rows.map(x => x.d)) * 0.999, 0) - base), name: 'At first expiry', line: { color: '#ff9f43', dash: 'dash' } }], { title: { text: 'Portfolio P&L against stock price', font: { size: 13 } }, xaxis: { title: 'Stock price' }, yaxis: { title: 'P&L $' } });
      } else {
        const xs = range(S * 0.7, S * 1.3, 32), ys = range(Math.max(2, N('gkT') * 0.05), N('gkT'), 24);
        A.plot('gkChart', [{ type: 'surface', x: xs, y: ys, z: ys.map(d => xs.map(s => A.greeks(s, p.K, d / 365, r, q, p.v, p.call)[w])), colorscale: 'Plasma', colorbar: { title: w, len: 0.6 } }],
          { scene: { xaxis: { title: 'Stock price' }, yaxis: { title: 'Days to expiry' }, zaxis: { title: w } }, margin: { l: 0, r: 0, t: 10, b: 0 } });
      }
      return { verdict: overall, summary: 'Net delta ' + fmt(tot.delta, 0) + ', gamma ' + fmt(tot.gamma, 1) + ', vega $' + fmt(tot.vega, 0) + '; worst stress $' + fmt(maxLoss, 0), metrics: { 'Net delta': fmt(tot.delta, 1), 'Net vega': fmt(tot.vega, 1), 'Worst stress': '$' + fmt(maxLoss, 0) },
        bias: tot.delta > 20 ? 'bullish' : tot.delta < -20 ? 'bearish' : 'neutral', risk: true };
    }
  };

  // ── 5. IV rank and percentile ────────────────────────────────────────────
  const VOLIDX = /^\^(VIX|VXN|VXD|RVX|GVZ|OVX|VVIX|VIX9D|VIX3M)$/;
  function volSeries(sym, closes) {
    if (VOLIDX.test(sym)) return { s: closes.map(x => x / 100), proxy: false };
    const r = closes.map((c, i) => i ? Math.log(c / closes[i - 1]) : 0).slice(1), out = [];
    for (let i = 20; i < r.length; i++) out.push(A.std(r.slice(i - 20, i + 1)) * Math.sqrt(252));
    return { s: out, proxy: true };
  }
  const ivrank = {
    key: 'ivrank', title: 'IV rank and percentile', blurb: 'Where today sits in its one-year volatility range.', modes: true,
    body: () => '<div class="arm-grid">' + F('irSyms', 'Tickers (up to 5)', 'AAPL, MSFT, NVDA', { type: 'text', nolive: true, hint: 'Use ^VIX, ^VXN or ^GVZ for a true implied-vol index' }) + F('irCur', 'Current IV % (optional)', '', { hint: 'Your option\'s ATM IV, for the first ticker' }) + '</div>' +
      '<div class="arm-row"><button class="arm-btn" id="irGo">Calculate</button><label class="arm-check"><input type="checkbox" id="irDemo" data-nolive="1"> Use demo data</label></div><div class="arm-err" id="irErr"></div><div id="irOut"><div class="arm-empty">Enter tickers and press Calculate.</div></div>',
    init() { $('irGo').onclick = async () => { $('irErr').textContent = ''; $('irGo').disabled = true;
      try { const syms = $('irSyms').value.split(',').map(s => s.trim().toUpperCase()).filter(Boolean).slice(0, 5); CACHE.ir = await getHistory(syms, '2y', $('irDemo').checked); this.run(); } catch (e) { $('irErr').textContent = e.message; } $('irGo').disabled = false; }; },
    run() {
      const d = CACHE.ir; if (!d) return;
      const rows = d.symbols.map(sym => { const vs = volSeries(sym, d.closes[sym]), yr = vs.s.slice(-252); let cur = vs.s[vs.s.length - 1];
        const o = parseFloat($('irCur').value) / 100; if (sym === d.symbols[0] && o > 0) cur = o;
        const lo = Math.min(...yr), hi = Math.max(...yr), rank = Math.max(0, Math.min(100, (cur - lo) / Math.max(1e-9, hi - lo) * 100)), pctile = A.rankOf(yr, cur);
        const w = n => { const s = vs.s.slice(-n); return Math.max(0, Math.min(100, (cur - Math.min(...s)) / Math.max(1e-9, Math.max(...s) - Math.min(...s)) * 100)); };
        return { sym, vs, yr, cur, lo, hi, rank, pctile, w63: w(63), w126: w(126), w252: w(252), proxy: vs.proxy }; });
      const f = rows[0], c = f.rank < 30 ? 'good' : f.rank > 70 ? 'bad' : 'warn', volv = f.rank < 30 ? 'cheap' : f.rank > 70 ? 'rich' : 'fair';
      const dts = d.dates.slice(-f.vs.s.length).slice(-252);
      $('irOut').innerHTML = (d.demo ? '<div class="arm-note">Demo data in use.</div>' : '') + kpis([{ l: f.sym + ' IV rank', v: fmt(f.rank, 0), c }, { l: 'IV percentile', v: fmt(f.pctile, 0), c }, { l: 'Current', v: A.pct(f.cur) }, { l: '1y low / high', v: A.pct(f.lo, 0) + ' / ' + A.pct(f.hi, 0) }]) +
        verdict(c, c === 'good' ? 'Low: ' : c === 'bad' ? 'High: ' : 'Middle: ', f.sym + ' volatility is at rank ' + fmt(f.rank, 0) + ', ' + (c === 'good' ? 'near the bottom of its range, which historically has made options cheaper for buyers.' : c === 'bad' ? 'near the top of its range, which historically has made options richer for sellers.' : 'mid-range, with no strong lean either way.')) +
        (f.proxy ? '<div class="arm-note">Rank here uses 21-day realised volatility as a stand-in for implied volatility, because free historical IV is not available per stock. Enter your option\'s current IV above to compare it with that range, or use ^VIX, ^VXN or ^GVZ for a true implied-vol index.</div>' : '') +
        '<div class="arm-two">' + chartBox('irChart', mode('ivrank') === '3d' ? 'tall' : 'short') + (mode('ivrank') === '2d' ? chartBox('irGauge', 'short') : '') + '</div>';
      if (mode('ivrank') === '2d') {
        A.plot('irChart', [{ x: dts, y: f.yr.map(x => x * 100), name: f.sym + (f.proxy ? ' 21d HV' : ' IV'), line: { color: '#a855f7' } }, { x: [dts[0], dts[dts.length - 1]], y: [f.hi * 100, f.hi * 100], name: 'High', line: { color: '#ff4757', dash: 'dot' } },
          { x: [dts[0], dts[dts.length - 1]], y: [f.lo * 100, f.lo * 100], name: 'Low', line: { color: '#00d4aa', dash: 'dot' } }, { x: [dts[dts.length - 1]], y: [f.cur * 100], mode: 'markers', name: 'Today', marker: { size: 12, color: A.COLORS[c] } }], { yaxis: { title: 'Volatility %' } });
        A.plot('irGauge', [{ type: 'indicator', mode: 'gauge+number', value: f.rank, title: { text: 'IV rank' }, gauge: { axis: { range: [0, 100] }, bar: { color: A.COLORS[c] }, steps: [{ range: [0, 30], color: 'rgba(0,212,170,0.25)' }, { range: [30, 70], color: 'rgba(255,159,67,0.2)' }, { range: [70, 100], color: 'rgba(255,71,87,0.25)' }] } }], { margin: { l: 20, r: 20, t: 40, b: 10 } });
      } else {
        const wins = ['63d', '126d', '252d'];
        A.plot('irChart', [{ type: 'surface', x: wins, y: rows.map(r => r.sym), z: rows.map(r => [r.w63, r.w126, r.w252]), colorscale: [[0, '#00d4aa'], [0.5, '#ff9f43'], [1, '#ff4757']], cmin: 0, cmax: 100, colorbar: { title: 'Rank', len: 0.6 } }],
          { scene: { xaxis: { title: 'Lookback' }, yaxis: { title: 'Ticker' }, zaxis: { title: 'IV rank', range: [0, 100] } }, margin: { l: 0, r: 0, t: 10, b: 0 } });
      }
      return { verdict: c, summary: f.sym + ' IV rank ' + fmt(f.rank, 0) + ', percentile ' + fmt(f.pctile, 0) + (f.proxy ? ' (realised-vol proxy)' : ''), metrics: { 'IV rank': fmt(f.rank, 0), Percentile: fmt(f.pctile, 0) }, vol: volv, symbol: f.sym };
    }
  };

  // ── 6. Put-call parity ───────────────────────────────────────────────────
  const parity = {
    key: 'parity', title: 'Put-call parity', blurb: 'Check that a call and put price stay consistent: C − P = S − K·e^(−rT).', modes: true,
    body: () => '<div class="arm-grid">' + F('pcS', 'Stock price', 100) + F('pcK', 'Strike', 100) + F('pcT', 'Days to expiry', 90, { min: 1 }) + F('pcR', 'Interest rate %', 4.5) + F('pcQ', 'Dividend yield %', 0) + F('pcC', 'Call price', 7.1) + F('pcP', 'Put price', 5.9) + F('pcTol', 'Tolerance $', 0.1, { hint: 'Roughly your bid-ask spread' }) + '</div>' +
      '<div class="arm-row"><span style="font-size:13px;color:var(--muted)">Or check a whole chain:</span><input id="pcSym" value="SPY" style="max-width:110px;background:var(--bg3);border:1px solid var(--border2);color:var(--text);border-radius:10px;padding:9px 12px" data-nolive="1"><button class="arm-btn ghost" id="pcGo">Load chain</button><label class="arm-check"><input type="checkbox" id="pcDemo" data-nolive="1"> Use demo data</label></div><div class="arm-err" id="pcErr"></div><div id="pcOut"></div>',
    init() { $('pcGo').onclick = async () => { $('pcErr').textContent = ''; $('pcGo').disabled = true;
      try { CACHE.chain = await getChain($('pcSym').value.trim().toUpperCase(), $('pcDemo').checked); CACHE.pcChain = true; this.run(); } catch (e) { $('pcErr').textContent = e.message; } $('pcGo').disabled = false; }; },
    run() {
      const S = N('pcS'), K = N('pcK'), Tt = T('pcT'), r = N('pcR') / 100, q = N('pcQ') / 100, C = N('pcC'), P = N('pcP'), tol = Math.max(0.001, N('pcTol') || 0.1);
      if (!okNums(S, K, Tt) || !isFinite(C) || !isFinite(P)) { $('pcOut').innerHTML = ''; return; }
      const theo = S * Math.exp(-q * Tt) - K * Math.exp(-r * Tt), gap = (C - P) - theo, ag = Math.abs(gap), c = ag <= tol ? 'good' : ag <= 3 * tol ? 'warn' : 'bad';
      const why = gap > 0 ? 'The call is rich against the put (or the put is cheap). Textbook parity says that gap can be locked in with a conversion, but in practice it usually points to dividends, borrow costs or stale quotes.' : 'The put is rich against the call. Textbook parity says that gap can be locked in with a reversal, but in practice it usually points to borrow costs, early-exercise value or stale quotes.';
      let chainBlock = '', chainRows = null;
      if (CACHE.pcChain && CACHE.chain) { const ch = CACHE.chain; chainRows = ch.expiries.map(e => ({ days: e.days, pts: e.calls.map(co => { const po = e.puts.find(x => x.strike === co.strike); if (!po || !mid(co) || !mid(po)) return null;
        const Tt2 = e.days / 365; return { K: co.strike, gap: (mid(co) - mid(po)) - (ch.spot * Math.exp(-q * Tt2) - co.strike * Math.exp(-r * Tt2)) }; }).filter(Boolean) }));
        const all = chainRows.flatMap(x => x.pts), bad = all.filter(x => Math.abs(x.gap) > tol).length; chainBlock = '<div class="arm-note">Chain ' + esc(ch.symbol) + ': ' + (all.length - bad) + ' of ' + all.length + ' strike pairs sit within the tolerance.' + (ch.demo ? ' (Demo data.)' : '') + '</div>'; }
      $('pcOut').innerHTML = kpis([{ l: 'Market C − P', v: fmt(C - P, 3) }, { l: 'Theoretical S − K·e^(−rT)', v: fmt(theo, 3) }, { l: 'Parity gap', v: fmt(gap, 3), c }]) + verdict(c, c === 'good' ? 'Within tolerance: ' : c === 'warn' ? 'Small mismatch: ' : 'Mismatch: ', c === 'good' ? 'The call and put prices are consistent with parity.' : why) + chainBlock + chartBox('pcChart', mode('parity') === '3d' ? 'tall' : '');
      if (mode('parity') === '2d') {
        if (chainRows) { const pts = chainRows.find(x => x.pts.length > 3) || chainRows[0];
          A.plot('pcChart', [{ type: 'bar', x: pts.pts.map(x => x.K), y: pts.pts.map(x => x.gap), marker: { color: pts.pts.map(x => Math.abs(x.gap) <= tol ? '#00d4aa' : Math.abs(x.gap) <= 3 * tol ? '#ff9f43' : '#ff4757') }, name: 'Gap' }], { title: { text: 'Parity gap by strike (' + pts.days + ' days)', font: { size: 13 } }, xaxis: { title: 'Strike' }, yaxis: { title: 'Gap $' } }); }
        else { const ks = range(K * 0.7, K * 1.3, 40); A.plot('pcChart', [{ x: ks, y: ks.map(k => S * Math.exp(-q * Tt) - k * Math.exp(-r * Tt)), name: 'Parity line', line: { color: '#a855f7', width: 3 } }, { x: [K], y: [C - P], mode: 'markers', name: 'Market C − P', marker: { size: 14, color: A.COLORS[c], symbol: 'diamond' } }], { xaxis: { title: 'Strike' }, yaxis: { title: 'Call − Put' } }); }
      } else if (chainRows) {
        const live = chainRows.filter(x => x.pts.length > 3), ks = Array.from(new Set(live.flatMap(x => x.pts.map(p => p.K)))).sort((a, b) => a - b);
        A.plot('pcChart', [{ type: 'surface', x: ks, y: live.map(x => x.days), z: live.map(x => ks.map(k => { const p = x.pts.find(y => y.K === k); return p ? p.gap : null; })), colorscale: [[0, '#ff4757'], [0.5, '#00d4aa'], [1, '#ff4757']], cmid: 0, colorbar: { title: 'Gap $', len: 0.6 } }],
          { scene: { xaxis: { title: 'Strike' }, yaxis: { title: 'Days to expiry' }, zaxis: { title: 'Gap $' } }, margin: { l: 0, r: 0, t: 10, b: 0 } });
      } else {
        const ks = range(K * 0.8, K * 1.2, 26), ds = range(7, Math.max(30, N('pcT') * 2), 20);
        A.plot('pcChart', [{ type: 'surface', x: ks, y: ds, z: ds.map(d => ks.map(k => (C - P) - (S * Math.exp(-q * d / 365) - k * Math.exp(-r * d / 365)))), colorscale: [[0, '#ff4757'], [0.5, '#00d4aa'], [1, '#ff4757']], cmid: 0, colorbar: { title: 'Gap $', len: 0.6 } }],
          { scene: { xaxis: { title: 'Strike' }, yaxis: { title: 'Days' }, zaxis: { title: 'Gap if C, P unchanged' } }, margin: { l: 0, r: 0, t: 10, b: 0 } });
      }
      return { verdict: c, summary: 'Parity gap ' + fmt(gap, 3) + ' vs tolerance ' + fmt(tol, 2), metrics: { Gap: fmt(gap, 3), Tolerance: fmt(tol, 2) }, risk: true };
    }
  };

  // ── 7. Volatility-adjusted position sizing ───────────────────────────────
  function sizeFor(o, v, riskPct) {
    const T0 = o.dte / 365, ht = o.hold / 365, em = o.S * v * Math.sqrt(ht);
    const now = A.bs(o.S, o.K, T0, o.r, o.q, v, o.call);
    const s2 = o.S + em * (o.long ? (o.call ? -1 : 1) : (o.call ? 1 : -1)); // the adverse 1-sigma move
    const v2 = v * (o.long ? 0.8 : 1.2), then = A.bs(Math.max(0.01, s2), o.K, Math.max(1e-6, T0 - ht), o.r, o.q, v2, o.call);
    let loss = o.long ? Math.max(0, now - then) : Math.max(0, then - now); loss *= 100; if (o.long) loss = Math.min(loss, now * 100);
    return { loss, em, now, n: loss > 0 ? Math.floor(o.acct * riskPct / loss) : 0 };
  }
  const size = {
    key: 'size', title: 'Position sizing', blurb: 'How many contracts fit a risk budget once volatility is taken into account.', modes: true,
    body: () => '<div class="arm-grid">' + F('szAcct', 'Account size $', 25000) + F('szRisk', 'Risk per trade %', 2, { hint: 'Share of the account you are willing to lose' }) + common('sz') +
      F('szSide', 'Side', 'long', { options: [['long', 'Long (buy)'], ['short', 'Short (sell)']] }) + F('szHold', 'Holding days', 10, { min: 1 }) + F('szN', 'Contracts you plan', 1, { min: 0 }) + '</div><div id="szOut"></div>',
    run() {
      const p = readCommon('sz'), o = { acct: N('szAcct'), S: p.S, K: p.K, dte: N('szT'), hold: Math.min(N('szHold'), N('szT') - 0.5), r: p.r, q: p.q, call: p.call, long: $('szSide').value === 'long' }, rp = N('szRisk') / 100, plan = N('szN');
      if (!okNums(o.acct, p.S, p.K, o.dte, p.v, rp) || !(o.hold > 0)) { $('szOut').innerHTML = '<div class="arm-empty">Enter positive numbers (holding days must be shorter than days to expiry).</div>'; return; }
      const r0 = sizeFor(o, p.v, rp), ratio = r0.n > 0 ? plan / r0.n : (plan > 0 ? 9 : 0), c = ratio <= 1 ? 'good' : ratio <= 1.5 ? 'warn' : 'bad', budget = o.acct * rp;
      $('szOut').innerHTML = kpis([{ l: 'Max contracts', v: r0.n, c: 'good' }, { l: 'Risk per contract', v: '$' + fmt(r0.loss, 0) }, { l: 'Risk budget', v: '$' + fmt(budget, 0) }, { l: '1σ expected move', v: '±' + fmt(r0.em, 2) }, { l: 'Option price', v: fmt(r0.now, 2) }, { l: 'Your plan uses', v: A.pct(ratio, 0) + ' of max', c }]) +
        verdict(c, c === 'good' ? 'Within budget: ' : c === 'warn' ? 'Stretching: ' : 'Oversized: ', plan + ' contracts would risk about $' + fmt(plan * r0.loss, 0) + ' against a $' + fmt(budget, 0) + ' budget. The stress case is a 1σ adverse move over ' + o.hold + ' days with implied volatility ' + (o.long ? 'falling' : 'rising') + ' 20%.') + chartBox('szChart', mode('size') === '3d' ? 'tall' : '');
      if (mode('size') === '2d') { const vs = range(0.1, 1, 40); A.plot('szChart', [{ x: vs.map(x => x * 100), y: vs.map(v => sizeFor(o, v, rp).n), name: 'Max contracts', line: { color: '#a855f7', width: 3 }, mode: 'lines' }, { x: [p.v * 100], y: [r0.n], mode: 'markers', name: 'Your IV', marker: { size: 13, color: A.COLORS[c] } }, { x: [10, 100], y: [plan, plan], name: 'Planned', line: { color: '#ff9f43', dash: 'dot' } }], { xaxis: { title: 'Implied volatility %' }, yaxis: { title: 'Max contracts' } }); }
      else { const vs = range(0.1, 1, 22), rs = range(0.005, 0.05, 18); A.plot('szChart', [{ type: 'surface', x: vs.map(x => x * 100), y: rs.map(x => x * 100), z: rs.map(rr => vs.map(v => sizeFor(o, v, rr).n)), colorscale: 'Viridis', colorbar: { title: 'Contracts', len: 0.6 } }], { scene: { xaxis: { title: 'IV %' }, yaxis: { title: 'Account risk %' }, zaxis: { title: 'Max contracts' } }, margin: { l: 0, r: 0, t: 10, b: 0 } }); }
      return { verdict: c, summary: 'Max ' + r0.n + ' contracts at ' + A.pct(rp) + ' risk; plan of ' + plan + ' uses ' + A.pct(ratio, 0), metrics: { 'Max contracts': r0.n, 'Risk / contract': '$' + fmt(r0.loss, 0) }, risk: true };
    }
  };

  // ── 8. Kalman filter ─────────────────────────────────────────────────────
  const kalman = {
    key: 'kalman', title: 'Kalman filter', blurb: 'Trend and dynamic hedge ratio across up to three tickers.', modes: true,
    body: () => '<div class="arm-grid">' + F('kfA', 'Ticker 1 (the one to explain)', 'AAPL', { type: 'text', nolive: true }) + F('kfB', 'Ticker 2', 'QQQ', { type: 'text', nolive: true }) + F('kfC', 'Ticker 3 (optional)', 'MSFT', { type: 'text', nolive: true }) +
      F('kfP', 'History', '1y', { options: [['6mo', '6 months'], ['1y', '1 year'], ['2y', '2 years']], nolive: true }) + F('kfD', 'Adaptivity (log10 δ)', -4, { hint: 'Higher = ratios move faster' }) + '</div>' +
      '<div class="arm-row"><button class="arm-btn" id="kfGo">Run filter</button><label class="arm-check"><input type="checkbox" id="kfDemo" data-nolive="1"> Use demo data</label></div><div class="arm-err" id="kfErr"></div><div id="kfOut"><div class="arm-empty">Enter up to three tickers and press Run filter.</div></div>',
    init() { $('kfGo').onclick = async () => { $('kfErr').textContent = ''; $('kfGo').disabled = true;
      try { const syms = [$('kfA').value, $('kfB').value, $('kfC').value].map(s => s.trim().toUpperCase()).filter(Boolean); if (syms.length < 2) throw new Error('Enter at least two tickers.');
        CACHE.kf = await getHistory(Array.from(new Set(syms)), $('kfP').value, $('kfDemo').checked); this.run(); } catch (e) { $('kfErr').textContent = e.message; } $('kfGo').disabled = false; }; },
    run() {
      const d = CACHE.kf; if (!d) return; const syms = d.symbols, y = d.closes[syms[0]], X = y.map((_, i) => syms.slice(1).map(s => d.closes[s][i]));
      const delta = Math.pow(10, Math.max(-7, Math.min(-1, N('kfD') || -4))), ve = Math.max(1e-6, A.cov(y, y) * 1e-3), reg = A.kalmanRegression(y, X, delta, ve), last = reg.z[reg.z.length - 1], az = Math.abs(last);
      const c = az > 2 ? 'bad' : az > 1 ? 'warn' : 'good', tr = syms.map(s => A.kalmanTrend(d.closes[s].map(Math.log), 1e-6, 1e-9, 1e-4)), slopeA = tr[0].slope[tr[0].slope.length - 1] * 252;
      const bias = slopeA > 0.05 ? 'bullish' : slopeA < -0.05 ? 'bearish' : 'neutral', bl = reg.betas[reg.betas.length - 1];
      $('kfOut').innerHTML = (d.demo ? '<div class="arm-note">Demo data in use.</div>' : '') + kpis([{ l: syms[0] + ' trend (annualised)', v: A.pct(slopeA), c: bias === 'bullish' ? 'good' : bias === 'bearish' ? 'bad' : 'warn' }].concat(syms.slice(1).map((s, i) => ({ l: 'Hedge ratio vs ' + s, v: fmt(bl[i], 3) })), [{ l: 'Spread z-score', v: fmt(last, 2), c }])) +
        verdict(c, c === 'good' ? 'Normal: ' : c === 'warn' ? 'Stretching: ' : 'Stretched: ', syms[0] + ' is ' + fmt(Math.abs(last), 1) + ' standard deviations ' + (last >= 0 ? 'above' : 'below') + ' where the filter says it should sit against ' + syms.slice(1).join(' and ') + '. Beyond 2 is unusual and has historically tended to partly revert, though not always.') +
        chartBox('kfChart', mode('kalman') === '3d' ? 'tall' : '') + (mode('kalman') === '2d' ? chartBox('kfChart2', 'short') + chartBox('kfChart3', 'short') : '');
      const rb = s => d.closes[s].map(x => x / d.closes[s][0] * 100), cols = ['#a855f7', '#00d4aa', '#ff9f43'];
      if (mode('kalman') === '2d') {
        A.plot('kfChart', syms.flatMap((s, i) => [{ x: d.dates, y: rb(s), name: s, line: { color: cols[i], width: 1 }, opacity: 0.45 }, { x: d.dates, y: tr[i].level.map(l => Math.exp(l) / d.closes[s][0] * 100), name: s + ' filtered', line: { color: cols[i], width: 3 } }]), { title: { text: 'Prices (rebased to 100) and Kalman trend', font: { size: 13 } } });
        A.plot('kfChart2', syms.slice(1).map((s, i) => ({ x: d.dates, y: reg.betas.map(b => b[i]), name: 'β ' + s, line: { color: cols[i + 1] } })), { title: { text: 'Dynamic hedge ratio', font: { size: 13 } } });
        A.plot('kfChart3', [{ x: d.dates, y: reg.z, name: 'z-score', line: { color: '#a855f7' } }, { x: [d.dates[0], d.dates[d.dates.length - 1]], y: [2, 2], line: { color: '#ff4757', dash: 'dot' }, name: '+2' }, { x: [d.dates[0], d.dates[d.dates.length - 1]], y: [-2, -2], line: { color: '#ff4757', dash: 'dot' }, name: '−2' }], { title: { text: 'Spread z-score', font: { size: 13 } } });
      } else {
        A.plot('kfChart', [{ type: 'scatter3d', mode: 'lines+markers', x: reg.betas.map(b => b[0]), y: reg.betas.map(b => syms.length > 2 ? b[1] : b[b.length - 1]), z: d.dates.map((_, i) => i), marker: { size: 3, color: reg.z, colorscale: 'RdBu', reversescale: true, cmin: -3, cmax: 3, colorbar: { title: 'z', len: 0.6 } }, line: { color: 'rgba(168,85,247,0.5)' }, text: d.dates, hovertemplate: '%{text}<extra></extra>' }],
          { scene: { xaxis: { title: 'β ' + syms[1] }, yaxis: { title: syms.length > 2 ? 'β ' + syms[2] : 'Intercept' }, zaxis: { title: 'Day' } }, margin: { l: 0, r: 0, t: 10, b: 0 } });
      }
      return { verdict: c, summary: syms[0] + ' trend ' + A.pct(slopeA) + ' a year, spread z ' + fmt(last, 2), metrics: { Trend: A.pct(slopeA), 'Spread z': fmt(last, 2) }, bias, symbol: syms[0] };
    }
  };

  // ── 9. Modern Portfolio Theory ───────────────────────────────────────────
  const mpt = {
    key: 'mpt', title: 'Portfolio theory', blurb: 'Efficient frontier with optional Black-Litterman and risk parity.', modes: true,
    body: () => '<div class="arm-grid">' + F('mpSyms', 'Tickers (2 to 10)', 'AAPL, MSFT, JNJ, XOM, GLD, TLT', { type: 'text', nolive: true }) + F('mpBench', 'Benchmark', 'SPY', { type: 'text', nolive: true }) + F('mpP', 'History', '2y', { options: [['1y', '1 year'], ['2y', '2 years'], ['5y', '5 years']], nolive: true }) + F('mpRf', 'Risk-free rate %', 4, { nolive: true }) + '</div>' +
      '<div class="arm-row"><label class="arm-check"><input type="checkbox" id="mpBL" data-nolive="1"> Black-Litterman</label><label class="arm-check"><input type="checkbox" id="mpRP" data-nolive="1"> Risk parity</label><label class="arm-check"><input type="checkbox" id="mpDemo" data-nolive="1"> Use demo data</label></div>' +
      '<div id="mpViews" style="display:none"><div class="arm-note">Black-Litterman blends an equal-weight market prior with your views. Enter an expected annual return (%) for any ticker you have a view on and leave the rest blank.</div><div class="arm-grid" id="mpViewGrid"></div>' + F('mpConf', 'Confidence in views (10 to 90%)', 50, { nolive: true }) + '</div>' +
      '<div class="arm-row"><button class="arm-btn" id="mpGo">Build portfolios</button></div><div class="arm-err" id="mpErr"></div><div id="mpOut"><div class="arm-empty">Enter tickers and press Build portfolios.</div></div>',
    init() { const syms = () => $('mpSyms').value.split(',').map(s => s.trim().toUpperCase()).filter(Boolean).slice(0, 10);
      const draw = () => { $('mpViews').style.display = $('mpBL').checked ? 'block' : 'none'; $('mpViewGrid').innerHTML = syms().map((s, i) => F('mpV' + i, s + ' view %', '', { nolive: true })).join(''); };
      $('mpBL').onchange = draw; $('mpSyms').addEventListener('change', draw); draw();
      $('mpGo').onclick = async () => { $('mpErr').textContent = ''; $('mpGo').disabled = true;
        try { const s = syms(); if (s.length < 2) throw new Error('Enter at least two tickers.'); const bm = $('mpBench').value.trim().toUpperCase(), all = Array.from(new Set(s.concat(bm ? [bm] : [])));
          CACHE.mp = await getHistory(all, $('mpP').value, $('mpDemo').checked); CACHE.mp.assets = s; CACHE.mp.bench = bm && !s.includes(bm) ? bm : null; CACHE.mpViews = s.map((_, i) => parseFloat($('mpV' + i) ? $('mpV' + i).value : '')); this.run(); } catch (e) { $('mpErr').textContent = e.message; } $('mpGo').disabled = false; }; },
    run() {
      const d = CACHE.mp; if (!d) return; const rf = (N('mpRf') || 0) / 100, assets = d.assets, R = assets.map(s => A.returns(d.closes[s])), bench = d.bench ? A.returns(d.closes[d.bench]) : null, n = assets.length;
      const Sg = A.covMatrix(R).map(r => r.map(x => x * 252)), mu = R.map(r => A.mean(r) * 252), cands = [{ name: 'Equal weight', w: Array(n).fill(1 / n) }, { name: 'Max Sharpe', w: A.maxSharpe(mu, Sg, rf) }, { name: 'Min variance', w: A.minVariance(Sg) }];
      if ($('mpBL').checked) { const views = {}; CACHE.mpViews.forEach((v, i) => { if (isFinite(v)) views[i] = v / 100; }); const conf = Math.max(0.1, Math.min(0.9, (N('mpConf') || 50) / 100)), mbl = A.blackLitterman(Sg, views, conf, 2.5, 0.05); cands.push({ name: 'Black-Litterman', w: A.maxSharpe(mbl, Sg, rf) }); }
      if ($('mpRP').checked) cands.push({ name: 'Risk parity', w: A.riskParity(Sg) });
      cands.forEach(c => { c.m = A.portfolioMetrics(c.w, R, bench, rf); });
      const best = cands[1].m, cc = best.sharpe > 1 ? 'good' : best.sharpe > 0.5 ? 'warn' : 'bad', rate = (v, g, a) => v >= g ? 'good' : v >= a ? 'warn' : 'bad';
      const row = (lab, f, cls) => '<tr><td>' + lab + '</td>' + cands.map(c => { const v = f(c.m); return '<td' + (cls ? ' style="color:' + A.COLORS[cls(c.m)] + ';font-weight:700"' : '') + '>' + v + '</td>'; }).join('') + '</tr>';
      $('mpOut').innerHTML = (d.demo ? '<div class="arm-note">Demo data in use.</div>' : '') + verdict(cc, A.VERDICT_WORD[cc] + ': ', 'The max-Sharpe mix scored ' + fmt(best.sharpe, 2) + ' on this history. ' + (cc === 'good' ? 'Above 1 is strong, though it is in-sample.' : cc === 'warn' ? 'Between 0.5 and 1 is moderate.' : 'Below 0.5 is weak for the risk taken.')) +
        '<div class="arm-scroll"><table class="arm-table"><tr><th>Weights</th>' + cands.map(c => '<th>' + c.name + '</th>').join('') + '</tr>' + assets.map((s, i) => '<tr><td>' + esc(s) + '</td>' + cands.map(c => '<td>' + A.pct(c.w[i], 1) + '</td>').join('') + '</tr>').join('') + '</table>' +
        '<table class="arm-table"><tr><th>Risk and return</th>' + cands.map(c => '<th>' + c.name + '</th>').join('') + '</tr>' +
        row('Annual return', m => A.pct(m.ann)) + row('Volatility', m => A.pct(m.vol)) + row('Sharpe ratio', m => fmt(m.sharpe, 2), m => rate(m.sharpe, 1, 0.5)) + row('Sortino ratio', m => fmt(m.sortino, 2), m => rate(m.sortino, 1.5, 0.75)) +
        row('Max drawdown', m => A.pct(m.maxDD), m => m.maxDD > -0.15 ? 'good' : m.maxDD > -0.3 ? 'warn' : 'bad') + row('Calmar ratio', m => fmt(m.calmar, 2), m => rate(m.calmar, 1, 0.5)) + row('Treynor ratio', m => bench ? fmt(m.treynor, 3) : 'add benchmark') +
        row('VaR 95% (1 day)', m => A.pct(m.var95, 2)) + row('CVaR 95% (1 day)', m => A.pct(m.cvar95, 2)) + '</table></div>' +
        '<div class="arm-note">All figures come from the history above (in-sample), so they describe the past rather than a forecast. Weights are long-only and add to 100%.</div>' + chartBox('mpChart', mode('mpt') === '3d' ? 'tall' : '') + (mode('mpt') === '2d' ? chartBox('mpChart2', 'short') : '');
      const rng = A.rng(11), cloud = Array.from({ length: 1500 }, () => { const x = Array.from({ length: n }, () => -Math.log(rng() + 1e-12)), t = x.reduce((a, b) => a + b, 0), w = x.map(v => v / t), ret = A.dot(mu, w), vol = Math.sqrt(Math.max(0, A.dot(w, A.mulMV(Sg, w)))); return { ret, vol, sh: (ret - rf) / vol }; });
      const pcol = ['#8892b0', '#a855f7', '#00d4aa', '#38bdf8', '#ff9f43'];
      if (mode('mpt') === '2d') {
        A.plot('mpChart', [{ x: cloud.map(c => c.vol * 100), y: cloud.map(c => c.ret * 100), mode: 'markers', name: 'Random mixes', marker: { size: 4, color: cloud.map(c => c.sh), colorscale: 'Viridis', showscale: true, colorbar: { title: 'Sharpe', len: 0.6 } } }].concat(cands.map((c, i) => ({ x: [c.m.vol * 100], y: [c.m.ann * 100], mode: 'markers', name: c.name, marker: { size: 14, color: pcol[i], line: { color: '#fff', width: 1 } } }))), { title: { text: 'Risk and return: random long-only mixes and the optimised portfolios', font: { size: 13 } }, xaxis: { title: 'Volatility %' }, yaxis: { title: 'Annual return %' } });
        A.plot('mpChart2', cands.map((c, i) => ({ x: c.m.curve.map((_, k) => k), y: c.m.curve.map(v => v * 100), name: c.name, line: { color: pcol[i] } })), { title: { text: 'Growth of 100 over the period', font: { size: 13 } }, xaxis: { title: 'Trading day' } });
      } else {
        A.plot('mpChart', [{ type: 'scatter3d', mode: 'markers', x: cloud.map(c => c.vol * 100), y: cloud.map(c => c.ret * 100), z: cloud.map(c => c.sh), marker: { size: 2.5, color: cloud.map(c => c.sh), colorscale: 'Viridis', opacity: 0.6 }, name: 'Random mixes' }].concat(cands.map((c, i) => ({ type: 'scatter3d', mode: 'markers', x: [c.m.vol * 100], y: [c.m.ann * 100], z: [c.m.sharpe], name: c.name, marker: { size: 7, color: pcol[i] } }))),
          { scene: { xaxis: { title: 'Volatility %' }, yaxis: { title: 'Return %' }, zaxis: { title: 'Sharpe' } }, margin: { l: 0, r: 0, t: 10, b: 0 } });
      }
      const top = assets.map((s, i) => [s, cands[1].w[i]]).sort((a, b) => b[1] - a[1]).slice(0, 3).map(x => x[0] + ' ' + A.pct(x[1], 0)).join(', ');
      return { verdict: cc, summary: 'Max-Sharpe mix: Sharpe ' + fmt(best.sharpe, 2) + ', max drawdown ' + A.pct(best.maxDD) + ' (' + top + ')', metrics: { Sharpe: fmt(best.sharpe, 2), 'Max drawdown': A.pct(best.maxDD), 'VaR 95%': A.pct(best.var95, 2) }, risk: true };
    }
  };

  const CALCS = [bs, amer, iv, greeks, ivrank, parity, size, kalman, mpt];

  // ── Panel shell: tabs, 2D/3D toggle, Save toggle ─────────────────────────
  let timer = null;
  function currentCalc() { return CALCS.find(c => c.key === active); }
  function runActive() {
    const c = currentCalc(); let res;
    try { res = c.run(); } catch (e) { console.error(e); const el = document.querySelector('#armBody .arm-err.run'); if (el) el.textContent = 'Something went wrong with those inputs.'; }
    if (res) { LAST[c.key] = res; if (A.store.has(c.key)) A.store.setResult(c.key, snap(c, res)); }
    refreshSaveBtn();
  }
  const snap = (c, r) => Object.assign({}, r, { key: c.key, title: c.title, savedAt: new Date().toISOString() });
  function refreshSaveBtn() { const b = $('armSave'); if (b) b.classList.toggle('on', A.store.has(active)); renderTabs(); }
  function renderTabs() { $('armTabs').innerHTML = CALCS.map(c => '<button class="arm-tab' + (c.key === active ? ' on' : '') + (A.store.has(c.key) ? ' saved' : '') + '" data-k="' + c.key + '"><span class="dot" title="Saved"></span><b>' + c.title + '</b><small>' + c.blurb + '</small></button>').join(''); }
  function mount(key) {
    active = key; const c = currentCalc(); MODE[key] = MODE[key] || '2d';
    $('armPanel').innerHTML = '<div class="arm-panel-head"><div><h2>' + c.title + '</h2><div class="sub">' + c.blurb + '</div></div><div class="arm-controls">' +
      (c.modes ? '<div class="arm-seg" id="armSeg"><button data-m="2d" class="' + (MODE[key] === '2d' ? 'on' : '') + '">2D</button><button data-m="3d" class="' + (MODE[key] === '3d' ? 'on' : '') + '">3D</button></div>' : '') +
      '<button class="arm-save" id="armSave" title="Keep this result for the Strategy Builder"><span class="sw"></span>Save result</button></div></div><div id="armBody">' + c.body() + '</div>';
    if (c.init) c.init.call(c);
    $('armBody').addEventListener('input', e => { if (e.target.dataset.nolive || e.target.closest('[data-nolive]')) return; clearTimeout(timer); timer = setTimeout(runActive, 250); });
    $('armBody').addEventListener('change', e => { if (e.target.tagName === 'SELECT' && !e.target.dataset.nolive) runActive(); });
    const seg = $('armSeg'); if (seg) seg.onclick = e => { const m = e.target.dataset.m; if (!m) return; MODE[key] = m; seg.querySelectorAll('button').forEach(b => b.classList.toggle('on', b.dataset.m === m)); runActive(); };
    $('armSave').onclick = () => { if (A.store.has(key)) A.store.removeResult(key); else { if (!LAST[key]) runActive(); if (LAST[key]) A.store.setResult(key, snap(c, LAST[key])); else alert('Run this calculator first so there is a result to save.'); } refreshSaveBtn(); };
    runActive();
  }

  // ── Strategy Builder ─────────────────────────────────────────────────────
  const STRUCT = { 'bullish|cheap': ['Long call or call debit spread', 'Bullish trend with cheap options is the textbook case for buying premium.'], 'bullish|rich': ['Cash-secured put or bull put spread', 'Bullish trend with rich options is the textbook case for selling premium on the downside.'],
    'bearish|cheap': ['Long put or put debit spread', 'Bearish trend with cheap options is the textbook case for buying downside premium.'], 'bearish|rich': ['Bear call spread', 'Bearish trend with rich options is the textbook case for selling premium on the upside.'],
    'neutral|rich': ['Iron condor or short strangle (defined-risk versions are the textbook form)', 'No trend with rich options is the textbook case for collecting premium.'], 'neutral|cheap': ['Long straddle or strangle', 'No trend but cheap options is the textbook case for owning volatility.'] };
  function build() {
    const st = A.store.get(), res = Object.values(st.results), el = $('sbOut'); if (!el) return null;
    if (!res.length) { el.innerHTML = '<div class="arm-empty">Switch on "Save result" in any calculator above and it will appear here.</div>'; return null; }
    const biases = res.filter(r => r.bias && r.bias !== 'neutral').map(r => r.bias), bull = biases.filter(b => b === 'bullish').length, bear = biases.filter(b => b === 'bearish').length;
    const bias = bull > bear ? 'bullish' : bear > bull ? 'bearish' : (res.some(r => r.bias) ? 'neutral' : null), conflict = bull > 0 && bear > 0;
    const vols = res.map(r => r.vol).filter(Boolean), cheap = vols.filter(v => v === 'cheap').length, rich = vols.filter(v => v === 'rich').length, vol = cheap > rich ? 'cheap' : rich > cheap ? 'rich' : (vols.length ? 'fair' : null);
    const q = { good: 1, warn: 0.5, bad: 0, neutral: 0.5 }, meanQ = A.mean(res.map(r => q[r.verdict] == null ? 0.5 : q[r.verdict])), cover = Math.min(1, res.length / 5);
    let score = Math.round(100 * (0.6 * meanQ + 0.4 * cover)); if (conflict) score = Math.max(0, score - 15); if (!bias && !vol) score = Math.min(score, 40);
    const key = (bias || 'neutral') + '|' + (vol === 'fair' || !vol ? '' : vol), sug = STRUCT[key] || (vol === 'fair' || !vol ? (bias ? ['No clear options structure', 'Volatility looks fairly priced, so the options structure does not lean either way. A directional view alone is not enough to pick one.'] : ['Not enough to build a structure yet', 'Save a Kalman filter (trend) and an IV rank or Black-Scholes check (volatility) to get a structure.']) : ['Not enough to build a structure yet', 'Save more results.']);
    const sc = score >= 70 ? 'good' : score >= 45 ? 'warn' : 'bad', mp = st.results.mpt;
    const checks = res.filter(r => r.risk).map(r => '<li><span class="arm-tag ' + r.verdict + '">' + A.VERDICT_WORD[r.verdict] + '</span><span><b>' + esc(r.title) + '</b>: ' + esc(r.summary) + '</span></li>').join('') || '<li>No risk checks saved yet. Greeks, Parity, Sizing and Portfolio results count as risk checks.</li>';
    const sym = ($('sbSym').value.trim().toUpperCase()) || (res.find(r => r.symbol) || {}).symbol || '';
    el.innerHTML = '<div class="arm-two"><div><div class="arm-score" style="color:' + A.COLORS[sc] + '">' + score + '</div><div style="font-size:13px;color:var(--muted);margin:4px 0 10px">Conviction score out of 100. It measures how sound and consistent your saved results are: their quality (60%), how many analyses you covered (40%), less 15 if they disagree on direction.</div><div class="arm-bar"><i style="width:' + score + '%;background:' + A.COLORS[sc] + '"></i></div></div>' +
      '<div><h3 style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--arm-accent);margin-bottom:6px">Structure history associates with this set-up</h3><p style="font-size:16px;font-weight:700;margin-bottom:6px">' + sug[0] + '</p><p style="font-size:13px;color:var(--muted);line-height:1.6">' + sug[1] + '</p>' +
      '<p style="font-size:13px;margin-top:10px">Direction: <b>' + (bias || 'not set') + '</b>' + (conflict ? ' (your results disagree)' : '') + ' &middot; Volatility: <b>' + (vol || 'not set') + '</b>' + (mp ? '<br>Portfolio angle: ' + esc(mp.summary) : '') + '</p></div></div>' +
      '<h3 style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--arm-accent);margin:18px 0 6px">Risk checks</h3><ul class="arm-list">' + checks + '</ul>' +
      '<div class="arm-note">Educational use only. This describes how textbook strategies line up with the numbers you saved. It is not a recommendation to buy or sell anything, and past patterns do not predict future results.</div>';
    return { symbol: sym, bias: bias || 'neutral', vol: vol || 'fair', structure: sug[0], score, built: res.map(r => r.key) };
  }
  function renderSaved() {
    const st = A.store.get(), res = Object.values(st.results);
    $('sbSaved').innerHTML = res.length ? res.map(r => '<span class="arm-tag ' + (r.verdict || 'neutral') + '" style="margin:0 6px 6px 0;padding:5px 12px;cursor:pointer" data-rm="' + r.key + '" title="Click to remove">' + esc(r.title) + ' ×</span>').join('') : '<span style="color:var(--muted);font-size:13px">Nothing saved yet.</span>';
    $('sbPlans').innerHTML = st.plans.length ? '<h3 style="font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:16px 0 6px">Saved plans (used by the COT Report)</h3>' + st.plans.map(p => '<div class="arm-row" style="margin:4px 0"><span class="arm-tag ' + (p.score >= 70 ? 'good' : p.score >= 45 ? 'warn' : 'bad') + '">' + p.score + '</span><b>' + esc(p.name) + '</b><span style="color:var(--muted);font-size:13px">' + esc(p.symbol || 'no symbol') + ' &middot; ' + esc(p.bias) + ' &middot; ' + esc(p.structure) + '</span><button class="arm-btn ghost" style="padding:4px 10px" data-rmplan="' + esc(p.name) + '">Delete</button></div>').join('') : '';
  }

  // ── Boot ─────────────────────────────────────────────────────────────────
  function boot() {
    $('armTabs').onclick = e => { const b = e.target.closest('.arm-tab'); if (b) mount(b.dataset.k); };
    $('sbSaved').onclick = e => { if (e.target.dataset.rm) A.store.removeResult(e.target.dataset.rm); };
    $('sbPlans').onclick = e => { if (e.target.dataset.rmplan) A.store.removePlan(e.target.dataset.rmplan); };
    $('sbSym').oninput = () => build();
    $('sbSave').onclick = () => { const b = build(), name = ($('sbName').value || '').trim(); if (!b) return; if (!name) { $('sbMsg').textContent = 'Give the plan a name first.'; return; } A.store.addPlan(Object.assign({ name, createdAt: new Date().toISOString() }, b)); $('sbMsg').textContent = 'Saved "' + name + '". It is now available on the COT Report page.'; };
    A.store.onChange(() => { renderSaved(); build(); renderTabs(); const bt = $('armSave'); if (bt) bt.classList.toggle('on', A.store.has(active)); });
    mount('bs'); A.store.load();
  }
  document.addEventListener('DOMContentLoaded', boot);
})();
