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
    '#lb-panel{position:fixed;bottom:90px;right:24px;z-index:9999;width:340px;max-width:90vw;' +
    'height:440px;max-height:70vh;background:var(--lb-bg,#0b0f1a);color:var(--lb-fg,#e8ecf4);' +
    'border-radius:14px;box-shadow:0 12px 40px rgba(0,0,0,0.35);display:none;flex-direction:column;' +
    'overflow:hidden;font:14px/1.4 system-ui,sans-serif;border:1px solid rgba(255,255,255,0.08);}' +
    '#lb-panel.lb-open{display:flex;}' +
    '#lb-head{padding:12px 14px;background:rgba(0,212,170,0.12);font-weight:600;' +
    'border-bottom:1px solid rgba(255,255,255,0.08);}' +
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
    '<div id="lb-head">Ask about this lesson</div>' +
    '<div id="lb-msgs"></div>' +
    '<div id="lb-chips"></div>' +
    '<div class="lb-hint">Educational explanations only — not personalised investment advice.</div>' +
    '<form id="lb-form"><input id="lb-input" autocomplete="off" placeholder="Ask a question…">' +
    '<button id="lb-send" type="submit">Send</button></form>';
  document.body.appendChild(panel);

  var msgsEl = panel.querySelector('#lb-msgs');
  var chipsEl = panel.querySelector('#lb-chips');
  var inputEl = panel.querySelector('#lb-input');
  var suggestionsLoaded = false;

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
