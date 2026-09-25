"""Rule-based pattern detection on OHLCV candles — no AI, no third-party deps.

Input is a list of candles [time, open, high, low, close, volume], oldest first.
Everything here is deliberately conservative and explainable: each pattern is an
explicit rule, and descriptions live in pattern_knowledge.py. Geometry-heavy chart
patterns (double tops, head and shoulders, triangles...) are not covered yet.
"""
from .pattern_knowledge import CANDLESTICKS, CHART_PATTERNS, EVENTS, LEVELS

_T, _O, _H, _L, _C = 0, 1, 2, 3, 4

_BULLISH = {"hammer", "inverted_hammer", "bullish_engulfing", "morning_star",
            "three_white_soldiers", "piercing_line", "bullish_marubozu"}
_BEARISH = {"hanging_man", "shooting_star", "bearish_engulfing", "evening_star",
            "three_black_crows", "dark_cloud_cover", "bearish_marubozu"}


_EVENT_BIAS = {
    "breakout_up": "bullish", "retest_held_up": "bullish", "failed_breakout_down": "bullish",
    "breakout_down": "bearish", "retest_held_down": "bearish", "failed_breakout_up": "bearish",
}


def _bias(key: str) -> str:
    return "bullish" if key in _BULLISH else "bearish" if key in _BEARISH else "neutral"


def atr(candles: list, n: int = 14) -> float:
    trs = []
    for i in range(max(1, len(candles) - n), len(candles)):
        h, l, pc = candles[i][_H], candles[i][_L], candles[i - 1][_C]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs) / len(trs) if trs else 0.0


def swing_points(values: list, k: int = 2, high: bool = True) -> list:
    """Indices of local extremes that beat the k bars either side."""
    out = []
    for i in range(k, len(values) - k):
        window = values[i - k:i + k + 1]
        if values[i] == (max(window) if high else min(window)) and window.count(values[i]) == 1:
            out.append(i)
    return out


def _trend(candles: list, end: int, a: float, look: int = 5) -> str:
    """Direction of the move into bar `end`, measured against ATR so it scales by asset."""
    if end - look < 0 or a <= 0:
        return "flat"
    move = candles[end][_C] - candles[end - look][_C]
    return "up" if move > a else "down" if move < -a else "flat"


def _parts(c: list) -> tuple:
    o, h, l, cl = c[_O], c[_H], c[_L], c[_C]
    return abs(cl - o), h - l, h - max(o, cl), min(o, cl) - l  # body, range, upper wick, lower wick


def _patterns_at(candles: list, i: int, a: float, avg_body: float) -> list:
    found = []
    c = candles[i]
    o, cl = c[_O], c[_C]
    body, rng, upper, lower = _parts(c)
    tol = 0.1 * a
    green, red = cl > o, cl < o

    if rng > 0:
        trend = _trend(candles, i - 1, a) if i >= 1 else "flat"

        if body >= 0.9 * rng and body >= 1.3 * avg_body:
            found.append("bullish_marubozu" if green else "bearish_marubozu")
        elif rng >= 0.7 * a:
            hammer_shape = lower >= 0.6 * rng and lower >= 2 * body and upper <= 0.15 * rng
            inverted_shape = upper >= 0.6 * rng and upper >= 2 * body and lower <= 0.15 * rng
            if hammer_shape and trend == "down":
                found.append("hammer")
            elif hammer_shape and trend == "up":
                found.append("hanging_man")
            elif inverted_shape and trend == "down":
                found.append("inverted_hammer")
            elif inverted_shape and trend == "up":
                found.append("shooting_star")
            elif body <= 0.1 * rng:
                found.append("doji")

    if i >= 1:
        p = candles[i - 1]
        pbody, prng, _, _ = _parts(p)
        ptrend = _trend(candles, i - 1, a)
        p_lo, p_hi = min(p[_O], p[_C]), max(p[_O], p[_C])
        c_lo, c_hi = min(o, cl), max(o, cl)
        if pbody > 0 and body > pbody and c_lo <= p_lo and c_hi >= p_hi:
            if green and p[_C] < p[_O] and ptrend == "down":
                found.append("bullish_engulfing")
            elif red and p[_C] > p[_O] and ptrend == "up":
                found.append("bearish_engulfing")
        p_mid = (p[_O] + p[_C]) / 2
        if pbody >= 0.8 * avg_body:
            if p[_C] < p[_O] and green and o <= p[_C] + tol and p_mid < cl < p[_O] and ptrend == "down":
                found.append("piercing_line")
            if p[_C] > p[_O] and red and o >= p[_C] - tol and p[_O] < cl < p_mid and ptrend == "up":
                found.append("dark_cloud_cover")
        if c[_H] < p[_H] and c[_L] > p[_L]:
            found.append("inside_bar")

    if i >= 2:
        b1, b2 = candles[i - 2], candles[i - 1]
        body1, _, _, _ = _parts(b1)
        body2, _, _, _ = _parts(b2)
        t1 = _trend(candles, i - 2, a)
        mid1 = (b1[_O] + b1[_C]) / 2
        if body1 >= avg_body and body2 <= 0.4 * body1 and body >= 0.8 * avg_body:
            if b1[_C] < b1[_O] and green and cl > mid1 and t1 == "down":
                found.append("morning_star")
            if b1[_C] > b1[_O] and red and cl < mid1 and t1 == "up":
                found.append("evening_star")

        def _run(color_up: bool) -> bool:
            seq = [candles[i - 2], candles[i - 1], c]
            for j, s in enumerate(seq):
                sb, _, su, sl_ = _parts(s)
                if (s[_C] > s[_O]) != color_up or sb < 0.6 * avg_body:
                    return False
                if (su if color_up else sl_) > 0.4 * sb:
                    return False
                if j:
                    prev = seq[j - 1]
                    lo, hi = min(prev[_O], prev[_C]) - tol, max(prev[_O], prev[_C]) + tol
                    if not lo <= s[_O] <= hi:
                        return False
                    if (s[_C] <= prev[_C]) if color_up else (s[_C] >= prev[_C]):
                        return False
            return True

        if _run(True):
            found.append("three_white_soldiers")
        elif _run(False):
            found.append("three_black_crows")
    return found


