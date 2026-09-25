"""Rule-based pattern detection on OHLCV candles — no AI, no third-party deps.

Input is a list of candles [time, open, high, low, close, volume], oldest first.
Everything here is deliberately conservative and explainable: each pattern is an
explicit rule, and descriptions live in pattern_knowledge.py. Geometry-heavy chart
patterns (double tops, head and shoulders, triangles...) are not covered yet.
"""
from .pattern_knowledge import CANDLESTICKS, EVENTS, LEVELS

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
    }
    result["summary"] = summarize(result, candles[-1][_C])
    return result
