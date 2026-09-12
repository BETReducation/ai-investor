// Floating "Ask about this lesson" chat widget for /learn/<level>/<slug> pages.
// Self-contained (own markup + styles, injected on load) so it drops into any
// lesson file with a single <script> tag, same pattern as related-alpha.js.
// Answers come from POST /api/lesson-qa, which grounds the model in that one
// lesson's text and keeps replies educational, never personalised advice.
(function () {
  var m = location.pathname.match(/^\/learn\/([^/]+)\/([^/]+)\/?$/);
  if (!m) return; // not a lesson page (e.g. /learn/beginner index) — nothing to attach to
  var slug = m[2];

  var history = [];
  var open = false;

  var style = document.createElement('style');
  style.textContent =
    '#lb-fab{position:fixed;bottom:24px;right:24px;z-index:9999;width:56px;height:56px;' +
    'border-radius:50%;border:none;cursor:pointer;background:#00d4aa;color:#04120e;' +
    'font-size:24px;box-shadow:0 6px 20px rgba(0,0,0,0.25);display:flex;align-items:center;' +
    'justify-content:center;}' +
    '#lb-panel{position:fixed;bottom:90px;right:24px;z-index:9999;width:480px;max-width:92vw;' +
    'height:620px;max-height:82vh;min-width:300px;min-height:320px;background:var(--lb-bg,#0b0f1a);' +
    'color:var(--lb-fg,#e8ecf4);border-radius:14px;box-shadow:0 12px 40px rgba(0,0,0,0.35);' +
    'display:none;flex-direction:column;overflow:hidden;font:14px/1.4 system-ui,sans-serif;' +
    'border:1px solid rgba(255,255,255,0.08);}' +
    '#lb-panel.lb-open{display:flex;}' +
    '#lb-panel.lb-full{position:fixed;top:5vh;left:5vw;right:5vw;bottom:5vh;width:auto!important;' +
    'height:auto!important;max-width:none;max-height:none;}' +
    '#lb-panel.lb-full #lb-resize{display:none;}' +
    '#lb-resize{position:absolute;top:0;left:0;width:26px;height:26px;cursor:nwse-resize;' +
    'z-index:2;background:linear-gradient(135deg,#00d4aa 0 40%,transparent 40%);' +
    'border-top-left-radius:14px;}' +
    '#lb-resize::after{content:"";position:absolute;top:7px;left:7px;width:8px;height:8px;' +
    'border-top:3px solid #04120e;border-left:3px solid #04120e;}' +
    '#lb-head{padding:12px 14px 12px 30px;background:rgba(0,212,170,0.12);font-weight:600;' +
    'border-bottom:1px solid rgba(255,255,255,0.08);display:flex;align-items:center;' +
    'justify-content:space-between;flex-shrink:0;position:relative;}' +
    '#lb-expand{border:none;background:none;color:inherit;opacity:0.7;cursor:pointer;' +
    'font-size:16px;padding:2px 6px;line-height:1;}' +
    '#lb-expand:hover{opacity:1;}' +
    '#lb-msgs{flex:1;overflow-y:auto;padding:12px;display:flex;flex-direction:column;gap:10px;}' +
    '.lb-msg{max-width:85%;padding:8px 11px;border-radius:10px;white-space:pre-wrap;}' +
    '.lb-user{align-self:flex-end;background:#00d4aa;color:#04120e;}' +
    '.lb-bot{align-self:flex-start;background:rgba(255,255,255,0.08);}' +
    '.lb-hint{opacity:0.6;font-size:12px;padding:0 12px 8px;}' +
    '#lb-chips{display:flex;flex-wrap:wrap;gap:6px;padding:0 12px 10px;}' +
    '.lb-chip{border:1px solid rgba(0,212,170,0.5);color:#00d4aa;background:none;' +
    'border-radius:14px;padding:5px 10px;font-size:12px;cursor:pointer;text-align:left;}' +
    '.lb-chip:hover{background:rgba(0,212,170,0.12);}' +
    '#lb-form{display:flex;border-top:1px solid rgba(255,255,255,0.08);}' +
    '#lb-input{flex:1;border:none;background:transparent;color:inherit;padding:10px;font:inherit;}' +
    '#lb-input:focus{outline:none;}' +
    '#lb-send{border:none;background:none;color:#00d4aa;font-weight:600;padding:0 14px;cursor:pointer;}';
  document.head.appendChild(style);

  var fab = document.createElement('button');
  fab.id = 'lb-fab';
  fab.title = 'Ask about this lesson';
  fab.textContent = '💬';
  document.body.appendChild(fab);

  var panel = document.createElement('div');
  panel.id = 'lb-panel';
  panel.innerHTML =
    '<div id="lb-resize" title="Drag to resize"></div>' +
    '<div id="lb-head"><span>Ask about this lesson</span>' +
    '<button id="lb-expand" type="button" title="Toggle fullscreen">⤢</button></div>' +
    '<div id="lb-msgs"></div>' +
    '<div id="lb-chips"></div>' +
    '<div class="lb-hint">Educational explanations only — not personalised investment advice.</div>' +
    '<form id="lb-form"><input id="lb-input" autocomplete="off" placeholder="Ask a question…">' +
    '<button id="lb-send" type="submit">Send</button></form>';
  document.body.appendChild(panel);

  var msgsEl = panel.querySelector('#lb-msgs');
  var chipsEl = panel.querySelector('#lb-chips');
  var inputEl = panel.querySelector('#lb-input');
  var expandBtn = panel.querySelector('#lb-expand');
  var resizeHandle = panel.querySelector('#lb-resize');
  var suggestionsLoaded = false;

  // Remember a manually drag-resized size across visits (per browser, this
  // origin only). Wrapped in try/catch — storage can be blocked or throw in
  // some browser contexts, and the widget should degrade to default size.
  try {
    var savedSize = JSON.parse(localStorage.getItem('lb-size') || 'null');
    if (savedSize && savedSize.w && savedSize.h) {
      panel.style.width = savedSize.w;
      panel.style.height = savedSize.h;
    }
  } catch (e) {}

  function persistSize() {
    try {
      localStorage.setItem('lb-size', JSON.stringify({ w: panel.offsetWidth + 'px', h: panel.offsetHeight + 'px' }));
    } catch (e) {}
  }

  // Custom drag handle at the top-left corner — the panel is anchored to the
  // screen's bottom-right (fixed bottom/right), so growing it from the
  // opposite corner is what makes it visibly expand up and to the left.
  resizeHandle.addEventListener('pointerdown', function (e) {
    if (panel.classList.contains('lb-full')) return;
    e.preventDefault();
    var startX = e.clientX, startY = e.clientY;
    var startW = panel.offsetWidth, startH = panel.offsetHeight;
    resizeHandle.setPointerCapture(e.pointerId);

    function onMove(ev) {
      var w = startW + (startX - ev.clientX);
      var h = startH + (startY - ev.clientY);
      panel.style.width = w + 'px';
      panel.style.height = h + 'px';
    }
    function onUp() {
      document.removeEventListener('pointermove', onMove);
      document.removeEventListener('pointerup', onUp);
      persistSize();
    }
    document.addEventListener('pointermove', onMove);
    document.addEventListener('pointerup', onUp);
  });

  expandBtn.addEventListener('click', function () {
    panel.classList.toggle('lb-full');
    expandBtn.textContent = panel.classList.contains('lb-full') ? '⤡' : '⤢';
  });

  function addMsg(role, text) {
    var el = document.createElement('div');
    el.className = 'lb-msg ' + (role === 'user' ? 'lb-user' : 'lb-bot');
    el.textContent = text;
    msgsEl.appendChild(el);
    msgsEl.scrollTop = msgsEl.scrollHeight;
    return el;
  }

  function loadSuggestions() {
    if (suggestionsLoaded) return;
    suggestionsLoaded = true;
    fetch('/api/lesson-qa/suggestions?slug=' + encodeURIComponent(slug))
      .then(function (r) { return r.json(); })
      .then(function (data) {
        (data.suggestions || []).forEach(function (item) {
          var chip = document.createElement('button');
          chip.type = 'button';
          chip.className = 'lb-chip';
          chip.textContent = item.question;
          // Pre-written answer — no fetch, no API call, no quota used.
          chip.addEventListener('click', function () {
            addMsg('user', item.question);
            addMsg('bot', item.answer);
          });
          chipsEl.appendChild(chip);
        });
      })
      .catch(function () {});
  }

  fab.addEventListener('click', function () {
    open = !open;
    panel.classList.toggle('lb-open', open);
    if (open && !msgsEl.childElementCount) {
      addMsg('bot', "Hi! Ask me anything about this lesson and I'll explain it.");
      loadSuggestions();
      inputEl.focus();
    }
  });

  panel.querySelector('#lb-form').addEventListener('submit', function (e) {
    e.preventDefault();
    var q = inputEl.value.trim();
    if (!q) return;
    inputEl.value = '';
    addMsg('user', q);
    history.push({ role: 'user', content: q });
    var pending = addMsg('bot', '…');

    fetch('/api/lesson-qa', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ slug: slug, question: q, history: history }),
    })
      .then(function (r) {
        return r.json().then(function (data) { return { status: r.status, data: data }; });
      })
      .then(function (res) {
        var data = res.data;
        if (res.status === 401) {
          pending.textContent = 'Sign in to ask the lesson tutor questions.';
          return;
        }
        var answer = data.answer || data.error || "Sorry, I couldn't answer that.";
        pending.textContent = answer;
        if (data.answer) history.push({ role: 'assistant', content: answer });
      })
      .catch(function () {
        pending.textContent = 'Something went wrong reaching the tutor. Try again in a moment.';
      });
  });
})();