def detect_candlesticks(candles: list, lookback: int = 5, forming: bool = False) -> list:
    n = len(candles)
    a = atr(candles)
    recent = candles[-14:]
    avg_body = sum(abs(x[_C] - x[_O]) for x in recent) / len(recent) if recent else 0.0
    out = []
    for i in range(max(2, n - lookback), n):
        for key in _patterns_at(candles, i, a, avg_body):
            kb = CANDLESTICKS[key]
            out.append({
                "key": key, "label": kb["label"], "bias": _bias(key),
                "time": candles[i][_T], "bars_ago": n - 1 - i,
                "provisional": forming and i == n - 1,
                "what": kb["what"], "suggests": kb["suggests"], "invalidation": kb["invalidation"],
            })
    out.sort(key=lambda d: d["bars_ago"])
    return out


def support_resistance(candles: list, max_each: int = 3) -> dict:
    """Cluster swing highs/lows into levels touched at least twice."""
    a = atr(candles)
    close = candles[-1][_C]
    highs = [c[_H] for c in candles]
    lows = [c[_L] for c in candles]
    pts = [(highs[i], i) for i in swing_points(highs, 2, True)] + \
          [(lows[i], i) for i in swing_points(lows, 2, False)]
    pts.sort()
    tol = max(0.5 * a, 0.002 * close)
    groups = []
    for price, idx in pts:
        if groups and price - groups[-1][-1][0] <= tol:
            groups[-1].append((price, idx))
        else:
            groups.append([(price, idx)])
    levels = []
    for g in groups:
        if len(g) < 2:
            continue
        price = sum(p for p, _ in g) / len(g)
        last_idx = max(i for _, i in g)
        levels.append({
            "price": price, "touches": len(g), "last_touch": candles[last_idx][_T],
            "distance_pct": (price - close) / close * 100,
        })
    support = sorted((l for l in levels if l["price"] < close), key=lambda l: -l["price"])[:max_each]
    resistance = sorted((l for l in levels if l["price"] >= close), key=lambda l: l["price"])[:max_each]
    return {"support": support, "resistance": resistance, "all": levels, "atr": a}


