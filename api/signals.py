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
    "adx_trigger": "trend_threshold",  # trend_threshold | bull_di_cross | bear_di_cross |
                                        # above_25 | above_50 | above_75 |
                                        # strong_di_plus | strong_di_minus
    "adx_di_cross_lookback": 5,
    "psar_on": 0, "psar_flip_lookback": 3,
    "psar_trigger": "flip",  # flip | bull_flip | bear_flip | trend_state | trailing_stop
    "psar_gap_lookback": 3,
    "ichimoku_on": 0,
    "ichimoku_trigger": "cloud_position",  # cloud_position | bullish | bearish | tk_cross
    "ichimoku_tk_cross_lookback": 5,
    "supertrend_on": 0, "supertrend_flip_lookback": 3,
    "supertrend_trigger": "flip",  # flip | bull_flip | bear_flip | trend_state | trailing_stop
    "supertrend_gap_lookback": 3,
    "donchian_on": 0,
    "donchian_trigger": "breakout",  # breakout | bullish | bearish | middle_cross | two_channel_bull | two_channel_bear
    "donchian_mid_cross_lookback": 5,
    "hma_on": 0,
    "hma_trigger": "slope",  # slope | bullish_slope | bearish_slope | price_cross | two_hma_bull | two_hma_bear
    "hma_price_cross_lookback": 5,
    "hma_two_cross_lookback": 5,
    "stoch_on": 0, "stoch_oversold": 20, "stoch_overbought": 80,
    "stoch_trigger": "overbought_oversold",  # overbought_oversold | overbought | oversold | signal_cross
    "stoch_signal_cross_lookback": 5,
    "stochrsi_on": 0, "stochrsi_oversold": 20, "stochrsi_overbought": 80,
    "stochrsi_trigger": "overbought_oversold",
    # overbought_oversold | overbought | oversold | signal_cross | bullish_divergence | bearish_divergence
    "stochrsi_signal_cross_lookback": 5,
    "cci_on": 0, "cci_oversold": -100, "cci_overbought": 100,
    "cci_trigger": "overbought_oversold",  # overbought_oversold | overbought | oversold | centerline_cross |
                                            # breakout_bull | breakout_bear
    "cci_centerline_lookback": 5,
    "willr_on": 0, "willr_oversold": -80, "willr_overbought": -20,
    "willr_trigger": "overbought_oversold",
    # overbought_oversold | overbought | oversold | midline_cross | momentum_failure_bull |
    # momentum_failure_bear | trend_confirmation_bull | trend_confirmation_bear |
    # bullish_divergence | bearish_divergence
    "willr_midline_lookback": 5,
    "roc_on": 0, "roc_threshold": 2.0,
    "roc_trigger": "threshold",
    # threshold | bullish | bearish | centerline_cross | bull_momentum | bear_momentum |
    # bullish_divergence | bearish_divergence
    "roc_centerline_lookback": 5,
    "mfi_on": 0, "mfi_oversold": 20, "mfi_overbought": 80,
    "mfi_trigger": "overbought_oversold",
    # overbought_oversold | overbought | oversold | centerline_cross | bullish_divergence | bearish_divergence
    "mfi_centerline_lookback": 5,
    "tsi_on": 0, "tsi_oversold": -25, "tsi_overbought": 25,
    "tsi_trigger": "signal_cross",
    # signal_cross | bullish | bearish | centerline_cross | overbought | oversold |
    # bullish_divergence | bearish_divergence
    "tsi_centerline_lookback": 5,
    "ao_on": 0,
    "ao_trigger": "zero_state",
    # zero_state | bullish | bearish | zero_cross | bull_saucer | bear_saucer |
    # bull_twin_peaks | bear_twin_peaks | bull_divergence | bear_divergence
    "ao_zero_cross_lookback": 5,
    "atr_on": 0, "atr_trend_lookback": 5,
    "atr_trigger": "expansion",  # expansion | bullish_expansion | bearish_expansion | contraction
    "keltner_on": 0,
    "keltner_trigger": "breakout",
    # breakout | bullish | bearish | middle_cross | bull_band_riding | bear_band_riding |
    # bull_mean_reversion | bear_mean_reversion | keltner_squeeze
    "keltner_mid_cross_lookback": 5,
    "stdev_on": 0, "stdev_trend_lookback": 5,
    "stdev_trigger": "expansion",
    "chaikin_vol_on": 0, "chaikin_vol_trend_lookback": 5,
    "chaikin_vol_trigger": "expansion",
    "hist_vol_on": 0, "hist_vol_trend_lookback": 5,
    "hist_vol_trigger": "expansion",
    "obv_on": 0,
    "obv_trigger": "trend",  # trend | bullish | bearish | divergence
    "vwap_on": 0,
    "vwap_trigger": "position",  # position | bullish | bearish | band_touch | pullback_buy | pullback_sell
    "ad_on": 0,
    "ad_trigger": "trend",  # trend | bullish | bearish | divergence
    "cmf_on": 0, "cmf_threshold": 0.05,
    "cmf_trigger": "threshold",  # threshold | bullish | bearish | centerline_cross
    "cmf_centerline_lookback": 5,
    "vol_profile_on": 0,
    "vol_profile_trigger": "position",  # position | bullish | bearish | poc_breakout
    "vol_profile_breakout_lookback": 5,
    "fib_on": 0, "fib_tolerance_pct": 1.0,
    "fib_trigger": "bounce_reject",  # bounce_reject | bullish_bounce | bearish_reject | any_touch
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
    adx_trigger_mode = t.get("adx_trigger", "trend_threshold")
    if t.get("adx_on", 0) and adx_v is not None and dmp_v is not None and dmn_v is not None:
        if adx_trigger_mode == "bull_di_cross":
            bars = adx.get("di_cross_bars_since", 999)
            if bars <= int(t.get("adx_di_cross_lookback", 5)) and adx.get("di_direction", 0) > 0:
                signals.append({"indicator": "ADX", "type": "BUY", "detail": "+DI crossed above -DI — bullish", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "ADX", "type": "NEUTRAL", "detail": "No recent bullish DI crossover", "weight": 0})

        elif adx_trigger_mode == "bear_di_cross":
            bars = adx.get("di_cross_bars_since", 999)
            if bars <= int(t.get("adx_di_cross_lookback", 5)) and adx.get("di_direction", 0) < 0:
                signals.append({"indicator": "ADX", "type": "SELL", "detail": "-DI crossed above +DI — bearish", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "ADX", "type": "NEUTRAL", "detail": "No recent bearish DI crossover", "weight": 0})

        elif adx_trigger_mode in ("above_25", "above_50", "above_75"):
            fixed_threshold = {"above_25": 25, "above_50": 50, "above_75": 75}[adx_trigger_mode]
            if adx_v > fixed_threshold:
                label = "BUY" if dmp_v > dmn_v else "SELL"
                signals.append({"indicator": "ADX", "type": label, "detail": f"ADX {adx_v:.1f} — above {fixed_threshold}, {'+DI' if label=='BUY' else '-DI'} leading", "weight": 2})
                if label == "BUY": buy_score += 2
                else: sell_score += 2
            else:
                signals.append({"indicator": "ADX", "type": "NEUTRAL", "detail": f"ADX {adx_v:.1f} — below {fixed_threshold}", "weight": 0})

        elif adx_trigger_mode == "strong_di_plus":
            if adx_v > t["adx_trend_threshold"] and dmp_v > dmn_v:
                signals.append({"indicator": "ADX", "type": "BUY", "detail": f"ADX {adx_v:.1f} — strong trend, +DI leading", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "ADX", "type": "NEUTRAL", "detail": "No strong +DI trend", "weight": 0})

        elif adx_trigger_mode == "strong_di_minus":
            if adx_v > t["adx_trend_threshold"] and dmn_v > dmp_v:
                signals.append({"indicator": "ADX", "type": "SELL", "detail": f"ADX {adx_v:.1f} — strong trend, -DI leading", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "ADX", "type": "NEUTRAL", "detail": "No strong -DI trend", "weight": 0})

        else:  # "trend_threshold" (default) — unchanged from original behavior
            if adx_v > t["adx_trend_threshold"]:
                label = "BUY" if dmp_v > dmn_v else "SELL"
                signals.append({"indicator": "ADX", "type": label, "detail": f"ADX {adx_v:.1f} — strong trend, {'+DI' if label=='BUY' else '-DI'} leading", "weight": 2})
                if label == "BUY": buy_score += 2
                else: sell_score += 2
            else:
                signals.append({"indicator": "ADX", "type": "NEUTRAL", "detail": f"ADX {adx_v:.1f} — no strong trend", "weight": 0})

    # ── Parabolic SAR ─────────────────────────────────────────────────────────
    psar = indicators.get("psar", {})
    psar_trigger = t.get("psar_trigger", "flip")
    if t.get("psar_on", 0) and psar.get("is_bull") is not None:
        bars = psar.get("bars_since_flip", 999)
        recent = bars <= t["psar_flip_lookback"]
        if psar_trigger == "bull_flip":
            if recent and psar["is_bull"]:
                signals.append({"indicator": "Parabolic SAR", "type": "BUY", "detail": f"SAR flipped bullish {bars} bar(s) ago", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "Parabolic SAR", "type": "NEUTRAL", "detail": "No recent bullish SAR flip", "weight": 0})
        elif psar_trigger == "bear_flip":
            if recent and not psar["is_bull"]:
                signals.append({"indicator": "Parabolic SAR", "type": "SELL", "detail": f"SAR flipped bearish {bars} bar(s) ago", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "Parabolic SAR", "type": "NEUTRAL", "detail": "No recent bearish SAR flip", "weight": 0})
        elif psar_trigger == "trend_state":
            label = "BUY" if psar["is_bull"] else "SELL"
            signals.append({"indicator": "Parabolic SAR", "type": label, "detail": f"Dot currently {'below' if label=='BUY' else 'above'} price", "weight": 2})
            if label == "BUY": buy_score += 2
            else: sell_score += 2
        elif psar_trigger == "trailing_stop":
            if psar.get("gap_narrowing"):
                label = "SELL" if psar["is_bull"] else "BUY"
                signals.append({"indicator": "Parabolic SAR", "type": label, "detail": f"Price closing in on the trailing stop — {'bullish' if label=='BUY' else 'bearish'} momentum fading", "weight": 2})
                if label == "BUY": buy_score += 2
                else: sell_score += 2
            else:
                signals.append({"indicator": "Parabolic SAR", "type": "NEUTRAL", "detail": "Gap from the trailing stop stable or widening", "weight": 0})
        else:  # "flip" (default) — unchanged
            if recent:
                label = "BUY" if psar["is_bull"] else "SELL"
                signals.append({"indicator": "Parabolic SAR", "type": label, "detail": f"SAR flipped {label.lower()} {bars} bar(s) ago", "weight": 2})
                if label == "BUY": buy_score += 2
                else: sell_score += 2
            else:
                signals.append({"indicator": "Parabolic SAR", "type": "NEUTRAL", "detail": "No recent SAR flip", "weight": 0})

    # ── Ichimoku Cloud ────────────────────────────────────────────────────────
    ichimoku = indicators.get("ichimoku", {})
    cloud_pos = ichimoku.get("cloud_pos")
    ichimoku_trigger = t.get("ichimoku_trigger", "cloud_position")
    if t.get("ichimoku_on", 0) and cloud_pos:
        if ichimoku_trigger == "bullish":
            if cloud_pos > 0:
                signals.append({"indicator": "Ichimoku", "type": "BUY", "detail": "Price above the cloud — bullish", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "Ichimoku", "type": "NEUTRAL", "detail": "Price not above the cloud", "weight": 0})
        elif ichimoku_trigger == "bearish":
            if cloud_pos < 0:
                signals.append({"indicator": "Ichimoku", "type": "SELL", "detail": "Price below the cloud — bearish", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "Ichimoku", "type": "NEUTRAL", "detail": "Price not below the cloud", "weight": 0})
        elif ichimoku_trigger == "tk_cross":
            bars = ichimoku.get("tk_cross_bars_since", 999)
            if bars <= int(t.get("ichimoku_tk_cross_lookback", 5)):
                if ichimoku.get("tk_cross_direction", 0) > 0:
                    signals.append({"indicator": "Ichimoku", "type": "BUY", "detail": "Tenkan crossed above Kijun — bullish TK cross", "weight": 2})
                    buy_score += 2
                else:
                    signals.append({"indicator": "Ichimoku", "type": "SELL", "detail": "Tenkan crossed below Kijun — bearish TK cross", "weight": 2})
                    sell_score += 2
            else:
                signals.append({"indicator": "Ichimoku", "type": "NEUTRAL", "detail": "No recent TK cross", "weight": 0})
        else:  # "cloud_position" (default) — unchanged
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
    supertrend_trigger = t.get("supertrend_trigger", "flip")
    if t.get("supertrend_on", 0) and supertrend.get("is_bull") is not None:
        bars = supertrend.get("bars_since_flip", 999)
        recent = bars <= t["supertrend_flip_lookback"]
        if supertrend_trigger == "bull_flip":
            if recent and supertrend["is_bull"]:
                signals.append({"indicator": "Supertrend", "type": "BUY", "detail": f"Supertrend flipped bullish {bars} bar(s) ago", "weight": 2})
                buy_score += 2
            else:
                signals.append({"indicator": "Supertrend", "type": "NEUTRAL", "detail": "No recent bullish Supertrend flip", "weight": 0})
        elif supertrend_trigger == "bear_flip":
            if recent and not supertrend["is_bull"]:
                signals.append({"indicator": "Supertrend", "type": "SELL", "detail": f"Supertrend flipped bearish {bars} bar(s) ago", "weight": 2})
                sell_score += 2
            else:
                signals.append({"indicator": "Supertrend", "type": "NEUTRAL", "detail": "No recent bearish Supertrend flip", "weight": 0})
        elif supertrend_trigger == "trend_state":
            label = "BUY" if supertrend["is_bull"] else "SELL"
            signals.append({"indicator": "Supertrend", "type": label, "detail": f"Currently {'bullish' if label=='BUY' else 'bearish'}", "weight": 2})
            if label == "BUY": buy_score += 2
            else: sell_score += 2
        elif supertrend_trigger == "trailing_stop":
            if supertrend.get("gap_narrowing"):
                label = "SELL" if supertrend["is_bull"] else "BUY"
                signals.append({"indicator": "Supertrend", "type": label, "detail": f"Price closing in on the trailing stop — {'bullish' if label=='BUY' else 'bearish'} momentum fading", "weight": 2})
                if label == "BUY": buy_score += 2
                else: sell_score += 2
            else:
                signals.append({"indicator": "Supertrend", "type": "NEUTRAL", "detail": "Gap from the trailing stop stable or widening", "weight": 0})
        else:  # "flip" (default) — unchanged
            if recent:
                label = "BUY" if supertrend["is_bull"] else "SELL"
                signals.append({"indicator": "Supertrend", "type": label, "detail": f"Supertrend flipped {label.lower()} {bars} bar(s) ago", "weight": 2})
                if label == "BUY": buy_score += 2
                else: sell_score += 2
            else:
                signals.append({"indicator": "Supertrend", "type": "NEUTRAL", "detail": "No recent Supertrend flip", "weight": 0})

    # ── Donchian Channels (breakout) ──────────────────────────────────────────
    donchian = indicators.get("donchian", {})
    donchian_trigger = t.get("donchian_trigger", "breakout")
    if t.get("donchian_on", 0) and donchian.get("upper") is not None:
        close_v = donchian.get("close")
        if donchian_trigger == "bullish":
            if close_v is not None and close_v >= donchian["upper"]:
                signals.append({"indicator": "Donchian", "type": "BUY", "detail": "Breakout above the upper channel", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Donchian", "type": "NEUTRAL", "detail": "No upper breakout", "weight": 0})
        elif donchian_trigger == "bearish":
            if close_v is not None and close_v <= donchian["lower"]:
                signals.append({"indicator": "Donchian", "type": "SELL", "detail": "Breakdown below the lower channel", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Donchian", "type": "NEUTRAL", "detail": "No lower breakdown", "weight": 0})
        elif donchian_trigger == "middle_cross":
            bars = donchian.get("mid_cross_bars_since", 999)
            if bars <= int(t.get("donchian_mid_cross_lookback", 5)):
                if donchian.get("mid_cross_direction", 0) > 0:
                    signals.append({"indicator": "Donchian", "type": "BUY", "detail": "Price crossed above the channel midline", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "Donchian", "type": "SELL", "detail": "Price crossed below the channel midline", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "Donchian", "type": "NEUTRAL", "detail": "No recent midline cross", "weight": 0})
        elif donchian_trigger == "two_channel_bull":
            # Turtle-style long system: enter on an upper breakout of the (longer) entry
            # channel, exit on a lower breakdown of the (shorter) exit channel.
            exit_lower = donchian.get("exit_lower")
            if close_v is not None and close_v >= donchian["upper"]:
                signals.append({"indicator": "Donchian", "type": "BUY", "detail": "Long entry: breakout above the entry channel", "weight": 1})
                buy_score += 1
            elif close_v is not None and exit_lower is not None and close_v <= exit_lower:
                signals.append({"indicator": "Donchian", "type": "SELL", "detail": "Long exit: breakdown below the exit channel", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Donchian", "type": "NEUTRAL", "detail": "No entry or exit breakout", "weight": 0})
        elif donchian_trigger == "two_channel_bear":
            # Turtle-style short system: enter on a lower breakdown of the (longer) entry
            # channel, exit (cover) on an upper breakout of the (shorter) exit channel.
            exit_upper = donchian.get("exit_upper")
            if close_v is not None and close_v <= donchian["lower"]:
                signals.append({"indicator": "Donchian", "type": "SELL", "detail": "Short entry: breakdown below the entry channel", "weight": 1})
                sell_score += 1
            elif close_v is not None and exit_upper is not None and close_v >= exit_upper:
                signals.append({"indicator": "Donchian", "type": "BUY", "detail": "Short exit: breakout above the exit channel", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Donchian", "type": "NEUTRAL", "detail": "No entry or exit breakout", "weight": 0})
        else:  # "breakout" (default) — unchanged
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
    hma_trigger = t.get("hma_trigger", "slope")
    if t.get("hma_on", 0) and hma.get("value") is not None and hma.get("prev") is not None:
        if hma_trigger == "bullish_slope":
            if hma["value"] > hma["prev"]:
                signals.append({"indicator": "HMA", "type": "BUY", "detail": "HMA sloping up", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "HMA", "type": "NEUTRAL", "detail": "HMA not sloping up", "weight": 0})
        elif hma_trigger == "bearish_slope":
            if hma["value"] < hma["prev"]:
                signals.append({"indicator": "HMA", "type": "SELL", "detail": "HMA sloping down", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "HMA", "type": "NEUTRAL", "detail": "HMA not sloping down", "weight": 0})
        elif hma_trigger == "price_cross":
            bars = hma.get("price_cross_bars_since", 999)
            if bars <= int(t.get("hma_price_cross_lookback", 5)):
                if hma.get("price_cross_direction", 0) > 0:
                    signals.append({"indicator": "HMA", "type": "BUY", "detail": "Price crossed above the HMA", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "HMA", "type": "SELL", "detail": "Price crossed below the HMA", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "HMA", "type": "NEUTRAL", "detail": "No recent price/HMA cross", "weight": 0})
        elif hma_trigger == "two_hma_bull":
            bars = hma.get("two_cross_bars_since", 999)
            direction = hma.get("two_cross_direction", 0)
            if bars <= int(t.get("hma_two_cross_lookback", 5)) and direction > 0:
                signals.append({"indicator": "HMA", "type": "BUY", "detail": "Fast HMA crossed above the slow HMA — bullish", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "HMA", "type": "NEUTRAL", "detail": "No recent bullish HMA crossover", "weight": 0})
        elif hma_trigger == "two_hma_bear":
            bars = hma.get("two_cross_bars_since", 999)
            direction = hma.get("two_cross_direction", 0)
            if bars <= int(t.get("hma_two_cross_lookback", 5)) and direction < 0:
                signals.append({"indicator": "HMA", "type": "SELL", "detail": "Fast HMA crossed below the slow HMA — bearish", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "HMA", "type": "NEUTRAL", "detail": "No recent bearish HMA crossover", "weight": 0})
        else:  # "slope" (default) — unchanged
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
    stoch_trigger = t.get("stoch_trigger", "overbought_oversold")
    if t.get("stoch_on", 0) and stoch_k is not None:
        if stoch_trigger == "overbought":
            if stoch_k > t["stoch_overbought"]:
                signals.append({"indicator": "Stochastic", "type": "SELL", "detail": f"%K {stoch_k:.1f} — overbought", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Stochastic", "type": "NEUTRAL", "detail": f"%K {stoch_k:.1f} — not overbought", "weight": 0})
        elif stoch_trigger == "oversold":
            if stoch_k < t["stoch_oversold"]:
                signals.append({"indicator": "Stochastic", "type": "BUY", "detail": f"%K {stoch_k:.1f} — oversold", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Stochastic", "type": "NEUTRAL", "detail": f"%K {stoch_k:.1f} — not oversold", "weight": 0})
        elif stoch_trigger == "signal_cross":
            bars = stoch.get("signal_cross_bars_since", 999)
            if bars <= int(t.get("stoch_signal_cross_lookback", 5)):
                if stoch.get("signal_cross_direction", 0) > 0:
                    signals.append({"indicator": "Stochastic", "type": "BUY", "detail": "%K crossed above %D", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "Stochastic", "type": "SELL", "detail": "%K crossed below %D", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "Stochastic", "type": "NEUTRAL", "detail": "No recent %K/%D cross", "weight": 0})
        else:  # "overbought_oversold" (default) — unchanged
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
    stochrsi_trigger = t.get("stochrsi_trigger", "overbought_oversold")
    if t.get("stochrsi_on", 0) and srsi_k is not None:
        if stochrsi_trigger == "overbought":
            if srsi_k > t["stochrsi_overbought"]:
                signals.append({"indicator": "Stochastic RSI", "type": "SELL", "detail": f"%K {srsi_k:.1f} — overbought", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Stochastic RSI", "type": "NEUTRAL", "detail": f"%K {srsi_k:.1f} — not overbought", "weight": 0})
        elif stochrsi_trigger == "oversold":
            if srsi_k < t["stochrsi_oversold"]:
                signals.append({"indicator": "Stochastic RSI", "type": "BUY", "detail": f"%K {srsi_k:.1f} — oversold", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Stochastic RSI", "type": "NEUTRAL", "detail": f"%K {srsi_k:.1f} — not oversold", "weight": 0})
        elif stochrsi_trigger == "signal_cross":
            bars = stochrsi.get("signal_cross_bars_since", 999)
            if bars <= int(t.get("stochrsi_signal_cross_lookback", 5)):
                if stochrsi.get("signal_cross_direction", 0) > 0:
                    signals.append({"indicator": "Stochastic RSI", "type": "BUY", "detail": "%K crossed above %D", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "Stochastic RSI", "type": "SELL", "detail": "%K crossed below %D", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "Stochastic RSI", "type": "NEUTRAL", "detail": "No recent %K/%D cross", "weight": 0})
        elif stochrsi_trigger == "bullish_divergence":
            if stochrsi.get("bullish_divergence"):
                signals.append({"indicator": "Stochastic RSI", "type": "BUY", "detail": "Bullish divergence — price made a lower low, %K a higher low", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Stochastic RSI", "type": "NEUTRAL", "detail": "No bullish divergence", "weight": 0})
        elif stochrsi_trigger == "bearish_divergence":
            if stochrsi.get("bearish_divergence"):
                signals.append({"indicator": "Stochastic RSI", "type": "SELL", "detail": "Bearish divergence — price made a higher high, %K a lower high", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Stochastic RSI", "type": "NEUTRAL", "detail": "No bearish divergence", "weight": 0})
        else:  # "overbought_oversold" (default) — unchanged
            if srsi_k < t["stochrsi_oversold"]:
                signals.append({"indicator": "Stochastic RSI", "type": "BUY", "detail": f"%K {srsi_k:.1f} — oversold", "weight": 1})
                buy_score += 1
            elif srsi_k > t["stochrsi_overbought"]:
                signals.append({"indicator": "Stochastic RSI", "type": "SELL", "detail": f"%K {srsi_k:.1f} — overbought", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Stochastic RSI", "type": "NEUTRAL", "detail": f"%K {srsi_k:.1f} — neutral", "weight": 0})

    # ── Commodity Channel Index ───────────────────────────────────────────────
    cci = indicators.get("cci", {})
    cci_v = cci.get("value")
    cci_trigger = t.get("cci_trigger", "overbought_oversold")
    if t.get("cci_on", 0) and cci_v is not None:
        if cci_trigger == "overbought":
            if cci_v > t["cci_overbought"]:
                signals.append({"indicator": "CCI", "type": "SELL", "detail": f"CCI {cci_v:.1f} — overbought", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "CCI", "type": "NEUTRAL", "detail": f"CCI {cci_v:.1f} — not overbought", "weight": 0})
        elif cci_trigger == "oversold":
            if cci_v < t["cci_oversold"]:
                signals.append({"indicator": "CCI", "type": "BUY", "detail": f"CCI {cci_v:.1f} — oversold", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "CCI", "type": "NEUTRAL", "detail": f"CCI {cci_v:.1f} — not oversold", "weight": 0})
        elif cci_trigger == "centerline_cross":
            bars = cci.get("centerline_bars_since", 999)
            if bars <= int(t.get("cci_centerline_lookback", 5)):
                if cci.get("centerline_direction", 0) > 0:
                    signals.append({"indicator": "CCI", "type": "BUY", "detail": "CCI crossed above zero", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "CCI", "type": "SELL", "detail": "CCI crossed below zero", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "CCI", "type": "NEUTRAL", "detail": "No recent centerline cross", "weight": 0})
        elif cci_trigger == "breakout_bull":
            # Momentum-continuation read of the +100 level (opposite of "overbought" mean-reversion):
            # a push above +100 signals strengthening bullish momentum, not exhaustion.
            if cci_v > t["cci_overbought"]:
                signals.append({"indicator": "CCI", "type": "BUY", "detail": f"CCI {cci_v:.1f} — bullish breakout above +100", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "CCI", "type": "NEUTRAL", "detail": f"CCI {cci_v:.1f} — no bullish breakout", "weight": 0})
        elif cci_trigger == "breakout_bear":
            if cci_v < t["cci_oversold"]:
                signals.append({"indicator": "CCI", "type": "SELL", "detail": f"CCI {cci_v:.1f} — bearish breakout below -100", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "CCI", "type": "NEUTRAL", "detail": f"CCI {cci_v:.1f} — no bearish breakout", "weight": 0})
        else:  # "overbought_oversold" (default) — unchanged
            if cci_v < t["cci_oversold"]:
                signals.append({"indicator": "CCI", "type": "BUY", "detail": f"CCI {cci_v:.1f} — oversold", "weight": 1})
                buy_score += 1
            elif cci_v > t["cci_overbought"]:
                signals.append({"indicator": "CCI", "type": "SELL", "detail": f"CCI {cci_v:.1f} — overbought", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "CCI", "type": "NEUTRAL", "detail": f"CCI {cci_v:.1f} — neutral", "weight": 0})

    # ── Williams %R ───────────────────────────────────────────────────────────
    willr = indicators.get("willr", {})
    willr_v = willr.get("value")
    willr_trigger = t.get("willr_trigger", "overbought_oversold")
    if t.get("willr_on", 0) and willr_v is not None:
        if willr_trigger == "overbought":
            if willr_v > t["willr_overbought"]:
                signals.append({"indicator": "Williams %R", "type": "SELL", "detail": f"%R {willr_v:.1f} — overbought", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": f"%R {willr_v:.1f} — not overbought", "weight": 0})
        elif willr_trigger == "oversold":
            if willr_v < t["willr_oversold"]:
                signals.append({"indicator": "Williams %R", "type": "BUY", "detail": f"%R {willr_v:.1f} — oversold", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": f"%R {willr_v:.1f} — not oversold", "weight": 0})
        elif willr_trigger == "midline_cross":
            bars = willr.get("midline_bars_since", 999)
            if bars <= int(t.get("willr_midline_lookback", 5)):
                if willr.get("midline_direction", 0) > 0:
                    signals.append({"indicator": "Williams %R", "type": "BUY", "detail": "%R crossed above -50", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "Williams %R", "type": "SELL", "detail": "%R crossed below -50", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": "No recent midline cross", "weight": 0})
        elif willr_trigger == "momentum_failure_bull":
            if willr.get("bullish_failure_swing"):
                signals.append({"indicator": "Williams %R", "type": "BUY", "detail": "Bullish failure swing — %R failed to make a new low", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": "No bullish failure swing", "weight": 0})
        elif willr_trigger == "momentum_failure_bear":
            if willr.get("bearish_failure_swing"):
                signals.append({"indicator": "Williams %R", "type": "SELL", "detail": "Bearish failure swing — %R failed to make a new high", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": "No bearish failure swing", "weight": 0})
        elif willr_trigger == "trend_confirmation_bull":
            if willr.get("bullish_confirmation"):
                signals.append({"indicator": "Williams %R", "type": "BUY", "detail": "Trend confirmed — price and %R both made a higher high", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": "No bullish trend confirmation", "weight": 0})
        elif willr_trigger == "trend_confirmation_bear":
            if willr.get("bearish_confirmation"):
                signals.append({"indicator": "Williams %R", "type": "SELL", "detail": "Trend confirmed — price and %R both made a lower low", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": "No bearish trend confirmation", "weight": 0})
        elif willr_trigger == "bullish_divergence":
            if willr.get("bullish_divergence"):
                signals.append({"indicator": "Williams %R", "type": "BUY", "detail": "Bullish divergence — price made a lower low, %R a higher low", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": "No bullish divergence", "weight": 0})
        elif willr_trigger == "bearish_divergence":
            if willr.get("bearish_divergence"):
                signals.append({"indicator": "Williams %R", "type": "SELL", "detail": "Bearish divergence — price made a higher high, %R a lower high", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": "No bearish divergence", "weight": 0})
        else:  # "overbought_oversold" (default) — unchanged
            if willr_v < t["willr_oversold"]:
                signals.append({"indicator": "Williams %R", "type": "BUY", "detail": f"%R {willr_v:.1f} — oversold", "weight": 1})
                buy_score += 1
            elif willr_v > t["willr_overbought"]:
                signals.append({"indicator": "Williams %R", "type": "SELL", "detail": f"%R {willr_v:.1f} — overbought", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Williams %R", "type": "NEUTRAL", "detail": f"%R {willr_v:.1f} — neutral", "weight": 0})

    # ── Rate of Change ────────────────────────────────────────────────────────
    roc = indicators.get("roc", {})
    roc_v = roc.get("value")
    roc_trigger = t.get("roc_trigger", "threshold")
    if t.get("roc_on", 0) and roc_v is not None:
        if roc_trigger == "bullish":
            if roc_v > t["roc_threshold"]:
                signals.append({"indicator": "ROC", "type": "BUY", "detail": f"ROC {roc_v:.1f}% — upward momentum", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "ROC", "type": "NEUTRAL", "detail": f"ROC {roc_v:.1f}% — no upward momentum", "weight": 0})
        elif roc_trigger == "bearish":
            if roc_v < -t["roc_threshold"]:
                signals.append({"indicator": "ROC", "type": "SELL", "detail": f"ROC {roc_v:.1f}% — downward momentum", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "ROC", "type": "NEUTRAL", "detail": f"ROC {roc_v:.1f}% — no downward momentum", "weight": 0})
        elif roc_trigger == "centerline_cross":
            bars = roc.get("centerline_bars_since", 999)
            if bars <= int(t.get("roc_centerline_lookback", 5)):
                if roc.get("centerline_direction", 0) > 0:
                    signals.append({"indicator": "ROC", "type": "BUY", "detail": "ROC crossed above zero", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "ROC", "type": "SELL", "detail": "ROC crossed below zero", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "ROC", "type": "NEUTRAL", "detail": "No recent centerline cross", "weight": 0})
        elif roc_trigger == "bull_momentum":
            # Stronger than "bullish": ROC must be above threshold AND still rising,
            # i.e. momentum is actively building, not just sitting above the level.
            prev = roc.get("prev")
            if prev is not None and roc_v > t["roc_threshold"] and roc_v > prev:
                signals.append({"indicator": "ROC", "type": "BUY", "detail": f"ROC {roc_v:.1f}% — rising above threshold, bullish momentum building", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "ROC", "type": "NEUTRAL", "detail": "No bullish momentum building", "weight": 0})
        elif roc_trigger == "bear_momentum":
            prev = roc.get("prev")
            if prev is not None and roc_v < -t["roc_threshold"] and roc_v < prev:
                signals.append({"indicator": "ROC", "type": "SELL", "detail": f"ROC {roc_v:.1f}% — falling below threshold, bearish momentum building", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "ROC", "type": "NEUTRAL", "detail": "No bearish momentum building", "weight": 0})
        elif roc_trigger == "bullish_divergence":
            if roc.get("bullish_divergence"):
                signals.append({"indicator": "ROC", "type": "BUY", "detail": "Bullish divergence — price made a lower low, ROC a higher low", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "ROC", "type": "NEUTRAL", "detail": "No bullish divergence", "weight": 0})
        elif roc_trigger == "bearish_divergence":
            if roc.get("bearish_divergence"):
                signals.append({"indicator": "ROC", "type": "SELL", "detail": "Bearish divergence — price made a higher high, ROC a lower high", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "ROC", "type": "NEUTRAL", "detail": "No bearish divergence", "weight": 0})
        else:  # "threshold" (default) — unchanged
            if roc_v > t["roc_threshold"]:
                signals.append({"indicator": "ROC", "type": "BUY", "detail": f"ROC {roc_v:.1f}% — upward momentum", "weight": 1})
                buy_score += 1
            elif roc_v < -t["roc_threshold"]:
                signals.append({"indicator": "ROC", "type": "SELL", "detail": f"ROC {roc_v:.1f}% — downward momentum", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "ROC", "type": "NEUTRAL", "detail": f"ROC {roc_v:.1f}% — flat", "weight": 0})

    # ── Money Flow Index ──────────────────────────────────────────────────────
    mfi = indicators.get("mfi", {})
    mfi_v = mfi.get("value")
    mfi_trigger = t.get("mfi_trigger", "overbought_oversold")
    if t.get("mfi_on", 0) and mfi_v is not None:
        if mfi_trigger == "overbought":
            if mfi_v > t["mfi_overbought"]:
                signals.append({"indicator": "MFI", "type": "SELL", "detail": f"MFI {mfi_v:.1f} — overbought", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "MFI", "type": "NEUTRAL", "detail": f"MFI {mfi_v:.1f} — not overbought", "weight": 0})
        elif mfi_trigger == "oversold":
            if mfi_v < t["mfi_oversold"]:
                signals.append({"indicator": "MFI", "type": "BUY", "detail": f"MFI {mfi_v:.1f} — oversold", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "MFI", "type": "NEUTRAL", "detail": f"MFI {mfi_v:.1f} — not oversold", "weight": 0})
        elif mfi_trigger == "centerline_cross":
            bars = mfi.get("centerline_bars_since", 999)
            if bars <= int(t.get("mfi_centerline_lookback", 5)):
                if mfi.get("centerline_direction", 0) > 0:
                    signals.append({"indicator": "MFI", "type": "BUY", "detail": "MFI crossed above 50", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "MFI", "type": "SELL", "detail": "MFI crossed below 50", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "MFI", "type": "NEUTRAL", "detail": "No recent centerline cross", "weight": 0})
        elif mfi_trigger == "bullish_divergence":
            if mfi.get("bullish_divergence"):
                signals.append({"indicator": "MFI", "type": "BUY", "detail": "Bullish divergence — price made a lower low, MFI a higher low", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "MFI", "type": "NEUTRAL", "detail": "No bullish divergence", "weight": 0})
        elif mfi_trigger == "bearish_divergence":
            if mfi.get("bearish_divergence"):
                signals.append({"indicator": "MFI", "type": "SELL", "detail": "Bearish divergence — price made a higher high, MFI a lower high", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "MFI", "type": "NEUTRAL", "detail": "No bearish divergence", "weight": 0})
        else:  # "overbought_oversold" (default) — unchanged
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
    tsi_trigger = t.get("tsi_trigger", "signal_cross")
    if t.get("tsi_on", 0) and tsi_v is not None and tsi_sig is not None:
        if tsi_trigger == "bullish":
            if tsi_v > tsi_sig:
                signals.append({"indicator": "TSI", "type": "BUY", "detail": "TSI above its signal line", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "TSI", "type": "NEUTRAL", "detail": "TSI not above its signal line", "weight": 0})
        elif tsi_trigger == "bearish":
            if tsi_v < tsi_sig:
                signals.append({"indicator": "TSI", "type": "SELL", "detail": "TSI below its signal line", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "TSI", "type": "NEUTRAL", "detail": "TSI not below its signal line", "weight": 0})
        elif tsi_trigger == "centerline_cross":
            bars = tsi.get("centerline_bars_since", 999)
            if bars <= int(t.get("tsi_centerline_lookback", 5)):
                if tsi.get("centerline_direction", 0) > 0:
                    signals.append({"indicator": "TSI", "type": "BUY", "detail": "TSI crossed above zero", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "TSI", "type": "SELL", "detail": "TSI crossed below zero", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "TSI", "type": "NEUTRAL", "detail": "No recent centerline cross", "weight": 0})
        elif tsi_trigger == "overbought":
            if tsi_v > t["tsi_overbought"]:
                signals.append({"indicator": "TSI", "type": "SELL", "detail": f"TSI {tsi_v:.1f} — overbought", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "TSI", "type": "NEUTRAL", "detail": f"TSI {tsi_v:.1f} — not overbought", "weight": 0})
        elif tsi_trigger == "oversold":
            if tsi_v < t["tsi_oversold"]:
                signals.append({"indicator": "TSI", "type": "BUY", "detail": f"TSI {tsi_v:.1f} — oversold", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "TSI", "type": "NEUTRAL", "detail": f"TSI {tsi_v:.1f} — not oversold", "weight": 0})
        elif tsi_trigger == "bullish_divergence":
            if tsi.get("bullish_divergence"):
                signals.append({"indicator": "TSI", "type": "BUY", "detail": "Bullish divergence — price made a lower low, TSI a higher low", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "TSI", "type": "NEUTRAL", "detail": "No bullish divergence", "weight": 0})
        elif tsi_trigger == "bearish_divergence":
            if tsi.get("bearish_divergence"):
                signals.append({"indicator": "TSI", "type": "SELL", "detail": "Bearish divergence — price made a higher high, TSI a lower high", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "TSI", "type": "NEUTRAL", "detail": "No bearish divergence", "weight": 0})
        else:  # "signal_cross" (default) — unchanged
            if tsi_v > tsi_sig:
                signals.append({"indicator": "TSI", "type": "BUY", "detail": "TSI above its signal line", "weight": 1})
                buy_score += 1
            elif tsi_v < tsi_sig:
                signals.append({"indicator": "TSI", "type": "SELL", "detail": "TSI below its signal line", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "TSI", "type": "NEUTRAL", "detail": "TSI at its signal line", "weight": 0})

    # ── Awesome Oscillator ────────────────────────────────────────────────────
    ao = indicators.get("awesome_oscillator", {})
    ao_v = ao.get("value")
    ao_trigger = t.get("ao_trigger", "zero_state")
    if t.get("ao_on", 0) and ao_v is not None:
        if ao_trigger == "bullish":
            if ao_v > 0:
                signals.append({"indicator": "Awesome Oscillator", "type": "BUY", "detail": f"AO {ao_v:.3f} — above zero", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": f"AO {ao_v:.3f} — not above zero", "weight": 0})
        elif ao_trigger == "bearish":
            if ao_v < 0:
                signals.append({"indicator": "Awesome Oscillator", "type": "SELL", "detail": f"AO {ao_v:.3f} — below zero", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": f"AO {ao_v:.3f} — not below zero", "weight": 0})
        elif ao_trigger == "zero_cross":
            bars = ao.get("zero_cross_bars_since", 999)
            if bars <= int(t.get("ao_zero_cross_lookback", 5)):
                if ao.get("zero_cross_direction", 0) > 0:
                    signals.append({"indicator": "Awesome Oscillator", "type": "BUY", "detail": "AO crossed above zero", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "Awesome Oscillator", "type": "SELL", "detail": "AO crossed below zero", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": "No recent zero cross", "weight": 0})
        elif ao_trigger == "bull_saucer":
            if ao.get("bull_saucer"):
                signals.append({"indicator": "Awesome Oscillator", "type": "BUY", "detail": "Bull saucer — momentum dipped and turned back up above zero", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": "No bull saucer", "weight": 0})
        elif ao_trigger == "bear_saucer":
            if ao.get("bear_saucer"):
                signals.append({"indicator": "Awesome Oscillator", "type": "SELL", "detail": "Bear saucer — momentum ticked up and turned back down below zero", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": "No bear saucer", "weight": 0})
        elif ao_trigger == "bull_twin_peaks":
            if ao.get("bull_twin_peaks"):
                signals.append({"indicator": "Awesome Oscillator", "type": "BUY", "detail": "Bull twin peaks — second trough below zero shallower than the first", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": "No bull twin peaks", "weight": 0})
        elif ao_trigger == "bear_twin_peaks":
            if ao.get("bear_twin_peaks"):
                signals.append({"indicator": "Awesome Oscillator", "type": "SELL", "detail": "Bear twin peaks — second peak above zero lower than the first", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": "No bear twin peaks", "weight": 0})
        elif ao_trigger == "bull_divergence":
            if ao.get("bullish_divergence"):
                signals.append({"indicator": "Awesome Oscillator", "type": "BUY", "detail": "Bullish divergence — price made a lower low, AO a higher low", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": "No bullish divergence", "weight": 0})
        elif ao_trigger == "bear_divergence":
            if ao.get("bearish_divergence"):
                signals.append({"indicator": "Awesome Oscillator", "type": "SELL", "detail": "Bearish divergence — price made a higher high, AO a lower high", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": "No bearish divergence", "weight": 0})
        else:  # "zero_state" (default) — unchanged
            if ao_v > 0:
                signals.append({"indicator": "Awesome Oscillator", "type": "BUY", "detail": f"AO {ao_v:.3f} — above zero", "weight": 1})
                buy_score += 1
            elif ao_v < 0:
                signals.append({"indicator": "Awesome Oscillator", "type": "SELL", "detail": f"AO {ao_v:.3f} — below zero", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Awesome Oscillator", "type": "NEUTRAL", "detail": "AO at zero", "weight": 0})

    # ── Volatility-expansion + direction indicators (ATR / StdDev / Chaikin
    #    Volatility / Historical Volatility) — same heuristic for each, with
    #    bullish/bearish splits and a "contraction" (opposite) trigger. ──
    def _vol_direction_signal(name, key, expanding, close_v, close_prev):
        if not t.get(f"{key}_on", 0) or expanding is None or close_v is None or close_prev is None:
            return
        nonlocal buy_score, sell_score
        mode = t.get(f"{key}_trigger", "expansion")
        rising = close_v > close_prev
        falling = close_v < close_prev
        if mode == "bullish_expansion":
            if expanding and rising:
                signals.append({"indicator": name, "type": "BUY", "detail": f"{name} expanding with price rising", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": name, "type": "NEUTRAL", "detail": f"{name} not bullishly expanding", "weight": 0})
        elif mode == "bearish_expansion":
            if expanding and falling:
                signals.append({"indicator": name, "type": "SELL", "detail": f"{name} expanding with price falling", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": name, "type": "NEUTRAL", "detail": f"{name} not bearishly expanding", "weight": 0})
        elif mode == "contraction":
            if not expanding:
                label = "BUY" if rising else "SELL"
                signals.append({"indicator": name, "type": label, "detail": f"{name} contracting — potential squeeze, {label.lower()} bias from price", "weight": 1})
                if label == "BUY": buy_score += 1
                else: sell_score += 1
            else:
                signals.append({"indicator": name, "type": "NEUTRAL", "detail": f"{name} not contracting", "weight": 0})
        else:  # "expansion" (default) — unchanged
            if expanding and rising:
                signals.append({"indicator": name, "type": "BUY", "detail": f"{name} expanding with price rising", "weight": 1})
                buy_score += 1
            elif expanding and falling:
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
    keltner_trigger = t.get("keltner_trigger", "breakout")
    if t.get("keltner_on", 0) and keltner.get("upper") is not None and close_now is not None:
        if keltner_trigger == "bullish":
            if close_now >= keltner["upper"]:
                signals.append({"indicator": "Keltner Channels", "type": "BUY", "detail": "Breakout above the upper channel", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "No upper breakout", "weight": 0})
        elif keltner_trigger == "bearish":
            if close_now <= keltner["lower"]:
                signals.append({"indicator": "Keltner Channels", "type": "SELL", "detail": "Breakdown below the lower channel", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "No lower breakdown", "weight": 0})
        elif keltner_trigger == "middle_cross":
            bars = keltner.get("mid_cross_bars_since", 999)
            if bars <= int(t.get("keltner_mid_cross_lookback", 5)):
                if keltner.get("mid_cross_direction", 0) > 0:
                    signals.append({"indicator": "Keltner Channels", "type": "BUY", "detail": "Price crossed above the channel midline", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "Keltner Channels", "type": "SELL", "detail": "Price crossed below the channel midline", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "No recent midline cross", "weight": 0})
        elif keltner_trigger == "bull_band_riding":
            if keltner.get("walking_upper"):
                signals.append({"indicator": "Keltner Channels", "type": "BUY", "detail": "Price is riding the upper channel — strong uptrend", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "Not riding the upper channel", "weight": 0})
        elif keltner_trigger == "bear_band_riding":
            if keltner.get("walking_lower"):
                signals.append({"indicator": "Keltner Channels", "type": "SELL", "detail": "Price is riding the lower channel — strong downtrend", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "Not riding the lower channel", "weight": 0})
        elif keltner_trigger == "bull_mean_reversion":
            # Opposite read of "bearish": touching/piercing the lower band is treated as
            # oversold (expect a bounce back toward the mean) rather than a breakdown.
            if close_now <= keltner["lower"]:
                signals.append({"indicator": "Keltner Channels", "type": "BUY", "detail": "Price at/below the lower channel — oversold, expecting reversion", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "No mean-reversion setup", "weight": 0})
        elif keltner_trigger == "bear_mean_reversion":
            if close_now >= keltner["upper"]:
                signals.append({"indicator": "Keltner Channels", "type": "SELL", "detail": "Price at/above the upper channel — overbought, expecting reversion", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "No mean-reversion setup", "weight": 0})
        elif keltner_trigger == "keltner_squeeze":
            if keltner.get("squeeze_bull_release"):
                signals.append({"indicator": "Keltner Channels", "type": "BUY", "detail": "Squeeze released — breakout above the upper channel", "weight": 1})
                buy_score += 1
            elif keltner.get("squeeze_bear_release"):
                signals.append({"indicator": "Keltner Channels", "type": "SELL", "detail": "Squeeze released — breakdown below the lower channel", "weight": 1})
                sell_score += 1
            elif keltner.get("squeeze_on"):
                signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "Squeeze active — Bollinger Bands inside the channel, watching for breakout", "weight": 0})
            else:
                signals.append({"indicator": "Keltner Channels", "type": "NEUTRAL", "detail": "No squeeze", "weight": 0})
        else:  # "breakout" (default) — unchanged
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
    obv_trigger = t.get("obv_trigger", "trend")
    if t.get("obv_on", 0) and obv.get("obv") is not None and obv.get("obv_sma") is not None:
        if obv_trigger == "bullish":
            if obv["obv"] > obv["obv_sma"]:
                signals.append({"indicator": "OBV", "type": "BUY", "detail": "OBV above its average — accumulation", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "OBV", "type": "NEUTRAL", "detail": "OBV not above its average", "weight": 0})
        elif obv_trigger == "bearish":
            if obv["obv"] < obv["obv_sma"]:
                signals.append({"indicator": "OBV", "type": "SELL", "detail": "OBV below its average — distribution", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "OBV", "type": "NEUTRAL", "detail": "OBV not below its average", "weight": 0})
        elif obv_trigger == "divergence":
            if obv.get("bullish_divergence"):
                signals.append({"indicator": "OBV", "type": "BUY", "detail": "Bullish divergence — price made a lower low, OBV a higher low", "weight": 1})
                buy_score += 1
            elif obv.get("bearish_divergence"):
                signals.append({"indicator": "OBV", "type": "SELL", "detail": "Bearish divergence — price made a higher high, OBV a lower high", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "OBV", "type": "NEUTRAL", "detail": "No OBV divergence", "weight": 0})
        else:  # "trend" (default) — unchanged
            if obv["obv"] > obv["obv_sma"]:
                signals.append({"indicator": "OBV", "type": "BUY", "detail": "OBV above its average — accumulation", "weight": 1})
                buy_score += 1
            elif obv["obv"] < obv["obv_sma"]:
                signals.append({"indicator": "OBV", "type": "SELL", "detail": "OBV below its average — distribution", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "OBV", "type": "NEUTRAL", "detail": "OBV at its average", "weight": 0})

    # ── VWAP ──────────────────────────────────────────────────────────────────
    vwap = indicators.get("vwap", {})
    vwap_v = vwap.get("value")
    vwap_trigger = t.get("vwap_trigger", "position")
    if t.get("vwap_on", 0) and vwap_v is not None and close_now is not None:
        if vwap_trigger == "bullish":
            if close_now > vwap_v:
                signals.append({"indicator": "VWAP", "type": "BUY", "detail": "Price above VWAP", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "VWAP", "type": "NEUTRAL", "detail": "Price not above VWAP", "weight": 0})
        elif vwap_trigger == "bearish":
            if close_now < vwap_v:
                signals.append({"indicator": "VWAP", "type": "SELL", "detail": "Price below VWAP", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "VWAP", "type": "NEUTRAL", "detail": "Price not below VWAP", "weight": 0})
        elif vwap_trigger == "band_touch":
            upper_band, lower_band = vwap.get("upper_band"), vwap.get("lower_band")
            if upper_band is not None and close_now >= upper_band:
                signals.append({"indicator": "VWAP", "type": "SELL", "detail": "Price touched the upper VWAP band — overextended", "weight": 1})
                sell_score += 1
            elif lower_band is not None and close_now <= lower_band:
                signals.append({"indicator": "VWAP", "type": "BUY", "detail": "Price touched the lower VWAP band — overextended", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "VWAP", "type": "NEUTRAL", "detail": "Price within the VWAP band", "weight": 0})
        elif vwap_trigger == "pullback_buy":
            prev_close, prev_value = vwap.get("prev_close"), vwap.get("prev_value")
            if (prev_close is not None and prev_value is not None
                    and prev_close <= prev_value and close_now > vwap_v):
                signals.append({"indicator": "VWAP", "type": "BUY", "detail": "Price pulled back to VWAP and reclaimed it", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "VWAP", "type": "NEUTRAL", "detail": "No VWAP pullback-and-reclaim", "weight": 0})
        elif vwap_trigger == "pullback_sell":
            prev_close, prev_value = vwap.get("prev_close"), vwap.get("prev_value")
            if (prev_close is not None and prev_value is not None
                    and prev_close >= prev_value and close_now < vwap_v):
                signals.append({"indicator": "VWAP", "type": "SELL", "detail": "Price pulled back to VWAP and rejected it", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "VWAP", "type": "NEUTRAL", "detail": "No VWAP pullback-and-rejection", "weight": 0})
        else:  # "position" (default) — unchanged
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
    ad_trigger = t.get("ad_trigger", "trend")
    if t.get("ad_on", 0) and ad.get("ad") is not None and ad.get("ad_sma") is not None:
        if ad_trigger == "bullish":
            if ad["ad"] > ad["ad_sma"]:
                signals.append({"indicator": "A/D Line", "type": "BUY", "detail": "A/D Line above its average — accumulation", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "A/D Line", "type": "NEUTRAL", "detail": "A/D Line not above its average", "weight": 0})
        elif ad_trigger == "bearish":
            if ad["ad"] < ad["ad_sma"]:
                signals.append({"indicator": "A/D Line", "type": "SELL", "detail": "A/D Line below its average — distribution", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "A/D Line", "type": "NEUTRAL", "detail": "A/D Line not below its average", "weight": 0})
        elif ad_trigger == "divergence":
            if ad.get("bullish_divergence"):
                signals.append({"indicator": "A/D Line", "type": "BUY", "detail": "Bullish divergence — price made a lower low, A/D Line a higher low", "weight": 1})
                buy_score += 1
            elif ad.get("bearish_divergence"):
                signals.append({"indicator": "A/D Line", "type": "SELL", "detail": "Bearish divergence — price made a higher high, A/D Line a lower high", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "A/D Line", "type": "NEUTRAL", "detail": "No A/D Line divergence", "weight": 0})
        else:  # "trend" (default) — unchanged
            if ad["ad"] > ad["ad_sma"]:
                signals.append({"indicator": "A/D Line", "type": "BUY", "detail": "A/D Line above its average — accumulation", "weight": 1})
                buy_score += 1
            elif ad["ad"] < ad["ad_sma"]:
                signals.append({"indicator": "A/D Line", "type": "SELL", "detail": "A/D Line below its average — distribution", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "A/D Line", "type": "NEUTRAL", "detail": "A/D Line at its average", "weight": 0})

    # ── Chaikin Money Flow ────────────────────────────────────────────────────
    cmf = indicators.get("cmf", {})
    cmf_v = cmf.get("value")
    cmf_trigger = t.get("cmf_trigger", "threshold")
    if t.get("cmf_on", 0) and cmf_v is not None:
        if cmf_trigger == "bullish":
            if cmf_v > t["cmf_threshold"]:
                signals.append({"indicator": "CMF", "type": "BUY", "detail": f"CMF {cmf_v:.2f} — buying pressure", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "CMF", "type": "NEUTRAL", "detail": f"CMF {cmf_v:.2f} — no buying pressure", "weight": 0})
        elif cmf_trigger == "bearish":
            if cmf_v < -t["cmf_threshold"]:
                signals.append({"indicator": "CMF", "type": "SELL", "detail": f"CMF {cmf_v:.2f} — selling pressure", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "CMF", "type": "NEUTRAL", "detail": f"CMF {cmf_v:.2f} — no selling pressure", "weight": 0})
        elif cmf_trigger == "centerline_cross":
            bars = cmf.get("centerline_bars_since", 999)
            if bars <= int(t.get("cmf_centerline_lookback", 5)):
                if cmf.get("centerline_direction", 0) > 0:
                    signals.append({"indicator": "CMF", "type": "BUY", "detail": "CMF crossed above zero", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "CMF", "type": "SELL", "detail": "CMF crossed below zero", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "CMF", "type": "NEUTRAL", "detail": "No recent centerline cross", "weight": 0})
        else:  # "threshold" (default) — unchanged
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
    vol_profile_trigger = t.get("vol_profile_trigger", "position")
    if t.get("vol_profile_on", 0) and vp.get("poc") is not None and close_now is not None:
        if vol_profile_trigger == "bullish":
            if close_now > vp["poc"]:
                signals.append({"indicator": "Volume Profile", "type": "BUY", "detail": "Price above the point of control", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Volume Profile", "type": "NEUTRAL", "detail": "Price not above the point of control", "weight": 0})
        elif vol_profile_trigger == "bearish":
            if close_now < vp["poc"]:
                signals.append({"indicator": "Volume Profile", "type": "SELL", "detail": "Price below the point of control", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Volume Profile", "type": "NEUTRAL", "detail": "Price not below the point of control", "weight": 0})
        elif vol_profile_trigger == "poc_breakout":
            bars = vp.get("breakout_bars_since", 999)
            if bars <= int(t.get("vol_profile_breakout_lookback", 5)):
                if vp.get("breakout_direction", 0) > 0:
                    signals.append({"indicator": "Volume Profile", "type": "BUY", "detail": "Price crossed above the point of control", "weight": 1})
                    buy_score += 1
                else:
                    signals.append({"indicator": "Volume Profile", "type": "SELL", "detail": "Price crossed below the point of control", "weight": 1})
                    sell_score += 1
            else:
                signals.append({"indicator": "Volume Profile", "type": "NEUTRAL", "detail": "No recent POC cross", "weight": 0})
        else:  # "position" (default) — unchanged
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
    fib_trigger = t.get("fib_trigger", "bounce_reject")
    if (t.get("fib_on", 0) and nearest is not None and dist_pct is not None
            and close_now is not None and prev_close is not None):
        near_level = dist_pct <= t["fib_tolerance_pct"]
        if fib_trigger == "bullish_bounce":
            if near_level and trend == "up" and close_now > prev_close:
                signals.append({"indicator": "Fibonacci", "type": "BUY", "detail": f"Bounce off {nearest} retracement support", "weight": 1})
                buy_score += 1
            else:
                signals.append({"indicator": "Fibonacci", "type": "NEUTRAL", "detail": "No bullish bounce", "weight": 0})
        elif fib_trigger == "bearish_reject":
            if near_level and trend == "down" and close_now < prev_close:
                signals.append({"indicator": "Fibonacci", "type": "SELL", "detail": f"Rejected at {nearest} retracement resistance", "weight": 1})
                sell_score += 1
            else:
                signals.append({"indicator": "Fibonacci", "type": "NEUTRAL", "detail": "No bearish rejection", "weight": 0})
        elif fib_trigger == "any_touch":
            if near_level:
                label = "BUY" if trend == "up" else "SELL"
                signals.append({"indicator": "Fibonacci", "type": label, "detail": f"Price near {nearest} retracement level", "weight": 1})
                if label == "BUY": buy_score += 1
                else: sell_score += 1
            else:
                signals.append({"indicator": "Fibonacci", "type": "NEUTRAL", "detail": "No level touch", "weight": 0})
        else:  # "bounce_reject" (default) — unchanged
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
