// Makes every .info-dot (see .info-dot / .info-dot-popover in gca.css) work
// on tap, not just hover — a bare `title` attribute is invisible on touch on
// most mobile browsers, which is the whole reason these markers exist.
// Desktop keeps the native title-on-hover tooltip; this only adds a tap
// handler, it doesn't replace anything.
(function () {
  let openDot = null, openPopover = null;

  function closeOpen() {
    if (openPopover) { openPopover.remove(); openPopover = null; }
    openDot = null;
  }

  document.addEventListener('click', function (e) {
    const dot = e.target.closest('.info-dot');
    if (dot) {
      e.preventDefault();
      e.stopPropagation();
      if (openDot === dot) { closeOpen(); return; }
      closeOpen();
      const text = dot.getAttribute('title');
      if (!text) return;
      const pop = document.createElement('div');
      pop.className = 'info-dot-popover';
      pop.textContent = text;
      dot.appendChild(pop);
      openDot = dot;
      openPopover = pop;
      return;
    }
    // Any other click/tap closes an open popover.
    closeOpen();
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeOpen();
  });
})();