def detect_events(candles: list, levels: list, a: float, forming: bool = False, window: int = 10) -> list:
    """Breakouts, held retests and failed breakouts of known levels in the last `window` bars."""
    n = len(candles)
    closes = [c[_C] for c in candles]
    lows = [c[_L] for c in candles]
    highs = [c[_H] for c in candles]
    band = 0.25 * a
    events = []
    for lv in levels:
        p = lv["price"]
        for direction in ("up", "down"):
            up = direction == "up"
            j = None
            for x in range(max(3, n - window), n):
                beyond = closes[x] > p + band if up else closes[x] < p - band
                before = any((closes[m] <= p) if up else (closes[m] >= p) for m in range(x - 3, x))
                if beyond and before:
                    j = x
                    break
            if j is None:
                continue
            after = range(j + 1, n)

            def _failed(k):
                return closes[k] < p - band if up else closes[k] > p + band

            def _retested(k):
                if up:
                    return lows[k] <= p + band and closes[k] >= p - band
                return highs[k] >= p - band and closes[k] <= p + band

            failed = next((k for k in after if _failed(k)), None)
            retest = next((k for k in after if _retested(k)), None)
            holding = closes[-1] > p + band if up else closes[-1] < p - band
            if failed is not None:
                key, at = ("failed_breakout_up" if up else "failed_breakout_down"), failed
            elif retest is not None and holding:
                key, at = ("retest_held_up" if up else "retest_held_down"), retest
            else:
                key, at = ("breakout_up" if up else "breakout_down"), j
            kb = EVENTS[key]
            events.append({
                "key": key, "label": kb["label"], "bias": _EVENT_BIAS[key], "level": p, "touches": lv["touches"],
                "time": candles[at][_T], "breakout_time": candles[j][_T], "bars_ago": n - 1 - at,
                "provisional": forming and at == n - 1,
                "what": kb["what"], "suggests": kb["suggests"], "invalidation": kb["invalidation"],
            })
    events.sort(key=lambda e: e["bars_ago"])
    # One event per level and direction is already guaranteed; cap the list for readability.
    return events[:4]


_WIDTH_NOTES = {
    "Narrow": "Compact in time and price, so its levels are fairly precise, though small moves can trigger or break it.",
    "Standard": "A typical size for this kind of pattern.",
    "Wide": "Covers a lot of time and/or price, so it plays out slowly and its levels are better treated as rough zones than exact lines. Larger patterns are often read as more significant but less precise.",
}


def _human_duration(t1: str, t2: str) -> str:
    from datetime import datetime
    try:
        fmt = "%Y-%m-%d %H:%M"
        hours = (datetime.strptime(t2[:16], fmt) - datetime.strptime(t1[:16], fmt)).total_seconds() / 3600
    except ValueError:
        return ""
    if hours < 48:
        return f"about {max(1, round(hours))} hours"
    days = hours / 24
    if days < 21:
        return f"about {round(days)} days"
    if days < 90:
        return f"about {round(days / 7)} weeks"
    return f"about {round(days / 30)} months"


def _width(candles: list, start: int, end: int, height: float, ref_price: float) -> dict:
    """How wide or narrow a pattern is, by time covered and size of the price swing."""
    bars = max(1, end - start)
    pct = abs(height) / ref_price * 100 if ref_price else 0.0
    time_grade = 0 if bars < 15 else 1 if bars <= 35 else 2
    price_grade = 0 if pct < 5 else 1 if pct <= 15 else 2
    label = ("Narrow", "Standard", "Wide")[max(time_grade, price_grade)]
    span = _human_duration(candles[start][_T], candles[end][_T])
    return {
        "label": label, "bars": bars, "height_pct": round(pct, 1), "duration": span,
        "note": _WIDTH_NOTES[label],
    }


