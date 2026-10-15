// Include at the end of <body> on every Explainer page. Works out the page's slug
// from /static/explainers/<slug>/, looks it up in /api/explainers and adds a back
// link plus coloured category pills next to the title. Categories come from the
// EXPLAINERS list in app.py, so a new Explainer needs nothing extra on the page.
(function () {
  var m = location.pathname.match(/\/explainers\/([^\/]+)/);
  var h1 = document.querySelector('h1');
  if (!m || !h1) return;
  var slug = decodeURIComponent(m[1]), cats = window.GCG_EXPLAINER_CATS || [];

  var st = document.createElement('style');
  st.textContent =
    '.gcg-back{display:inline-block;margin:18px 0 0;font:600 .85rem system-ui,sans-serif;color:var(--accent,#2563eb);text-decoration:none}' +
    '.gcg-back:hover{text-decoration:underline}' +
    '.gcg-pills{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 4px}' +
    '.gcg-pill{font:700 .7rem system-ui,sans-serif;text-transform:uppercase;letter-spacing:.08em;color:#fff;text-decoration:none;padding:4px 11px;border-radius:999px}' +
    '.gcg-pill:hover{filter:brightness(1.1)}';
  document.head.appendChild(st);

  var back = document.createElement('a');
  back.className = 'gcg-back'; back.href = '/learn/artifacts'; back.textContent = '← All artifacts';
  var wrap = h1.closest('header') || h1;
  wrap.parentNode.insertBefore(back, wrap);

  fetch('/api/explainers').then(function (r) { return r.json(); }).then(function (d) {
    var seen = {};
    (d.items || []).forEach(function (e) { if (e.slug === slug) (e.categories || []).forEach(function (c) { seen[c] = 1; }); });
    var mine = cats.filter(function (c) { return seen[c.slug]; });
    if (!mine.length) return;
    var box = document.createElement('div');
    box.className = 'gcg-pills';
    box.innerHTML = mine.map(function (c) {
      return '<a class="gcg-pill" style="background:' + c.color + '" href="/learn/artifacts#' + c.slug + '">' + c.name + '</a>';
    }).join('');
    h1.parentNode.insertBefore(box, h1.nextSibling);
  }).catch(function () {});
})();
