(function () {
  var KEY = 'apex-theme';

  function preferred() {
    return window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark';
  }

  function apply(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    var btn = document.getElementById('themeToggle');
    if (btn) btn.textContent = theme === 'dark' ? '☀' : '☾';
    document.dispatchEvent(new CustomEvent('apex-theme-change', { detail: { theme: theme } }));
  }

  function toggle() {
    var current = document.documentElement.getAttribute('data-theme') || 'dark';
    var next = current === 'dark' ? 'light' : 'dark';
    localStorage.setItem(KEY, next);
    apply(next);
  }

  apply(localStorage.getItem(KEY) || preferred());

  window.toggleApexTheme = toggle;

  document.addEventListener('DOMContentLoaded', function () {
    apply(localStorage.getItem(KEY) || preferred());
  });
})();