def detect_double_tops_bottoms(candles: list, a: float, forming: bool = False, max_age: int = 30) -> list:
    """Most recent valid double top and double bottom (at most one of each)."""
    n = len(candles)
    highs = [c[_H] for c in candles]
    lows = [c[_L] for c in candles]
    closes = [c[_C] for c in candles]
    band = 0.25 * a
    tol = 0.6 * a
    out = []
    for top in (True, False):
        vals = highs if top else lows
        swings = swing_points(vals, 2, top)
        best = None
        for x in range(len(swings)):
            for y in range(x + 1, len(swings)):
                i1, i2 = swings[x], swings[y]
                if not 5 <= i2 - i1 <= 60 or n - 1 - i2 > max_age:
                    continue
                p1, p2 = vals[i1], vals[i2]
                if abs(p1 - p2) > tol:
                    continue
                if top:
                    neck, extreme = min(lows[i1:i2 + 1]), max(p1, p2)
                    if max(highs[i1 + 1:i2]) > extreme + tol:
                        continue
                    depth = min(p1, p2) - neck
                    lead = p1 - min(lows[max(0, i1 - 15):i1])
                else:
                    neck, extreme = max(highs[i1:i2 + 1]), min(p1, p2)
                    if min(lows[i1 + 1:i2]) < extreme - tol:
                        continue
                    depth = neck - max(p1, p2)
                    lead = max(highs[max(0, i1 - 15):i1]) - p1
                if depth < 1.5 * a or lead < 2.5 * a:
                    continue

                def _beyond_peaks(k):      # price closed past both peaks: pattern is void
                    return closes[k] > extreme + band if top else closes[k] < extreme - band

                def _through_neckline(k):  # the confirming move
                    return closes[k] < neck - band if top else closes[k] > neck + band

                def _back_over_neckline(k):
                    return closes[k] > neck + band if top else closes[k] < neck - band

                after = range(i2 + 1, n)
                if any(_beyond_peaks(k) for k in after):
                    continue
                brk = next((k for k in after if _through_neckline(k)), None)
                if brk is not None and any(_back_over_neckline(k) for k in range(brk + 1, n)):
                    continue
                cand = (i2, -abs(p1 - p2))
                if best is None or cand > best[0]:
                    best = (cand, i1, i2, neck, brk, depth)
        if best:
            _, i1, i2, neck, brk, depth = best
            key = "double_top" if top else "double_bottom"
            kb = CHART_PATTERNS[key]
            confirmed = brk is not None
            out.append({
                "key": key, "label": kb["label"], "bias": "bearish" if top else "bullish",
                "status": "confirmed" if confirmed else "forming",
                "clarity": "Clear" if confirmed else "Tentative",
                "points": [[candles[i1][_T], vals[i1]], [candles[i2][_T], vals[i2]]],
                "neckline": neck,
                "width": _width(candles, i1, i2, depth, (vals[i1] + vals[i2]) / 2),
                "break_time": candles[brk][_T] if confirmed else None,
                "provisional": forming and (brk == n - 1 or i2 == n - 1),
                "what": kb["what"], "suggests": kb["suggests"], "invalidation": kb["invalidation"],
            })
    return out


def detect_range(candles: list, a: float, forming: bool = False) -> list:
    """Sideways range: two or more touches of both a ceiling and a floor with little net drift."""
    n = len(candles)
    for window in (60, 45, 30, 20):
        if n < window:
            continue
        w = candles[-window:]
        hi, lo = max(c[_H] for c in w), min(c[_L] for c in w)
        height = hi - lo
        if height < 2 * a or height > 10 * a:
            continue

        def _touches(hit) -> int:
            count, last = 0, -10
            for i, c in enumerate(w):
                if hit(c) and i - last >= 3:
                    count += 1
                if hit(c):
                    last = i
            return count

        top_touches = _touches(lambda c: c[_H] >= hi - 0.2 * height)
        bottom_touches = _touches(lambda c: c[_L] <= lo + 0.2 * height)
        drift = abs(w[-1][_C] - w[0][_C])
        if top_touches >= 2 and bottom_touches >= 2 and drift <= 0.4 * height:
            kb = CHART_PATTERNS["range"]
            return [{
                "key": "range", "label": kb["label"], "bias": "neutral",
                "status": "active",
                "clarity": "Clear" if min(top_touches, bottom_touches) >= 3 else "Tentative",
                "top": hi, "bottom": lo, "bars": window,
                "top_touches": top_touches, "bottom_touches": bottom_touches,
                "start_time": w[0][_T],
                "width": _width(candles, n - window, n - 1, height, w[-1][_C]),
                "position_pct": round((w[-1][_C] - lo) / height * 100, 1),
                "provisional": False,
                "what": kb["what"], "suggests": kb["suggests"], "invalidation": kb["invalidation"],
            }]
    return []


