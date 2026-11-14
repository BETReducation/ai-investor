// Backtester UI shared by strategy-lab.html and strategy-lab-forex.html.
// Needs static/js/strategy-map.js and the pages' own functions (runBacktest, applyBacktestConfig,
// serializeBacktestConfig, setIndicatorMode). Loaded at the end of <body>.
(function () {
  'use strict';
  const $ = id => document.getElementById(id);
  const IS_FOREX = /forex/.test(location.pathname);
  const esc = t => String(t).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };

  // ── − / + buttons on number fields ─────────────────────────────────────────
  // The browser's own spinner is only a few px tall, so a click meant for "down" lands on "up".
  function stepNum(btn, dir) {
    const input = btn.parentElement.querySelector('input');
    if (!input) return;
    // Plain add/subtract: the built-in stepUp/stepDown step from the field's min, giving 2001 not 2050.
    const step = parseFloat(input.step) || 1;
    const decimals = (String(step).split('.')[1] || '').length;
    let v = (parseFloat(input.value) || 0) + dir * step;
    if (input.min !== '' && v < +input.min) v = +input.min;
    if (input.max !== '' && v > +input.max) v = +input.max;
    input.value = v.toFixed(decimals);
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
  }

  function wrapNumber(input) {
    if (input.closest('.num-step') || input.classList.contains('pct-input')) return;
    const wide = input.classList.contains('lab-input');
    const wrap = document.createElement('span');
    wrap.className = 'num-step' + (wide ? ' block' : '');
    if (wide) {
      wrap.style.marginBottom = getComputedStyle(input).marginBottom;
      input.style.marginBottom = '0';
    }
    const mk = (label, sign, text) => {
      const b = document.createElement('button');
      b.type = 'button'; b.tabIndex = -1; b.setAttribute('aria-label', label); b.textContent = text;
      b.addEventListener('click', () => stepNum(b, sign));
      return b;
    };
    input.parentNode.insertBefore(wrap, input);
    wrap.append(mk('Decrease', -1, '−'), input, mk('Increase', 1, '+'));
  }
  document.querySelectorAll('input[type="number"]').forEach(wrapNumber);

  // ── Layout: summary sidebar + set-up pop-up ────────────────────────────────
  const layout = document.querySelector('.lab-layout');
  const side = document.querySelector('.lab-sidebar');
  if (!layout || !side || !$('btSymbol')) return;

  const sec = id => $(id).closest('.ctrl-section');
  const nodes = {
    market: side.children[1],
    mode: $('modeBasic').parentElement,
    asset: sec('btSymbol'),
    currency: sec('btCurrency'),
    capital: sec('btCapital'),
    trade: sec('tradeAmountPct'),
    risk: sec('stopLoss'),
    basic: $('basicIndicators'),
    detailed: $('detailedIndicators'),
  };
  const runBar = $('runBtn').parentElement;
  runBar.id = 'btRunBar';

  const STEPS = [
    { title: 'Asset & period', h: 'What should the strategy be tested on?', hint: 'Pick the asset, how far back to look and the candle size. Nothing real is bought or sold. This is a simulation of what the rules would have done historically.', nodes: ['market', 'asset'] },
    { title: 'Capital & risk', h: 'How much would each simulated trade use?', hint: 'Starting capital, trade size, stop-loss and take-profit shape the simulated trades. Change them freely and compare the results.', nodes: ['currency', 'capital', 'trade', 'risk'] },
    { title: 'Indicators', h: 'Which indicators decide the entries?', hint: 'Switch on the indicators you want. A trade is simulated when enough of them agree (set by Min Confidence in the previous step). You can also copy a strategy you built on the Signals page.', nodes: ['mode', 'basic', 'detailed'] },
    { title: 'Review', h: 'Check it over', hint: '', nodes: [] },
  ];
  const LAST = STEPS.length;

  // Wizard shell
  const overlay = document.createElement('div');
  overlay.className = 'bt-wz-overlay';
  overlay.id = 'btWizard';
  overlay.innerHTML = `
    <div class="bt-wz" role="dialog" aria-modal="true" aria-labelledby="btWzTitle">
      <div class="bt-wz-head"><div class="bt-wz-title" id="btWzTitle">SET UP YOUR BACKTEST</div>
        <button type="button" class="bt-wz-close" aria-label="Close">&#10005;</button></div>
      <div class="bt-wz-steps">${STEPS.map((s, i) => `<button type="button" data-step="${i + 1}"><b>${i + 1}</b> ${esc(s.title)}</button>`).join('')}</div>
      <div class="bt-wz-body">${STEPS.map((s, i) => `<section class="bt-wz-step" data-step="${i + 1}" style="display:none;"><h3>${esc(s.h)}</h3><div class="bt-wz-hint">${esc(s.hint)}</div></section>`).join('')}</div>
      <div class="bt-wz-foot"><button type="button" class="bt-wz-btn" id="btWzBack">&larr; BACK</button>
        <button type="button" class="bt-wz-btn primary" id="btWzNext">NEXT &rarr;</button></div>
    </div>`;
  document.body.appendChild(overlay);
  const stepEl = n => overlay.querySelector(`.bt-wz-step[data-step="${n}"]`);

  // Move the existing controls (same ids, so the page's own code keeps working) into the steps.
  STEPS.forEach((s, i) => s.nodes.forEach(k => {
    const n = nodes[k];
    if (!n) return;
    if (!n.classList.contains('ctrl-section') && n.id !== 'basicIndicators') { n.style.paddingLeft = '0'; n.setAttribute('data-wz-moved', ''); }
    stepEl(i + 1).appendChild(n);
  }));
  const detailsEl = nodes.detailed && nodes.detailed.querySelector('details');
  if (detailsEl) detailsEl.open = true;

  // Copy-from-Signals box at the top of the indicators step
  const sigBox = document.createElement('div');
  sigBox.className = 'bt-sig-box';
  sigBox.innerHTML = `<button type="button" class="bt-sig-btn" id="btSigBtn" title="Translate a strategy you built on the Signals page into indicator toggles here">COPY STRATEGY FROM SIGNALS</button>
    <div class="bt-sig-hint" id="btSigHint">Pulls a strategy from the Signals page into the indicators below. Review it before running.</div>`;
  stepEl(3).insertBefore(sigBox, stepEl(3).children[2]);

  // Sidebar: header (with collapse), summary cards, saved strategies, run bar
  const header = side.querySelector('.sidebar-header');
  header.innerHTML = `<span>BACKTEST PARAMETERS</span><button type="button" class="bt-collapse-btn" id="btCollapseBtn" title="Collapse panel">&#171;</button>`;
  const sum = document.createElement('div');
  sum.className = 'bt-sum-wrap';
  const card = (n, t) => `<div class="sum-card" id="btSumCard${n}"><div class="sum-head"><span class="sum-title">${n} · ${t}</span><button type="button" class="sum-edit" data-open="${n}">EDIT</button></div><div class="sum-body" id="btSumBody${n}"></div></div>`;
  sum.innerHTML = `<button type="button" class="bt-open-btn" data-open="1">SET UP BACKTEST</button>${card(1, 'ASSET &amp; PERIOD')}${card(2, 'CAPITAL &amp; RISK')}${card(3, 'INDICATORS')}`;
  header.insertAdjacentElement('afterend', sum);
  sum.addEventListener('click', e => { const t = e.target.closest('[data-open]'); if (t) openWizard(+t.dataset.open); });

  // Collapse + drag-resize (desktop)
  const resizer = document.createElement('div');
  resizer.className = 'bt-resizer'; resizer.id = 'btResizer';
  side.insertAdjacentElement('afterend', resizer);
  const reopen = document.createElement('button');
  reopen.type = 'button'; reopen.className = 'bt-reopen'; reopen.title = 'Show panel'; reopen.innerHTML = '&#187;';
  layout.appendChild(reopen);
  const savedW = parseInt(store.get('gcgBtSideW'), 10);
  if (savedW >= 220) side.style.width = Math.min(savedW, 560) + 'px';
  const setCollapsed = c => { layout.classList.toggle('bt-collapsed', c); store.set('gcgBtSideCollapsed', c ? '1' : '0'); window.dispatchEvent(new Event('resize')); };
  if (store.get('gcgBtSideCollapsed') === '1') layout.classList.add('bt-collapsed');
  $('btCollapseBtn').addEventListener('click', () => setCollapsed(true));
  reopen.addEventListener('click', () => setCollapsed(false));
  resizer.addEventListener('pointerdown', e => {
    e.preventDefault();
    resizer.setPointerCapture(e.pointerId);
    const startX = e.clientX, startW = side.offsetWidth;
    resizer.classList.add('dragging');
    document.body.style.userSelect = 'none';
    const onMove = ev => { side.style.width = Math.min(560, Math.max(220, startW + ev.clientX - startX)) + 'px'; };
    const onUp = () => {
      resizer.classList.remove('dragging');
      document.body.style.userSelect = '';
      resizer.removeEventListener('pointermove', onMove);
      resizer.removeEventListener('pointerup', onUp);
      store.set('gcgBtSideW', side.offsetWidth);
      window.dispatchEvent(new Event('resize'));
    };
    resizer.addEventListener('pointermove', onMove);
    resizer.addEventListener('pointerup', onUp);
  });

  // ── Summary text ───────────────────────────────────────────────────────────
  const line = (k, v) => `<div class="sum-line"><span>${k}</span><span>${v}</span></div>`;
  const optText = id => { const s = $(id); return s && s.selectedOptions[0] ? s.selectedOptions[0].textContent.trim() : ''; };
  const ccy = () => (typeof getCurrencySymbol === 'function' ? getCurrencySymbol() : '');
  const money = n => ccy() + (parseFloat(n) || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
  const fieldText = (id, unit) => { const el = $(id); if (!el) return ''; return el.tagName === 'INPUT' ? (parseFloat(el.value) || 0).toFixed(1) + unit : el.textContent.trim(); };

  function enabledIndicators() {
    const root = (typeof indicatorMode !== 'undefined' && indicatorMode === 'detailed') ? $('detailedIndicators') : $('basicIndicators');
    return [...root.querySelectorAll('input[type="checkbox"][id^="tog"]:checked')].map(cb => {
      const lab = cb.closest('.ind-row') && cb.closest('.ind-row').querySelector('.ind-label > span');
      return lab ? lab.textContent.trim() : cb.id.replace(/^tog|Basic$/g, '');
    });
  }

  function sumAsset() {
    const custom = $('customPanel').style.display !== 'none';
    const period = custom ? `${$('btStartDate').value || '?'} → ${$('btEndDate').value || 'today'}` : optText('btPeriod');
    return line('Asset', esc($('btSymbol').value || '—')) + line('Period', esc(period)) + line('Candle', esc(optText('btInterval')));
  }
  function sumRisk() {
    const gbpMode = $('tradeAmountGbpRow').style.display !== 'none';
    const per = gbpMode ? money($('tradeAmountGbp').value) : $('tradeAmountPct').value + '% of pot';
    return line('Capital', money($('btCapital').value)) + line('Per trade', per)
      + line('Stop-loss', '−' + esc(fieldText('slVal', '%'))) + line('Take-profit', '+' + esc(fieldText('tpVal', '%')))
      + ($('trailSL').checked ? line('Trailing stop', parseFloat($('trailDist').value).toFixed(1) + '%') : '')
      + line('Min confidence', $('minConf').value + '%');
  }
  function sumInd() {
    const list = enabledIndicators();
    const mode = (typeof indicatorMode !== 'undefined' && indicatorMode === 'detailed') ? 'Advanced' : 'Basic';
    const note = $('btGatingNote') ? `<div class="sum-note">${esc($('btGatingNote').textContent)}</div>` : '';
    const body = list.length ? `<div class="sum-chips">${list.map(n => `<span class="sum-chip">${esc(n)}</span>`).join('')}</div>` : '<div class="sum-empty">No indicators switched on.</div>';
    return line('Mode', mode) + body + note
      + `<button type="button" class="bt-sig-btn" style="margin-top:8px;" data-sig>COPY STRATEGY FROM SIGNALS</button>`;
  }
  const snapshot = () => [sumAsset(), sumRisk(), sumInd()];

  // Runs on a timer and only touches the DOM when a card changed, so edits made anywhere
  // (pop-up, saved strategy load, copy from Signals) reach the sidebar.
  function renderSummary() {
    let snap;
    try { snap = snapshot(); } catch (e) { return; }
    snap.forEach((html, i) => {
      const el = $('btSumBody' + (i + 1));
      if (el && el.dataset.h !== html) { el.innerHTML = html; el.dataset.h = html; }
    });
  }
  setInterval(renderSummary, 600);
  renderSummary();
  sum.addEventListener('click', e => { if (e.target.closest('[data-sig]')) openSignalsImport(); });

  // ── Wizard flow ────────────────────────────────────────────────────────────
  let step = 1, snapBefore = null;
  function openWizard(n) {
    snapBefore = snapshot();
    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    go(n || 1);
  }
  function closeWizard() {
    overlay.style.display = 'none';
    document.body.style.overflow = '';
    renderSummary();
    snapshot().forEach((html, i) => {
      if (!snapBefore || snapBefore[i] === html) return;
      const c = $('btSumCard' + (i + 1));
      if (c) { c.classList.remove('flash'); void c.offsetWidth; c.classList.add('flash'); }
    });
  }
  function go(n) {
    step = Math.max(1, Math.min(LAST, n));
    overlay.querySelectorAll('.bt-wz-step').forEach(el => { el.style.display = +el.dataset.step === step ? '' : 'none'; });
    overlay.querySelectorAll('.bt-wz-steps button').forEach(b => b.classList.toggle('active', +b.dataset.step === step));
    $('btWzBack').disabled = step === 1;
    $('btWzNext').innerHTML = step === LAST ? '&#10003; DONE' : 'NEXT &rarr;';
    overlay.querySelector('.bt-wz-body').scrollTop = 0;
    if (step === LAST) renderReview();
  }
  function renderReview() {
    const [a, b, c] = snapshot();
    const warns = [];
    if (!enabledIndicators().length) warns.push('No indicators are switched on, so no trades can be simulated. Go back to step 3.');
    const cd = (t, body, s) => `<div class="sum-card"><div class="sum-head"><span class="sum-title">${t}</span><button type="button" class="sum-edit" data-go="${s}">EDIT</button></div><div class="sum-body">${body}</div></div>`;
    stepEl(LAST).innerHTML = `<h3>${esc(STEPS[LAST - 1].h)}</h3>`
      + warns.map(w => `<div class="bt-wz-warn">${w}</div>`).join('')
      + `<div class="bt-wz-review">${cd('ASSET &amp; PERIOD', a, 1)}${cd('CAPITAL &amp; RISK', b, 2)}${cd('INDICATORS', c.replace(/<button[\s\S]*?<\/button>/, ''), 3)}</div>`
      + `<div class="bt-wz-hint" style="margin-top:10px;">Results show what the rules would have done historically. This is a simulation for learning, not advice.</div>`
      + `<button type="button" class="bt-wz-run" id="btWzRun">&#9654; RUN BACKTEST</button>`;
  }
  overlay.addEventListener('click', e => {
    if (e.target === overlay) return closeWizard();
    const g = e.target.closest('[data-go]');
    if (g) return go(+g.dataset.go);
    if (e.target.closest('#btWzRun')) { closeWizard(); window.runBacktest(); }
  });
  overlay.querySelector('.bt-wz-close').addEventListener('click', closeWizard);
  overlay.querySelectorAll('.bt-wz-steps button').forEach(b => b.addEventListener('click', () => go(+b.dataset.step)));
  $('btWzBack').addEventListener('click', () => go(step - 1));
  $('btWzNext').addEventListener('click', () => (step >= LAST ? closeWizard() : go(step + 1)));
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (sigOverlay.style.display !== 'none') sigOverlay.style.display = 'none';
    else if (overlay.style.display !== 'none') closeWizard();
  });

  // On phones the results sit below the controls; bring them into view when a run starts.
  const origRun = window.runBacktest;
  if (typeof origRun === 'function') {
    window.runBacktest = function () {
      if (window.innerWidth <= 768 && $('labMain')) $('labMain').scrollIntoView({ behavior: 'smooth', block: 'start' });
      return origRun.apply(this, arguments);
    };
  }

  // ── Copy strategy from Signals ─────────────────────────────────────────────
  // Inverse of the Signals page's "Import from Backtester": Signals conditions -> Backtester toggles + trigger modes.
  const sigOverlay = document.createElement('div');
  sigOverlay.className = 'bt-sig-overlay';
  sigOverlay.innerHTML = `<div class="bt-sig-modal"><div class="bt-wz-head"><div class="bt-wz-title">COPY STRATEGY FROM SIGNALS</div>
    <button type="button" class="bt-wz-close" aria-label="Close">&#10005;</button></div>
    <div class="bt-wz-hint" style="margin:10px 16px 0;">Pick a strategy from the Signals page. Its conditions become indicator switches and trigger modes here. Review them before running.</div>
    <div class="bt-sig-list" id="btSigList"></div></div>`;
  document.body.appendChild(sigOverlay);
  sigOverlay.addEventListener('click', e => { if (e.target === sigOverlay || e.target.closest('.bt-wz-close')) sigOverlay.style.display = 'none'; });
  $('btSigBtn').addEventListener('click', openSignalsImport);

  let sigCache = [];
  async function openSignalsImport() {
    const list = $('btSigList');
    list.innerHTML = '<div style="font-size:9px;color:var(--text-muted);">Loading…</div>';
    sigOverlay.style.display = 'flex';
    try {
      const res = await fetch('/api/load-preferences', { credentials: 'include' });
      if (res.status === 401) { list.innerHTML = '<div style="font-size:10px;color:var(--text-muted);">Sign in to copy a strategy from your Signals page.</div>'; return; }
      const prefs = (await res.json()).preferences || {};
      sigCache = [];
      if (Array.isArray(prefs.strategyConditions) && prefs.strategyConditions.length) {
        sigCache.push({ name: prefs.strategyName || 'Current strategy', sub: 'Open on the Signals page now', conditions: prefs.strategyConditions, prefs });
      }
      (Array.isArray(prefs.savedStrategies) ? prefs.savedStrategies : []).forEach(s => {
        if (s && Array.isArray(s.conditions) && s.conditions.length) sigCache.push({ name: s.name, sub: 'Saved on Signals', conditions: s.conditions, prefs });
      });
      if (!sigCache.length) { list.innerHTML = '<div style="font-size:10px;color:var(--text-muted);">No Signals strategies yet. Build one on the Signals page first.</div>'; return; }
      list.innerHTML = sigCache.map((s, i) => `<div class="bt-sig-row"><div style="min-width:0;"><div class="nm">${esc(s.name)}</div><div class="sub">${esc(s.sub)} · ${s.conditions.length} condition${s.conditions.length === 1 ? '' : 's'}</div></div>
        <button type="button" class="bt-sig-btn" style="width:auto;padding:5px 10px;" data-i="${i}">COPY</button></div>`).join('');
    } catch (e) {
      list.innerHTML = `<div style="font-size:10px;color:var(--accent-red);">Failed to load: ${esc(e.message)}</div>`;
    }
  }
  $('btSigList').addEventListener('click', e => {
    const b = e.target.closest('[data-i]');
    if (b) copyFromSignals(sigCache[+b.dataset.i]);
  });

  // Prefer the mode that maps to exactly this one condition; otherwise any mode that includes it.
  function findMode(type) {
    let best = null;
    Object.entries(BT_INDICATOR_MAP).forEach(([togId, spec]) => {
      Object.entries(spec.modes).forEach(([mode, types]) => {
        if (!types.includes(type)) return;
        if (!best || types.length < best.n) best = { togId, spec, mode, n: types.length };
      });
    });
    return best;
  }

  function translateSignals(conditions, basicOnly) {
    const used = new Map();          // togId -> { spec, modes:Set }
    const values = {}, params = {};
    const skipped = [];
    conditions.forEach(c => {
      const hit = findMode(c.type);
      if (!hit) { skipped.push(c.type); return; }
      const basicEntry = Object.values(BT_BASIC_TOGGLE_MAP).find(b => b.togId === hit.togId);
      if (basicOnly) {
        if (!basicEntry || !(hit.spec.modes[basicEntry.defaultMode] || []).includes(c.type)) { skipped.push(c.type + ' (needs Advanced)'); return; }
        hit.mode = basicEntry.defaultMode;
      }
      if (!used.has(hit.togId)) used.set(hit.togId, { spec: hit.spec, modes: new Set() });
      used.get(hit.togId).modes.add(hit.mode);
      const vk = CONDITION_VALUE_KEYS[c.type];
      const field = vk && (basicOnly ? vk.basic : vk.detailed);
      const raw = parseFloat(c.value);
      if (field && isFinite(raw)) values[field] = vk.transform ? vk.transform(raw) : raw;
      if (!basicOnly && c.params) {
        const map = SIGNALS_PARAM_FIELDS[hit.spec.group] || {};
        Object.entries(c.params).forEach(([pid, v]) => { if (map[pid] && $(map[pid])) params[map[pid]] = v; });
      }
    });
    return { used, values, params, skipped };
  }

  function copyFromSignals(item) {
    const restricted = typeof btGating !== 'undefined' && btGating && btGating.restricted;
    const t = translateSignals(item.conditions, restricted);
    const hint = $('btSigHint');
    if (!t.used.size) {
      hint.textContent = `"${item.name}" has no conditions the Backtester can run${restricted ? ' on your plan' : ''}.`;
      sigOverlay.style.display = 'none';
      return;
    }
    const cfg = serializeBacktestConfig();
    Object.keys(cfg).forEach(k => { if (/^tog[A-Z]/.test(k)) cfg[k] = false; });
    cfg._indicatorMode = restricted ? 'basic' : 'detailed';
    t.used.forEach(({ spec, modes }, togId) => {
      if (restricted) {
        const bk = Object.keys(BT_BASIC_TOGGLE_MAP).find(k => BT_BASIC_TOGGLE_MAP[k].togId === togId);
        if (bk) cfg[bk] = true;
      } else {
        cfg[togId] = true;
        if (spec.chips) cfg[spec.chips] = [...modes];
      }
    });
    Object.assign(cfg, t.values, t.params);

    // Risk settings from the Signals page (percent-based on both pages). Forex here is pip-based, so skip those.
    const p = item.prefs || {};
    if (!IS_FOREX) {
      if (isFinite(p.stopLoss) && !p.stopLossCcyMode) cfg.stopLoss = p.stopLoss;
      if (isFinite(p.targetGain) && !p.targetGainCcyMode) cfg.takeProfit = p.targetGain;
      if (typeof p.trailSL === 'boolean') cfg.trailSL = p.trailSL;
      if (isFinite(p.trailDist)) cfg.trailDist = p.trailDist;
    }
    if (isFinite(p.minConfidence)) cfg.minConf = p.minConfidence;
    if (isFinite(p.capital)) cfg.btCapital = p.capital;
    if (p.currency && [...$('btCurrency').options].some(o => o.value === p.currency)) cfg.btCurrency = p.currency;

    applyBacktestConfig(cfg);
    $('btStrategyName').value = `${item.name} (from Signals)`;
    const msg = `Copied "${item.name}": ${item.conditions.length - t.skipped.length} of ${item.conditions.length} conditions across ${t.used.size} indicator${t.used.size === 1 ? '' : 's'}.`
      + (t.skipped.length ? ` Skipped (no Backtester equivalent): ${t.skipped.join(', ')}.` : '')
      + ' Buy/sell direction does not carry over; the Backtester trades each indicator’s own triggers.';
    hint.textContent = msg;
    const h2 = $('btStrategyHint'); if (h2) h2.textContent = msg;
    sigOverlay.style.display = 'none';
    renderSummary();
    const c = $('btSumCard3');
    if (c) { c.classList.remove('flash'); void c.offsetWidth; c.classList.add('flash'); }
  }

  window.btUi = { openWizard, closeWizard, openSignalsImport, copyFromSignals };
})();
