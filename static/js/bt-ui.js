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
    { key: 'entry', title: '', h: '', hint: '', nodes: [] },
    { key: 'exit', title: '', h: '', hint: '', nodes: [] },
    { key: 'short', title: '', h: '', hint: '', nodes: [] },
    { key: 'cover', title: '', h: '', hint: '', nodes: [] },
    { title: 'Review', h: 'Check it over', hint: '', nodes: [] },
  ];
  const LAST = STEPS.length;   // the Review step
  let step = 1, snapBefore = null;
  const dirMode = () => (typeof tradeDirection !== 'undefined' ? tradeDirection : 'long');
  const isSplit = () => dirMode() === 'both' && !!$('splitShort') && $('splitShort').checked;
  // Steps 5 and 6 (the short rules) only exist when shorts have their own rule sets.
  const visibleSteps = () => (isSplit() ? [1, 2, 3, 4, 5, 6, LAST] : [1, 2, 3, 4, LAST]);

  // What each rule step is called and says, by trade direction.
  const COPY = {
    long: {
      entry: ['Buy rules', 'When should it buy?', 'Switch on the indicators that decide entries. A buy is simulated when enough of them agree (the Entry Min Confidence in step 2). You can also copy a strategy from the Signals page: its buy conditions become these rules and its sell conditions become the sell rules.'],
      exit: ['Sell rules', 'When should it sell?', 'Choose the indicators that close a trade. A sell happens when these agree, or sooner if the stop-loss or take-profit is hit. Pick sell-side triggers, such as overbought or a bearish cross. Without sell rules a position would only ever close on its stop or target.'],
      verbs: { entry: 'Buy when', exit: 'Sell when' }, confs: { exit: 'Sell' }, cards: { entry: 'BUY RULES', exit: 'SELL RULES' },
    },
    short: {
      entry: ['Short entry rules', 'When should it go short?', 'Switch on the indicators that decide when to open a short, using sell-side triggers such as overbought or a bearish cross. A short is simulated when enough of them agree (the Entry Min Confidence in step 2). A short gains when the price falls.'],
      exit: ['Cover rules', 'When should it close the short?', 'Choose the indicators that close a short (buy it back). Use buy-side triggers, such as oversold or a bullish cross. A cover happens when these agree, or sooner if the stop-loss or take-profit is hit.'],
      verbs: { entry: 'Short when', exit: 'Cover when' }, confs: { exit: 'Cover' }, cards: { entry: 'SHORT ENTRY RULES', exit: 'COVER RULES' },
    },
    both: {
      entry: ['Entry rules', 'What should open a position?', 'One set of rules drives both sides: buy-side triggers (oversold, bullish cross) open longs and sell-side triggers (overbought, bearish cross) open shorts. Each side\'s signal closes the opposite position, so the strategy reverses between long and short. Turn on "Separate rules for shorts" in the sidebar to give shorts their own indicators.'],
      exit: ['Exit rules', 'When should a position close early?', 'Optional. Sell-side triggers close longs and buy-side triggers cover shorts before a reversal. Stops and reversals close trades even if this is left empty.'],
      verbs: { entry: 'Enter when', exit: 'Exit when' }, confs: { exit: 'Exit' }, cards: { entry: 'ENTRY RULES', exit: 'EXIT RULES' },
    },
    split: {
      entry: ['Long entry rules', 'When should it go long?', 'Switch on the indicators that open a long, using buy-side triggers such as oversold or a bullish cross. Shorts have their own rules in step 5. When a short entry fires, any open long is closed first.'],
      exit: ['Long exit rules', 'When should a long close early?', 'Optional. Sell-side indicators that close a long before a short entry would. Stops and the short entry (step 5) also close longs.'],
      short: ['Short entry rules', 'When should it go short?', 'Switch on the indicators that open a short, using sell-side triggers such as overbought or a bearish cross. When one fires, any open long is closed and the short opens in its place. A short gains when the price falls.'],
      cover: ['Short exit rules', 'When should a short close early?', 'Optional. Buy-side indicators that cover a short before a long entry would. Stops and the long entry (step 3) also cover shorts.'],
      verbs: { entry: 'Go long when', exit: 'Close long when', short: 'Go short when', cover: 'Cover when' }, confs: { exit: 'Long exit', short: 'Short entry', cover: 'Short exit' },
      cards: { entry: 'LONG ENTRY RULES', exit: 'LONG EXIT RULES', short: 'SHORT ENTRY RULES', cover: 'SHORT EXIT RULES' },
    },
  };
  const copyFor = () => COPY[isSplit() ? 'split' : dirMode()] || COPY.long;

  // Wizard shell
  const overlay = document.createElement('div');
  overlay.className = 'bt-wz-overlay';
  overlay.id = 'btWizard';
  overlay.innerHTML = `
    <div class="bt-wz" role="dialog" aria-modal="true" aria-labelledby="btWzTitle">
      <div class="bt-wz-head"><div class="bt-wz-title" id="btWzTitle">SET UP YOUR BACKTEST</div>
        <button type="button" class="bt-wz-close" aria-label="Close">&#10005;</button></div>
      <div class="bt-wz-steps"></div>
      <div class="bt-wz-body">${STEPS.map((s, i) => `<section class="bt-wz-step" data-step="${i + 1}" style="display:none;"><h3 data-h></h3><div class="bt-wz-hint" data-hint>${esc(s.hint)}</div></section>`).join('')}</div>
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

  // One set of indicator controls serves both the buy and the sell rules: it is moved into step 3 or 4 and
  // loaded with that side's saved values (see activate()).
  const indWrap = document.createElement('div');
  indWrap.id = 'btIndWrap';
  ['mode', 'basic', 'detailed'].forEach(k => nodes[k] && indWrap.appendChild(nodes[k]));

  const sigBox = document.createElement('div');
  sigBox.className = 'bt-sig-box';
  sigBox.innerHTML = `<button type="button" class="bt-sig-btn" id="btSigBtn" title="Translate a strategy you built on the Signals page into buy and sell rules here">COPY STRATEGY FROM SIGNALS</button>
    <div class="bt-sig-hint" id="btSigHint">Pulls a strategy from the Signals page: buy conditions become the buy rules, sell conditions the sell rules. Review them before running.</div>`;
  // One confidence slider + "start from" shortcut per extra rule set (exit, short entry, short exit).
  const COPY_FROM = { exit: ['entry', 'THE ENTRY RULES'], short: ['entry', 'THE LONG ENTRY RULES'], cover: ['short', 'THE SHORT ENTRY RULES'] };
  const mkConfBox = key => {
    const box = document.createElement('div');
    box.className = 'bt-sig-box';
    box.style.borderColor = 'var(--accent-red, #ef4444)';
    box.innerHTML = `<div style="display:flex;justify-content:space-between;align-items:center;font-size:10px;color:var(--text-secondary);margin-bottom:4px;"><span><span data-conf-label="${key}">Sell</span> Min Confidence <span class="info-dot" tabindex="0" data-tip="The % of these indicators that must agree before this rule set acts on a signal.">?</span></span><b data-conf-val="${key}">60%</b></div>
      <input type="range" min="50" max="100" step="5" value="60" data-conf="${key}" style="width:100%;">
      <button type="button" class="bt-sig-btn" data-copy="${key}:${COPY_FROM[key][0]}" style="margin-top:8px;">START FROM ${COPY_FROM[key][1]}</button>
      <div class="bt-sig-hint">Copies those indicators across so you can adjust them, for example switching RSI from oversold to overbought.</div>`;
    return box;
  };
  const exitBox = mkConfBox('exit'), shortBox = mkConfBox('short'), coverBox = mkConfBox('cover');
  const gainBox = document.createElement('div');
  gainBox.className = 'bt-sig-box';
  gainBox.innerHTML = `<label style="display:flex;align-items:center;gap:8px;font-size:10px;color:var(--text-primary);cursor:pointer;"><input type="checkbox" data-gain-on> Profit from the buy price is at least</label>
    <div style="display:flex;align-items:center;gap:6px;margin-top:8px;"><span style="color:var(--text-muted);">+</span><input type="number" class="lab-input" data-gain-pct min="0.5" max="1000" step="0.5" value="30" style="width:90px;margin:0;"><span style="color:var(--text-muted);">%</span></div>
    <select class="lab-input" data-gain-mode style="margin:8px 0 0;">
      <option value="signal">Counts as a sell signal, alongside the sell indicators</option>
      <option value="require">Must be reached first, then the sell indicators can sell</option>
    </select>
    <div class="bt-sig-hint">Unlike the take-profit in step 2, which sells the moment it is hit, this works as one of your sell rules. "Must be reached first" means an indicator sell is ignored until the trade is up by this much, e.g. RSI overbought AND +30%.</div>`;
  stepEl(3).appendChild(sigBox);
  const mkMatch = key => {
    const d = document.createElement('div');
    d.innerHTML = `<div style="display:flex;align-items:center;gap:8px;font-size:10px;color:var(--text-secondary);margin-bottom:10px;max-width:480px;"><span data-verb="${key}"></span>
      <select class="lab-input" data-match="${key}" style="width:auto;margin:0;"><option value="any">ANY indicator signals</option><option value="all">ALL indicators signal</option></select></div>`;
    return d.firstChild;
  };
  stepEl(3).appendChild(mkMatch('entry'));
  stepEl(3).appendChild(indWrap);
  stepEl(4).appendChild(exitBox);
  stepEl(4).appendChild(gainBox);
  stepEl(4).appendChild(mkMatch('exit'));
  stepEl(5).appendChild(shortBox);
  stepEl(5).appendChild(mkMatch('short'));
  stepEl(6).appendChild(coverBox);
  stepEl(6).appendChild(mkMatch('cover'));
  wrapNumber(gainBox.querySelector('[data-gain-pct]'));

  // Rename the entry confidence slider now that sells have their own.
  const mc = $('minConf') && $('minConf').closest('.slider-row') && $('minConf').closest('.slider-row').querySelector('.ctrl-name');
  if (mc && mc.firstChild && mc.firstChild.nodeType === 3) mc.firstChild.textContent = 'Entry Min Confidence ';

  // Sidebar: header (with collapse), summary cards, saved strategies, run bar
  const header = side.querySelector('.sidebar-header');
  header.innerHTML = `<span>BACKTEST PARAMETERS</span><button type="button" class="bt-collapse-btn" id="btCollapseBtn" title="Collapse panel">&#171;</button>`;
  const sum = document.createElement('div');
  sum.className = 'bt-sum-wrap';
  const card = (n, t) => `<div class="sum-card" id="btSumCard${n}"><div class="sum-head"><span class="sum-title">${n} · ${t}</span><button type="button" class="sum-edit" data-open="${n}">EDIT</button></div><div class="sum-body" id="btSumBody${n}"></div></div>`;
  sum.innerHTML = `<button type="button" class="bt-open-btn" data-open="1">SET UP BACKTEST</button><div style="margin:8px 0 2px;font-size:8px;letter-spacing:1px;color:var(--text-muted);">LONG &amp; SHORT STARTERS</div><div style="display:flex;flex-direction:column;gap:4px;margin-bottom:8px;"><button type="button" class="bt-sig-btn" data-starter="range">Oversold Long / Overbought Short</button><button type="button" class="bt-sig-btn" data-starter="trend">MACD Cross Flip</button><button type="button" class="bt-sig-btn" data-starter="level">Golden Cross Long / Short if Level Lost</button></div>${card(1, 'ASSET &amp; PERIOD')}${card(2, 'CAPITAL &amp; RISK')}${card(3, 'BUY RULES')}${card(4, 'SELL RULES')}${card(5, 'SHORT ENTRY RULES')}${card(6, 'SHORT EXIT RULES')}`;
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

  // ── Buy / sell rule sets ───────────────────────────────────────────────────
  // The page has one set of indicator controls. The buy rules and sell rules are two snapshots of it; the
  // controls show whichever side is active and swap when you move between steps 3 and 4.
  const IND_ROOT = '#basicIndicators, #detailedIndicators';
  const rawSerialize = window.serializeBacktestConfig;
  const rawApply = window.applyBacktestConfig;
  const sets = { entry: null, exit: null, short: null, cover: null };
  let activeSet = 'entry';
  const confs = { exit: 60, short: 60, cover: 60 };   // entry uses the page's own Entry Min Confidence slider
  let exitGain = { on: false, pct: 30, mode: 'signal' };
  const match = { entry: 'any', exit: 'any', short: 'any', cover: 'any' };   // ALL = every indicator needs at least one trigger firing
  const SET_KEYS = ['entry', 'exit', 'short', 'cover'];

  const indSubset = cfg => { const o = {}; Object.keys(cfg).forEach(k => { const el = $(k); if (el && el.closest(IND_ROOT)) o[k] = cfg[k]; }); return o; };
  const blankSet = cfg => { const o = indSubset(cfg); Object.keys(o).forEach(k => { if (/^tog[A-Z]/.test(k)) o[k] = false; }); return o; };
  sets.exit = blankSet(rawSerialize());
  sets.short = blankSet(rawSerialize());
  sets.cover = blankSet(rawSerialize());

  const getSet = name => (name === activeSet ? indSubset(rawSerialize()) : (sets[name] || {}));
  function activate(name) {
    if (name === activeSet) return;
    sets[activeSet] = indSubset(rawSerialize());
    activeSet = name;
    rawApply({ ...rawSerialize(), ...sets[name] });
  }

  // Saved strategies keep the buy rules at the top level (as before) plus the sell rules under _exit.
  window.serializeBacktestConfig = function () {
    const live = rawSerialize();
    const liveInd = indSubset(live);
    const cfg = { ...live, ...(activeSet === 'entry' ? liveInd : sets.entry) };
    ['exit', 'short', 'cover'].forEach(k => { cfg['_' + k] = activeSet === k ? liveInd : sets[k]; });
    cfg._exitMinConf = confs.exit;
    cfg._shortMinConf = confs.short;
    cfg._coverMinConf = confs.cover;
    cfg._exitGain = { ...exitGain };
    cfg._match = { ...match };
    return cfg;
  };
  window.applyBacktestConfig = function (cfg) {
    activeSet = 'entry';
    // Strategies saved before sell rules existed: reuse the one indicator set for selling, as they always ran.
    sets.exit = cfg._exit ? { ...cfg._exit } : indSubset(cfg);
    // Strategies saved before shorts had their own rules have no short/cover sets.
    sets.short = cfg._short ? { ...cfg._short } : blankSet(cfg);
    sets.cover = cfg._cover ? { ...cfg._cover } : blankSet(cfg);
    sets.entry = null;
    setMatch(cfg._match || {});
    setExitGain(cfg._exitGain || { on: false, pct: 30, mode: 'signal' });
    setConf('exit', cfg._exitMinConf !== undefined ? cfg._exitMinConf : (cfg.minConf !== undefined ? cfg.minConf : 60));
    setConf('short', cfg._shortMinConf !== undefined ? cfg._shortMinConf : 60);
    setConf('cover', cfg._coverMinConf !== undefined ? cfg._coverMinConf : 60);
    return rawApply(cfg);
  };

  function setConf(key, v) {
    confs[key] = Math.min(100, Math.max(50, parseFloat(v) || 60));
    const r = overlay.querySelector(`[data-conf="${key}"]`), l = overlay.querySelector(`[data-conf-val="${key}"]`);
    if (r) r.value = confs[key];
    if (l) l.textContent = confs[key] + '%';
  }
  function setMatch(m) {
    SET_KEYS.forEach(k => {
      match[k] = m[k] === 'all' ? 'all' : 'any';
      const el = overlay.querySelector(`[data-match="${k}"]`);
      if (el) el.value = match[k];
    });
  }
  overlay.addEventListener('change', e => { if (e.target.matches('[data-match]')) match[e.target.dataset.match] = e.target.value; });
  function setExitGain(g) {
    exitGain = { on: !!g.on, pct: parseFloat(g.pct) > 0 ? parseFloat(g.pct) : 30, mode: g.mode === 'require' ? 'require' : 'signal' };
    overlay.querySelector('[data-gain-on]').checked = exitGain.on;
    overlay.querySelector('[data-gain-pct]').value = exitGain.pct;
    overlay.querySelector('[data-gain-mode]').value = exitGain.mode;
  }
  const readGain = () => setExitGain({
    on: overlay.querySelector('[data-gain-on]').checked,
    pct: overlay.querySelector('[data-gain-pct]').value,
    mode: overlay.querySelector('[data-gain-mode]').value,
  });
  overlay.addEventListener('input', e => { if (e.target.matches('[data-conf]')) setConf(e.target.dataset.conf, e.target.value); });
  overlay.addEventListener('input', e => { if (e.target.matches('[data-gain-pct]')) exitGain.pct = parseFloat(e.target.value) > 0 ? parseFloat(e.target.value) : exitGain.pct; });
  overlay.addEventListener('change', e => { if (e.target.matches('[data-gain-on],[data-gain-pct],[data-gain-mode]')) readGain(); });
  overlay.addEventListener('click', e => {
    const b = e.target.closest('[data-copy]');
    if (!b) return;
    const [key, src] = b.dataset.copy.split(':');
    // The source set was stored when its own step was left, so it is available here.
    if (activeSet === key && sets[src]) rawApply({ ...rawSerialize(), ...sets[src] });
  });

  // ── Summary text ───────────────────────────────────────────────────────────
  const line = (k, v) => `<div class="sum-line"><span>${k}</span><span>${v}</span></div>`;
  const optText = id => { const s = $(id); return s && s.selectedOptions[0] ? s.selectedOptions[0].textContent.trim() : ''; };
  const ccy = () => (typeof getCurrencySymbol === 'function' ? getCurrencySymbol() : '');
  const money = n => ccy() + (parseFloat(n) || 0).toLocaleString(undefined, { maximumFractionDigits: 2 });
  const fieldText = (id, unit) => { const el = $(id); if (!el) return ''; return el.tagName === 'INPUT' ? (parseFloat(el.value) || 0).toFixed(1) + unit : el.textContent.trim(); };

  // Indicators switched on in one side's set, with the trigger modes chosen for each.
  function rulesFor(set) {
    const detailed = typeof indicatorMode !== 'undefined' && indicatorMode === 'detailed';
    return Object.keys(set).filter(k => /^tog[A-Z]/.test(k) && set[k] && (detailed ? !/Basic$/.test(k) : /Basic$/.test(k))).map(k => {
      const el = $(k);
      const lab = el && el.closest('.ind-row') && el.closest('.ind-row').querySelector('.ind-label > span');
      const name = (lab ? lab.textContent : k.replace(/^tog|Basic$/g, '')).replace(/\s*\(.*\)\s*$/, '').trim();
      const spec = detailed && BT_INDICATOR_MAP[k];
      const modes = spec && spec.chips && Array.isArray(set[spec.chips]) ? set[spec.chips].map(m => m.replace(/_/g, ' ')).join(', ') : '';
      return modes ? `${name}: ${modes}` : name;
    });
  }
  const ruleChips = (list, optional) => list.length
    ? `<div class="sum-chips">${list.map(n => `<span class="sum-chip">${esc(n)}</span>`).join('')}</div>`
    : (optional ? '<div class="sum-empty">None set. Optional.</div>' : '<div class="sum-empty" style="color:var(--accent-amber);">None set yet. Required to run.</div>');
  // Entry rules always need something; exit rules only when stops are the sole other way out (long or short mode).
  const required = key => key === 'entry' || key === 'short' || (key === 'exit' && !isSplit() && dirMode() !== 'both');
  const CARD_STEP = { entry: 3, exit: 4, short: 5, cover: 6 };

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
      + (parseFloat($('feePct').value) > 0 ? line('Fee', parseFloat($('feePct').value) + '% per side') : '')
      + (parseFloat($('borrowPct').value) > 0 ? line('Short borrow', parseFloat($('borrowPct').value) + '% / yr') : '');
  }
  function sumSet(key) {
    const c = copyFor();
    const rules = rulesFor(getSet(key));
    if (key === 'exit' && exitGain.on) rules.push(`Profit +${exitGain.pct}% from entry (${exitGain.mode === 'require' ? 'must be reached first' : 'counts as a signal'})`);
    const verb = (c.verbs[key] || '');
    if (key === 'entry') {
      const mode = (typeof indicatorMode !== 'undefined' && indicatorMode === 'detailed') ? 'Advanced' : 'Basic';
      const note = $('btGatingNote') ? `<div class="sum-note">${esc($('btGatingNote').textContent)}</div>` : '';
      return line('Mode', mode) + line(verb, match.entry === 'all' ? 'ALL signal' : 'ANY signals') + line('Min confidence', $('minConf').value + '%') + ruleChips(rules, false) + note
        + `<button type="button" class="bt-sig-btn" style="margin-top:8px;" data-sig>COPY STRATEGY FROM SIGNALS</button>`;
    }
    const closes = key === 'exit' ? (dirMode() === 'both' || isSplit() ? 'Also closes at a stop-loss, take-profit or the opposite entry.' : 'Also closes at the stop-loss or take-profit.')
      : 'Also closes at a stop-loss, take-profit or the opposite entry.';
    return line(verb, match[key] === 'all' ? 'ALL signal' : 'ANY signals') + line('Min confidence', confs[key] + '%') + ruleChips(rules, !required(key))
      + `<div class="sum-note">${closes}</div>`;
  }
  const snapshot = () => [sumAsset(), sumRisk(), sumSet('entry'), sumSet('exit'), sumSet('short'), sumSet('cover')];

  // Runs on a timer and only touches the DOM when a card changed, so edits made anywhere
  // (pop-up, saved strategy load, copy from Signals) reach the sidebar.
  function renderSummary() {
    let snap;
    try { snap = snapshot(); } catch (e) { return; }
    applyTitles();
    snap.forEach((html, i) => {
      const el = $('btSumBody' + (i + 1));
      if (el && el.dataset.h !== html) { el.innerHTML = html; el.dataset.h = html; }
    });
  }
  // Keeps every label that depends on trade direction in step with it.
  let titlesKey = '';
  function applyTitles() {
    const c = copyFor(), split = isSplit();
    const k = dirMode() + (split ? '+split' : '');
    if (k === titlesKey) return;
    titlesKey = k;
    ['entry', 'exit', 'short', 'cover'].forEach(key => {
      const idx = CARD_STEP[key] - 1, t = c[key];
      if (t) { STEPS[idx].title = t[0]; STEPS[idx].h = t[1]; STEPS[idx].hint = t[2]; }
      const sec = stepEl(CARD_STEP[key]);
      if (sec && t) { sec.querySelector('[data-h]').textContent = t[1]; sec.querySelector('[data-hint]').textContent = t[2]; }
      overlay.querySelectorAll(`[data-verb="${key}"]`).forEach(el => { el.textContent = c.verbs[key] || ''; });
      overlay.querySelectorAll(`[data-conf-label="${key}"]`).forEach(el => { el.textContent = (c.confs && c.confs[key]) || ''; });
      const card = $('btSumCard' + CARD_STEP[key]);
      if (card) {
        const ttl = card.querySelector('.sum-title');
        if (ttl) ttl.textContent = `${CARD_STEP[key]} · ${(c.cards && c.cards[key]) || ''}`;
        if (key === 'short' || key === 'cover') card.style.display = split ? '' : 'none';
      }
    });
    renderStepsBar();
    if (overlay.style.display === 'flex' && !visibleSteps().includes(step)) go(4);
  }
  function renderStepsBar() {
    const vis = visibleSteps();
    overlay.querySelector('.bt-wz-steps').innerHTML = vis.map((id, i) =>
      `<button type="button" data-step="${id}" class="${id === step ? 'active' : ''}"><b>${i + 1}</b> ${esc(STEPS[id - 1].title)}</button>`).join('');
  }
  // Rough candle count for the chosen period + timeframe, so a too-short combination
  // is flagged before the run (the backend needs ~35 candles for MACD at defaults).
  const PERIOD_TRADING_DAYS = { halfday: 0.5, '1d': 1, '2d': 2, '3d': 3, '4d': 4, '5d': 5, '1wk': 5, '2wk': 10, '3wk': 15,
    '1mo': 21, '3mo': 63, '6mo': 126, '1y': 252, '2y': 504, '5y': 1260 };
  const BARS_PER_DAY = { '1m': 390, '5m': 78, '15m': 26, '30m': 13, '1h': 7, '2h': 4, '4h': 2, '1d': 1, '1wk': 0.2, '1mo': 1 / 21, '3mo': 1 / 63 };
  const MIN_CANDLES = 35;
  function updateShortWarning() {
    const per = $('btPeriod'), itv = $('btInterval');
    if (!per || !itv) return;
    let warn = $('btShortWarn');
    if (!warn) {
      warn = document.createElement('div');
      warn.id = 'btShortWarn';
      warn.style.cssText = 'display:none;margin-top:6px;padding:6px 8px;font-size:10px;line-height:1.4;border:1px solid #d9a400;border-radius:4px;background:rgba(217,164,0,.12);color:var(--text-primary);';
      itv.insertAdjacentElement('afterend', warn);
    }
    let days;
    const custom = $('customPanel') && $('customPanel').style.display !== 'none';
    if (custom) {
      const sd = $('btStartDate').value;
      if (!sd) { warn.style.display = 'none'; return; }
      const end = $('btEndDate').value ? new Date($('btEndDate').value) : new Date();
      days = Math.max(0, (end - new Date(sd)) / 864e5) * 5 / 7;
    } else {
      days = PERIOD_TRADING_DAYS[per.value];
    }
    const bpd = BARS_PER_DAY[itv.value];
    if (days == null || bpd == null) { warn.style.display = 'none'; return; }
    const est = Math.round(days * bpd);
    if (est >= MIN_CANDLES) { warn.style.display = 'none'; return; }
    warn.textContent = `This gives roughly ${est} candles. The indicators need about ${MIN_CANDLES}, so the backtest will likely fail. Pick a longer period or a smaller candle size.`;
    warn.style.display = 'block';
  }
  setInterval(() => { renderSummary(); updateShortWarning(); }, 600);
  renderSummary();
  updateShortWarning();
  sum.addEventListener('click', e => { if (e.target.closest('[data-sig]')) openSignalsImport(); });

  // ── Wizard flow ────────────────────────────────────────────────────────────
  function openWizard(n) {
    snapBefore = snapshot();
    overlay.style.display = 'flex';
    document.body.style.overflow = 'hidden';
    go(n || 1);
  }
  function closeWizard() {
    activate('entry');
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
    applyTitles();
    const vis = visibleSteps();
    step = vis.includes(n) ? n : (vis.find(v => v >= n) || LAST);
    // The shared indicator controls live in whichever rule step is open; load that rule set's values.
    const key = STEPS[step - 1].key;
    if (key) { activate(key); stepEl(step).appendChild(indWrap); }
    else { activate('entry'); stepEl(3).appendChild(indWrap); }
    renderStepsBar();
    overlay.querySelectorAll('.bt-wz-step').forEach(el => { el.style.display = +el.dataset.step === step ? '' : 'none'; });
    $('btWzBack').disabled = step === vis[0];
    $('btWzNext').innerHTML = step === LAST ? '&#10003; DONE' : 'NEXT &rarr;';
    overlay.querySelector('.bt-wz-body').scrollTop = 0;
    if (step === LAST) renderReview();
  }
  function missingRules() {
    const m = [];
    const c = copyFor();
    ['entry', 'exit', 'short', 'cover'].forEach(key => {
      if (!visibleSteps().includes(CARD_STEP[key]) || !required(key)) return;
      if (rulesFor(getSet(key)).length || (key === 'exit' && exitGain.on)) return;
      m.push([CARD_STEP[key], `No ${c[key][0].toLowerCase()} are set. Choose at least one indicator in the "${c[key][0]}" step.`]);
    });
    return m;
  }
  function renderReview() {
    const snap = snapshot();
    const warns = missingRules().map(x => x[1]);
    const cd = (t, body, st) => `<div class="sum-card"><div class="sum-head"><span class="sum-title">${t}</span><button type="button" class="sum-edit" data-go="${st}">EDIT</button></div><div class="sum-body">${body}</div></div>`;
    const noBtn = h => h.replace(/<button[\s\S]*?<\/button>/, '');
    const c = copyFor();
    const cards = [cd('ASSET &amp; PERIOD', snap[0], 1), cd('CAPITAL &amp; RISK', snap[1], 2)];
    ['entry', 'exit', 'short', 'cover'].forEach((key, i) => {
      if (visibleSteps().includes(CARD_STEP[key])) cards.push(cd(c.cards[key], noBtn(snap[2 + i]), CARD_STEP[key]));
    });
    stepEl(LAST).innerHTML = `<h3>${esc(STEPS[LAST - 1].h)}</h3>`
      + warns.map(w => `<div class="bt-wz-warn">${w}</div>`).join('')
      + `<div class="bt-wz-review">${cards.join('')}</div>`
      + `<div class="bt-wz-hint" style="margin-top:10px;">Results show what the rules would have done historically. This is a simulation for learning, not advice.</div>`
      + `<button type="button" class="bt-wz-run" id="btWzRun">&#9654; RUN BACKTEST</button>`;
  }
  overlay.addEventListener('click', e => {
    if (e.target === overlay) return closeWizard();
    const g = e.target.closest('[data-go]');
    if (g) return go(+g.dataset.go);
    const sb = e.target.closest('.bt-wz-steps button');
    if (sb) return go(+sb.dataset.step);
    if (e.target.closest('#btWzRun')) {
      const miss = missingRules();
      if (miss.length) return go(miss[0][0]);
      closeWizard(); window.runBacktest();
    }
  });
  overlay.querySelector('.bt-wz-close').addEventListener('click', closeWizard);
  $('btWzBack').addEventListener('click', () => { const v = visibleSteps(); go(v[Math.max(0, v.indexOf(step) - 1)]); });
  $('btWzNext').addEventListener('click', () => { const v = visibleSteps(); return step >= LAST ? closeWizard() : go(v[v.indexOf(step) + 1]); });
  document.addEventListener('keydown', e => {
    if (e.key !== 'Escape') return;
    if (sigOverlay.style.display !== 'none') sigOverlay.style.display = 'none';
    else if (overlay.style.display !== 'none') closeWizard();
  });

  // ── Running: entry rules go as normal params; each extra rule set as a prefixed param (POST body) ──
  //   x_ = exit rules, s_ = short entry rules, c_ = short exit rules
  const SHARED_KEYS = new Set(['symbol', 'period', 'interval', 'start_date', 'end_date', 'stop_loss', 'take_profit', 'sl_tp_unit',
    'trailing_stop', 'trail_distance', 'capital', 'trade_amount_mode', 'trade_amount', 'min_confidence',
    'direction', 'reverse_on_stop', 'level_price', 'level_cross', 'fee_pct', 'borrow_pct']);
  let captured = null, extra = null;
  window.btParamsHook = function (params) {
    if (captured) { captured.params = params; return 'stop'; }
    if (extra) extra.forEach(([k, v]) => params.append(k, v));
    return null;
  };
  const origRun = window.runBacktest;
  window.runBacktest = async function () {
    const miss = missingRules();
    if (miss.length) {
      $('errorMsg').textContent = miss.map(x => x[1]).join(' ');
      ['idleState', 'loadingState', 'resultsPanel'].forEach(id => { $(id).style.display = 'none'; });
      $('errorState').style.display = 'flex';
      openWizard(miss[0][0]);
      return;
    }
    if (window.innerWidth <= 768 && $('labMain')) $('labMain').scrollIntoView({ behavior: 'smooth', block: 'start' });
    // Let the page build each extra rule set's params from the controls (dry runs), then do the real run.
    const split = isSplit();
    const wanted = [['exit', 'x_']];
    if (split) { wanted.push(['short', 's_']); if (rulesFor(getSet('cover')).length) wanted.push(['cover', 'c_']); }
    const got = {};
    for (const [key] of wanted) {
      activate(key);
      captured = {};
      try { await origRun.apply(this, arguments); } finally { got[key] = captured.params; captured = null; activate('entry'); }
      if (!got[key]) return;   // page-level validation already showed its message
    }
    extra = [['x_set', '1'], ['x_min_confidence', confs.exit], ['entry_match', match.entry], ['x_match', match.exit]];
    if (exitGain.on) {
      // "Must be reached first" needs indicators to gate; with none it is just a profit-target close signal.
      extra.push(['x_exit_gain_pct', exitGain.pct], ['x_exit_gain_mode', exitGain.mode === 'require' && rulesFor(sets.exit).length ? 'require' : 'signal']);
    }
    wanted.forEach(([key, pre]) => {
      if (key !== 'exit') extra.push([pre + 'set', '1'], [pre + 'min_confidence', confs[key]], [pre + 'match', match[key]]);
      got[key].forEach((v, k) => { if (!SHARED_KEYS.has(k)) extra.push([pre + k, v]); });
    });
    try { return await origRun.apply(this, arguments); } finally { extra = null; }
  };

  // ── Copy strategy from Signals ─────────────────────────────────────────────
  // Inverse of the Signals page's "Import from Backtester": Signals conditions -> Backtester toggles + trigger modes.
  const sigOverlay = document.createElement('div');
  sigOverlay.className = 'bt-sig-overlay';
  sigOverlay.innerHTML = `<div class="bt-sig-modal"><div class="bt-wz-head"><div class="bt-wz-title">COPY STRATEGY FROM SIGNALS</div>
    <button type="button" class="bt-wz-close" aria-label="Close">&#10005;</button></div>
    <div class="bt-wz-hint" style="margin:10px 16px 0;">Pick a strategy from the Signals page. Its buy conditions become the buy rules and its sell conditions the sell rules. Review them before running.</div>
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
        sigCache.push({ name: prefs.strategyName || 'Current strategy', sub: 'Open on the Signals page now', conditions: prefs.strategyConditions, match: prefs.strategyMatch, direction: prefs.strategyDirection, current: true, prefs });
      }
      (Array.isArray(prefs.savedStrategies) ? prefs.savedStrategies : []).forEach(s => {
        if (s && Array.isArray(s.conditions) && s.conditions.length) sigCache.push({ name: s.name, sub: 'Saved on Signals', conditions: s.conditions, match: s.match, direction: s.direction, prefs });
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

  // Signals conditions carry a buy/sell direction and the strategy a trade direction. Which Backtester rule set a
  // condition feeds depends on that direction:
  //   long  - buys open (entry), sells close (exit)         short - sells open (entry), buys close (exit)
  //   both  - buys open a long (entry), sells open a short (own short rules)
  function setFromSignals(t, restricted) {
    const o = blankSet(rawSerialize());
    t.used.forEach(({ spec, modes }, togId) => {
      if (restricted) {
        const bk = Object.keys(BT_BASIC_TOGGLE_MAP).find(k => BT_BASIC_TOGGLE_MAP[k].togId === togId);
        if (bk) o[bk] = true;
      } else {
        o[togId] = true;
        if (spec.chips) o[spec.chips] = [...modes];
      }
    });
    return Object.assign(o, t.values, t.params);
  }

  function copyFromSignals(item) {
    const restricted = typeof btGating !== 'undefined' && btGating && btGating.restricted;
    const p0 = item.prefs || {};
    const hasBuy = item.conditions.some(c => c.direction !== 'sell'), hasSell = item.conditions.some(c => c.direction === 'sell');
    const inferred = hasBuy && hasSell ? 'both' : (hasSell ? 'short' : 'long');   // older Signals saves have no direction
    const dir = ['long', 'short', 'both'].includes(item.direction) ? item.direction
      : (item.current && ['long', 'short', 'both'].includes(p0.strategyDirection) ? p0.strategyDirection : inferred);
    const buys = item.conditions.filter(c => c.direction !== 'sell');
    const sells = item.conditions.filter(c => c.direction === 'sell');
    const split = dir === 'both' && !item.noSplit;
    const groups = dir === 'short' ? { entry: sells, exit: buys } : dir === 'both' ? (split ? { entry: buys, short: sells } : { entry: item.conditions }) : { entry: buys, exit: sells };
    const tr = {};
    Object.entries(groups).forEach(([k, conds]) => { tr[k] = translateSignals(conds, restricted); });
    const hint = $('btSigHint');
    if (!Object.values(tr).some(t => t.used.size)) {
      hint.textContent = `"${item.name}" has no conditions the Backtester can run${restricted ? ' on your plan' : ''}.`;
      sigOverlay.style.display = 'none';
      return;
    }
    const blank = blankSet(rawSerialize());
    const cfg = { ...rawSerialize(), ...setFromSignals(tr.entry, restricted) };
    cfg._indicatorMode = restricted ? 'basic' : 'detailed';
    cfg._exit = tr.exit ? setFromSignals(tr.exit, restricted) : blank;
    cfg._short = tr.short ? setFromSignals(tr.short, restricted) : blank;
    cfg._cover = blank;
    const m = item.match === 'all' ? 'all' : 'any';
    cfg._match = { entry: m, exit: m, short: m, cover: m };
    cfg.splitShort = split;
    cfg._direction = dir;

    // Risk settings from the Signals page (percent-based on both pages). Forex here is pip-based, so skip those.
    const p = item.prefs || {};
    if (!IS_FOREX) {
      if (isFinite(p.stopLoss) && !p.stopLossCcyMode) cfg.stopLoss = p.stopLoss;
      if (isFinite(p.targetGain) && !p.targetGainCcyMode) cfg.takeProfit = p.targetGain;
      if (typeof p.trailSL === 'boolean') cfg.trailSL = p.trailSL;
      if (isFinite(p.trailDist)) cfg.trailDist = p.trailDist;
    }
    if (isFinite(p.minConfidence)) { cfg.minConf = p.minConfidence; cfg._exitMinConf = p.minConfidence; cfg._shortMinConf = p.minConfidence; }
    else { cfg._exitMinConf = confs.exit; cfg._shortMinConf = confs.short; }
    cfg._coverMinConf = confs.cover;
    if (isFinite(p.capital)) cfg.btCapital = p.capital;
    if (p.currency && [...$('btCurrency').options].some(o => o.value === p.currency)) cfg.btCurrency = p.currency;

    window.applyBacktestConfig(cfg);
    $('btStrategyName').value = item.starter ? item.name : `${item.name} (from Signals)`;
    const skipped = Object.values(tr).flatMap(t => t.skipped);
    const parts = Object.entries(tr).map(([k, t]) => `${t.used.size} for the ${copyFor().cards[k].toLowerCase()}`);
    const msg = `${item.starter ? 'Loaded starter' : 'Copied'} "${item.name}" (${dir === 'both' ? 'long & short' : dir + ' only'}): ${parts.join(', ')}.`
      + (!tr.entry.used.size ? ' It has no conditions for the entry rules, so set those before running.' : '')
      + (tr.exit && !tr.exit.used.size && dir !== 'both' ? ' It has no exit conditions, so set the exit rules before running.' : '')
      + (skipped.length ? ` Skipped (no Backtester equivalent): ${skipped.join(', ')}.` : '');
    hint.textContent = msg;
    const h2 = $('btStrategyHint'); if (h2) h2.textContent = msg;
    sigOverlay.style.display = 'none';
    renderSummary();
    [3, 4, 5, 6].forEach(n => { const c = $('btSumCard' + n); if (c) { c.classList.remove('flash'); void c.offsetWidth; c.classList.add('flash'); } });
  }

  // ── Starter strategies ─────────────────────────────────────────────────────
  // Ready-made two-sided setups. Same conditions as the Signals page starters; they load through the same
  // translation, so the Backtester shows them as ordinary rules to review and change.
  const STARTERS = {
    range: { name: 'Oversold Long / Overbought Short', direction: 'both', match: 'all',
      conditions: [{ type: 'rsi_below', value: 30, direction: 'buy' }, { type: 'bb_lower', value: 10, direction: 'buy' },
        { type: 'rsi_above', value: 70, direction: 'sell' }, { type: 'bb_upper', value: 90, direction: 'sell' }] },
    trend: { name: 'MACD Cross Flip', direction: 'both', match: 'all',
      conditions: [{ type: 'macd_bull_cross', value: 5, direction: 'buy' }, { type: 'macd_bear_cross', value: 5, direction: 'sell' }] },
    level: { name: 'Golden Cross Long / Short if Level Lost', direction: 'both', match: 'all', noSplit: true, level: true,
      conditions: [{ type: 'ma_golden', value: 10, direction: 'buy' }] },
  };
  function applyStarter(key) {
    const st = STARTERS[key];
    if (!st) return;
    // Reset the leftovers a previous run might have left behind, then load the rules.
    $('levelPrice').value = ''; $('levelCross').value = 'below';
    copyFromSignals({ ...st, starter: true, prefs: {} });
    if (st.level) {
      $('levelCross').value = 'below';
      const msg = 'Loaded "' + st.name + '". Enter the price to treat as lost in the Price-level trigger box (Trade Direction section), then run it. A close below that price closes the long and opens a short.';
      $('btSigHint').textContent = msg; const h2 = $('btStrategyHint'); if (h2) h2.textContent = msg;
      $('levelPrice').focus();
    }
  }
  sum.addEventListener('click', e => { const b = e.target.closest('[data-starter]'); if (b) applyStarter(b.dataset.starter); });

  window.btUi = { applyStarter, openWizard, closeWizard, openSignalsImport, copyFromSignals };
})();