def detect_head_and_shoulders(candles: list, a: float, forming: bool = False, max_age: int = 30) -> list:
    """Most recent head-and-shoulders top and inverse (at most one of each)."""
    n = len(candles)
    highs = [c[_H] for c in candles]
    lows = [c[_L] for c in candles]
    closes = [c[_C] for c in candles]
    band = 0.25 * a
    out = []
    for top in (True, False):
        vals = highs if top else lows
        opp = lows if top else highs
        swings = swing_points(vals, 2, top)[-12:]
        best = None
        for x in range(len(swings)):
            for y in range(x + 1, len(swings)):
                for z in range(y + 1, len(swings)):
                    il, ih, ir = swings[x], swings[y], swings[z]
                    if n - 1 - ir > max_age or not (3 <= ih - il <= 40 and 3 <= ir - ih <= 40):
                        continue
                    ls, hd, rs = vals[il], vals[ih], vals[ir]
                    over = (hd - max(ls, rs)) if top else (min(ls, rs) - hd)  # head's margin over shoulders
                    if over < 1.5 * a or abs(ls - rs) > 1.0 * a:
                        continue
                    span = vals[il:ir + 1]
                    if (max(span) if top else min(span)) != hd:
                        continue
                    t1 = min(range(il, ih + 1), key=lambda i: opp[i]) if top else max(range(il, ih + 1), key=lambda i: opp[i])
                    t2 = min(range(ih, ir + 1), key=lambda i: opp[i]) if top else max(range(ih, ir + 1), key=lambda i: opp[i])
                    if t2 == t1:
                        continue
                    tv1, tv2 = opp[t1], opp[t2]
                    depth = (hd - max(tv1, tv2)) if top else (min(tv1, tv2) - hd)
                    lead = (ls - min(lows[max(0, il - 20):il])) if top else (max(highs[max(0, il - 20):il]) - ls)
                    if depth < 2 * a or lead < 2 * a:
                        continue
                    slope = (tv2 - tv1) / (t2 - t1)

                    def neck(k, tv1=tv1, t1=t1, slope=slope):
                        return tv1 + slope * (k - t1)

                    def _above_head(k, hd=hd):
                        return closes[k] > hd + band if top else closes[k] < hd - band

                    def _through(k, neck=neck):
                        return closes[k] < neck(k) - band if top else closes[k] > neck(k) + band

                    def _back(k, neck=neck):
                        return closes[k] > neck(k) + band if top else closes[k] < neck(k) - band

                    after = range(ir + 1, n)
                    if any(_above_head(k) for k in after):
                        continue
                    brk = next((k for k in after if _through(k)), None)
                    if brk is not None and any(_back(k) for k in range(brk + 1, n)):
                        continue
                    cand = (ir, -abs(ls - rs))
                    if best is None or cand > best[0]:
                        best = (cand, il, ih, ir, t1, t2, neck(n - 1), brk, depth)
        if best:
            _, il, ih, ir, t1, t2, neck_now, brk, depth = best
            key = "head_and_shoulders" if top else "inverse_head_and_shoulders"
            kb = CHART_PATTERNS[key]
            confirmed = brk is not None
            out.append({
                "key": key, "label": kb["label"], "bias": "bearish" if top else "bullish",
                "status": "confirmed" if confirmed else "forming",
                "clarity": "Clear" if confirmed else "Tentative",
                "points": [[candles[i][_T], vals[i]] for i in (il, ih, ir)],
                "neckline": neck_now,
                "neckline_points": [[candles[t1][_T], opp[t1]], [candles[t2][_T], opp[t2]]],
                "width": _width(candles, il, ir, depth, vals[ih]),
                "break_time": candles[brk][_T] if confirmed else None,
                "provisional": forming and (brk == n - 1 or ir == n - 1),
                "what": kb["what"], "suggests": kb["suggests"], "invalidation": kb["invalidation"],
            })
    return out


def _fit(points: list) -> tuple:
    """Least-squares line through (index, price) points -> (slope, intercept)."""
    m = len(points)
    mx = sum(p[0] for p in points) / m
    my = sum(p[1] for p in points) / m
    den = sum((p[0] - mx) ** 2 for p in points)
    slope = sum((p[0] - mx) * (p[1] - my) for p in points) / den if den else 0.0
    return slope, my - slope * mx


