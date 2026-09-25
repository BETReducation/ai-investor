import unittest

from api import patterns


def bars(rows):
    return [[f"t{i:03d}", o, h, l, c, 1000] for i, (o, h, l, c) in enumerate(rows)]


def downtrend(n=20, start=100.0, step=0.5):
    rows, price = [], start
    for _ in range(n):
        rows.append((price, price + 0.3, price - step - 0.3, price - step))
        price -= step
    return rows, price


def path(closes):
    rows, prev = [], closes[0]
    for c in closes:
        # small asymmetric wicks so turning points are unique swing extremes, not ties
        rows.append((prev, max(prev, c) + (0.2 if c >= prev else 0.05), min(prev, c) - (0.2 if c <= prev else 0.05), c))
        prev = c
    return rows


def keys(result):
    return {c["key"] for c in result}


class CandlestickTests(unittest.TestCase):
    def test_hammer_after_decline(self):
        rows, p = downtrend()
        rows.append((p, p + 0.2, p - 2.0, p + 0.1))
        self.assertIn("hammer", keys(patterns.detect_candlesticks(bars(rows))))

    def test_same_shape_after_rise_is_hanging_man(self):
        rows, p = downtrend(step=-0.5)
        rows.append((p, p + 0.2, p - 2.0, p + 0.1))
        self.assertIn("hanging_man", keys(patterns.detect_candlesticks(bars(rows))))

    def test_bullish_engulfing(self):
        rows, p = downtrend()
        rows.append((p, p + 0.1, p - 0.5, p - 0.4))
        rows.append((p - 0.5, p + 1.0, p - 0.6, p + 0.9))
        self.assertIn("bullish_engulfing", keys(patterns.detect_candlesticks(bars(rows))))

    def test_doji(self):
        rows, p = downtrend()
        rows.append((p, p + 1.0, p - 1.0, p + 0.02))
        self.assertIn("doji", keys(patterns.detect_candlesticks(bars(rows))))

    def test_morning_star(self):
        rows, p = downtrend()
        rows.append((p, p + 0.1, p - 2.1, p - 2.0))
        q = p - 2.0
        rows.append((q - 0.2, q - 0.1, q - 0.5, q - 0.3))
        rows.append((q - 0.2, q + 1.7, q - 0.3, q + 1.5))
        self.assertIn("morning_star", keys(patterns.detect_candlesticks(bars(rows))))

    def test_inside_bar(self):
        rows, p = downtrend()
        rows.append((p, p + 2.0, p - 2.0, p + 0.5))
        rows.append((p + 0.2, p + 1.0, p - 1.0, p + 0.3))
        self.assertIn("inside_bar", keys(patterns.detect_candlesticks(bars(rows))))

    def test_quiet_market_reports_nothing_bullish_or_bearish(self):
        rows = [(100, 100.4, 99.6, 100.1 if i % 2 else 99.9) for i in range(30)]
        found = patterns.detect_candlesticks(bars(rows))
        self.assertFalse([c for c in found if c["bias"] != "neutral"])

    def test_forming_flag_marks_last_bar_only(self):
        rows, p = downtrend()
        rows.append((p, p + 0.2, p - 2.0, p + 0.1))
        found = patterns.detect_candlesticks(bars(rows), forming=True)
        hammer = next(c for c in found if c["key"] == "hammer")
        self.assertTrue(hammer["provisional"])
        self.assertEqual(hammer["bars_ago"], 0)


RANGE = [105, 107, 109, 110, 108, 106, 104, 102, 100, 102, 104, 106, 108, 110,
         108, 106, 104, 102, 100, 102, 104, 106, 108, 110, 108, 106, 104, 102,
         100, 102, 104, 106, 107, 105, 104]


