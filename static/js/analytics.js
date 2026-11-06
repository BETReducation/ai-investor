// Site analytics. Cloudflare Web Analytics is cookieless, so it loads straight away.
// GA4 sets cookies, so it loads only after the visitor accepts the banner.
// Fill in the two IDs below; an empty ID disables that tool.
(function () {
  var GA_ID = '';       // GA4 measurement ID, e.g. G-XXXXXXXXXX
  var CF_TOKEN = '';    // Cloudflare Web Analytics beacon token
  var KEY = 'gcg-analytics-consent';

  // Skip local dev so test traffic doesn't pollute the numbers.
  if (/^(localhost|127\.0\.0\.1)$/.test(location.hostname)) return;

  function get() { try { return localStorage.getItem(KEY); } catch (e) { return null; } }
  function set(v) { try { localStorage.setItem(KEY, v); } catch (e) {} }

  function addScript(src, attrs) {
    var s = document.createElement('script');
    s.src = src; s.defer = true;
    for (var k in (attrs || {})) s.setAttribute(k, attrs[k]);
    document.head.appendChild(s);
  }

  function loadGA() {
    if (!GA_ID || window.__gaLoaded) return;
    window.__gaLoaded = true;
    window.dataLayer = window.dataLayer || [];
    window.gtag = function () { window.dataLayer.push(arguments); };
    gtag('js', new Date());
    gtag('config', GA_ID, { anonymize_ip: true });
    addScript('https://www.googletagmanager.com/gtag/js?id=' + GA_ID);
  }

  if (CF_TOKEN) {
    addScript('https://static.cloudflareinsights.com/beacon.min.js',
      { 'data-cf-beacon': JSON.stringify({ token: CF_TOKEN }) });
  }

  if (!GA_ID) return;
  var choice = get();
  if (choice === 'granted') return loadGA();
  if (choice === 'denied') return;

  function showBanner() {
    var bar = document.createElement('div');
    bar.setAttribute('role', 'dialog');
    bar.setAttribute('aria-label', 'Cookie preferences');
    bar.style.cssText = 'position:fixed;left:16px;right:16px;bottom:16px;max-width:560px;margin:0 auto;' +
      'z-index:99999;background:var(--bg2,#090c18);color:var(--text,#e8eaf6);' +
      'border:1px solid var(--border2,rgba(255,255,255,.12));border-radius:12px;padding:16px 18px;' +
      'box-shadow:0 8px 32px rgba(0,0,0,.35);font:14px/1.5 "Space Grotesk",system-ui,sans-serif;';
    bar.innerHTML =
      '<div style="margin-bottom:12px">We use Google Analytics cookies to see how the site is used. ' +
      'Nothing is shared for advertising. <a href="/privacy" style="color:var(--green,#00d4aa)">Details</a></div>' +
      '<div style="display:flex;gap:8px;justify-content:flex-end">' +
      '<button data-v="denied" style="padding:8px 16px;border-radius:8px;cursor:pointer;font:inherit;' +
      'background:transparent;color:inherit;border:1px solid var(--border2,rgba(255,255,255,.2))">Decline</button>' +
      '<button data-v="granted" style="padding:8px 16px;border-radius:8px;cursor:pointer;font:inherit;' +
      'font-weight:600;background:var(--green,#00d4aa);color:#04120e;border:0">Accept</button></div>';
    bar.addEventListener('click', function (e) {
      var v = e.target && e.target.getAttribute('data-v');
      if (!v) return;
      set(v);
      bar.remove();
      if (v === 'granted') loadGA();
    });
    document.body.appendChild(bar);
  }

  if (document.body) showBanner();
  else document.addEventListener('DOMContentLoaded', showBanner);
})();
