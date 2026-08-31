// Makes every .info-dot (see .info-dot / .info-dot-popover in gca.css) show
// its explanation reliably — on hover AND on tap, and never clipped by a
// scrolling sidebar or cut off by the page edge.
//
// Deliberately does NOT use the native `title` attribute for the tooltip
// text (that's what data-tip is for) — a real `title` fires the browser's
// own hover tooltip *at the same time* as this one, which is what produced
// the double, overlapping tooltip Gary flagged. The text lives in data-tip
// only; the popover here is the single source of the tooltip.
(function () {
  let openDot = null, openPopover = null;

  function closeOpen() {
    if (openPopover) { openPopover.remove(); openPopover = null; }
    openDot = null;
  }

  function showFor(dot) {
    if (openDot === dot) return;
    closeOpen();
    const text = dot.getAttribute('data-tip');
    if (!text) return;

    const pop = document.createElement('div');
    pop.className = 'info-dot-popover';
    pop.textContent = text;
    // Appended to <body> with fixed positioning so it can never be clipped
    // by a sidebar's overflow:auto/hidden, and always sits above everything.
    document.body.appendChild(pop);

    const dotRect = dot.getBoundingClientRect();
    const popRect = pop.getBoundingClientRect();
    let left = dotRect.left + dotRect.width / 2 - popRect.width / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - popRect.width - 8));

    const spaceAbove = dotRect.top;
    const showAbove = spaceAbove > popRect.height + 16;
    const top = showAbove ? dotRect.top - popRect.height - 8 : dotRect.bottom + 8;

    pop.style.left = left + 'px';
    pop.style.top = top + 'px';
    pop.classList.toggle('below', !showAbove);

    openDot = dot;
    openPopover = pop;
  }

  document.addEventListener('click', function (e) {
    const dot = e.target.closest('.info-dot');
    if (dot) {
      e.preventDefault();
      e.stopPropagation();
      if (openDot === dot) { closeOpen(); } else { showFor(dot); }
      return;
    }
    closeOpen();
  });

  document.addEventListener('mouseover', function (e) {
    const dot = e.target.closest('.info-dot');
    if (dot) showFor(dot);
  });
  document.addEventListener('mouseout', function (e) {
    const dot = e.target.closest('.info-dot');
    if (dot && (!e.relatedTarget || !e.relatedTarget.closest('.info-dot'))) closeOpen();
  });
  document.addEventListener('focusin', function (e) {
    const dot = e.target.closest('.info-dot');
    if (dot) showFor(dot);
  });

  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') closeOpen();
  });
  window.addEventListener('scroll', closeOpen, true);
  window.addEventListener('resize', closeOpen);
})();
