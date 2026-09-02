// Shared site footer — single source of truth for the footer markup, used
// by every marketing/content page instead of each page hand-copying its
// own <footer>. document.write()s the markup in place, same pattern as
// nav.js. Studio only shows once /api/me confirms an alpha_role, same gate
// nav.js uses for its Studio nav item.
//
// A page can override the logo via a data-logo attribute on this <script>
// tag, e.g. <script src="/static/js/footer.js" data-logo="GCE Square.png"></script>
(function () {
  var thisScript = document.currentScript;
  var logoFile = (thisScript && thisScript.getAttribute('data-logo')) || 'Green Square.png';
  var style = (thisScript && thisScript.getAttribute('data-style')) || 'default';

  var FOOTER_HTML = style === 'tool' ? (
'<footer class="tool-footer">' +
'  <div class="tool-footer-logo"><img src="/static/logos/' + logoFile + '" alt="Growth Capital Group"></div>' +
'  <div class="tool-footer-links">' +
'    <a href="/">Home</a>' +
'    <a href="/learn">Education</a>' +
'    <a href="/tools">Tools</a>' +
'    <a href="/arena">Arena</a>' +
'    <a href="/alpha/studio" id="footerStudioLink" style="display:none;">Studio</a>' +
'    <a href="/company">Group</a>' +
'  </div>' +
'  <div class="tool-footer-copy">© 2026 Growth Capital Group</div>' +
'</footer>'
  ) : (
'<footer>' +
'  <div class="footer-inner">' +
'    <div class="footer-logo"><img id="footerLogo" src="/static/logos/' + logoFile + '" alt="Growth Capital Group" style="height:40px;width:auto;border-radius:6px;"></div>' +
'    <div class="footer-links">' +
'      <a href="/">Home</a>' +
'      <a href="/learn">Education</a>' +
'      <a href="/tools">Tools</a>' +
'      <a href="/arena">Arena</a>' +
'      <a href="/alpha/studio" id="footerStudioLink" style="display:none;">Studio</a>' +
'      <a href="/company">Group</a>' +
'    </div>' +
'    <div class="footer-copy">© 2026 Growth Capital Group. All rights reserved.</div>' +
'  </div>' +
'</footer>'
  );

  document.write(FOOTER_HTML);

  (async function checkAuth() {
    try {
      const res = await fetch('/api/me', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.alpha_role) {
          const studioLink = document.getElementById('footerStudioLink');
          if (studioLink) studioLink.style.display = '';
        }
      }
    } catch (e) { /* not logged in, keep hidden */ }
  })();
})();
