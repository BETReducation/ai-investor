// Sign-up pop-up: register free (with the plan options) or just the newsletter by email with four triggers: timed engagement, scroll depth, desktop exit intent,
// and a gate on lesson-PDF downloads. Loaded from nav.js. Shows at most once per page view, never to signed-in
// members, and stays quiet for 14 days after a dismissal (365 days after signing up).
(function () {
  if (window.top !== window.self || window.__gcgNl) return;
  window.__gcgNl = true;
  var SKIP = /^\/(admin|login|profile|reset-password|alpha\/studio|dataviz-studio|signal|newsletter|api)/;
  if (SKIP.test(location.pathname)) return;

  function getC(n) { var m = document.cookie.match('(?:^|; )' + n + '=([^;]*)'); return m ? m[1] : ''; }
  function setC(n, v, days) { document.cookie = n + '=' + v + ';max-age=' + days * 86400 + ';path=/;SameSite=Lax'; }
  var PLANS = null, member = false, shown = false, root = null, gatedHref = null, sawMe = false;

  function quiet() { return member || getC('gcg_nl') || getC('gcg_nl_x'); }

  var css = '#gcgNl{position:fixed;inset:0;z-index:100000;display:flex;align-items:center;justify-content:center;padding:16px;background:rgba(5,12,24,.55)}' +
    '#gcgNl .b{position:relative;width:100%;max-width:420px;background:var(--gcg-nl-bg,#fff);color:var(--gcg-nl-tx,#0b1f3a);border-radius:18px;padding:28px 24px 22px;box-shadow:0 20px 60px rgba(0,0,0,.35);font:15px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}' +
    '#gcgNl h2{margin:0 0 6px;font-size:22px;line-height:1.25;letter-spacing:-.02em}#gcgNl p{margin:0 0 14px;color:var(--gcg-nl-mu,#5b6b80);font-size:14px}' +
    '#gcgNl .x{position:absolute;top:6px;right:6px;width:44px;height:44px;border:0;background:none;color:inherit;font-size:26px;line-height:1;cursor:pointer;border-radius:50%}' +
    '#gcgNl input[type=email]{width:100%;padding:12px 14px;font:inherit;border-radius:10px;border:1.5px solid var(--gcg-nl-ln,#c9d3df);background:transparent;color:inherit;box-sizing:border-box}' +
    '#gcgNl label.c{display:flex;gap:8px;align-items:flex-start;margin:10px 0 14px;font-size:12.5px;color:var(--gcg-nl-mu,#5b6b80);cursor:pointer}#gcgNl label.c input{margin-top:3px;flex:none}' +
    '#gcgNl .go{width:100%;padding:13px;border:0;border-radius:10px;background:#f7931a;color:#fff;font:inherit;font-weight:700;cursor:pointer}#gcgNl .go[disabled]{opacity:.6}' +
    '#gcgNl .er{color:#d6453d;font-size:13px;margin:8px 0 0;min-height:1em}#gcgNl .hp{position:absolute;left:-9999px;opacity:0}' +
    '#gcgNl .b{max-height:92vh;overflow:auto}#gcgNl .pls{display:grid;gap:6px;margin:0 0 14px}#gcgNl .pl{display:grid;grid-template-columns:auto 1fr;column-gap:10px;align-items:baseline;border:1px solid var(--gcg-nl-ln,#c9d3df);border-radius:10px;padding:8px 12px}#gcgNl .pl small{grid-column:1/-1;color:var(--gcg-nl-mu,#5b6b80);font-size:12.5px}#gcgNl .pr{justify-self:end;font-weight:800}#gcgNl .pr small{font-weight:400;color:var(--gcg-nl-mu,#5b6b80)}' +
    '#gcgNl a.go{display:block;text-align:center;text-decoration:none;box-sizing:border-box}#gcgNl .pp{display:block;text-align:center;margin:8px 0 2px;font-size:13px;color:var(--gcg-nl-mu,#5b6b80)}#gcgNl .or{display:flex;align-items:center;gap:10px;margin:14px 0 10px;font-size:12px;color:var(--gcg-nl-mu,#5b6b80)}#gcgNl .or:before,#gcgNl .or:after{content:"";flex:1;border-top:1px solid var(--gcg-nl-ln,#c9d3df)}#gcgNl .go.alt{background:transparent;color:inherit;border:1.5px solid var(--gcg-nl-ln,#c9d3df)}' +
    '@media(max-width:520px){#gcgNl{align-items:flex-end;padding:0}#gcgNl .b{max-width:none;border-radius:18px 18px 0 0;padding-bottom:calc(22px + env(safe-area-inset-bottom))}}';
  var dark = '--gcg-nl-bg:#112240;--gcg-nl-tx:#eef2f7;--gcg-nl-mu:#93a4bb;--gcg-nl-ln:#2c4a78;';
  css += ':root[data-theme="dark"] #gcgNl{' + dark + '}@media(prefers-color-scheme:dark){:root:not([data-theme="light"]) #gcgNl{' + dark + '}}';

  function close(dismiss) {
    if (dismiss && root && root.querySelector('#gcgNlT') && /PDF/.test(root.querySelector('#gcgNlT').textContent)) dismiss = false;
    if (!root) return;
    root.remove(); root = null; document.removeEventListener('keydown', onKey);
    if (dismiss) setC('gcg_nl_x', '1', 14);
    if (prevFocus && prevFocus.focus) try { prevFocus.focus(); } catch (e) {}
  }
  var prevFocus = null;
  function onKey(e) { if (e.key === 'Escape') close(true); }

  function open(mode) {
    if (shown || root || (mode !== 'pdf' && quiet())) return;
    shown = true; prevFocus = document.activeElement;
    if (!document.getElementById('gcgNlCss')) { var st = document.createElement('style'); st.id = 'gcgNlCss'; st.textContent = css; document.head.appendChild(st); }
    var gate = mode === 'pdf';
    root = document.createElement('div'); root.id = 'gcgNl';
    var reg = '/login?tab=register&next=' + encodeURIComponent(location.pathname + location.search);
    var tiers = (PLANS || [{ id: 'free', name: 'Free', monthly: 0, blurb: 'Explore the basics and see how everything works.' }, { id: 'beginner', name: 'Beginner', monthly: 500, blurb: 'Full Alpha posts, intermediate lessons and the community chat.' }, { id: 'pro', name: 'Pro', monthly: 2000, blurb: 'Everything, including the full Backtester and Signals suite.' }]).map(function (p) {
      return '<div class="pl"><b>' + p.name + '</b><span class="pr">' + (p.monthly ? '$' + (p.monthly / 100) + '<small>/mo</small>' : 'Free') + '</span><small>' + p.blurb + '</small></div>';
    }).join('');
    root.innerHTML = '<div class="b" role="dialog" aria-modal="true" aria-labelledby="gcgNlT"><button class="x" type="button" aria-label="Close">×</button>' +
      '<h2 id="gcgNlT">' + (gate ? 'Free PDF: register or enter your email' : 'Join Growth Capital Group free') + '</h2>' +
      '<p>' + (gate ? 'Register free and this PDF is yours, or just enter your email below and it downloads straight away.' : 'Create a free account for beginner lessons, selected data visualisations and the basic tools. Upgrade whenever you want more.') + '</p>' +
      '<div class="pls">' + tiers + '</div>' +
      '<a class="go reg" href="' + reg + '">Register free</a><a class="pp" href="/pricing">Compare plans in full</a>' +
      '<div class="or"><span>or just the newsletter</span></div>' +
      '<form novalidate><input class="hp" name="website" tabindex="-1" autocomplete="off" aria-hidden="true">' +
      '<input type="email" name="email" placeholder="you@example.com" autocomplete="email" required aria-label="Email address">' +
      '<label class="c"><input type="checkbox" name="consent"><span>Yes, email me the weekly newsletter. Educational and historical content only. Unsubscribe any time.</span></label>' +
      '<button class="go alt" type="submit">' + (gate ? 'Email me &amp; download' : 'Newsletter only, no account') + '</button><div class="er" role="alert"></div></form></div>';
    document.body.appendChild(root);
    var f = root.querySelector('form'), er = root.querySelector('.er'), go = root.querySelector('.go');
    root.querySelector('.x').onclick = function () { close(true); };
    root.addEventListener('mousedown', function (e) { if (e.target === root) close(true); });
    document.addEventListener('keydown', onKey);
    root.querySelector('.reg').focus();
    f.onsubmit = function (e) {
      e.preventDefault(); er.textContent = ''; go.disabled = true;
      fetch('/api/newsletter/signup', { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: f.email.value, consent: f.consent.checked, website: f.website.value, source: gate ? 'pdf:' + location.pathname : 'popup:' + location.pathname }) })
        .then(function (r) { return r.json().then(function (j) { return [r.ok, j]; }); })
        .then(function (x) {
          if (!x[0]) { er.textContent = x[1].error || 'Something went wrong. Please try again.'; go.disabled = false; return; }
          setC('gcg_nl', '1', 365);
          root.querySelector('.b').innerHTML = '<button class="x" type="button" aria-label="Close">×</button><h2>You are in</h2><p>' + (gate && gatedHref ? 'Your download is starting.' : 'Thanks. Look out for the next newsletter.') + '</p>';
          root.querySelector('.x').onclick = function () { close(false); };
          setTimeout(function () { close(false); }, 2500);
          if (gate && gatedHref) { var a = document.createElement('a'); a.href = gatedHref; a.download = ''; document.body.appendChild(a); a.click(); a.remove(); }
        }).catch(function () { er.textContent = 'Could not reach the server. Please try again.'; go.disabled = false; });
    };
  }

  // 1. Timed engagement: 45 seconds on the page, only counting while the tab is visible.
  var vis = 0, tick = setInterval(function () {
    if (document.visibilityState === 'visible') vis++;
    if (vis >= 45) { clearInterval(tick); if (ready()) open('popup'); }
  }, 1000);
  function ready() { return sawMe && !quiet(); }

  // 2. Scroll depth: 60% down a long page (skips short pages, where the whole page is already in view).
  window.addEventListener('scroll', function onS() {
    var d = document.documentElement, long = d.scrollHeight > innerHeight * 2.5;
    if (long && (scrollY + innerHeight) / d.scrollHeight >= 0.6 && ready()) { window.removeEventListener('scroll', onS); open('popup'); }
  }, { passive: true });

  // 3. Exit intent: cursor leaves through the top of the window (desktop pointers only), after 10 seconds.
  var t0 = Date.now();
  if (matchMedia('(pointer:fine)').matches) document.addEventListener('mouseout', function (e) {
    if (!e.relatedTarget && e.clientY <= 0 && Date.now() - t0 > 10000 && ready()) open('popup');
  });

  // 4. Content gate: lesson PDFs ask for an email first (once; signed-in members and subscribers skip it).
  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[href]');
    if (!a || !/\.pdf(\?|#|$)/i.test(a.getAttribute('href')) || a.origin !== location.origin) return;
    if (!sawMe || member || getC('gcg_nl')) return;
    e.preventDefault(); gatedHref = a.href; shown = false; open('pdf');
  }, true);

  fetch('/api/plans', { credentials: 'include' }).then(function (r) { return r.json(); })
    .then(function (d) { member = !!(d && d.me && d.me.authenticated); if (d && d.plans && d.plans.length) PLANS = d.plans; }).catch(function () {}).then(function () { sawMe = true; });
})();
