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


if __name__ == "__main__":
    unittest.main()
