// Greys out links to plan-locked pages and shows an upgrade prompt on click.
// The server enforces the same list (app.py _plan_gate); this just keeps the links visible.
(function () {
  var P = null;

  function needFor(a) {
    if (!P || !a.getAttribute('href')) return null;
    var u;
    try { u = new URL(a.href, location.origin); } catch (e) { return null; }
    if (u.origin !== location.origin) return null;
    var need = P.gates[u.pathname.replace(/\/$/, '')];
    if (!need) return null;
    return (P.rank[P.me.tier] || 0) < (P.rank[need] || 0) ? need : null;
  }

  function mark() {
    document.querySelectorAll('a[href]:not([data-gated])').forEach(function (a) {
      var need = needFor(a);
      a.dataset.gated = need ? '1' : '0';
      if (!need) return;
      a.dataset.need = need;
      a.style.opacity = '0.55';
      a.title = (P.names[need] || 'Paid') + ' plan';
      var lock = document.createElement('span');
      lock.textContent = ' 🔒'; lock.style.fontSize = '0.85em';
      a.appendChild(lock);
    });
  }

  function modal(need) {
    var name = P.names[need] || 'paid';
    var ov = document.createElement('div');
    ov.style.cssText = 'position:fixed;inset:0;background:rgba(0,0,0,.6);z-index:100000;display:flex;align-items:center;justify-content:center;padding:20px;font-family:"Space Grotesk",sans-serif';
    ov.innerHTML = '<div style="background:var(--bg2,#fff);color:var(--text,#111);border:1px solid var(--border2,#ccc);border-radius:18px;padding:30px;max-width:420px;width:100%">' +
      '<div style="font-size:30px">🔒</div>' +
      '<div style="font-family:Outfit,sans-serif;font-weight:800;font-size:22px;margin:8px 0">Part of the ' + name + ' plan</div>' +
      '<p style="color:var(--muted,#667);font-size:14px;line-height:1.6;margin-bottom:20px">Upgrade to unlock this and everything else in the ' + name + ' plan. You can cancel any time.</p>' +
      '<div style="display:flex;gap:10px"><a href="/pricing?need=' + need + '" style="background:var(--green,#00a882);color:#04110d;font-weight:700;padding:11px 20px;border-radius:10px;text-decoration:none;font-size:14px">See plans</a>' +
      '<button style="background:none;border:1px solid var(--border2,#ccc);color:inherit;padding:11px 20px;border-radius:10px;cursor:pointer;font:inherit;font-size:14px">Not now</button></div></div>';
    ov.addEventListener('click', function (e) { if (e.target === ov || e.target.tagName === 'BUTTON') ov.remove(); });
    document.body.appendChild(ov);
  }

  document.addEventListener('click', function (e) {
    var a = e.target.closest && e.target.closest('a[data-gated="1"]');
    if (!a) return;
    e.preventDefault(); e.stopPropagation();
    modal(a.dataset.need);
  }, true);

  fetch('/api/plans', { credentials: 'include' }).then(function (r) { return r.json(); }).then(function (d) {
    P = d; mark();
    var t;
    new MutationObserver(function () { clearTimeout(t); t = setTimeout(mark, 150); }).observe(document.body, { childList: true, subtree: true });
  }).catch(function () {});
})();
