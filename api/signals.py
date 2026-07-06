from __future__ import annotations
from typing import Any


DEFAULT_THRESHOLDS = {
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "rsi_trigger": "overbought_oversold",  # overbought_oversold | overbought | oversold |
                                            # centerline_cross | bullish_divergence |
                                            # bearish_divergence | failure_swings
    "volume_surge": 1.5,
    "macd_threshold": 0,
    "bb_oversold": 0.05,        # price must be at/near lower band (within 5%)
    "bb_overbought": 0.95,      # price must be at/near upper band (within 5%)
    "rsi_on": 1,
    "macd_on": 1,
    "bb_on": 1,
    "ma_on": 1,
    "vol_on": 1,
    "macd_cross_lookback": 5,   # only fire MACD signal if line crossed signal within N bars
    "ema_cross_lookback": 10,   # only fire EMA signal if cross happened within N bars
    "ma_cross_lookback": 10,    # only fire MA signal if cross happened within N bars
    "macd_trigger": "signal_cross",  # signal_cross | bullish_signal_cross | bearish_signal_cross |
                                      # centerline_cross | bullish_divergence | bearish_divergence |
                                      # histogram_reversal | overbought | oversold
    "macd_centerline_lookback": 5,
    "macd_zscore_overbought": 2.0,
    "macd_zscore_oversold": -2.0,
    "bb_trigger": "percent_b",  # percent_b | upper_touch | lower_touch | volatility_breakout |
                                # walking_upper | walking_lower | w_bottom | m_top
    "ma_trigger": "dual_cross",  # dual_cross | price_cross | two_ma_bull | two_ma_bear |
                                  # three_ma_bull | three_ma_bear
    "ma_trigger_lookback": 5,

    # ── Extended indicator set (Backtester) — all default OFF ────────────────
    "adx_on": 0, "adx_trend_threshold": 25,
    "psar_on": 0, "psar_flip_lookback": 3,
    "ichimoku_on": 0,
    "supertrend_on": 0, "supertrend_flip_lookback": 3,
    "donchian_on": 0,
    "hma_on": 0,
    "stoch_on": 0, "stoch_oversold": 20, "stoch_overbought": 80,
    "stochrsi_on": 0, "stochrsi_oversold": 20, "stochrsi_overbought": 80,
    "cci_on": 0, "cci_oversold": -100, "cci_overbought": 100,
    "willr_on": 0, "willr_oversold": -80, "willr_overbought": -20,
    "roc_on": 0, "roc_threshold": 2.0,
    "mfi_on": 0, "mfi_oversold": 20, "mfi_overbought": 80,
    "tsi_on": 0,
    "ao_on": 0,
    "atr_on": 0, "atr_trend_lookback": 5,
    "keltner_on": 0,
    "stdev_on": 0, "stdev_trend_lookback": 5,
    "chaikin_vol_on": 0, "chaikin_vol_trend_lookback": 5,
    "hist_vol_on": 0, "hist_vol_trend_lookback": 5,
    "obv_on": 0,
    "vwap_on": 0,
    "ad_on": 0,
    "cmf_on": 0, "cmf_threshold": 0.05,
    "vol_profile_on": 0,
    "fib_on": 0, "fib_tolerance_pct": 1.0,
}