class LevelTests(unittest.TestCase):
    def test_finds_range_support_and_resistance(self):
        lv = patterns.support_resistance(bars(path(RANGE)))
        self.assertTrue(any(abs(l["price"] - 110.2) < 1 and l["touches"] >= 2 for l in lv["resistance"]))
        self.assertTrue(any(abs(l["price"] - 99.8) < 1 and l["touches"] >= 2 for l in lv["support"]))

    def test_breakout_and_held_retest(self):
        candles = bars(path(RANGE + [108, 109, 110, 112, 111, 111.5]))
        # make the pullback bar actually touch the old resistance
        candles[-2][3] = 110.4
        result = patterns.analyze(candles)
        found = {e["key"] for e in result["events"]}
        self.assertTrue(found & {"retest_held_up", "breakout_up"}, found)

    def test_failed_breakout(self):
        candles = bars(path(RANGE + [108, 109, 110, 112, 111, 108]))
        result = patterns.analyze(candles)
        self.assertIn("failed_breakout_up", {e["key"] for e in result["events"]})

    def test_no_crash_on_tiny_input(self):
        result = patterns.analyze(bars(path([100, 101, 102])))
        self.assertIn("summary", result)


def ramp(a, b, steps):
    return [a + (b - a) * (k + 1) / steps for k in range(steps)]


class ChartPatternTests(unittest.TestCase):
    def _double_top(self, tail):
        closes = [100.0] * 3 + ramp(100, 110, 8) + ramp(110, 104, 6) + ramp(104, 110, 6) + tail
        return bars(path(closes))

    def _double_bottom(self, tail):
        closes = [110.0] * 3 + ramp(110, 100, 8) + ramp(100, 106, 6) + ramp(106, 100, 6) + tail
        return bars(path(closes))

    def _find(self, candles, key):
        result = patterns.analyze(candles)
        return next((c for c in result["chart_patterns"] if c["key"] == key), None)

    def test_double_top_forming(self):
        cp = self._find(self._double_top(ramp(110, 107, 3)), "double_top")
        self.assertIsNotNone(cp)
        self.assertEqual((cp["status"], cp["clarity"], cp["bias"]), ("forming", "Tentative", "bearish"))

    def test_double_top_confirmed_on_neckline_break(self):
        cp = self._find(self._double_top(ramp(110, 102, 6)), "double_top")
        self.assertIsNotNone(cp)
        self.assertEqual(cp["status"], "confirmed")
        self.assertIsNotNone(cp["break_time"])

    def test_double_top_voided_by_close_above_peaks(self):
        candles = self._double_top(ramp(110, 108, 2) + ramp(108, 113, 3))
        self.assertIsNone(self._find(candles, "double_top"))

    def test_double_bottom_confirmed(self):
        cp = self._find(self._double_bottom(ramp(100, 108, 6)), "double_bottom")
        self.assertIsNotNone(cp)
        self.assertEqual((cp["status"], cp["bias"]), ("confirmed", "bullish"))

    def test_unequal_peaks_are_not_a_double_top(self):
        closes = [100.0] * 3 + ramp(100, 110, 8) + ramp(110, 104, 6) + ramp(104, 116, 6) + ramp(116, 113, 3)
        self.assertIsNone(self._find(bars(path(closes)), "double_top"))

    def test_range_detected(self):
        cp = self._find(bars(path(RANGE)), "range")
        self.assertIsNotNone(cp)
        self.assertTrue(cp["bottom"] < 101 and cp["top"] > 109)

    def test_steady_trend_is_not_a_range(self):
        closes = ramp(100, 130, 40)
        self.assertIsNone(self._find(bars(path(closes)), "range"))


def zigzag(turns, steps=5, tail=()):
    closes = [turns[0]]
    for a, b in zip(turns, turns[1:]):
        closes += ramp(a, b, steps)
    return closes + list(tail)