def detect_triangles(candles: list, a: float, forming: bool = False) -> list:
    """Ascending, descending or symmetrical triangle from converging swing highs/lows."""
    n = len(candles)
    highs = [c[_H] for c in candles]
    lows = [c[_L] for c in candles]
    closes = [c[_C] for c in candles]
    band = 0.25 * a
    cutoff = n - 6  # keep breakout bars out of the fit
    sh = [i for i in swing_points(highs, 2, True) if i <= cutoff]
    sl = [i for i in swing_points(lows, 2, False) if i <= cutoff]
    for window in (30, 45, 60):
        hs = [(i, highs[i]) for i in sh if i >= n - window]
        ls = [(i, lows[i]) for i in sl if i >= n - window]
        if len(hs) < 2 or len(ls) < 2 or len(hs) + len(ls) < 5:
            continue
        x0 = min(hs[0][0], ls[0][0])
        span = cutoff - x0
        if span < 12:
            continue
        sh_s, sh_i = _fit(hs)
        sl_s, sl_i = _fit(ls)
        if max(abs(p - (sh_s * i + sh_i)) for i, p in hs) > 0.75 * a or \
           max(abs(p - (sl_s * i + sl_i)) for i, p in ls) > 0.75 * a:
            continue

        def up_line(k):
            return sh_s * k + sh_i

        def lo_line(k):
            return sl_s * k + sl_i

        dh, dl = sh_s * span, sl_s * span
        gap_start, gap_now = up_line(x0) - lo_line(x0), up_line(n - 1) - lo_line(n - 1)
        if gap_start < 2 * a or gap_now < 0.3 * a or gap_now > 0.75 * gap_start:
            continue
        flat_h, flat_l = abs(dh) <= 0.75 * a, abs(dl) <= 0.75 * a
        if flat_h and dl >= 1.0 * a:
            key = "ascending_triangle"
        elif flat_l and dh <= -1.0 * a:
            key = "descending_triangle"
        elif dh <= -1.0 * a and dl >= 1.0 * a:
            key = "symmetrical_triangle"
        else:
            continue

        def outside(k):
            if closes[k] > up_line(k) + band:
                return "up"
            if closes[k] < lo_line(k) - band:
                return "down"
            return None

        status, broke_at, direction = "forming", None, None
        for k in range(cutoff + 1, n):
            if outside(k):
                broke_at, direction = k, outside(k)
                break
        if broke_at is not None:
            if outside(n - 1) != direction:
                broke_at, direction = None, None  # poked out and came back in
            else:
                status = "broke_" + direction
        elif outside(n - 1):
            continue
        kb = CHART_PATTERNS[key]
        bias = "neutral" if status == "forming" else ("bullish" if direction == "up" else "bearish")
        return [{
            "key": key, "label": kb["label"], "bias": bias, "status": status,
            "clarity": "Clear" if status != "forming" and len(hs) + len(ls) >= 5 else "Tentative",
            "upper_line": [[candles[x0][_T], up_line(x0)], [candles[n - 1][_T], up_line(n - 1)]],
            "lower_line": [[candles[x0][_T], lo_line(x0)], [candles[n - 1][_T], lo_line(n - 1)]],
            "width": _width(candles, x0, n - 1, gap_start, closes[-1]),
            "high_touches": len(hs), "low_touches": len(ls), "bars": n - x0,
            "break_time": candles[broke_at][_T] if broke_at is not None else None,
            "break_direction": direction,
            "provisional": forming and broke_at == n - 1,
            "what": kb["what"], "suggests": kb["suggests"], "invalidation": kb["invalidation"],
        }]
    return []


def _fmt(x: float) -> str:
    a = abs(x)
    return f"{x:.0f}" if a >= 100 else f"{x:.2f}" if a >= 1 else f"{x:.4f}" if a >= 0.01 else f"{x:.6f}"


