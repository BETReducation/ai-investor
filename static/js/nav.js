// Shared site nav — single source of truth for the nav bar markup + its
// behavior (theme toggle, mobile menu, auth state, site search), used by
// every marketing/content page instead of each page hand-copying its own
// <nav>. Loaded synchronously (no defer/async) from exactly where the old
// <nav> markup used to sit, and document.write()s the markup in place —
// that keeps it part of the normal parse stream, so it's in the DOM (and
// findable by document.querySelector('nav') etc.) before the page's own
// bottom-of-body <script> runs, same as if it had been static HTML.
//
// A page can override the logo via a data-logo attribute on this <script>
// tag itself, e.g. <script src="/static/js/nav.js" data-logo="GCA Simple Logo.svg"></script>
// (lesson pages use the simple mark instead of the full logo).
(function () {
  var thisScript = document.currentScript;
  var logoFile = (thisScript && thisScript.getAttribute('data-logo')) || 'Green Square.png';

  var NAV_HTML = '' +
'<nav>' +
'  <div class="nav-left">' +
'  <a href="/" class="nav-logo">' +
'    <img id="navLogo" src="/static/logos/' + logoFile + '" alt="Growth Capital Academy">' +
'  </a>' +
'  <ul class="nav-links">' +
'    <li><a href="/">Home</a></li>' +
'    <li class="has-dropdown">' +
'      <a href="/learn">Learn <span class="nav-chevron">▾</span></a>' +
'      <ul class="nav-dropdown">' +
'        <li><a href="/learn/beginner">Beginner</a></li>' +
'        <li><a href="/learn/intermediate">Intermediate</a></li>' +
'        <li><a href="/learn/pro">Pro</a></li>' +
'      </ul>' +
'    </li>' +
'    <li class="has-dropdown">' +
'      <a href="/tools">Tools <span class="nav-chevron">▾</span></a>' +
'      <ul class="nav-dropdown">' +
'        <li><a href="/tools/signals">Signals</a></li>' +
'        <li><a href="/backtester">Backtester</a></li>' +
'        <li><a href="/tools/portfolio">Portfolio Manager</a></li>' +
'        <li><a href="/tools/calculator">Calculator</a></li>' +
'        <li><a href="/tools/data-visualisation">Data Visualisation</a></li>' +
'      </ul>' +
'    </li>' +
'    <li class="has-dropdown">' +
'      <a href="/arena">The Arena <span class="nav-chevron">▾</span></a>' +
'      <ul class="nav-dropdown">' +
'        <li><a href="/arena/market-xi">Market XI</a></li>' +
'        <li><a href="/arena/competitions">Trading Competitions</a></li>' +
'        <li><a href="/arena/predictions">Predictions Markets</a></li>' +
'      </ul>' +
'    </li>' +
'    <li class="has-dropdown">' +
'      <a href="/alpha">Alpha <span class="nav-chevron">▾</span></a>' +
'      <ul class="nav-dropdown">' +
'        <li><a href="/alpha/connor">Connor</a></li>' +
'        <li><a href="/alpha/dave">Dave</a></li>' +
'        <li><a href="/alpha/gary">Gary</a></li>' +
'        <li><a href="/alpha/tom">Tom</a></li>' +
'        <li><a href="/alpha/podcast">Podcast</a></li>' +
'      </ul>' +
'    </li>' +
'    <li class="has-dropdown" id="navStudioLi" style="display:none;">' +
'      <a href="#" onclick="return false;">Studio <span class="nav-chevron">▾</span></a>' +
'      <ul class="nav-dropdown">' +
'        <li><a href="/alpha/studio">Alpha Studio</a></li>' +
'        <li><a href="/social-post-studio">Social Post Studio</a></li>' +
'        <li id="navDatavizStudioLi" style="display:none;"><a href="/dataviz-studio">Data Viz Studio</a></li>' +
'      </ul>' +
'    </li>' +
'    <li><a href="/partners">Partners</a></li>' +
'  </ul>' +
'  </div>' +
'  <div class="nav-cta">' +
'    <div class="nav-search" id="navSearch">' +
'      <button class="nav-search-toggle" id="navSearchToggle" title="Search" aria-label="Search">🔍</button>' +
'      <div class="nav-search-box" id="navSearchBox">' +
'        <div class="nav-search-input-wrap">' +
'          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>' +
'          <input class="nav-search-input" id="navSearchInput" type="text" placeholder="Search the site…" autocomplete="off">' +
'        </div>' +
'        <div class="nav-search-results" id="navSearchResults"></div>' +
'      </div>' +
'    </div>' +
'    <button class="theme-toggle" id="themeToggle" title="Toggle light/dark mode" onclick="toggleTheme()">🌙</button>' +
'    <a href="/login" class="btn-ghost" id="navSignIn">Sign Up / Sign In</a>' +
'    <button class="nav-hamburger" id="navHamburger" onclick="toggleMobileNav()" aria-label="Toggle menu" aria-expanded="false">' +
'      <span></span><span></span><span></span>' +
'    </button>' +
'  </div>' +
'</nav>';

  document.write(NAV_HTML);

  // ── Auth check on load — mirrors what every page used to inline ────────
  (async function checkAuth() {
    try {
      const res = await fetch('/api/me', { credentials: 'include' });
      if (res.ok) {
        const data = await res.json();
        if (data.authenticated && data.username) {
          const signIn = document.getElementById('navSignIn');
          if (signIn) {
            signIn.textContent = data.username;
            signIn.href = '/profile';
            signIn.style.color = 'var(--green)';
            signIn.style.borderColor = 'var(--green)';
          }
          if (data.alpha_role) {
            const studioLink = document.getElementById('navStudioLi');
            if (studioLink) studioLink.style.display = '';
            if (['tom', 'gary'].includes(data.alpha_role)) {
              const datavizStudioLi = document.getElementById('navDatavizStudioLi');
              if (datavizStudioLi) datavizStudioLi.style.display = '';
            }
          }
        }
      }
    } catch (e) { /* not logged in, keep defaults */ }
  })();

  // ── Theme toggle ────────────────────────────────────────────────────────
  function updateToggleIcon(theme) {
    const btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = theme === 'light' ? '🌙' : '☀️';
  }
  window.toggleTheme = function () {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'light' ? 'dark' : 'light';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('gca-theme', next);
    updateToggleIcon(next);
    document.dispatchEvent(new CustomEvent('gca-theme-change', { detail: { theme: next } }));
  };
  const _initialTheme = document.documentElement.getAttribute('data-theme') || 'light';
  updateToggleIcon(_initialTheme);

  // ── Mobile nav ──────────────────────────────────────────────────────────
  window.toggleMobileNav = function () {
    const links = document.querySelector('.nav-links');
    const btn = document.getElementById('navHamburger');
    const isOpen = links.classList.toggle('open');
    btn.classList.toggle('active', isOpen);
    btn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
  };
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.nav-chevron').forEach(function (chevron) {
      chevron.addEventListener('click', function (e) {
        if (window.innerWidth <= 900) {
          e.preventDefault();
          e.stopPropagation();
          chevron.closest('.has-dropdown').classList.toggle('open');
        }
      });
    });
  });
  window.addEventListener('resize', function () {
    if (window.innerWidth > 900) {
      const links = document.querySelector('.nav-links');
      const hamburger = document.getElementById('navHamburger');
      if (links) links.classList.remove('open');
      if (hamburger) hamburger.classList.remove('active');
      document.querySelectorAll('.has-dropdown.open').forEach(function (li) { li.classList.remove('open'); });
    }
  });

  // ── Nav background on scroll ───────────────────────────────────────────
  window.addEventListener('scroll', function () {
    const navEl = document.querySelector('nav');
    if (!navEl) return;
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    if (window.scrollY > 40) {
      navEl.style.background = isDark ? 'rgba(6,8,18,0.96)' : 'rgba(245,247,255,0.96)';
    } else {
      navEl.style.background = isDark ? 'rgba(6,8,18,0.82)' : 'rgba(245,247,255,0.88)';
    }
  });

  // ── Site search ─────────────────────────────────────────────────────────
  document.addEventListener('DOMContentLoaded', function () {
    const wrap = document.getElementById('navSearch');
    const toggleBtn = document.getElementById('navSearchToggle');
    const box = document.getElementById('navSearchBox');
    const input = document.getElementById('navSearchInput');
    const results = document.getElementById('navSearchResults');
    if (!wrap) return;

    let activeIndex = -1;
    let currentItems = [];
    let debounceTimer = null;
    let requestSeq = 0;

    function openBox() {
      wrap.classList.add('open');
      input.focus();
    }
    function closeBox() {
      wrap.classList.remove('open');
      activeIndex = -1;
    }
    toggleBtn.addEventListener('click', function () {
      if (wrap.classList.contains('open')) closeBox(); else openBox();
    });
    document.addEventListener('click', function (e) {
      if (!wrap.contains(e.target)) closeBox();
    });
    document.addEventListener('keydown', function (e) {
      if (e.key === '/' && document.activeElement !== input && !/input|textarea/i.test((document.activeElement || {}).tagName || '')) {
        e.preventDefault();
        openBox();
      } else if (e.key === 'Escape' && wrap.classList.contains('open')) {
        closeBox();
      }
    });

    function renderEmpty(msg) {
      results.innerHTML = '';
      const div = document.createElement('div');
      div.className = 'nav-search-empty';
      div.textContent = msg;
      results.appendChild(div);
    }

    function renderResults(groups) {
      results.innerHTML = '';
      currentItems = [];
      activeIndex = -1;
      const hasAny = groups.some(function (g) { return g.items.length; });
      if (!hasAny) { renderEmpty('No matches. Try a different search.'); return; }
      groups.forEach(function (group) {
        if (!group.items.length) return;
        const label = document.createElement('div');
        label.className = 'nav-search-group-label';
        label.textContent = group.label;
        results.appendChild(label);
        group.items.forEach(function (item) {
          const a = document.createElement('a');
          a.className = 'nav-search-result';
          a.href = item.url;
          const title = document.createElement('div');
          title.className = 'nav-search-result-title';
          title.textContent = item.title;
          a.appendChild(title);
          if (item.sub) {
            const sub = document.createElement('div');
            sub.className = 'nav-search-result-sub';
            sub.textContent = item.sub;
            a.appendChild(sub);
          }
          results.appendChild(a);
          currentItems.push(a);
        });
      });
    }

    function highlight(idx) {
      currentItems.forEach(function (a, i) { a.classList.toggle('active', i === idx); });
      if (currentItems[idx]) currentItems[idx].scrollIntoView({ block: 'nearest' });
    }

    input.addEventListener('keydown', function (e) {
      if (e.key === 'ArrowDown') {
        e.preventDefault();
        if (currentItems.length) { activeIndex = Math.min(activeIndex + 1, currentItems.length - 1); highlight(activeIndex); }
      } else if (e.key === 'ArrowUp') {
        e.preventDefault();
        if (currentItems.length) { activeIndex = Math.max(activeIndex - 1, 0); highlight(activeIndex); }
      } else if (e.key === 'Enter') {
        if (activeIndex >= 0 && currentItems[activeIndex]) {
          e.preventDefault();
          window.location.href = currentItems[activeIndex].getAttribute('href');
        }
      }
    });

    input.addEventListener('input', function () {
      const q = input.value.trim();
      clearTimeout(debounceTimer);
      if (!q) { renderEmpty('Start typing to search pages, lessons and Alpha posts.'); return; }
      if (q.length < 2) { renderEmpty('Keep typing…'); return; }
      debounceTimer = setTimeout(function () {
        const seq = ++requestSeq;
        fetch('/api/search?q=' + encodeURIComponent(q))
          .then(function (r) { return r.json(); })
          .then(function (data) {
            if (seq !== requestSeq) return; // a newer keystroke's request already landed
            renderResults(data.groups || []);
          })
          .catch(function () {
            if (seq !== requestSeq) return;
            renderEmpty('Search is unavailable right now.');
          });
      }, 220);
    });
  });
})();