class ShapeTests(unittest.TestCase):
    def _find(self, closes, key):
        result = patterns.analyze(bars(path(closes)))
        return next((c for c in result["chart_patterns"] if c["key"] == key), None)

    def _hs(self, tail, head=110):
        return [100.0] * 3 + ramp(100, 106, 5) + ramp(106, 102, 4) + ramp(102, head, 6) \
            + ramp(head, 102, 6) + ramp(102, 106, 4) + tail

    def test_head_and_shoulders_forming(self):
        cp = self._find(self._hs(ramp(106, 104.5, 3)), "head_and_shoulders")
        self.assertIsNotNone(cp)
        self.assertEqual((cp["status"], cp["bias"]), ("forming", "bearish"))

    def test_head_and_shoulders_confirmed(self):
        cp = self._find(self._hs(ramp(106, 99, 5)), "head_and_shoulders")
        self.assertIsNotNone(cp)
        self.assertEqual(cp["status"], "confirmed")

    def test_head_barely_above_shoulders_is_not_a_pattern(self):
        self.assertIsNone(self._find(self._hs(ramp(106, 104.5, 3), head=106.5), "head_and_shoulders"))

    def test_inverse_head_and_shoulders_confirmed(self):
        closes = [110.0] * 3 + ramp(110, 104, 5) + ramp(104, 108, 4) + ramp(108, 100, 6) \
            + ramp(100, 108, 6) + ramp(108, 104, 4) + ramp(104, 111, 5)
        cp = self._find(closes, "inverse_head_and_shoulders")
        self.assertIsNotNone(cp)
        self.assertEqual((cp["status"], cp["bias"]), ("confirmed", "bullish"))

    def test_ascending_triangle(self):
        closes = zigzag([100, 110, 102, 110, 104, 110, 106, 110, 107.5], tail=ramp(107.5, 108.5, 2))
        cp = self._find(closes, "ascending_triangle")
        self.assertIsNotNone(cp)
        self.assertEqual(cp["status"], "forming")

    def test_ascending_triangle_breakout(self):
        closes = zigzag([100, 110, 102, 110, 104, 110, 106, 110, 107.5, 113], tail=[])
        cp = self._find(closes, "ascending_triangle")
        self.assertIsNotNone(cp)
        self.assertEqual((cp["status"], cp["bias"]), ("broke_up", "bullish"))

    def test_descending_triangle(self):
        closes = zigzag([110, 100, 108, 100, 106, 100, 104, 100, 102.5], tail=ramp(102.5, 101.5, 2))
        self.assertIsNotNone(self._find(closes, "descending_triangle"))

    def test_symmetrical_triangle(self):
        closes = zigzag([100, 110, 101, 109, 102, 108, 103, 107, 104], tail=ramp(104, 105, 2))
        self.assertIsNotNone(self._find(closes, "symmetrical_triangle"))

    def test_plain_range_is_not_a_triangle(self):
        cp = self._find(RANGE, "ascending_triangle") or self._find(RANGE, "descending_triangle") \
            or self._find(RANGE, "symmetrical_triangle")
        self.assertIsNone(cp)


class WidthTests(unittest.TestCase):
    def _c(self, n=100):
        return bars(path([100 + 0.01 * i for i in range(n)]))

    def test_narrow_standard_wide_by_time(self):
        c = self._c()
        self.assertEqual(patterns._width(c, 0, 10, 1, 100)["label"], "Narrow")
        self.assertEqual(patterns._width(c, 0, 25, 1, 100)["label"], "Standard")
        self.assertEqual(patterns._width(c, 0, 50, 1, 100)["label"], "Wide")

    def test_wide_by_price_swing(self):
        c = self._c()
        self.assertEqual(patterns._width(c, 0, 10, 20, 100)["label"], "Wide")
        self.assertEqual(patterns._width(c, 0, 10, 8, 100)["label"], "Standard")

    def test_duration_text(self):
        c = self._c()
        c[0][0], c[35][0] = "2026-08-01 00:00", "2026-09-05 00:00"
        self.assertEqual(patterns._width(c, 0, 35, 1, 100)["duration"], "about 5 weeks")

    def test_every_chart_pattern_carries_a_width(self):
        candles = bars(path(RANGE))
        for cp in patterns.analyze(candles)["chart_patterns"]:
            self.assertIn(cp["width"]["label"], ("Narrow", "Standard", "Wide"))


if __name__ == "__main__":
    unittest.main()
