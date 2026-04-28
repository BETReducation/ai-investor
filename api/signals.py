from __future__ import annotations
from typing import Any


DEFAULT_THRESHOLDS = {
    "rsi_oversold": 30,
    "rsi_overbought": 70,
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
}


def score_signals(indicators: dict, thresholds: dict | None = None) -> dict:
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    signals: list[dict] = []
    buy_score = 0
    sell_score = 0

    rsi = indicators.get("rsi")
    if t.get("rsi_on", 1) and rsi is not None:
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
    if t.get("macd_on", 1) and macd_val is not None and macd_sig_val is not None:
        crossovers = indicators.get("crossovers", {})
        macd_lookback = int(t.get("macd_cross_lookback", 5))
        macd_bars = crossovers.get("macd_bars_since_cross", 999)
        macd_dir = crossovers.get("macd_direction", 0)
        if macd_bars <= macd_lookback:
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
    if t.get("bb_on", 1) and pct_b is not None:
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
    if t.get("ma_on", 1):
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
