from __future__ import annotations
import pandas as pd
from api.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_moving_averages, calculate_volume_indicators,
)
from api.signals import score_signals, DEFAULT_THRESHOLDS


def run_backtest(
    df: pd.DataFrame,
    thresholds: dict | None = None,
    calc_params: dict | None = None,
    stop_loss_pct: float = 2.0,
    take_profit_pct: float = 4.0,
    min_confidence: float = 60.0,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Bar-by-bar backtest using the existing indicator + signal pipeline.
    Returns (trades, equity_curve, bah_curve) where bah = buy-and-hold baseline.
    Entry at close when BUY fires; exit at close on SELL, or intrabar SL/TP.
    """
    t  = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    cp = calc_params or {}

    macd_fast   = int(cp.get("macd_fast",   12))
    macd_slow   = int(cp.get("macd_slow",   26))
    macd_signal = int(cp.get("macd_signal",  9))
    bb_length   = int(cp.get("bb_length",   20))
    bb_std      = float(cp.get("bb_std",    2.0))
    ema_short   = int(cp.get("ema_short",    9))
    ema_long    = int(cp.get("ema_long",    21))

    # ── Compute full indicator series upfront (O(n), not O(n²)) ──────────
    rsi_s   = calculate_rsi(df)
    macd_df = calculate_macd(df, fast=macd_fast, slow=macd_slow, signal=macd_signal)
    bb_df   = calculate_bollinger_bands(df, length=bb_length, std=bb_std)
    mas_df  = calculate_moving_averages(df, ema_short=ema_short, ema_long=ema_long)
    vol_df  = calculate_volume_indicators(df)

    combined = pd.concat(
        [df[["Open", "High", "Low", "Close", "Volume"]],
         mas_df, vol_df, rsi_s.rename("RSI"), macd_df, bb_df],
        axis=1,
    ).copy()

    macd_cols     = list(macd_df.columns)
    bb_cols       = list(bb_df.columns)
    ema_sc        = f"EMA_{ema_short}"
    ema_lc        = f"EMA_{ema_long}"
    macd_line_col = macd_cols[0] if macd_cols else None
    macd_sig_col  = macd_cols[2] if len(macd_cols) > 2 else None

    # Precompute crossover age at every bar
    ema_cross  = _bars_since_cross_series(combined[ema_sc],        combined[ema_lc])
    ma_cross   = _bars_since_cross_series(combined["MA_20"],        combined["MA_50"])
    macd_cross = (
        _bars_since_cross_series(combined[macd_line_col], combined[macd_sig_col])
        if macd_line_col and macd_sig_col
        else pd.Series(999, index=combined.index)
    )

    warmup = max(50, macd_slow + macd_signal + 5, bb_length + 5)

    # ── Simulation ────────────────────────────────────────────────────────
    trades: list[dict] = []
    equity      = 1.0
    equity_curve: list[dict] = []
    position: dict | None = None

    # Buy-and-hold baseline (normalised to 1.0 at warmup bar)
    bah_curve: list[dict] = []
    bah_start: float | None = None

    for i in range(warmup, len(combined)):
        row      = combined.iloc[i]
        date_str = str(combined.index[i])

        close = _sf(row.get("Close"))
        high  = _sf(row.get("High"))
        low   = _sf(row.get("Low"))
        if close is None or high is None or low is None:
            equity_curve.append({"date": date_str, "equity": round(equity, 6)})
            bah_curve.append({"date": date_str, "equity": round(bah_start or 1.0, 6)})
            continue

        # Buy-and-hold reference
        if bah_start is None:
            bah_start = close
        bah_equity = close / bah_start
        bah_curve.append({"date": date_str, "equity": round(bah_equity, 6)})

        # Resolve per-bar indicator values
        esn = _sf(row.get(ema_sc))
        eln = _sf(row.get(ema_lc))
        m20 = _sf(row.get("MA_20"))
        m50 = _sf(row.get("MA_50"))
        mln = _sf(row.get(macd_line_col)) if macd_line_col else None
        msn = _sf(row.get(macd_sig_col))  if macd_sig_col  else None

        vol_sma = _sf(row.get("Vol_SMA_20"))
        vol_now = _sf(row.get("Volume"))

        indicators = {
            "rsi": _sf(row.get("RSI")),
            "macd": {
                "macd":      mln,
                "histogram": _sf(row.get(macd_cols[1]) if len(macd_cols) > 1 else None),
                "signal":    msn,
            },
            "bollinger_bands": {
                "lower":     _sf(row.get(bb_cols[0]) if bb_cols else None),
                "mid":       _sf(row.get(bb_cols[1]) if len(bb_cols) > 1 else None),
                "upper":     _sf(row.get(bb_cols[2]) if len(bb_cols) > 2 else None),
                "bandwidth": _sf(row.get(bb_cols[3]) if len(bb_cols) > 3 else None),
                "percent_b": _sf(row.get(bb_cols[4]) if len(bb_cols) > 4 else None),
            },
            "moving_averages": {
                "ma_20":    m20, "ma_50": m50,
                "ma_200":   _sf(row.get("MA_200")),
                "ema_short": esn, "ema_long": eln,
            },
            "volume": {
                "current": vol_now, "sma_20": vol_sma,
                "obv":     _sf(row.get("OBV")),
                "ratio":   _sf(vol_now / vol_sma if (vol_sma and vol_sma != 0 and vol_now is not None) else None),
            },
            "price": {
                "close": close, "open": _sf(row.get("Open")),
                "high": high,   "low":  low,
            },
            "crossovers": {
                "ema_bars_since_cross":  int(ema_cross.iloc[i]),
                "ema_direction":         1 if (esn and eln and esn > eln) else -1,
                "ma_bars_since_cross":   int(ma_cross.iloc[i]),
                "ma_direction":          1 if (m20 and m50 and m20 > m50) else -1,
                "macd_bars_since_cross": int(macd_cross.iloc[i]),
                "macd_direction":        1 if (mln and msn and mln > msn) else -1,
            },
        }

        result     = score_signals(indicators, t)
        overall    = result["overall"]
        confidence = result["confidence"]

        # ── Manage open position ──────────────────────────────────────────
        if position is not None:
            ep       = position["entry_price"]
            sl_price = ep * (1 - stop_loss_pct    / 100)
            tp_price = ep * (1 + take_profit_pct  / 100)

            exit_reason = exit_price = None

            if low <= sl_price:
                exit_reason = "Stop Loss"
                exit_price  = max(low, sl_price)
            elif high >= tp_price:
                exit_reason = "Take Profit"
                exit_price  = min(high, tp_price)
            elif overall == "SELL" and confidence >= min_confidence:
                exit_reason = "Signal"
                exit_price  = close

            if exit_reason:
                ret     = (exit_price - ep) / ep * 100
                equity *= 1 + ret / 100
                trades.append({
                    "entry_date":  position["entry_date"],
                    "exit_date":   date_str,
                    "entry_price": round(ep, 4),
                    "exit_price":  round(exit_price, 4),
                    "return_pct":  round(ret, 2),
                    "exit_reason": exit_reason,
                })
                position = None

        else:
            if overall == "BUY" and confidence >= min_confidence:
                position = {"entry_price": close, "entry_date": date_str}

        equity_curve.append({"date": date_str, "equity": round(equity, 6)})

    # Close any position still open at end of data
    if position is not None:
        lc  = _sf(combined.iloc[-1].get("Close")) or position["entry_price"]
        ret = (lc - position["entry_price"]) / position["entry_price"] * 100
        equity *= 1 + ret / 100
        trades.append({
            "entry_date":  position["entry_date"],
            "exit_date":   str(combined.index[-1]),
            "entry_price": round(position["entry_price"], 4),
            "exit_price":  round(lc, 4),
            "return_pct":  round(ret, 2),
            "exit_reason": "End of Data",
        })
        if equity_curve:
            equity_curve[-1]["equity"] = round(equity, 6)

    return trades, equity_curve, bah_curve


# ── Helpers ───────────────────────────────────────────────────────────────────

def _bars_since_cross_series(a: pd.Series, b: pd.Series) -> pd.Series:
    """O(n) precomputation: how many bars since a last crossed b at each index."""
    result     = [999] * len(a)
    bars_since = 999
    prev_sign  = None
    for i in range(len(a)):
        av = a.iloc[i]
        bv = b.iloc[i]
        if av != av or bv != bv:   # NaN check without importing math
            result[i] = 999
            continue
        curr_sign = av > bv
        if prev_sign is not None and curr_sign != prev_sign:
            bars_since = 0
        result[i] = bars_since
        if bars_since < 999:
            bars_since += 1
        prev_sign = curr_sign
    return pd.Series(result, index=a.index, dtype=int)


def _sf(val):
    try:
        if val is None:
            return None
        v = float(val)
        return None if v != v else round(v, 6)  # NaN → None
    except Exception:
        return None
