// Include at the end of <body> on every Explainer page. Works out the page's slug
// from /static/explainers/<slug>/, looks it up in /api/explainers and adds
// breadcrumbs plus coloured category pills next to the title. Categories come from the
// EXPLAINERS list in app.py, so a new Explainer needs nothing extra on the page.
(function () {
  // A #tab hash makes the browser jump to that panel, so open at the top instead.
  try { history.scrollRestoration = 'manual'; } catch (e) {}
  var go = true;
  function up() { if (go) scrollTo(0, 0); }
  ['wheel', 'touchstart', 'keydown', 'mousedown'].forEach(function (k) { addEventListener(k, function () { go = false; }, { once: true, passive: true }); });
  up(); addEventListener('load', up); setTimeout(up, 150); setTimeout(up, 500);

  var m = location.pathname.match(/\/explainers\/([^\/]+)/);
  var h1 = document.querySelector('h1');
  if (!m || !h1) return;
  var slug = decodeURIComponent(m[1]), cats = window.GCG_EXPLAINER_CATS || [];

  var st = document.createElement('style');
  st.textContent =
    '.gcg-crumbs{display:flex;flex-wrap:wrap;gap:6px;margin:18px 0 0;font:.85rem system-ui,sans-serif;color:var(--muted,#667)}' +
    '.gcg-crumbs a{color:var(--accent,#2563eb);text-decoration:none}.gcg-crumbs a:hover{text-decoration:underline}' +
    '.gcg-crumbs i{font-style:normal;opacity:.5}' +
    '.gcg-pills{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0 4px}' +
    '.gcg-pill{font:700 .7rem system-ui,sans-serif;text-transform:uppercase;letter-spacing:.08em;color:#fff;text-decoration:none;padding:4px 11px;border-radius:999px}' +
    '.gcg-pill:hover{filter:brightness(1.1)}';
  document.head.appendChild(st);

  var crumbs = document.createElement('nav');
  crumbs.className = 'gcg-crumbs'; crumbs.setAttribute('aria-label', 'Breadcrumb');
  var wrap = h1.closest('header') || h1;
  wrap.parentNode.insertBefore(crumbs, wrap);
  var base = [['Home', '/'], ['Education', '/learn'], ['Artifacts', '/learn/artifacts']];
  function drawCrumbs(cat) {
    var parts = base.slice();
    if (cat) parts.push([cat.name, '/learn/artifacts#' + cat.slug]);
    crumbs.innerHTML = parts.map(function (p) { return '<a href="' + p[1] + '">' + p[0] + '</a>'; }).concat(['<span>' + h1.textContent + '</span>']).join('<i>/</i>');
  }
  drawCrumbs();

  fetch('/api/explainers').then(function (r) { return r.json(); }).then(function (d) {
    var seen = {};
    (d.items || []).forEach(function (e) { if (e.slug === slug) (e.categories || []).forEach(function (c) { seen[c] = 1; }); });
    var mine = cats.filter(function (c) { return seen[c.slug]; });
    if (!mine.length) return;
    drawCrumbs(mine[0]);
    var box = document.createElement('div');
    box.className = 'gcg-pills';
    box.innerHTML = mine.map(function (c) {
      return '<a class="gcg-pill" style="background:' + c.color + '" href="/learn/artifacts#' + c.slug + '">' + c.name + '</a>';
    }).join('');
    h1.parentNode.insertBefore(box, h1.nextSibling);
  }).catch(function () {});
})();