def score_signals(indicators: dict, thresholds: dict | None = None) -> dict:
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    signals: list[dict] = []
    buy_score = 0
    sell_score = 0

    rsi = indicators.get("rsi")
    rsi_trig = indicators.get("rsi_trigger", {})
    trigger  = t.get("rsi_trigger", "overbought_oversold")
    if t.get("rsi_on", 1) and rsi is not None:
        if trigger == "overbought":
            if rsi > t["rsi_overbought"]:
                signals.append({"indicator": "RSI", "type": "SELL", "detail": f"RSI {rsi:.1f} — overbought (>{t['rsi_overbought']})", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "RSI", "type": "NEUTRAL", "detail": f"RSI {rsi:.1f} — not overbought", "weight": 0})

        elif trigger == "oversold":
            if rsi < t["rsi_oversold"]:
                signals.append({"indicator": "RSI", "type": "BUY", "detail": f"RSI {rsi:.1f} — oversold (<{t['rsi_oversold']})", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "RSI", "type": "NEUTRAL", "detail": f"RSI {rsi:.1f} — not oversold", "weight": 0})

        elif trigger == "centerline_cross":
            cross = rsi_trig.get("centerline_cross", 0)
            if cross > 0:
                signals.append({"indicator": "RSI", "type": "BUY", "detail": "RSI crossed above the 50 centerline", "weight": 2})
                buy_score += 2
            elif cross < 0:
                signals.append({"indicator": "RSI", "type": "SELL", "detail": "RSI crossed below the 50 centerline", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "RSI", "type": "NEUTRAL", "detail": "No centerline cross", "weight": 0})

        elif trigger == "bullish_divergence":
            if rsi_trig.get("bullish_divergence"):
                signals.append({"indicator": "RSI", "type": "BUY", "detail": "Bullish divergence — price made a lower low, RSI a higher low", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "RSI", "type": "NEUTRAL", "detail": "No bullish divergence", "weight": 0})

        elif trigger == "bearish_divergence":
            if rsi_trig.get("bearish_divergence"):
                signals.append({"indicator": "RSI", "type": "SELL", "detail": "Bearish divergence — price made a higher high, RSI a lower high", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "RSI", "type": "NEUTRAL", "detail": "No bearish divergence", "weight": 0})

        elif trigger == "failure_swings":
            if rsi_trig.get("bullish_failure_swing"):
                signals.append({"indicator": "RSI", "type": "BUY", "detail": "Bullish failure swing confirmed", "weight": 2})
                buy_score += 2
            elif rsi_trig.get("bearish_failure_swing"):
                signals.append({"indicator": "RSI", "type": "SELL", "detail": "Bearish failure swing confirmed", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "RSI", "type": "NEUTRAL", "detail": "No failure swing", "weight": 0})

        else:  # "overbought_oversold" (default) — unchanged from original behavior
            if rsi < t["rsi_oversold"]:
                signals.append({"indicator": "RSI", "type": "BUY", "detail": f"RSI {rsi:.1f} — oversold (<{t['rsi_oversold']})", "weight": 2})
                buy_score += 2
            elif rsi > t["rsi_overbought"]:
                signals.append({"indicator": "RSI", "type": "SELL", "detail": f"RSI {rsi:.1f} — overbought (>{t['rsi_overbought']})", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "RSI", "type": "NEUTRAL", "detail": f"RSI {rsi:.1f} — neutral", "weight": 0})

    macd_data = indicators.get("macd", {})
    macd_val = macd_data.get("macd")
    macd_sig_val = macd_data.get("signal")
    macd_trig = indicators.get("macd_trigger", {})
    macd_trigger_mode = t.get("macd_trigger", "signal_cross")
    if t.get("macd_on", 1) and macd_val is not None and macd_sig_val is not None:
        crossovers = indicators.get("crossovers", {})
        macd_lookback = int(t.get("macd_cross_lookback", 5))
        macd_bars = crossovers.get("macd_bars_since_cross", 999)
        macd_dir = crossovers.get("macd_direction", 0)
        macd_crossed_recently = macd_bars <= macd_lookback

        if macd_trigger_mode == "bullish_signal_cross":
            if macd_crossed_recently and macd_dir > 0:
                signals.append({"indicator": "MACD", "type": "BUY", "detail": f"MACD crossed above signal {macd_bars} bar(s) ago — bullish cross", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": "No recent bullish signal cross", "weight": 0})

        elif macd_trigger_mode == "bearish_signal_cross":
            if macd_crossed_recently and macd_dir < 0:
                signals.append({"indicator": "MACD", "type": "SELL", "detail": f"MACD crossed below signal {macd_bars} bar(s) ago — bearish cross", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": "No recent bearish signal cross", "weight": 0})

        elif macd_trigger_mode == "centerline_cross":
            cl_bars = macd_trig.get("centerline_bars_since_cross", 999)
            cl_dir = macd_trig.get("centerline_direction", 0)
            if cl_bars <= int(t.get("macd_centerline_lookback", 5)):
                if cl_dir > 0:
                    signals.append({"indicator": "MACD", "type": "BUY", "detail": "MACD crossed above the zero line", "weight": 2})
                    buy_score += 2
                else:
                    signals.append({"indicator": "MACD", "type": "SELL", "detail": "MACD crossed below the zero line", "weight": 2})
                    sell_score += 2
            else:
                signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": "No recent centerline cross", "weight": 0})

        elif macd_trigger_mode == "bullish_divergence":
            if macd_trig.get("bullish_divergence"):
                signals.append({"indicator": "MACD", "type": "BUY", "detail": "Bullish divergence — price made a lower low, MACD a higher low", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": "No bullish divergence", "weight": 0})

        elif macd_trigger_mode == "bearish_divergence":
            if macd_trig.get("bearish_divergence"):
                signals.append({"indicator": "MACD", "type": "SELL", "detail": "Bearish divergence — price made a higher high, MACD a lower high", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": "No bearish divergence", "weight": 0})

        elif macd_trigger_mode == "histogram_reversal":
            if macd_trig.get("bullish_histogram_reversal"):
                signals.append({"indicator": "MACD", "type": "BUY", "detail": "Histogram reversed higher — bullish momentum shift", "weight": 2})
                buy_score += 2
            elif macd_trig.get("bearish_histogram_reversal"):
                signals.append({"indicator": "MACD", "type": "SELL", "detail": "Histogram reversed lower — bearish momentum shift", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": "No histogram reversal", "weight": 0})

        elif macd_trigger_mode == "overbought":
            z = macd_trig.get("zscore")
            if z is not None and z > t.get("macd_zscore_overbought", 2.0):
                signals.append({"indicator": "MACD", "type": "SELL", "detail": f"MACD z-score {z:.2f} — overbought", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": "MACD not overbought", "weight": 0})

        elif macd_trigger_mode == "oversold":
            z = macd_trig.get("zscore")
            if z is not None and z < t.get("macd_zscore_oversold", -2.0):
                signals.append({"indicator": "MACD", "type": "BUY", "detail": f"MACD z-score {z:.2f} — oversold", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": "MACD not oversold", "weight": 0})

        else:  # "signal_cross" (default) — unchanged from original behavior
            if macd_crossed_recently:
                if macd_dir > 0:
                    signals.append({"indicator": "MACD", "type": "BUY", "detail": f"MACD crossed above signal {macd_bars} bar(s) ago — bullish cross", "weight": 2})
                    buy_score += 2
                else:
                    signals.append({"indicator": "MACD", "type": "SELL", "detail": f"MACD crossed below signal {macd_bars} bar(s) ago — bearish cross", "weight": 2})
                    sell_score += 2
            else:
                signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": f"No MACD cross in last {macd_lookback} bars", "weight": 0})

    bb = indicators.get("bollinger_bands", {})
    pct_b = bb.get("percent_b")
    close = indicators.get("price", {}).get("close")
    bb_trig = indicators.get("bb_trigger", {})
    bb_trigger_mode = t.get("bb_trigger", "percent_b")
    if t.get("bb_on", 1) and pct_b is not None:
        if bb_trigger_mode == "upper_touch":
            if bb.get("upper") is not None and close is not None and close >= bb["upper"]:
                signals.append({"indicator": "Bollinger Bands", "type": "SELL", "detail": "Price touched the upper band", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Bollinger Bands", "type": "NEUTRAL", "detail": "No upper band touch", "weight": 0})

        elif bb_trigger_mode == "lower_touch":
            if bb.get("lower") is not None and close is not None and close <= bb["lower"]:
                signals.append({"indicator": "Bollinger Bands", "type": "BUY", "detail": "Price touched the lower band", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Bollinger Bands", "type": "NEUTRAL", "detail": "No lower band touch", "weight": 0})

        elif bb_trigger_mode == "volatility_breakout":
            if bb_trig.get("bull_breakout"):
                signals.append({"indicator": "Bollinger Bands", "type": "BUY", "detail": "Volatility breakout above the upper band after a squeeze", "weight": 1})
                buy_score += 1
            elif bb_trig.get("bear_breakout"):
                signals.append({"indicator": "Bollinger Bands", "type": "SELL", "detail": "Volatility breakout below the lower band after a squeeze", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Bollinger Bands", "type": "NEUTRAL", "detail": "No squeeze breakout", "weight": 0})

        elif bb_trigger_mode == "walking_upper":
            if bb_trig.get("walking_upper"):
                signals.append({"indicator": "Bollinger Bands", "type": "BUY", "detail": "Walking the upper band — trend continuation", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Bollinger Bands", "type": "NEUTRAL", "detail": "Not walking the upper band", "weight": 0})

        elif bb_trigger_mode == "walking_lower":
            if bb_trig.get("walking_lower"):
                signals.append({"indicator": "Bollinger Bands", "type": "SELL", "detail": "Walking the lower band — trend continuation", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Bollinger Bands", "type": "NEUTRAL", "detail": "Not walking the lower band", "weight": 0})

        elif bb_trigger_mode == "w_bottom":
            if bb_trig.get("w_bottom"):
                signals.append({"indicator": "Bollinger Bands", "type": "BUY", "detail": "W-bottom confirmed — reversal, not continuation", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Bollinger Bands", "type": "NEUTRAL", "detail": "No W-bottom", "weight": 0})

        elif bb_trigger_mode == "m_top":
            if bb_trig.get("m_top"):
                signals.append({"indicator": "Bollinger Bands", "type": "SELL", "detail": "M-top confirmed — reversal, not continuation", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Bollinger Bands", "type": "NEUTRAL", "detail": "No M-top", "weight": 0})

        else:  # "percent_b" (default) — unchanged from original behavior
            if pct_b < t["bb_oversold"]:
                signals.append({"indicator": "Bollinger Bands", "type": "BUY", "detail": f"%B {pct_b:.2f} — price near lower band (oversold)", "weight": 1})
                buy_score += 1
            elif pct_b > t["bb_overbought"]:
                signals.append({"indicator": "Bollinger Bands", "type": "SELL", "detail": f"%B {pct_b:.2f} — price near upper band (overbought)", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Bollinger Bands", "type": "NEUTRAL", "detail": f"%B {pct_b:.2f} — price within bands", "weight": 0})

    mas = indicators.get("moving_averages", {})
    ma20 = mas.get("ma_20")
    ma50 = mas.get("ma_50")
    ema_short_val = mas.get("ema_short")
    ema_long_val = mas.get("ema_long")
    crossovers = indicators.get("crossovers", {})
    ma_trig = indicators.get("ma_trigger", {})
    ma_trigger_mode = t.get("ma_trigger", "dual_cross")
    ma_trig_lookback = int(t.get("ma_trigger_lookback", 5))
    if t.get("ma_on", 1):
        if ma_trigger_mode == "price_cross":
            bars = ma_trig.get("price_cross_bars_since", 999)
            direction = ma_trig.get("price_cross_direction", 0)
            if bars <= ma_trig_lookback:
                if direction > 0:
                    signals.append({"indicator": "MA", "type": "BUY", "detail": "Price crossed above the MA", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "MA", "type": "SELL", "detail": "Price crossed below the MA", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "MA", "type": "NEUTRAL", "detail": "No recent price/MA cross", "weight": 0})

        elif ma_trigger_mode == "two_ma_bull":
            bars = ma_trig.get("two_ma_bars_since", 999)
            direction = ma_trig.get("two_ma_direction", 0)
            if bars <= ma_trig_lookback and direction > 0:
                signals.append({"indicator": "MA", "type": "BUY", "detail": "Short MA crossed above long MA — bullish", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "MA", "type": "NEUTRAL", "detail": "No recent bullish MA crossover", "weight": 0})

        elif ma_trigger_mode == "two_ma_bear":
            bars = ma_trig.get("two_ma_bars_since", 999)
            direction = ma_trig.get("two_ma_direction", 0)
            if bars <= ma_trig_lookback and direction < 0:
                signals.append({"indicator": "MA", "type": "SELL", "detail": "Short MA crossed below long MA — bearish", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "MA", "type": "NEUTRAL", "detail": "No recent bearish MA crossover", "weight": 0})

        elif ma_trigger_mode == "three_ma_bull":
            if ma_trig.get("three_ma_bull"):
                signals.append({"indicator": "MA", "type": "BUY", "detail": "Short > Medium > Long MA — bullish trend alignment", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "MA", "type": "NEUTRAL", "detail": "No bullish 3-MA alignment", "weight": 0})

        elif ma_trigger_mode == "three_ma_bear":
            if ma_trig.get("three_ma_bear"):
                signals.append({"indicator": "MA", "type": "SELL", "detail": "Short < Medium < Long MA — bearish trend alignment", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "MA", "type": "NEUTRAL", "detail": "No bearish 3-MA alignment", "weight": 0})

        else:  # "dual_cross" (default) — unchanged from original behavior
            ma_lookback = int(t.get("ma_cross_lookback", 10))
            ma_bars = crossovers.get("ma_bars_since_cross", 999)
            ma_dir = crossovers.get("ma_direction", 0)
            if ma20 and ma50:
                if ma_bars <= ma_lookback:
                    if ma_dir > 0:
                        signals.append({"indicator": "MA", "type": "BUY", "detail": f"MA20 crossed above MA50 {ma_bars} bar(s) ago — golden cross", "weight": 1})
                        buy_score += 1
                    else:
                        signals.append({"indicator": "MA", "type": "SELL", "detail": f"MA20 crossed below MA50 {ma_bars} bar(s) ago — death cross", "weight": 1})
                        sell_score += 1
                else:
                    signals.append({"indicator": "MA", "type": "NEUTRAL", "detail": f"No MA cross in last {ma_lookback} bars", "weight": 0})

            ema_lookback = int(t.get("ema_cross_lookback", 10))
            ema_bars = crossovers.get("ema_bars_since_cross", 999)
            ema_dir = crossovers.get("ema_direction", 0)
            if ema_short_val and ema_long_val:
                if ema_bars <= ema_lookback:
                    es = int(t.get("ema_short", 9))
                    el = int(t.get("ema_long", 21))
                    if ema_dir > 0:
                        signals.append({"indicator": "EMA", "type": "BUY", "detail": f"EMA{es} crossed above EMA{el} {ema_bars} bar(s) ago — bullish cross", "weight": 1})
                        buy_score += 1
                    else:
                        signals.append({"indicator": "EMA", "type": "SELL", "detail": f"EMA{es} crossed below EMA{el} {ema_bars} bar(s) ago — bearish cross", "weight": 1})
                        sell_score += 1
                else:
                    signals.append({"indicator": "EMA", "type": "NEUTRAL", "detail": f"No EMA cross in last {ema_lookback} bars", "weight": 0})

    vol = indicators.get("volume", {})
    vol_ratio = vol.get("ratio")
    if t.get("vol_on", 1) and vol_ratio is not None:
        if vol_ratio > t["volume_surge"]:
            label = "BUY" if buy_score >= sell_score else "SELL"
            signals.append({"indicator": "Volume", "type": label, "detail": f"Volume surge {vol_ratio:.1f}x avg — confirms {label.lower()} pressure", "weight": 1})
            if label == "BUY":
                buy_score += 1
            else:
                sell_score += 1
        else:
            signals.append({"indicator": "Volume", "type": "NEUTRAL", "detail": f"Volume {vol_ratio:.1f}x avg — no surge", "weight": 0})

    # ── ADX (trend strength + direction) ─────────────────────────────────────
    adx = indicators.get("adx", {})
    adx_v, dmp_v, dmn_v = adx.get("adx"), adx.get("dmp"), adx.get("dmn")
    if t.get("adx_on", 0) and adx_v is not None and dmp_v is not None and dmn_v is not None:
        if adx_v > t["adx_trend_threshold"]:
            label = "BUY" if dmp_v > dmn_v else "SELL"
            signals.append({"indicator": "ADX", "type": label, "detail": f"ADX {adx_v:.1f} — strong trend, {'+DI' if label=='BUY' else '-DI'} leading", "weight": 2})
            if label == "BUY": buy_score += 2
            else: sell_score += 2
        else:
            signals.append({"indicator": "ADX", "type": "NEUTRAL", "detail": f"ADX {adx_v:.1f} — no strong trend", "weight": 0})

    # ── Parabolic SAR ─────────────────────────────────────────────────────────
    psar = indicators.get("psar", {})
    if t.get("psar_on", 0) and psar.get("is_bull") is not None:
        bars = psar.get("bars_since_flip", 999)
        if bars <= t["psar_flip_lookback"]:
            label = "BUY" if psar["is_bull"] else "SELL"
            signals.append({"indicator": "Parabolic SAR", "type": label, "detail": f"SAR flipped {label.lower()} {bars} bar(s) ago", "weight": 2})
            if label == "BUY": buy_score += 2
            else: sell_score += 2
        else:
            signals.append({"indicator": "Parabolic SAR", "type": "NEUTRAL", "detail": "No recent SAR flip", "weight": 0})

    # ── Ichimoku Cloud ────────────────────────────────────────────────────────
    ichimoku = indicators.get("ichimoku", {})
    cloud_pos = ichimoku.get("cloud_pos")
    if t.get("ichimoku_on", 0) and cloud_pos:
        if cloud_pos > 0:
            signals.append({"indicator": "Ichimoku", "type": "BUY", "detail": "Price above the cloud — bullish", "weight": 2})
            buy_score += 2
        elif cloud_pos < 0:
            signals.append({"indicator": "Ichimoku", "type": "SELL", "detail": "Price below the cloud — bearish", "weight": 2})
            sell_score += 2
        else:
            signals.append({"indicator": "Ichimoku", "type": "NEUTRAL", "detail": "Price inside the cloud", "weight": 0})

    # ── Supertrend ────────────────────────────────────────────────────────────
    supertrend = indicators.get("supertrend", {})
    if t.get("supertrend_on", 0) and supertrend.get("is_bull") is not None:
        bars = supertrend.get("bars_since_flip", 999)
        if bars <= t["supertrend_flip_lookback"]:
            label = "BUY" if supertrend["is_bull"] else "SELL"
            signals.append({"indicator": "Supertrend", "type": label, "detail": f"Supertrend flipped {label.lower()} {bars} bar(s) ago", "weight": 2})
            if label == "BUY": buy_score += 2
            else: sell_score += 2
        else:
            signals.append({"indicator": "Supertrend", "type": "NEUTRAL", "detail": "No recent Supertrend flip", "weight": 0})

    # ── Donchian Channels (breakout) ──────────────────────────────────────────
    donchian = indicators.get("donchian", {})
    if t.get("donchian_on", 0) and donchian.get("upper") is not None:
        close_v = donchian.get("close")
        if close_v is not None and close_v >= donchian["upper"]:
            signals.append({"indicator": "Donchian", "type": "BUY", "detail": "Breakout above the upper channel", "weight": 1})
            buy_score += 1
        elif close_v is not None and close_v <= donchian["lower"]:
            signals.append({"indicator": "Donchian", "type": "SELL", "detail": "Breakdown below the lower channel", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "Donchian", "type": "NEUTRAL", "detail": "Price inside the channel", "weight": 0})

    # ── Hull Moving Average (slope) ───────────────────────────────────────────
    hma = indicators.get("hma", {})
    if t.get("hma_on", 0) and hma.get("value") is not None and hma.get("prev") is not None:
        if hma["value"] > hma["prev"]:
            signals.append({"indicator": "HMA", "type": "BUY", "detail": "HMA sloping up", "weight": 1})
            buy_score += 1
        elif hma["value"] < hma["prev"]:
            signals.append({"indicator": "HMA", "type": "SELL", "detail": "HMA sloping down", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "HMA", "type": "NEUTRAL", "detail": "HMA flat", "weight": 0})

    # ── Stochastic Oscillator ─────────────────────────────────────────────────
    stoch = indicators.get("stochastic", {})
    stoch_k = stoch.get("k")
    if t.get("stoch_on", 0) and stoch_k is not None:
        if stoch_k < t["stoch_oversold"]:
            signals.append({"indicator": "Stochastic", "type": "BUY", "detail": f"%K {stoch_k:.1f} — oversold", "weight": 1})
            buy_score += 1
        elif stoch_k > t["stoch_overbought"]:
            signals.append({"indicator": "Stochastic", "type": "SELL", "detail": f"%K {stoch_k:.1f} — overbought", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "Stochastic", "type": "NEUTRAL", "detail": f"%K {stoch_k:.1f} — neutral", "weight": 0})

    # ── Stochastic RSI ────────────────────────────────────────────────────────
    stochrsi = indicators.get("stochrsi", {})
    srsi_k = stochrsi.get("k")
    if t.get("stochrsi_on", 0) and srsi_k is not None:
        if srsi_k < t["stochrsi_oversold"]:
            signals.append({"indicator": "Stochastic RSI", "type": "BUY", "detail": f"%K {srsi_k:.1f} — oversold", "weight": 1})
            buy_score += 1
        elif srsi_k > t["stochrsi_overbought"]:
            signals.append({"indicator": "Stochastic RSI", "type": "SELL", "detail": f"%K {srsi_k:.1f} — overbought", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "Stochastic RSI", "type": "NEUTRAL", "detail": f"%K {srsi_k:.1f} — neutral", "weight": 0})

    # ── Commodity Channel Index ───────────────────────────────────────────────
    cci_v = indicators.get("cci")
    if t.get("cci_on", 0) and cci_v is not None:
        if cci_v < t["cci_oversold"]:
            signals.append({"indicator": "CCI", "type": "BUY", "detail": f"CCI {cci_v:.1f} — oversold", "weight": 1})
            buy_score += 1
        elif cci_v > t["cci_overbought"]:
            signals.append({"indicator": "CCI", "type": "SELL", "detail": f"CCI {cci_v:.1f} — overbought", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "CCI", "type": "NEUTRAL", "detail": f"CCI {cci_v:.1f} — neutral", "weight": 0})

    # ── Williams %R ───────────────────────────────────────────────────────────
    willr_v = indicators.get("willr")
    if t.get("willr_on", 0) and willr_v is not None:
        if willr_v < t["willr_oversold"]:
            signals.append({"indicator": "Williams %R", "type": "BUY", "detail": f"%R {willr_v:.1f} — oversold", "weight": 1})
            buy_score += 1
        elif willr_v > t["willr_overbought"]:
            signals.append({"indicator": "Williams %R", "type": "SELL", "detail": f"%R {willr_v:.1f} — overbought", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": f"%R {willr_v:.1f} — neutral", "weight": 0})

    # ── Rate of Change ────────────────────────────────────────────────────────
    roc_v = indicators.get("roc")
    if t.get("roc_on", 0) and roc_v is not None:
        if roc_v > t["roc_threshold"]:
            signals.append({"indicator": "ROC", "type": "BUY", "detail": f"ROC {roc_v:.1f}% — upward momentum", "weight": 1})
            buy_score += 1
        elif roc_v < -t["roc_threshold"]:
            signals.append({"indicator": "ROC", "type": "SELL", "detail": f"ROC {roc_v:.1f}% — downward momentum", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "ROC", "type": "NEUTRAL", "detail": f"ROC {roc_v:.1f}% — flat", "weight": 0})

    # ── Money Flow Index ──────────────────────────────────────────────────────
    mfi_v = indicators.get("mfi")
    if t.get("mfi_on", 0) and mfi_v is not None:
        if mfi_v < t["mfi_oversold"]:
            signals.append({"indicator": "MFI", "type": "BUY", "detail": f"MFI {mfi_v:.1f} — oversold", "weight": 1})
            buy_score += 1
        elif mfi_v > t["mfi_overbought"]:
            signals.append({"indicator": "MFI", "type": "SELL", "detail": f"MFI {mfi_v:.1f} — overbought", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "MFI", "type": "NEUTRAL", "detail": f"MFI {mfi_v:.1f} — neutral", "weight": 0})

    # ── True Strength Index ───────────────────────────────────────────────────
    tsi = indicators.get("tsi", {})
    tsi_v, tsi_sig = tsi.get("value"), tsi.get("signal")
    if t.get("tsi_on", 0) and tsi_v is not None and tsi_sig is not None:
        if tsi_v > tsi_sig:
            signals.append({"indicator": "TSI", "type": "BUY", "detail": "TSI above its signal line", "weight": 1})
            buy_score += 1
        elif tsi_v < tsi_sig:
            signals.append({"indicator": "TSI", "type": "SELL", "detail": "TSI below its signal line", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "TSI", "type": "NEUTRAL", "detail": "TSI at its signal line", "weight": 0})

    # ── Awesome Oscillator ────────────────────────────────────────────────────
    ao_v = indicators.get("awesome_oscillator")
    if t.get("ao_on", 0) and ao_v is not None:
        if ao_v > 0:
            signals.append({"indicator": "Awesome Oscillator", "type": "BUY", "detail": f"AO {ao_v:.3f} — above zero", "weight": 1})
            buy_score += 1
        elif ao_v < 0:
            signals.append({"indicator": "Awesome Oscillator", "type": "SELL", "detail": f"AO {ao_v:.3f} — below zero", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": "AO at zero", "weight": 0})

    # ── Volatility-expansion + direction indicators (ATR / StdDev / Chaikin
    #    Volatility / Historical Volatility) — same heuristic for each:
    #    rising volatility confirms whichever direction price is already moving. ──
    def _vol_direction_signal(name, key, expanding, close_v, close_prev):
        if not t.get(f"{key}_on", 0) or expanding is None or close_v is None or close_prev is None:
            return
        nonlocal buy_score, sell_score
        if expanding and close_v > close_prev:
            signals.append({"indicator": name, "type": "BUY", "detail": f"{name} expanding with price rising", "weight": 1})
            buy_score += 1
        elif expanding and close_v < close_prev:
            signals.append({"indicator": name, "type": "SELL", "detail": f"{name} expanding with price falling", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": name, "type": "NEUTRAL", "detail": f"{name} not expanding", "weight": 0})

    close_now = indicators.get("price", {}).get("close")

    atr = indicators.get("atr", {})
    _vol_direction_signal("ATR", "atr", atr.get("expanding"), close_now, atr.get("close_trend_ref"))

    stdev = indicators.get("stdev", {})
    _vol_direction_signal("Std Dev", "stdev", stdev.get("expanding"), close_now, stdev.get("close_trend_ref"))

    chaikin_vol = indicators.get("chaikin_vol", {})
    _vol_direction_signal("Chaikin Volatility", "chaikin_vol", chaikin_vol.get("expanding"), close_now, chaikin_vol.get("close_trend_ref"))

    hist_vol = indicators.get("hist_vol", {})
    _vol_direction_signal("Historical Volatility", "hist_vol", hist_vol.get("expanding"), close_now, hist_vol.get("close_trend_ref"))

    # ── Keltner Channels (breakout) ───────────────────────────────────────────
    keltner = indicators.get("keltner", {})
    if t.get("keltner_on", 0) and keltner.get("upper") is not None and close_now is not None:
        if close_now >= keltner["upper"]:
            signals.append({"indicator": "Keltner Channels", "type": "BUY", "detail": "Breakout above the upper channel", "weight": 1})
            buy_score += 1
        elif close_now <= keltner["lower"]:
            signals.append({"indicator": "Keltner Channels", "type": "SELL", "detail": "Breakdown below the lower channel", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "Price inside the channel", "weight": 0})

    # ── On Balance Volume (trend vs its own average) ──────────────────────────
    obv = indicators.get("obv_trend", {})
    if t.get("obv_on", 0) and obv.get("obv") is not None and obv.get("obv_sma") is not None:
        if obv["obv"] > obv["obv_sma"]:
            signals.append({"indicator": "OBV", "type": "BUY", "detail": "OBV above its average — accumulation", "weight": 1})
            buy_score += 1
        elif obv["obv"] < obv["obv_sma"]:
            signals.append({"indicator": "OBV", "type": "SELL", "detail": "OBV below its average — distribution", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "OBV", "type": "NEUTRAL", "detail": "OBV at its average", "weight": 0})

    # ── VWAP ──────────────────────────────────────────────────────────────────
    vwap_v = indicators.get("vwap")
    if t.get("vwap_on", 0) and vwap_v is not None and close_now is not None:
        if close_now > vwap_v:
            signals.append({"indicator": "VWAP", "type": "BUY", "detail": "Price above VWAP", "weight": 1})
            buy_score += 1
        elif close_now < vwap_v:
            signals.append({"indicator": "VWAP", "type": "SELL", "detail": "Price below VWAP", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "VWAP", "type": "NEUTRAL", "detail": "Price at VWAP", "weight": 0})

    # ── Accumulation/Distribution Line (trend vs its own average) ────────────
    ad = indicators.get("ad_trend", {})
    if t.get("ad_on", 0) and ad.get("ad") is not None and ad.get("ad_sma") is not None:
        if ad["ad"] > ad["ad_sma"]:
            signals.append({"indicator": "A/D Line", "type": "BUY", "detail": "A/D Line above its average — accumulation", "weight": 1})
            buy_score += 1
        elif ad["ad"] < ad["ad_sma"]:
            signals.append({"indicator": "A/D Line", "type": "SELL", "detail": "A/D Line below its average — distribution", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "A/D Line", "type": "NEUTRAL", "detail": "A/D Line at its average", "weight": 0})

    # ── Chaikin Money Flow ────────────────────────────────────────────────────
    cmf_v = indicators.get("cmf")
    if t.get("cmf_on", 0) and cmf_v is not None:
        if cmf_v > t["cmf_threshold"]:
            signals.append({"indicator": "CMF", "type": "BUY", "detail": f"CMF {cmf_v:.2f} — buying pressure", "weight": 1})
            buy_score += 1
        elif cmf_v < -t["cmf_threshold"]:
            signals.append({"indicator": "CMF", "type": "SELL", "detail": f"CMF {cmf_v:.2f} — selling pressure", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "CMF", "type": "NEUTRAL", "detail": f"CMF {cmf_v:.2f} — neutral", "weight": 0})

    # ── Volume Profile (price vs point of control) ────────────────────────────
    vp = indicators.get("volume_profile", {})
    if t.get("vol_profile_on", 0) and vp.get("poc") is not None and close_now is not None:
        if close_now > vp["poc"]:
            signals.append({"indicator": "Volume Profile", "type": "BUY", "detail": "Price above the point of control", "weight": 1})
            buy_score += 1
        elif close_now < vp["poc"]:
            signals.append({"indicator": "Volume Profile", "type": "SELL", "detail": "Price below the point of control", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "Volume Profile", "type": "NEUTRAL", "detail": "Price at the point of control", "weight": 0})

    # ── Fibonacci Retracement (bounce/reject off nearest level) ───────────────
    fib = indicators.get("fibonacci", {})
    nearest, dist_pct, trend, prev_close = (
        fib.get("nearest_level"), fib.get("distance_pct"), fib.get("trend"), fib.get("prev_close"),
    )
    if (t.get("fib_on", 0) and nearest is not None and dist_pct is not None
            and close_now is not None and prev_close is not None):
        near_level = dist_pct <= t["fib_tolerance_pct"]
        if near_level and trend == "up" and close_now > prev_close:
            signals.append({"indicator": "Fibonacci", "type": "BUY", "detail": f"Bounce off {nearest} retracement support", "weight": 1})
            buy_score += 1
        elif near_level and trend == "down" and close_now < prev_close:
            signals.append({"indicator": "Fibonacci", "type": "SELL", "detail": f"Rejected at {nearest} retracement resistance", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "Fibonacci", "type": "NEUTRAL", "detail": "No level reaction", "weight": 0})

    total_weight = buy_score + sell_score
    confidence = round((max(buy_score, sell_score) / total_weight * 100) if total_weight > 0 else 50, 1)

    if buy_score > sell_score:
        overall = "BUY"
    elif sell_score > buy_score:
        overall = "SELL"
    else:
        overall = "NEUTRAL"

    return {
        "overall": overall,
        "buy_score": buy_score,
        "sell_score": sell_score,
        "confidence": confidence,
        "signals": signals,
        "thresholds_used": t,
    }
