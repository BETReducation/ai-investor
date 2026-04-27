from __future__ import annotations
from typing import Any


DEFAULT_THRESHOLDS = {
    "rsi_oversold": 30,
    "rsi_overbought": 70,
    "volume_surge": 1.5,       # volume / 20-day avg
    "macd_threshold": 0,
    "bb_oversold": 0.2,        # percent_b below this = oversold
    "bb_overbought": 0.8,      # percent_b above this = overbought
}


def score_signals(indicators: dict, thresholds: dict | None = None) -> dict:
    t = {**DEFAULT_THRESHOLDS, **(thresholds or {})}

    signals: list[dict] = []
    buy_score = 0
    sell_score = 0

    rsi = indicators.get("rsi")
    if rsi is not None:
        if rsi < t["rsi_oversold"]:
            signals.append({"indicator": "RSI", "type": "BUY", "detail": f"RSI {rsi:.1f} — oversold (<{t['rsi_oversold']})", "weight": 2})
            buy_score += 2
        elif rsi > t["rsi_overbought"]:
            signals.append({"indicator": "RSI", "type": "SELL", "detail": f"RSI {rsi:.1f} — overbought (>{t['rsi_overbought']})", "weight": 2})
            sell_score += 2
        else:
            signals.append({"indicator": "RSI", "type": "NEUTRAL", "detail": f"RSI {rsi:.1f} — neutral", "weight": 0})

    macd = indicators.get("macd", {})
    macd_val = macd.get("macd")
    macd_hist = macd.get("histogram")
    macd_sig = macd.get("signal")
    if macd_val is not None and macd_sig is not None:
        if macd_val > macd_sig and macd_hist and macd_hist > t["macd_threshold"]:
            signals.append({"indicator": "MACD", "type": "BUY", "detail": "MACD above signal line — bullish crossover", "weight": 2})
            buy_score += 2
        elif macd_val < macd_sig and macd_hist and macd_hist < t["macd_threshold"]:
            signals.append({"indicator": "MACD", "type": "SELL", "detail": "MACD below signal line — bearish crossover", "weight": 2})
            sell_score += 2
        else:
            signals.append({"indicator": "MACD", "type": "NEUTRAL", "detail": "MACD — no clear crossover", "weight": 0})

    bb = indicators.get("bollinger_bands", {})
    pct_b = bb.get("percent_b")
    close = indicators.get("price", {}).get("close")
    bb_lower = bb.get("lower")
    bb_upper = bb.get("upper")
    if pct_b is not None:
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
    ema9 = mas.get("ema_9")
    ema21 = mas.get("ema_21")
    if close and ma20 and ma50:
        if close > ma20 and ma20 > ma50:
            signals.append({"indicator": "MA", "type": "BUY", "detail": "Price > MA20 > MA50 — bullish alignment", "weight": 1})
            buy_score += 1
        elif close < ma20 and ma20 < ma50:
            signals.append({"indicator": "MA", "type": "SELL", "detail": "Price < MA20 < MA50 — bearish alignment", "weight": 1})
            sell_score += 1
        else:
            signals.append({"indicator": "MA", "type": "NEUTRAL", "detail": "MA — mixed alignment", "weight": 0})

    if close and ema9 and ema21:
        if ema9 > ema21:
            signals.append({"indicator": "EMA", "type": "BUY", "detail": "EMA9 > EMA21 — short-term bullish", "weight": 1})
            buy_score += 1
        else:
            signals.append({"indicator": "EMA", "type": "SELL", "detail": "EMA9 < EMA21 — short-term bearish", "weight": 1})
            sell_score += 1

    vol = indicators.get("volume", {})
    vol_ratio = vol.get("ratio")
    if vol_ratio is not None and vol_ratio > t["volume_surge"]:
        label = "BUY" if buy_score >= sell_score else "SELL"
        signals.append({"indicator": "Volume", "type": label, "detail": f"Volume surge {vol_ratio:.1f}x avg — confirms {label.lower()} pressure", "weight": 1})
        if label == "BUY":
            buy_score += 1
        else:
            sell_score += 1
    elif vol_ratio is not None:
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
