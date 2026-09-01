/*
 * Shared realistic candlestick chart renderer for the Intermediate Technical
 * Analysis lessons (chart patterns, RSI, MACD, Bollinger Bands, confluence).
 * Renders TradingView-style dark candlestick charts (real green/red OHLC
 * candles, price gridlines, optional RSI/MACD sub-panels) into an inline SVG,
 * with indicator values computed via the actual formulas (SMA/EMA/stddev/
 * RSI/MACD) from a synthetic-but-deterministic OHLC series, not hand-drawn
 * lines. No external charting library — plain SVG, so it works with the
 * site's existing no-build-step setup.
 */
(function (global) {
  'use strict';

  var COLORS = {
    bg: '#131722',
    grid: '#2a2e39',
    gridText: '#787b86',
    up: '#26a69a',
    down: '#ef5350',
    divider: '#363a45',
  };

  // ---- seeded RNG (mulberry32) so charts are deterministic per page load ----
  function mulberry32(seed) {
    return function () {
      seed |= 0;
      seed = (seed + 0x6d2b79f5) | 0;
      var t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ---- OHLC generator from drift/volatility segments ----
  // segments: [{n, drift, vol}] — drift/vol are per-candle fractions of price.
  function buildCandles(seed, startPrice, segments) {
    var rng = mulberry32(seed);
    var candles = [];
    var price = startPrice;
    segments.forEach(function (seg) {
      for (var i = 0; i < seg.n; i++) {
        var open = price;
        var noise = (rng() - 0.5) * 2 * seg.vol;
        var close = open * (1 + seg.drift + noise);
        var wickUp = Math.abs(open - close) * (0.3 + rng() * 0.9) + open * seg.vol * 0.4 * rng();
        var wickDown = Math.abs(open - close) * (0.3 + rng() * 0.9) + open * seg.vol * 0.4 * rng();
        var high = Math.max(open, close) + wickUp;
        var low = Math.min(open, close) - wickDown;
        candles.push({ o: open, h: high, l: low, c: close });
        price = close;
      }
    });
    return candles;
  }

  // ---- indicator math (real formulas) ----
  function sma(values, period) {
    var out = new Array(values.length).fill(null);
    for (var i = period - 1; i < values.length; i++) {
      var sum = 0;
      for (var j = i - period + 1; j <= i; j++) sum += values[j];
      out[i] = sum / period;
    }
    return out;
  }

  function stddevSeries(values, period) {
    var out = new Array(values.length).fill(null);
    for (var i = period - 1; i < values.length; i++) {
      var slice = values.slice(i - period + 1, i + 1);
      var mean = slice.reduce(function (a, b) { return a + b; }, 0) / period;
      var variance = slice.reduce(function (a, b) { return a + (b - mean) * (b - mean); }, 0) / period;
      out[i] = Math.sqrt(variance);
    }
    return out;
  }

  function emaSeries(values, period) {
    var out = new Array(values.length).fill(null);
    var k = 2 / (period + 1);
    var seeded = false;
    var prev = null;
    for (var i = 0; i < values.length; i++) {
      if (values[i] == null) continue;
      if (!seeded) {
        // seed with SMA of first `period` valid points
        var startIdx = i;
        if (startIdx + period > values.length) { continue; }
        var sum = 0;
        for (var j = startIdx; j < startIdx + period; j++) sum += values[j];
        prev = sum / period;
        out[startIdx + period - 1] = prev;
        i = startIdx + period - 1;
        seeded = true;
        continue;
      }
      prev = values[i] * k + prev * (1 - k);
      out[i] = prev;
    }
    return out;
  }

  function rsiSeries(closes, period) {
    period = period || 14;
    var out = new Array(closes.length).fill(null);
    var gains = 0, losses = 0;
    for (var i = 1; i <= period; i++) {
      var diff = closes[i] - closes[i - 1];
      if (diff >= 0) gains += diff; else losses -= diff;
    }
    var avgGain = gains / period, avgLoss = losses / period;
    out[period] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    for (i = period + 1; i < closes.length; i++) {
      diff = closes[i] - closes[i - 1];
      var gain = diff > 0 ? diff : 0;
      var loss = diff < 0 ? -diff : 0;
      avgGain = (avgGain * (period - 1) + gain) / period;
      avgLoss = (avgLoss * (period - 1) + loss) / period;
      out[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
    }
    return out;
  }

  function macdSeries(closes, fast, slow, signalP) {
    fast = fast || 12; slow = slow || 26; signalP = signalP || 9;
    var emaFast = emaSeries(closes, fast);
    var emaSlow = emaSeries(closes, slow);
    var macdLine = closes.map(function (_, i) {
      return emaFast[i] != null && emaSlow[i] != null ? emaFast[i] - emaSlow[i] : null;
    });
    var signalLine = emaSeries(macdLine, signalP);
    var hist = macdLine.map(function (v, i) {
      return v != null && signalLine[i] != null ? v - signalLine[i] : null;
    });
    return { macdLine: macdLine, signalLine: signalLine, hist: hist };
  }

  // ---- rendering ----
  function svgEl(name, attrs) {
    var el = document.createElementNS('http://www.w3.org/2000/svg', name);
    for (var k in attrs) el.setAttribute(k, attrs[k]);
    return el;
  }

  function niceRange(min, max, padFrac) {
    var pad = (max - min) * (padFrac == null ? 0.1 : padFrac) || Math.abs(max) * 0.05 || 1;
    return { min: min - pad, max: max + pad };
  }

  function render(svgNode, config) {
    var width = config.width || 640;
    var hasMarkerLabels = (config.verticalMarkers || []).some(function (m) { return m.label; });
    var markerLabelSpace = hasMarkerLabels ? 18 : 0;
    var marginLeft = 8, marginRight = 54, marginTop = 10 + markerLabelSpace;
    var panelGap = 10;
    var xCount = config.xCount;
    var plotWidth = width - marginLeft - marginRight;
    var slot = plotWidth / xCount;

    var totalHeight = marginTop;
    config.panels.forEach(function (p, i) { totalHeight += p.height + (i > 0 ? panelGap : 0); });
    totalHeight += 8;

    while (svgNode.firstChild) svgNode.removeChild(svgNode.firstChild);
    svgNode.setAttribute('viewBox', '0 0 ' + width + ' ' + totalHeight);

    svgNode.appendChild(svgEl('rect', { x: 0, y: 0, width: width, height: totalHeight, fill: COLORS.bg, rx: 8 }));

    function xScale(idx) { return marginLeft + (idx + 0.5) * slot; }

    var panelTops = [];
    var y = marginTop;
    config.panels.forEach(function (p, i) {
      if (i > 0) {
        svgNode.appendChild(svgEl('line', { x1: marginLeft, x2: width - marginRight + 40, y1: y - panelGap / 2, y2: y - panelGap / 2, stroke: COLORS.divider, 'stroke-width': 1 }));
      }
      panelTops.push(y);
      y += p.height + panelGap;
    });

    config.panels.forEach(function (panel, pi) {
      var top = panelTops[pi];
      var bottom = top + panel.height;
      drawPanel(svgNode, panel, top, bottom, xScale, xCount);
    });

    // vertical markers spanning the whole chart (confluence alignment line etc)
    (config.verticalMarkers || []).forEach(function (m) {
      var x = xScale(m.x);
      var lineTop = m.label ? marginTop - markerLabelSpace + 4 : marginTop - 2;
      svgNode.appendChild(svgEl('line', { x1: x, x2: x, y1: lineTop, y2: totalHeight - 6, stroke: m.color, 'stroke-width': 1.4, 'stroke-dasharray': '4 3', opacity: 0.85 }));
      if (m.label) {
        var t = svgEl('text', { x: x, y: 14, fill: m.color, 'font-size': 9, 'font-family': 'Helvetica', 'text-anchor': 'middle', 'font-weight': 'bold' });
        t.textContent = m.label;
        svgNode.appendChild(t);
      }
    });
  }

  function drawGridAndLabels(svgNode, top, bottom, left, right, domain, decimals, xCount, xScale) {
    var levels = 4;
    for (var i = 0; i <= levels; i++) {
      var v = domain.min + (domain.max - domain.min) * (i / levels);
      var yy = bottom - ((v - domain.min) / (domain.max - domain.min)) * (bottom - top);
      svgNode.appendChild(svgEl('line', { x1: left, x2: right, y1: yy, y2: yy, stroke: COLORS.grid, 'stroke-width': 0.6 }));
      var t = svgEl('text', { x: right + 6, y: yy + 3, fill: COLORS.gridText, 'font-size': 8.5, 'font-family': 'Helvetica' });
      t.textContent = v.toFixed(decimals);
      svgNode.appendChild(t);
    }
    var vStep = Math.max(1, Math.round(xCount / 8));
    for (var idx = 0; idx < xCount; idx += vStep) {
      var x = xScale(idx);
      svgNode.appendChild(svgEl('line', { x1: x, x2: x, y1: top, y2: bottom, stroke: COLORS.grid, 'stroke-width': 0.4 }));
    }
  }

  function drawPanel(svgNode, panel, top, bottom, xScale, xCount) {
    var left = 8, right = xScale(xCount - 1) + 8;

    if (panel.type === 'price') {
      var candles = panel.candles;
      var lo = Math.min.apply(null, candles.map(function (c) { return c.l; }));
      var hi = Math.max.apply(null, candles.map(function (c) { return c.h; }));
      (panel.overlays || []).forEach(function (ov) {
        ov.data.forEach(function (pt) { if (pt && pt[1] != null) { lo = Math.min(lo, pt[1]); hi = Math.max(hi, pt[1]); } });
      });
      (panel.levelLines || []).forEach(function (l) { lo = Math.min(lo, l.price); hi = Math.max(hi, l.price); });
      var domain = niceRange(lo, hi, 0.08);
      var yFor = function (v) { return bottom - ((v - domain.min) / (domain.max - domain.min)) * (bottom - top); };

      drawGridAndLabels(svgNode, top, bottom, left, right, domain, 2, xCount, xScale);

      var bodyW = Math.max(1.5, (right - left) / xCount * 0.6);
      candles.forEach(function (c, i) {
        var x = xScale(i);
        var color = c.c >= c.o ? COLORS.up : COLORS.down;
        svgNode.appendChild(svgEl('line', { x1: x, x2: x, y1: yFor(c.h), y2: yFor(c.l), stroke: color, 'stroke-width': 1 }));
        var yOpen = yFor(c.o), yClose = yFor(c.c);
        var bodyTop = Math.min(yOpen, yClose);
        var bodyH = Math.max(1.1, Math.abs(yOpen - yClose));
        svgNode.appendChild(svgEl('rect', { x: x - bodyW / 2, y: bodyTop, width: bodyW, height: bodyH, fill: color }));
      });

      (panel.levelLines || []).forEach(function (l) {
        var yy = yFor(l.price);
        svgNode.appendChild(svgEl('line', { x1: left, x2: right, y1: yy, y2: yy, stroke: l.color, 'stroke-width': 1.3, 'stroke-dasharray': l.dash ? '5 3' : '' }));
        if (l.label) {
          var t = svgEl('text', { x: left + 4, y: yy - 4, fill: l.color, 'font-size': 8.5, 'font-family': 'Helvetica', 'font-weight': 'bold' });
          t.textContent = l.label;
          svgNode.appendChild(t);
        }
      });

      (panel.overlays || []).forEach(function (ov) {
        var pts = ov.data.filter(function (p) { return p && p[1] != null; }).map(function (p) { return xScale(p[0]) + ',' + yFor(p[1]); }).join(' ');
        svgNode.appendChild(svgEl('polyline', { points: pts, fill: 'none', stroke: ov.color, 'stroke-width': ov.width || 1.8, 'stroke-dasharray': ov.dash ? '5 3' : '' }));
      });

      (panel.annotations || []).forEach(function (a) { drawAnnotation(svgNode, a, xScale(a.x), yFor(a.y)); });
      if (panel.title) drawTitle(svgNode, panel.title, left, top);
    }

    if (panel.type === 'rsi') {
      var domainR = { min: 0, max: 100 };
      var yForR = function (v) { return bottom - (v / 100) * (bottom - top); };
      drawGridAndLabels(svgNode, top, bottom, left, right, domainR, 0, xCount, xScale);
      [30, 70].forEach(function (lvl) {
        var yy = yForR(lvl);
        var col = lvl === 70 ? COLORS.down : COLORS.up;
        svgNode.appendChild(svgEl('line', { x1: left, x2: right, y1: yy, y2: yy, stroke: col, 'stroke-width': 1, 'stroke-dasharray': '4 3', opacity: 0.8 }));
      });
      var pts = panel.values.map(function (v, i) { return v == null ? null : [i, v]; }).filter(Boolean)
        .map(function (p) { return xScale(p[0]) + ',' + yForR(p[1]); }).join(' ');
      svgNode.appendChild(svgEl('polyline', { points: pts, fill: 'none', stroke: '#b47cff', 'stroke-width': 1.8 }));
      (panel.annotations || []).forEach(function (a) { drawAnnotation(svgNode, a, xScale(a.x), yForR(a.y)); });
      drawTitle(svgNode, panel.title || 'RSI (14)', left, top);
    }

    if (panel.type === 'macd') {
      var all = panel.macdLine.concat(panel.signalLine, panel.hist).filter(function (v) { return v != null; });
      var lo2 = Math.min.apply(null, all), hi2 = Math.max.apply(null, all);
      var extent = Math.max(Math.abs(lo2), Math.abs(hi2)) * 1.15 || 1;
      var domainM = { min: -extent, max: extent };
      var yForM = function (v) { return bottom - ((v - domainM.min) / (domainM.max - domainM.min)) * (bottom - top); };
      drawGridAndLabels(svgNode, top, bottom, left, right, domainM, 2, xCount, xScale);
      var zeroY = yForM(0);
      svgNode.appendChild(svgEl('line', { x1: left, x2: right, y1: zeroY, y2: zeroY, stroke: COLORS.gridText, 'stroke-width': 0.8 }));

      var barW = Math.max(1, (right - left) / xCount * 0.55);
      panel.hist.forEach(function (v, i) {
        if (v == null) return;
        var x = xScale(i);
        var yv = yForM(v);
        var color = v >= 0 ? COLORS.up : COLORS.down;
        var rectTop = v >= 0 ? yv : zeroY;
        var h = Math.abs(zeroY - yv);
        svgNode.appendChild(svgEl('rect', { x: x - barW / 2, y: rectTop, width: barW, height: Math.max(0.8, h), fill: color, opacity: 0.65 }));
      });
      var macdPts = panel.macdLine.map(function (v, i) { return v == null ? null : [i, v]; }).filter(Boolean)
        .map(function (p) { return xScale(p[0]) + ',' + yForM(p[1]); }).join(' ');
      svgNode.appendChild(svgEl('polyline', { points: macdPts, fill: 'none', stroke: '#2962ff', 'stroke-width': 1.8 }));
      var sigPts = panel.signalLine.map(function (v, i) { return v == null ? null : [i, v]; }).filter(Boolean)
        .map(function (p) { return xScale(p[0]) + ',' + yForM(p[1]); }).join(' ');
      svgNode.appendChild(svgEl('polyline', { points: sigPts, fill: 'none', stroke: '#ff9800', 'stroke-width': 1.6, 'stroke-dasharray': '4 3' }));
      (panel.annotations || []).forEach(function (a) { drawAnnotation(svgNode, a, xScale(a.x), yForM(a.y)); });
      drawTitle(svgNode, panel.title || 'MACD (12, 26, 9)', left, top);
    }
  }

  function drawTitle(svgNode, text, left, top) {
    var t = svgEl('text', { x: left + 4, y: top + 11, fill: COLORS.gridText, 'font-size': 9, 'font-family': 'Helvetica', 'font-weight': 'bold' });
    t.textContent = text;
    svgNode.appendChild(t);
  }

  function drawAnnotation(svgNode, a, x, y) {
    if (a.dot !== false) {
      svgNode.appendChild(svgEl('circle', { cx: x, cy: y, r: a.r || 4, fill: a.color }));
    }
    if (a.text) {
      var t = svgEl('text', {
        x: x + (a.dx || 0), y: y + (a.dy || -10),
        fill: a.color, 'font-size': a.size || 9, 'font-family': 'Helvetica',
        'font-weight': a.bold === false ? 'normal' : 'bold',
        'text-anchor': a.anchor || 'middle',
      });
      t.textContent = a.text;
      svgNode.appendChild(t);
    }
  }

  global.GCGChart = {
    mulberry32: mulberry32,
    buildCandles: buildCandles,
    sma: sma,
    stddevSeries: stddevSeries,
    emaSeries: emaSeries,
    rsiSeries: rsiSeries,
    macdSeries: macdSeries,
    render: render,
    colors: COLORS,
  };
})(window);
