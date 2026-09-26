// "Mark Complete" button on every lesson page, plus YouTube play tracking for the newsletter stats.
(function () {
  var m = location.pathname.match(/^\/learn\/(beginner|intermediate|pro)\/([^\/]+)\/?$/);
  if (!m) return;
  var slug = m[2];

  function track(kind, detail) {
    try {
      fetch('/api/track', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        credentials: 'same-origin', keepalive: true,
        body: JSON.stringify({ kind: kind, detail: detail || '' })
      }).catch(function () {});
    } catch (e) {}
  }

  // YouTube only emits state changes to pages that ask for the JS API, so
  // make sure each embed has enablejsapi=1 and subscribe to its messages.
  var ytPlayed = {};
  function watchYouTube() {
    var frames = document.querySelectorAll('iframe[src*="youtube.com/embed"], iframe[src*="youtube-nocookie.com/embed"]');
    frames.forEach(function (f, i) {
      var url = new URL(f.src, location.href);
      if (url.searchParams.get('enablejsapi') !== '1') {
        url.searchParams.set('enablejsapi', '1');
        url.searchParams.set('origin', location.origin);
        f.src = url.toString();
      }
      f.dataset.gcgVideo = url.pathname.split('/').pop();
      f.addEventListener('load', function () {
        f.contentWindow.postMessage(JSON.stringify({ event: 'listening', id: i }), '*');
        f.contentWindow.postMessage(JSON.stringify({ event: 'command', func: 'addEventListener', args: ['onStateChange'] }), '*');
      });
    });
    window.addEventListener('message', function (e) {
      if (!/youtube(-nocookie)?\.com$/.test(new URL(e.origin).hostname)) return;
      var d; try { d = typeof e.data === 'string' ? JSON.parse(e.data) : e.data; } catch (err) { return; }
      var state = d && (d.event === 'onStateChange' ? d.info : d.info && d.info.playerState);
      if (state !== 1) return;
      frames.forEach(function (f) {
        if (f.contentWindow === e.source && !ytPlayed[f.dataset.gcgVideo]) {
          ytPlayed[f.dataset.gcgVideo] = true;
          track('video_play', 'youtube:' + f.dataset.gcgVideo);
        }
      });
    });
  }

  function buildButton(done, signedIn) {
    var sec = document.createElement('section');
    sec.className = 'content-section';
    sec.innerHTML = '<div class="content-inner" style="text-align:center;">' +
      '<div id="gcgComplete" style="display:inline-block;background:var(--card);border:1px solid var(--border);border-radius:20px;padding:28px 36px;max-width:520px;">' +
      '<div style="font-family:Outfit,sans-serif;font-weight:800;font-size:20px;color:var(--text);margin-bottom:8px;">Finished this lesson?</div>' +
      '<div id="gcgCompleteNote" style="font-size:14px;color:var(--muted);line-height:1.6;margin-bottom:16px;"></div>' +
      '<button id="gcgCompleteBtn" style="border:none;border-radius:10px;padding:12px 26px;font-size:15px;font-weight:700;font-family:inherit;cursor:pointer;"></button>' +
      '</div></div>';
    var cta = document.querySelector('.cta-grid');
    var anchor = cta && cta.closest('section');
    if (anchor) anchor.parentNode.insertBefore(sec, anchor);
    else (document.querySelector('main') || document.body).appendChild(sec);

    var btn = sec.querySelector('#gcgCompleteBtn'), note = sec.querySelector('#gcgCompleteNote');
    function render() {
      if (!signedIn) {
        note.textContent = 'Sign in to track your progress across the Education section.';
        btn.textContent = 'Sign in'; btn.style.background = 'var(--purple2)'; btn.style.color = '#fff';
        return;
      }
      if (done) {
        note.textContent = 'Nicely done. This lesson is counted in your Education Progress.';
        btn.textContent = '✓ Completed (undo)'; btn.style.background = 'transparent';
        btn.style.color = 'var(--green)'; btn.style.border = '1px solid var(--green)';
      } else {
        note.textContent = 'Mark it complete to fill in your progress bar on your profile.';
        btn.textContent = 'Mark Complete'; btn.style.background = 'var(--green)';
        btn.style.color = '#03130f'; btn.style.border = 'none';
      }
    }
    btn.addEventListener('click', function () {
      if (!signedIn) { location.href = '/login'; return; }
      btn.disabled = true;
      fetch('/api/lesson-progress', {
        method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin',
        body: JSON.stringify({ slug: slug, done: !done })
      }).then(function (r) { if (r.ok) done = !done; }).finally(function () { btn.disabled = false; render(); });
    });
    render();
  }

  function init() {
    watchYouTube();
    fetch('/api/lesson-progress', { credentials: 'same-origin' })
      .then(function (r) { return r.ok ? r.json() : null; })
      .then(function (d) { buildButton(!!(d && d.completed.indexOf(slug) !== -1), !!d); })
      .catch(function () { buildButton(false, false); });
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', init); else init();
})();
