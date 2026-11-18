/* The Armoury, COT Report page: search the CFTC Traders in Financial Futures data and compare the
   positioning with a saved strategy. Educational and historical only. */
(function () {
  'use strict';
  const A = window.Armoury, esc = A.esc, fmt = A.fmt, $ = id => document.getElementById(id);
  let CUR = null; // { market, rows, series }

  // Tickers mapped to the TFF market name to search for. TFF covers financial futures only (no gold or oil).
  const MAP = { SPY: 'S&P 500', VOO: 'S&P 500', IVV: 'S&P 500', '^GSPC': 'S&P 500', 'ES=F': 'S&P 500', QQQ: 'NASDAQ', '^NDX': 'NASDAQ', 'NQ=F': 'NASDAQ', IWM: 'RUSSELL', '^RUT': 'RUSSELL', DIA: 'DJIA', '^DJI': 'DJIA',
    TLT: 'UST BOND', IEF: '10-YEAR', ZN: '10-YEAR', 'ZN=F': '10-YEAR', 'ZB=F': 'UST BOND', SHY: '2-YEAR', 'EURUSD=X': 'EURO FX', FXE: 'EURO FX', 'GBPUSD=X': 'BRITISH POUND', 'USDJPY=X': 'JAPANESE YEN', FXY: 'JAPANESE YEN',
    'AUDUSD=X': 'AUSTRALIAN DOLLAR', 'USDCAD=X': 'CANADIAN DOLLAR', 'USDCHF=X': 'SWISS FRANC', 'BTC-USD': 'BITCOIN', IBIT: 'BITCOIN', GBTC: 'BITCOIN', 'ETH-USD': 'ETHER', '^VIX': 'VIX', UUP: 'U.S. DOLLAR INDEX', 'DX-Y.NYB': 'U.S. DOLLAR INDEX' };

  // ── Data ─────────────────────────────────────────────────────────────────
  function demoMarkets(q) {
    const all = [['13874A', 'E-MINI S&P 500 - CHICAGO MERCANTILE EXCHANGE', 2100000], ['209742', 'NASDAQ MINI - CHICAGO MERCANTILE EXCHANGE', 290000], ['099741', 'EURO FX - CHICAGO MERCANTILE EXCHANGE', 700000], ['133741', 'BITCOIN - CHICAGO MERCANTILE EXCHANGE', 30000], ['043602', 'UST 10Y NOTE - CHICAGO BOARD OF TRADE', 4300000]];
    const words = (q || '').toUpperCase().split(/\s+/).filter(Boolean);
    return all.filter(m => words.every(w => m[1].includes(w))).map(m => ({ code: m[0], name: m[1], latest: new Date().toISOString().slice(0, 10), oi: m[2] }));
  }
  function demoReport(code) {
    const rng = A.rng(parseInt(code, 36) % 9973 + 5), rows = []; let am = 200000, lf = -150000, dl = 20000, d = new Date(); d.setDate(d.getDate() - 7 * 200);
    for (let i = 0; i < 200; i++) { d = new Date(d.getTime() + 7 * 86400000); am += (rng() - 0.48) * 30000; lf += (rng() - 0.52) * 30000; dl += (rng() - 0.5) * 8000;
      const oi = 2000000 + 200000 * Math.sin(i / 20);
      rows.push({ report_date_as_yyyy_mm_dd: d.toISOString().slice(0, 10), open_interest_all: oi, asset_mgr_positions_long: Math.max(0, am + 600000), asset_mgr_positions_short: 400000, lev_money_positions_long: 250000, lev_money_positions_short: Math.max(0, 250000 - lf),
        dealer_positions_long_all: 300000 + Math.max(0, dl), dealer_positions_short_all: 300000 + Math.max(0, -dl), traders_asset_mgr_long_all: 160, traders_asset_mgr_short_all: 60, traders_lev_money_long_all: 90, traders_lev_money_short_all: 130 }); }
    return { market: { code, name: 'Demo market', units: 'contracts' }, rows, demo: true };
  }
  async function searchMarkets(q) { return $('cotDemo').checked ? { markets: demoMarkets(q) } : A.getJSON('/api/cot/markets?q=' + encodeURIComponent(q)); }
  async function fetchReport(code) { return $('cotDemo').checked ? demoReport(code) : A.getJSON('/api/cot/report?code=' + encodeURIComponent(code) + '&weeks=260'); }

  function derive(rows) {
    const n = x => parseFloat(x) || 0, out = { dates: [], am: [], lf: [], dl: [], oi: [], amPct: [], lfPct: [], amChg: [], lfChg: [], amTr: [], lfTr: [] };
    rows.forEach((r, i) => { const am = n(r.asset_mgr_positions_long) - n(r.asset_mgr_positions_short), lf = n(r.lev_money_positions_long) - n(r.lev_money_positions_short), dl = n(r.dealer_positions_long_all) - n(r.dealer_positions_short_all), oi = n(r.open_interest_all) || 1;
      out.dates.push(String(r.report_date_as_yyyy_mm_dd).slice(0, 10)); out.am.push(am); out.lf.push(lf); out.dl.push(dl); out.oi.push(oi); out.amPct.push(am / oi * 100); out.lfPct.push(lf / oi * 100);
      out.amChg.push(i ? am - out.am[i - 1] : 0); out.lfChg.push(i ? lf - out.lf[i - 1] : 0); out.amTr.push(n(r.traders_asset_mgr_long_all) + n(r.traders_asset_mgr_short_all)); out.lfTr.push(n(r.traders_lev_money_long_all) + n(r.traders_lev_money_short_all)); });
    return out;
  }
  const last = a => a[a.length - 1];

  // ── Report view ──────────────────────────────────────────────────────────
  function group(label, color, net, pct, trd, chg4) {
    const win = net.slice(-156), p = A.rankOf(win, last(net)), tag = p >= 85 ? ['warn', 'Crowded long'] : p <= 15 ? ['warn', 'Crowded short'] : ['neutral', 'Mid-range'];
    return '<div class="arm-card" style="border-top:4px solid ' + color + '"><h2>' + label + '</h2>' + '<div class="arm-kpis">' +
      '<div class="arm-kpi"><span>Net position</span><b>' + fmt(last(net), 0) + '</b></div><div class="arm-kpi"><span>Net, % of open interest</span><b>' + fmt(last(pct), 1) + '%</b></div>' +
      '<div class="arm-kpi"><span>4-week change</span><b>' + (chg4 > 0 ? '+' : '') + fmt(chg4, 0) + '</b></div><div class="arm-kpi"><span>3-year percentile</span><b>' + fmt(p, 0) + '</b></div></div>' +
      '<span class="arm-tag ' + tag[0] + '">' + tag[1] + '</span> <span style="font-size:13px;color:var(--muted)">' + fmt(last(trd), 0) + ' reporting traders on the latest report. Percentile compares today\'s net position with the last three years.</span></div>';
  }
  function showReport(rep) {
    const s = derive(rep.rows); CUR = { market: rep.market, rows: rep.rows, s }; const L = s.dates.length;
    const c4 = a => L > 4 ? last(a) - a[L - 5] : 0;
    $('cotReport').innerHTML = '<div class="arm-card"><h2>' + esc(rep.market.name) + '</h2><div class="sub">Latest report: ' + esc(last(s.dates)) + ' · ' + L + ' weeks loaded · open interest ' + fmt(last(s.oi), 0) + (rep.demo ? ' · demo data' : '') + '</div>' +
      '<div class="arm-two">' + group('Asset managers', '#00d4aa', s.am, s.amPct, s.amTr, c4(s.am)) + group('Leveraged funds', '#ff9f43', s.lf, s.lfPct, s.lfTr, c4(s.lf)) + '</div>' +
      '<div class="arm-chart tall" id="cotC1"></div><div class="arm-two"><div class="arm-chart short" id="cotC2"></div><div class="arm-chart short" id="cotC3"></div></div>' +
      '<div class="arm-note">Asset managers are mostly institutions holding positions for the long term, so they are often net long. Leveraged funds are faster-moving speculators and tend to be on the other side. Dealers (banks) are shown on the first chart for context.</div></div>';
    A.plot('cotC1', [{ x: s.dates, y: s.am, name: 'Asset managers', line: { color: '#00d4aa', width: 3 } }, { x: s.dates, y: s.lf, name: 'Leveraged funds', line: { color: '#ff9f43', width: 3 } }, { x: s.dates, y: s.dl, name: 'Dealers', line: { color: '#8892b0', dash: 'dot' } }], { title: { text: 'Net positions (long minus short, contracts)', font: { size: 13 } } });
    A.plot('cotC2', [{ x: s.dates, y: s.amPct, name: 'Asset managers', line: { color: '#00d4aa' } }, { x: s.dates, y: s.lfPct, name: 'Leveraged funds', line: { color: '#ff9f43' } }], { title: { text: 'Net position as % of open interest', font: { size: 13 } } });
    A.plot('cotC3', [{ type: 'bar', x: s.dates.slice(-52), y: s.amChg.slice(-52), name: 'Asset managers', marker: { color: '#00d4aa' } }, { type: 'bar', x: s.dates.slice(-52), y: s.lfChg.slice(-52), name: 'Leveraged funds', marker: { color: '#ff9f43' } }], { title: { text: 'Weekly change in net position (last 52 weeks)', font: { size: 13 } }, barmode: 'group' });
  }
  async function loadMarket(code) { $('cotErr').textContent = ''; try { showReport(await fetchReport(code)); $('cotReport').scrollIntoView({ behavior: 'smooth', block: 'start' }); } catch (e) { $('cotErr').textContent = e.message; } }
  function showList(ms) {
    $('cotList').innerHTML = ms.length ? ms.map(m => '<button class="arm-pill" data-code="' + esc(m.code) + '" style="cursor:pointer;font-family:inherit">' + esc(m.name) + ' <small style="color:var(--muted)">' + fmt(m.oi, 0) + ' OI</small></button>').join('') : '<span style="color:var(--muted);font-size:13px">No matches. Try a shorter name such as "S&P", "euro" or "bitcoin". Gold and oil are not in this report, which covers financial futures only.</span>';
  }
  async function doSearch() { $('cotErr').textContent = ''; $('cotGo').disabled = true; try { const d = await searchMarkets($('cotQ').value.trim()); showList(d.markets || []); } catch (e) { $('cotErr').textContent = e.message; } $('cotGo').disabled = false; }

  // ── Compare with a saved strategy ────────────────────────────────────────
  function fillPicker() {
    const st = A.store.get(), opts = [];
    st.plans.forEach(p => opts.push(['plan:' + p.name, 'Plan: ' + p.name + (p.symbol ? ' (' + p.symbol + ', ' + p.bias + ')' : '')]));
    (A.savedBacktests || []).forEach(b => opts.push(['bt:' + b.name, 'Backtest: ' + b.name + ((b.config || {}).btSymbol ? ' (' + b.config.btSymbol + ')' : '')]));
    $('cmpPick').innerHTML = opts.length ? opts.map(o => '<option value="' + esc(o[0]) + '">' + esc(o[1]) + '</option>').join('') : '<option value="">No saved strategies yet</option>';
    pickChanged();
  }
  function selected() {
    const v = $('cmpPick').value || '', st = A.store.get();
    if (v.startsWith('plan:')) { const p = st.plans.find(x => x.name === v.slice(5)); return p ? { kind: 'plan', name: p.name, symbol: p.symbol, bias: p.bias, structure: p.structure } : null; }
    if (v.startsWith('bt:')) { const b = (A.savedBacktests || []).find(x => x.name === v.slice(3)); return b ? { kind: 'backtest', name: b.name, symbol: (b.config || {}).btSymbol, bias: 'bullish' } : null; }
    return null;
  }
  function pickChanged() { const s = selected(); if (s && s.symbol) $('cmpSym').value = String(s.symbol).toUpperCase(); }

  async function compare() {
    $('cmpErr').textContent = ''; $('cmpOut').innerHTML = ''; const sel = selected(), sym = $('cmpSym').value.trim().toUpperCase();
    if (!sym) { $('cmpErr').textContent = 'Enter the asset ticker for the strategy.'; return; }
    $('cmpGo').disabled = true;
    try {
      if (!CUR) { const q = MAP[sym]; if (!q) throw new Error('Pick a market above first. ' + sym + ' does not map to one automatically.'); const d = await searchMarkets(q); if (!d.markets.length) throw new Error('No COT market found for ' + q + '.'); showReport(await fetchReport(d.markets[0].code)); }
      const s = CUR.s, hist = $('cotDemo').checked ? { dates: A.demoCloses([sym], 1850).dates, closes: A.demoCloses([sym], 1850).closes } : await A.getJSON('/api/armoury/history?symbols=' + encodeURIComponent(sym) + '&period=5y');
      const px = hist.closes[sym], pd = hist.dates, at = date => { let lo = 0, hi = pd.length - 1, r = -1; while (lo <= hi) { const m = (lo + hi) >> 1; if (pd[m] <= date) { r = m; lo = m + 1; } else hi = m - 1; } return r; };
      const idx = s.dates.map(at), wr = [], lfc = [], amc = [], fwd = [], amP = [], lfP = [];
      for (let i = 1; i < s.dates.length; i++) { if (idx[i] < 1 || idx[i - 1] < 0 || idx[i] === idx[i - 1]) continue; const r = px[idx[i]] / px[idx[i - 1]] - 1; wr.push(r); lfc.push(s.lfChg[i] / s.oi[i]); amc.push(s.amChg[i] / s.oi[i]);
        const j = i + 8 < s.dates.length ? idx[i + 8] : -1; fwd.push(j > 0 ? px[j] / px[idx[i]] - 1 : null); amP.push(A.rankOf(s.am.slice(Math.max(0, i - 156), i + 1), s.am[i])); lfP.push(A.rankOf(s.lf.slice(Math.max(0, i - 156), i + 1), s.lf[i])); }
      if (wr.length < 30) throw new Error('Not enough overlapping history between the price data and the COT report.');
      const corr = (a, b) => { const sa = A.std(a), sb = A.std(b); return sa && sb ? A.cov(a, b) / (sa * sb) : NaN; };
      const cLf = corr(lfc, wr), cAm = corr(amc, wr), avg = (cond, pctArr) => { const v = fwd.filter((f, i) => f != null && cond(pctArr[i])); return v.length >= 5 ? { m: A.mean(v), n: v.length } : null; };
      const amHi = avg(p => p >= 70, amP), amLo = avg(p => p <= 30, amP), lfHi = avg(p => p >= 70, lfP), lfLo = avg(p => p <= 30, lfP);
      const pAm = last(amP), pLf = last(lfP), long = !sel || sel.bias !== 'bearish', stance = long ? 'long' : 'short';
      // Backdrop score: for a long stance, favour asset managers at/above mid-range and leveraged funds not crowded long (and the reverse for a short stance).
      let pts = 0; const why = [];
      const amSup = long ? pAm >= 50 : pAm <= 50; pts += amSup ? 1 : -1; why.push('Asset managers sit at the ' + fmt(pAm, 0) + 'th percentile of their 3-year range, ' + (amSup ? 'which lines up with a ' + stance + ' stance.' : 'which runs against a ' + stance + ' stance.'));
      const lfCrowd = long ? pLf >= 85 : pLf <= 15; pts += lfCrowd ? -1 : 0; if (lfCrowd) why.push('Leveraged funds are at the ' + fmt(pLf, 0) + 'th percentile, so speculative money is already crowded on the ' + stance + ' side, which has historically made reversals sharper.'); else why.push('Leveraged funds are at the ' + fmt(pLf, 0) + 'th percentile, so speculative positioning is not stretched.');
      const trend = (long ? 1 : -1) * (s.am[s.am.length - 1] - s.am[Math.max(0, s.am.length - 5)]); pts += trend > 0 ? 1 : -1; why.push('Asset managers have ' + (s.am[s.am.length - 1] >= s.am[Math.max(0, s.am.length - 5)] ? 'added to' : 'cut') + ' their net position over the last four weeks, ' + (trend > 0 ? 'in the direction of the strategy.' : 'against the direction of the strategy.'));
      if (isFinite(cLf)) why.push('Over the history loaded, weekly changes in leveraged-fund positioning had a correlation of ' + fmt(cLf, 2) + ' with the asset\'s same-week return' + (cLf > 0.2 ? ' (they have tended to chase price).' : cLf < -0.2 ? ' (they have tended to fade price).' : ' (a weak link).'));
      if (isFinite(cAm)) why.push('Asset managers showed a ' + fmt(cAm, 2) + ' correlation with same-week return' + (cAm > 0.2 ? ', so they too have followed price.' : cAm < -0.2 ? ', so they have tended to buy weakness.' : ', a weak link.'));
      if (amHi && amLo) why.push('Historically, the eight weeks after asset managers were in the top 30% of their range averaged ' + A.pct(amHi.m) + ' for ' + esc(sym) + ' (' + amHi.n + ' weeks) versus ' + A.pct(amLo.m) + ' after the bottom 30% (' + amLo.n + ' weeks).');
      if (lfHi && lfLo) why.push('The same split for leveraged funds: ' + A.pct(lfHi.m) + ' after top-30% readings (' + lfHi.n + ' weeks) versus ' + A.pct(lfLo.m) + ' after bottom-30% readings (' + lfLo.n + ' weeks).');
      const c = pts >= 2 ? 'good' : pts >= 0 ? 'warn' : 'bad', head = c === 'good' ? 'Supportive backdrop' : c === 'warn' ? 'Mixed backdrop' : 'Unsupportive backdrop';
      $('cmpOut').innerHTML = '<div class="arm-verdict ' + c + '"><strong>' + head + ':</strong> historically, positioning in <b>' + esc(CUR.market.name) + '</b> lines up ' + (c === 'good' ? 'well' : c === 'warn' ? 'partly' : 'poorly') + ' with a ' + stance + ' strategy on ' + esc(sym) + '.</div>' +
        '<ul class="arm-list">' + why.map(w => '<li><span>•</span><span>' + w + '</span></li>').join('') + '</ul>' +
        '<div class="arm-note">' + (sel && sel.kind === 'backtest' ? 'Backtester strategies are treated as long-only here. ' : '') + (MAP[sym] && !CUR.market.name.toUpperCase().includes(MAP[sym].split(' ')[0]) ? 'Check that the market selected above really tracks ' + esc(sym) + '. ' : '') +
        'This is a historical comparison of two datasets, not a verdict on whether the strategy is a good investment. It cannot see fees, taxes, or anything outside the weeks loaded, and positioning rarely changes outcomes on its own.</div>';
    } catch (e) { $('cmpErr').textContent = e.message; }
    $('cmpGo').disabled = false;
  }

  document.addEventListener('DOMContentLoaded', () => {
    $('cotGo').onclick = doSearch; $('cotQ').addEventListener('keydown', e => { if (e.key === 'Enter') doSearch(); });
    $('cotList').onclick = e => { const b = e.target.closest('[data-code]'); if (b) loadMarket(b.dataset.code); };
    $('cmpPick').onchange = pickChanged; $('cmpGo').onclick = compare;
    A.store.onChange(fillPicker); A.store.load().then(fillPicker);
    searchMarkets('').then(d => showList((d.markets || []).slice(0, 12))).catch(() => {});
  });
})();
