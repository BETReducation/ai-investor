// Shows a small "From the Alpha desk" callout on a /learn/<level>/<slug> lesson
// page, linking to any published Alpha post an author has confirmed relates to
// this lesson (set from the Alpha Studio's "Related Learn lesson" field — see
// api_lesson_related_alpha in app.py). Self-contained: derives its own slug
// from the URL, so a lesson page just needs this one <script> tag, no wiring.
(function () {
  const m = location.pathname.match(/^\/learn\/[^/]+\/([^/]+)\/?$/);
  if (!m) return;
  const slug = m[1];

  fetch('/api/lessons/' + slug + '/related-alpha')
    .then(function (r) { return r.ok ? r.json() : { items: [] }; })
    .then(function (data) {
      const items = data.items || [];
      if (!items.length) return;

      const footer = document.querySelector('footer');
      const box = document.createElement('div');
      box.style.cssText = 'max-width:900px;margin:0 auto 48px;padding:0 5%;';
      box.innerHTML = items.map(function (a) {
        const author = a.author.charAt(0).toUpperCase() + a.author.slice(1);
        return (
          '<a href="' + a.url + '" style="display:block;padding:18px 22px;border:1px solid var(--border);border-radius:14px;background:var(--card);text-decoration:none;margin-bottom:12px;">' +
          '<div style="font-size:11px;letter-spacing:.08em;text-transform:uppercase;color:var(--purple2,#7c3aed);margin-bottom:6px;">🔎 From the Alpha desk — ' + author + '</div>' +
          '<div style="font-weight:700;color:var(--text);">' + a.title + '</div>' +
          (a.note ? '<div style="font-size:13.5px;color:var(--muted);margin-top:4px;">' + a.note + '</div>' : '') +
          '</a>'
        );
      }).join('');

      if (footer && footer.parentNode) {
        footer.parentNode.insertBefore(box, footer);
      } else {
        document.body.appendChild(box);
      }
    })
    .catch(function () { /* silent — a missing/failed fetch just skips the callout */ });
})();