def summarize(result: dict, close: float) -> str:
    parts = []
    cs = [c for c in result["candlesticks"] if c["bias"] != "neutral"]
    bull = [c for c in cs if c["bias"] == "bullish"]
    bear = [c for c in cs if c["bias"] == "bearish"]
    if result["candlesticks"]:
        newest = result["candlesticks"][0]
        parts.append(
            f"The last few candles show {len(bull)} bullish and {len(bear)} bearish pattern"
            f"{'' if len(bull) + len(bear) == 1 else 's'}; the most recent is {newest['label'].lower()} "
            f"({'this bar' if newest['bars_ago'] == 0 else str(newest['bars_ago']) + ' bar' + ('s' if newest['bars_ago'] > 1 else '') + ' ago'})."
        )
    else:
        parts.append("No notable candlestick patterns appear in the last few bars.")

    res, sup = result["levels"]["resistance"], result["levels"]["support"]
    if res and sup:
        parts.append(
            f"Price sits {abs(res[0]['distance_pct']):.1f}% below resistance at {_fmt(res[0]['price'])} "
            f"(tested {res[0]['touches']} times) and {abs(sup[0]['distance_pct']):.1f}% above support at {_fmt(sup[0]['price'])}."
        )
    elif res:
        parts.append(f"Nearest resistance is {_fmt(res[0]['price'])}, {abs(res[0]['distance_pct']):.1f}% above price.")
    elif sup:
        parts.append(f"Nearest support is {_fmt(sup[0]['price'])}, {abs(sup[0]['distance_pct']):.1f}% below price.")

    ev_bull = [e for e in result["events"] if e["bias"] == "bullish"]
    ev_bear = [e for e in result["events"] if e["bias"] == "bearish"]
    phrases = {
        "breakout_up": "Price broke above {lv} on {d}.",
        "breakout_down": "Price broke below {lv} on {d}.",
        "retest_held_up": "Price broke above {lv}, then pulled back to it and held (on {d}).",
        "retest_held_down": "Price broke below {lv}, then bounced back to it and was rejected (on {d}).",
        "failed_breakout_up": "Price broke above {lv} but closed back below it (on {d}).",
        "failed_breakout_down": "Price broke below {lv} but closed back above it (on {d}).",
    }
    for e in result["events"][:2]:
        parts.append(phrases[e["key"]].format(lv=_fmt(e["level"]), d=e["time"][:10]))

    for cp in result.get("chart_patterns", []):
        name = cp["label"].lower()
        if cp["key"] == "range":
            where = "near the top of" if cp["position_pct"] >= 75 else "near the bottom of" if cp["position_pct"] <= 25 else "in the middle of"
            parts.append(f"Price has been moving sideways between {_fmt(cp['bottom'])} and {_fmt(cp['top'])} for about {cp['bars']} bars and is {where} that range.")
        elif cp["key"].endswith("triangle"):
            if cp["status"] == "forming":
                parts.append(f"Price is squeezing into a possible {name} ({cp['bars']} bars); a close outside either line would resolve it.")
            else:
                parts.append(f"Price broke {cp['break_direction']}ward out of a {name} on {cp['break_time'][:10]}.")
                (ev_bull if cp["bias"] == "bullish" else ev_bear).append(cp)
        else:
            pts = " / ".join(_fmt(p) for _, p in cp["points"])
            if cp["status"] == "confirmed":
                parts.append(f"A {name} ({pts}) has been confirmed by a close through the neckline on {cp['break_time'][:10]}.")
                (ev_bull if cp["bias"] == "bullish" else ev_bear).append(cp)
            elif cp["key"] in ("double_top", "double_bottom"):
                parts.append(f"A possible {name} is forming at {pts}; it would only be confirmed by a close through {_fmt(cp['neckline'])}.")
            else:
                parts.append(f"A possible {name} ({pts}) is forming; it would only be confirmed by a close through the neckline, now near {_fmt(cp['neckline'])}.")

    wide = [cp["label"].lower() for cp in result.get("chart_patterns", []) if cp["width"]["label"] == "Wide"]
    if wide:
        parts.append(f"The {' and '.join(wide)} {'is a wide pattern' if len(wide) == 1 else 'are wide patterns'}, so treat {'its' if len(wide) == 1 else 'their'} levels as rough zones rather than exact lines.")

    score = len(bull) + len(ev_bull) - len(bear) - len(ev_bear)
    if bull or ev_bull or bear or ev_bear:
        if (bull or ev_bull) and (bear or ev_bear):
            parts.append("The candles and levels give mixed signals, so no single reading dominates.")
        elif score > 0:
            parts.append("The candles and levels lean bullish, and they agree with each other.")
        else:
            parts.append("The candles and levels lean bearish, and they agree with each other.")
    if any(c["provisional"] for c in result["candlesticks"]) or any(e["provisional"] for e in result["events"]):
        parts.append("The newest bar is still forming, so patterns involving it may change.")
    return " ".join(parts)


def analyze(candles: list, forming: bool = False) -> dict:
    sr = support_resistance(candles)
    result = {
        "candlesticks": detect_candlesticks(candles, 5, forming),
        "levels": {"support": sr["support"], "resistance": sr["resistance"], "kb": LEVELS},
        "events": detect_events(candles, sr["all"], sr["atr"], forming),
        "chart_patterns": (detect_double_tops_bottoms(candles, sr["atr"], forming)
                           + detect_head_and_shoulders(candles, sr["atr"], forming)
                           + detect_triangles(candles, sr["atr"], forming)
                           + detect_range(candles, sr["atr"], forming)),
    }
    result["summary"] = summarize(result, candles[-1][_C])
    return result
