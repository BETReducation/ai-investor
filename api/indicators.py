import numpy as np
import pandas as pd
import pandas_ta as ta


# ── Legacy wrappers (used by backtest.py) ─────────────────────────────────────

def _rsi_series(close: pd.Series, length: int = 14, smoothing: str = "wilder") -> pd.Series:
    delta = close.diff()
    gain  = delta.clip(lower=0)
    loss  = (-delta).clip(lower=0)
    if smoothing == "ema":
        avg_gain = gain.ewm(span=length, adjust=False).mean()
        avg_loss = loss.ewm(span=length, adjust=False).mean()
    elif smoothing == "sma":
        avg_gain = gain.rolling(length).mean()
        avg_loss = loss.rolling(length).mean()
    else:  # wilder / rma (default — matches TradingView)
        avg_gain = gain.ewm(alpha=1 / length, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1 / length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, float("nan"))
    return 100 - (100 / (1 + rs))


def calculate_rsi(df: pd.DataFrame, length: int = 14, smoothing: str = "wilder") -> pd.Series:
    return _rsi_series(df["Close"], length=length, smoothing=smoothing)


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    return ta.macd(df["Close"], fast=fast, slow=slow, signal=signal)


def calculate_bollinger_bands(df: pd.DataFrame, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    return ta.bbands(df["Close"], length=length, std=std)


def calculate_moving_averages(df: pd.DataFrame, ema_short: int = 9, ema_long: int = 21) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    result["MA_20"]  = ta.sma(df["Close"], length=20)
    result["MA_50"]  = ta.sma(df["Close"], length=50)
    result["MA_200"] = ta.sma(df["Close"], length=200)
    result[f"EMA_{ema_short}"] = ta.ema(df["Close"], length=ema_short)
    result[f"EMA_{ema_long}"]  = ta.ema(df["Close"], length=ema_long)
    return result


def calculate_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    result["Volume"]     = df["Volume"]
    result["Vol_SMA_20"] = ta.sma(df["Volume"], length=20)
    result["OBV"]        = ta.obv(df["Close"], df["Volume"])
    return result


def _safe_float(val):
    try:
        if val is None:
            return None
        f = float(val)
        return None if pd.isna(f) else round(f, 6)
    except Exception:
        return None


def _bars_since_cross(a: pd.Series, b: pd.Series) -> int:
    diff = (a - b).dropna()
    if len(diff) < 2:
        return 999
    signs = diff > 0
    changed = signs != signs.shift()
    changed.iloc[0] = False
    crosses = changed[changed]
    if crosses.empty:
        return 999
    last_cross_loc = diff.index.get_loc(crosses.index[-1])
    return len(diff) - 1 - last_cross_loc


def _swing_pivots(hi, lo, w: int, start: int, end: int):
    """Confirmed swing pivots in [start, end): a bar is a swing low if it is the
    strict min of `w` bars on each side (swing high = strict max). Returns
    (lows, highs) as lists of (idx, price)."""
    piv_lows, piv_highs = [], []
    for i in range(start, end):
        seg_lo = lo[i - w:i + w + 1]
        if lo[i] == seg_lo.min() and seg_lo.argmin() == w:
            piv_lows.append((i, lo[i]))
        seg_hi = hi[i - w:i + w + 1]
        if hi[i] == seg_hi.max() and seg_hi.argmax() == w:
            piv_highs.append((i, hi[i]))
    return piv_lows, piv_highs


def _match_inverse_hs(piv_lows, piv_highs, cur_idx: int):
    """Find the most recent valid inverse head-and-shoulders in the given confirmed
    pivots and return its neckline projected to `cur_idx`, or None. A valid pattern
    is three swing lows (left shoulder / head / right shoulder) with the head lowest,
    the shoulders roughly level, and a swing high in each gap forming the neckline."""
    if len(piv_lows) < 3:
        return None
    best = None
    recent_lows = piv_lows[-8:]
    for a in range(len(recent_lows)):
        for b in range(a + 1, len(recent_lows)):
            for c in range(b + 1, len(recent_lows)):
                ls_i, ls_p = recent_lows[a]
                h_i,  h_p  = recent_lows[b]
                rs_i, rs_p = recent_lows[c]
                if not (h_p < ls_p and h_p < rs_p):               # head is lowest
                    continue
                if abs(ls_p - rs_p) / ((ls_p + rs_p) / 2.0) > 0.10:  # shoulders ~level
                    continue
                gap1 = [(pi, pp) for pi, pp in piv_highs if ls_i < pi < h_i]
                gap2 = [(pi, pp) for pi, pp in piv_highs if h_i  < pi < rs_i]
                if not gap1 or not gap2:                           # a neckline high in each gap
                    continue
                h1i, h1p = max(gap1, key=lambda tt: tt[1])
                h2i, h2p = max(gap2, key=lambda tt: tt[1])
                if not (h_p < h1p and h_p < h2p):                  # head below the neckline
                    continue
                if best is None or rs_i > best["rs_i"]:
                    best = {"rs_i": rs_i, "h1i": h1i, "h1p": h1p, "h2i": h2i, "h2p": h2p}
    if best is None:
        return None
    h1i, h1p, h2i, h2p = best["h1i"], best["h1p"], best["h2i"], best["h2p"]
    if h2i == h1i:
        return max(h1p, h2p)
    slope = (h2p - h1p) / (h2i - h1i)
    return h1p + slope * (cur_idx - h1i)


def _detect_inverse_head_shoulders(high: pd.Series, low: pd.Series, close: pd.Series,
                                   pivot: int = 3, lookback: int = 90) -> dict:
    """Heuristic inverse head-and-shoulders detector (point-in-time, latest bar).

    Projects the neckline (the line through the two swing highs) forward to the
    latest bar — the level a long entry watches. `detected` is False for anything
    it can't confirm; callers decide the trigger (touch vs. break) using
    `pct_from_neckline` / `broke_neckline`.
    """
    result = {
        "detected": False, "neckline": None, "close": None,
        "pct_from_neckline": None, "broke_neckline": False,
    }
    try:
        n = len(close)
        if n < 20:
            return result
        w = max(2, int(pivot))
        lookback = max(30, int(lookback))
        lo = low.to_numpy(dtype=float)
        hi = high.to_numpy(dtype=float)
        cl = close.to_numpy(dtype=float)
        start = max(w, n - lookback)
        piv_lows, piv_highs = _swing_pivots(hi, lo, w, start, n - w)
        neckline = _match_inverse_hs(piv_lows, piv_highs, n - 1)
        if neckline is None or neckline <= 0:
            return result
        last = cl[-1]
        pct = (last - neckline) / neckline * 100.0
        result.update({
            "detected": True,
            "neckline": round(float(neckline), 6),
            "close": round(float(last), 6),
            "pct_from_neckline": round(float(pct), 4),
            "broke_neckline": bool(last > neckline),
        })
        return result
    except Exception:
        return result


def _inverse_hs_series(high: pd.Series, low: pd.Series, close: pd.Series,
                       pivot: int = 3, lookback: int = 90):
    """Causal (no-lookahead) per-bar inverse head-and-shoulders state, for the
    backtester. At each bar j only pivots confirmed as of j (index <= j - w) and
    within `lookback` are considered, and the neckline is projected to j.

    Returns (detected, neckline, pct_from_neckline, broke_neckline) as numpy arrays
    aligned to the input index."""
    n = len(close)
    detected  = np.zeros(n, dtype=bool)
    neckline  = np.full(n, np.nan)
    pct       = np.full(n, np.nan)
    broke     = np.zeros(n, dtype=bool)
    try:
        if n < 20:
            return detected, neckline, pct, broke
        w = max(2, int(pivot))
        lookback = max(30, int(lookback))
        lo = low.to_numpy(dtype=float)
        hi = high.to_numpy(dtype=float)
        cl = close.to_numpy(dtype=float)
        # All confirmed pivots over the whole series (computed once).
        all_lows, all_highs = _swing_pivots(hi, lo, w, w, n - w)
        for j in range(w, n):
            lo_vis = [(i, p) for i, p in all_lows  if j - lookback <= i <= j - w]
            if len(lo_vis) < 3:
                continue
            hi_vis = [(i, p) for i, p in all_highs if j - lookback <= i <= j - w]
            neck = _match_inverse_hs(lo_vis, hi_vis, j)
            if neck is None or neck <= 0:
                continue
            detected[j] = True
            neckline[j] = neck
            pct[j]      = (cl[j] - neck) / neck * 100.0
            broke[j]    = cl[j] > neck
        return detected, neckline, pct, broke
    except Exception:
        return detected, neckline, pct, broke


def _recent_ohlcv(df: pd.DataFrame, n: int = 100) -> list:
    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    subset = df[cols].tail(n).copy()
    subset = subset.loc[:, ~subset.columns.duplicated()]
    subset.index = subset.index.astype(str)
    records = subset.reset_index()
    records.rename(columns={records.columns[0]: "date"}, inplace=True)
    return records.to_dict(orient="records")


def calculate_all(
    df: pd.DataFrame,
    # Core (existing)
    rsi_length: int = 14,
    rsi_smoothing: str = "wilder",
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    bb_length: int = 20,
    bb_std: float = 2.0,
    ema_short: int = 9,
    ema_long: int = 21,
    # Stochastic
    stoch_k: int = 14,
    stoch_d: int = 3,
    stoch_smooth: int = 3,
    # Stochastic RSI
    stochrsi_length: int = 14,
    stochrsi_k: int = 3,
    stochrsi_d: int = 3,
    # Oscillators
    cci_length: int = 20,
    willr_length: int = 14,
    # Trend
    adx_length: int = 14,
    aroon_length: int = 25,
    supertrend_length: int = 10,
    supertrend_mult: float = 3.0,
    psar_start: float = 0.02,
    psar_inc: float = 0.02,
    psar_max: float = 0.2,
    # Volatility/Volume
    atr_length: int = 14,
    mfi_length: int = 14,
    # MAs
    wma_length: int = 20,
    hma_length: int = 20,
    # Momentum
    roc_length: int = 12,
    # Chart patterns
    hs_pivot: int = 3,
    hs_lookback: int = 90,
    # ── Extended set (ported from Backtester) ───────────────────────────────
    rsi_oversold: float = 30.0, rsi_overbought: float = 70.0, rsi_div_lookback: int = 5,
    macd_div_lookback: int = 5, macd_zscore_length: int = 100,
    bb_squeeze_lookback: int = 100, bb_breakout_window: int = 10,
    bb_squeeze_percentile: float = 20.0, bb_walk_min_consecutive: int = 3,
    bb_walk_tolerance_pct: float = 0.5, bb_pattern_lookback: int = 5,
    ma_type: str = "exponential",
    ma_short_length: int = 9, ma_medium_length: int = 20, ma_long_length: int = 50,
    psar_gap_lookback: int = 3,
    supertrend_gap_lookback: int = 3,
    stochrsi_div_lookback: int = 5,
    willr_oversold: float = -80.0, willr_overbought: float = -20.0,
    willr_div_lookback: int = 5, willr_confirm_lookback: int = 5,
    roc_div_lookback: int = 5, roc_momentum_lookback: int = 3,
    mfi_div_lookback: int = 5,
    hma_fast_length: int = 9, hma_slope_lookback: int = 3,
    ichimoku_tenkan: int = 9, ichimoku_kijun: int = 26, ichimoku_senkou: int = 52,
    donchian_length: int = 20,
    keltner_length: int = 20, keltner_atr_length: int = 10, keltner_mult: float = 2.0,
    keltner_walk_min_consecutive: int = 3, keltner_walk_tolerance_pct: float = 0.5,
    keltner_squeeze_lookback: int = 10,
    stdev_length: int = 20,
    chaikin_vol_ema_length: int = 10, chaikin_vol_roc_length: int = 10,
    hist_vol_length: int = 20,
    atr_trend_lookback: int = 5, stdev_trend_lookback: int = 5,
    chaikin_vol_trend_lookback: int = 5, hist_vol_trend_lookback: int = 5,
    vwap_length: int = 20, vwap_anchored: int = 0, vwap_band_pct: float = 1.0,
    ad_sma_length: int = 20, ad_div_lookback: int = 5,
    cmf_length: int = 20,
    tsi_long: int = 25, tsi_short: int = 13, tsi_signal: int = 13, tsi_div_lookback: int = 5,
    ao_fast: int = 5, ao_slow: int = 34, ao_div_lookback: int = 5, ao_twin_peaks_lookback: int = 5,
    obv_sma_length: int = 20, obv_div_lookback: int = 5,
    vol_profile_lookback: int = 50, vol_profile_bins: int = 24,
    fib_lookback: int = 50, fib_tolerance_pct: float = 0.5,
) -> dict:

    close = df["Close"]
    high  = df["High"]
    low   = df["Low"]
    vol   = df["Volume"]

    # ── Core ──────────────────────────────────────────────────────────────────
    rsi_s   = _rsi_series(close, length=rsi_length, smoothing=rsi_smoothing)
    macd_df = ta.macd(close, fast=macd_fast, slow=macd_slow, signal=macd_signal)
    bb_df   = ta.bbands(close, length=bb_length, std=bb_std)

    mas = pd.DataFrame(index=df.index)
    mas["MA_20"]  = ta.sma(close, length=20)
    mas["MA_50"]  = ta.sma(close, length=50)
    mas["MA_200"] = ta.sma(close, length=200)
    ema_sc = f"EMA_{ema_short}"
    ema_lc = f"EMA_{ema_long}"
    mas[ema_sc] = ta.ema(close, length=ema_short)
    mas[ema_lc] = ta.ema(close, length=ema_long)

    vol_df = pd.DataFrame(index=df.index)
    vol_df["Volume"]     = vol
    vol_df["Vol_SMA_20"] = ta.sma(vol, length=20)
    vol_df["OBV"]        = ta.obv(close, vol)

    # ── New indicators ────────────────────────────────────────────────────────
    def _try(fn):
        try:    return fn()
        except: return None

    stoch_df      = _try(lambda: ta.stoch(high, low, close, k=stoch_k, d=stoch_d, smooth_k=stoch_smooth))
    stochrsi_df   = _try(lambda: ta.stochrsi(close, length=stochrsi_length, rsi_length=stochrsi_length, k=stochrsi_k, d=stochrsi_d))
    cci_s         = _try(lambda: ta.cci(high, low, close, length=cci_length))
    willr_s       = _try(lambda: ta.willr(high, low, close, length=willr_length))
    adx_df        = _try(lambda: ta.adx(high, low, close, length=adx_length))
    atr_s         = _try(lambda: ta.atr(high, low, close, length=atr_length))
    mfi_s         = _try(lambda: ta.mfi(high, low, close, vol, length=mfi_length))
    vwap_s        = _try(lambda: ta.vwap(high, low, close, vol))
    psar_df       = _try(lambda: ta.psar(high, low, close, af0=psar_start, af=psar_inc, max_af=psar_max))
    supertrend_df = _try(lambda: ta.supertrend(high, low, close, length=supertrend_length, multiplier=supertrend_mult))
    aroon_df      = _try(lambda: ta.aroon(high, low, length=aroon_length))
    wma_s         = _try(lambda: ta.wma(close, length=wma_length))
    hma_s         = _try(lambda: ta.hma(close, length=hma_length))
    roc_s         = _try(lambda: ta.roc(close, length=roc_length))

    inverse_hs    = _try(lambda: _detect_inverse_head_shoulders(
        high, low, close, pivot=hs_pivot, lookback=hs_lookback)) or {
        "detected": False, "neckline": None, "close": None,
        "pct_from_neckline": None, "broke_neckline": False,
    }

    # ── Extended indicators (ported from the Backtester's extended set) ────────
    # Same calc functions Backtester already uses (below, in this file) — computed
    # independently of `combined` above so this block can't affect the existing
    # RSI/MACD/BB/MA/Volume pipeline. Only the latest bar's value/state is kept;
    # `_bars_since_cross` (defined above) gives an O(n) "bars since" int straight
    # from two full series, so no per-bar simulation loop is needed here.
    macd_line_s = macd_df.iloc[:, 0] if macd_df is not None else None
    macd_hist_s = macd_df.iloc[:, 1] if macd_df is not None and macd_df.shape[1] > 1 else None
    bb_lower_s, bb_mid_s, bb_upper_s, bb_bw_s = (None, None, None, None)
    if bb_df is not None and bb_df.shape[1] >= 4:
        bb_lower_s, bb_mid_s, bb_upper_s, bb_bw_s = bb_df.iloc[:, 0], bb_df.iloc[:, 1], bb_df.iloc[:, 2], bb_df.iloc[:, 3]

    rsi_centerline_bars = _bars_since_cross(rsi_s, pd.Series(50.0, index=rsi_s.index)) if rsi_s is not None else 999
    rsi_bull_div = rsi_bear_div = rsi_bull_fs = rsi_bear_fs = False
    if rsi_s is not None:
        d = _try(lambda: calculate_rsi_divergence(close, rsi_s, lookback=rsi_div_lookback))
        if d: rsi_bull_div, rsi_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])
        fs = _try(lambda: calculate_rsi_failure_swings(rsi_s, oversold=rsi_oversold, overbought=rsi_overbought))
        if fs: rsi_bull_fs, rsi_bear_fs = bool(fs[0].iloc[-1]), bool(fs[1].iloc[-1])

    macd_centerline_bars = macd_zscore_v = None
    macd_bull_div = macd_bear_div = macd_bull_hr = macd_bear_hr = False
    if macd_line_s is not None:
        macd_centerline_bars = _bars_since_cross(macd_line_s, pd.Series(0.0, index=macd_line_s.index))
        d = _try(lambda: calculate_macd_divergence(close, macd_line_s, lookback=macd_div_lookback))
        if d: macd_bull_div, macd_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])
        if macd_hist_s is not None:
            hr = _try(lambda: calculate_macd_histogram_reversal(macd_hist_s))
            if hr: macd_bull_hr, macd_bear_hr = bool(hr[0].iloc[-1]), bool(hr[1].iloc[-1])
        z = _try(lambda: calculate_macd_zscore(macd_line_s, length=macd_zscore_length))
        if z is not None: macd_zscore_v = _safe_float(z.iloc[-1])

    bb_bull_breakout = bb_bear_breakout = bb_walking_upper = bb_walking_lower = False
    bb_w_bottom = bb_m_top = False
    if bb_upper_s is not None:
        brk = _try(lambda: calculate_bb_squeeze_breakout(
            close, bb_upper_s, bb_lower_s, bb_bw_s,
            squeeze_lookback=bb_squeeze_lookback, squeeze_percentile=bb_squeeze_percentile,
            breakout_window=bb_breakout_window))
        if brk: bb_bull_breakout, bb_bear_breakout = bool(brk[0].iloc[-1]), bool(brk[1].iloc[-1])
        walk = _try(lambda: calculate_bb_walking_band(
            close, bb_upper_s, bb_lower_s,
            min_consecutive=bb_walk_min_consecutive, tolerance_pct=bb_walk_tolerance_pct))
        if walk: bb_walking_upper, bb_walking_lower = bool(walk[0].iloc[-1]), bool(walk[1].iloc[-1])
        pat = _try(lambda: calculate_bb_double_patterns(
            close, low, high, bb_lower_s, bb_mid_s, bb_upper_s, lookback=bb_pattern_lookback))
        if pat: bb_w_bottom, bb_m_top = bool(pat[0].iloc[-1]), bool(pat[1].iloc[-1])

    ma_short_s  = _try(lambda: calculate_ma_by_type(df, ma_short_length,  ma_type))
    ma_medium_s = _try(lambda: calculate_ma_by_type(df, ma_medium_length, ma_type))
    ma_long_s   = _try(lambda: calculate_ma_by_type(df, ma_long_length,   ma_type))
    price_ma_short_bars = _bars_since_cross(close, ma_short_s) if ma_short_s is not None else 999
    two_ma_bars         = _bars_since_cross(ma_short_s, ma_long_s) if (ma_short_s is not None and ma_long_s is not None) else 999
    three_ma_bull = three_ma_bear = False
    ma_short_v = ma_medium_v = ma_long_v = None
    if ma_short_s is not None and ma_medium_s is not None and ma_long_s is not None:
        three_ma_bull = bool(ma_short_s.iloc[-1] > ma_medium_s.iloc[-1] > ma_long_s.iloc[-1])
        three_ma_bear = bool(ma_short_s.iloc[-1] < ma_medium_s.iloc[-1] < ma_long_s.iloc[-1])
        ma_short_v  = _safe_float(ma_short_s.iloc[-1])
        ma_medium_v = _safe_float(ma_medium_s.iloc[-1])
        ma_long_v   = _safe_float(ma_long_s.iloc[-1])

    di_cross_bars = 999
    if adx_df is not None:
        _ac = list(adx_df.columns)
        _dmp = next((c for c in _ac if c.upper().startswith("DMP")), None)
        _dmn = next((c for c in _ac if c.upper().startswith("DMN")), None)
        if _dmp and _dmn:
            di_cross_bars = _bars_since_cross(adx_df[_dmp], adx_df[_dmn])

    psar_flip_bars = 999
    psar_narrowing = False
    if psar_df is not None:
        _pc = list(psar_df.columns)
        _pl = next((c for c in _pc if c.upper().startswith("PSARL")), None)
        _ps = next((c for c in _pc if c.upper().startswith("PSARS")), None)
        if _pl and _ps:
            _long_notna  = psar_df[_pl].notna()
            _short_notna = psar_df[_ps].notna()
            _psar_dir_s  = pd.Series(np.where(_long_notna, 1.0, np.where(_short_notna, -1.0, np.nan)), index=psar_df.index)
            psar_flip_bars = _bars_since_cross(_psar_dir_s, pd.Series(0.0, index=_psar_dir_s.index))
            _psar_value_s = psar_df[_pl].where(_long_notna, psar_df[_ps])
            _psar_gap_s   = (close - _psar_value_s).abs()
            if len(_psar_gap_s) > psar_gap_lookback:
                psar_narrowing = bool(_psar_gap_s.iloc[-1] < _psar_gap_s.shift(psar_gap_lookback).iloc[-1])

    st_flip_bars = 999
    st_narrowing = False
    if supertrend_df is not None:
        _sc = list(supertrend_df.columns)
        _std = next((c for c in _sc if c.upper().startswith("SUPERTD")), None)
        _stv = next((c for c in _sc if c.upper().startswith("SUPERT_")), None)
        if _std:
            st_flip_bars = _bars_since_cross(supertrend_df[_std], pd.Series(0.0, index=supertrend_df.index))
        if _stv:
            _st_gap_s = (close - supertrend_df[_stv]).abs()
            if len(_st_gap_s) > supertrend_gap_lookback:
                st_narrowing = bool(_st_gap_s.iloc[-1] < _st_gap_s.shift(supertrend_gap_lookback).iloc[-1])

    stoch_signal_bars = 999
    if stoch_df is not None and stoch_df.shape[1] >= 2:
        stoch_signal_bars = _bars_since_cross(stoch_df.iloc[:, 0], stoch_df.iloc[:, 1])

    stochrsi_signal_bars = 999
    stochrsi_bull_div = stochrsi_bear_div = False
    if stochrsi_df is not None and stochrsi_df.shape[1] >= 2:
        stochrsi_signal_bars = _bars_since_cross(stochrsi_df.iloc[:, 0], stochrsi_df.iloc[:, 1])
        d = _try(lambda: calculate_price_divergence(close, stochrsi_df.iloc[:, 0], lookback=stochrsi_div_lookback))
        if d: stochrsi_bull_div, stochrsi_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])

    cci_centerline_bars = _bars_since_cross(cci_s, pd.Series(0.0, index=cci_s.index)) if cci_s is not None else 999
    cci_breakout_bull = cci_breakout_bear = False
    if cci_s is not None and len(cci_s) > 1:
        cci_breakout_bull = bool(cci_s.iloc[-1] > 100 and cci_s.iloc[-2] <= 100)
        cci_breakout_bear = bool(cci_s.iloc[-1] < -100 and cci_s.iloc[-2] >= -100)

    willr_midline_bars = _bars_since_cross(willr_s, pd.Series(-50.0, index=willr_s.index)) if willr_s is not None else 999
    willr_bull_div = willr_bear_div = willr_bull_conf = willr_bear_conf = willr_bull_fs = willr_bear_fs = False
    if willr_s is not None:
        d = _try(lambda: calculate_price_divergence(close, willr_s, lookback=willr_div_lookback))
        if d: willr_bull_div, willr_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])
        c = _try(lambda: calculate_trend_confirmation(close, willr_s, lookback=willr_confirm_lookback))
        if c: willr_bull_conf, willr_bear_conf = bool(c[0].iloc[-1]), bool(c[1].iloc[-1])
        fs = _try(lambda: calculate_willr_failure_swings(willr_s, oversold=willr_oversold, overbought=willr_overbought))
        if fs: willr_bull_fs, willr_bear_fs = bool(fs[0].iloc[-1]), bool(fs[1].iloc[-1])

    roc_centerline_bars = _bars_since_cross(roc_s, pd.Series(0.0, index=roc_s.index)) if roc_s is not None else 999
    roc_bull_momentum = roc_bear_momentum = roc_bull_div = roc_bear_div = False
    if roc_s is not None and len(roc_s) > roc_momentum_lookback:
        _roc_prev = roc_s.shift(roc_momentum_lookback).iloc[-1]
        roc_bull_momentum = bool(roc_s.iloc[-1] > _roc_prev and _roc_prev is not None and roc_s.iloc[-1] > 0)
        roc_bear_momentum = bool(roc_s.iloc[-1] < _roc_prev and roc_s.iloc[-1] < 0)
        d = _try(lambda: calculate_price_divergence(close, roc_s, lookback=roc_div_lookback))
        if d: roc_bull_div, roc_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])

    mfi_centerline_bars = _bars_since_cross(mfi_s, pd.Series(50.0, index=mfi_s.index)) if mfi_s is not None else 999
    mfi_bull_div = mfi_bear_div = False
    if mfi_s is not None:
        d = _try(lambda: calculate_price_divergence(close, mfi_s, lookback=mfi_div_lookback))
        if d: mfi_bull_div, mfi_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])

    hma_fast_s = _try(lambda: ta.hma(close, length=hma_fast_length))
    hma_fast_v = _safe_float(hma_fast_s.iloc[-1]) if hma_fast_s is not None else None
    hma_slope_bull = hma_slope_bear = False
    hma_price_bars = hma_two_bars = 999
    if hma_s is not None:
        hma_price_bars = _bars_since_cross(close, hma_s)
        if len(hma_s) > hma_slope_lookback:
            _hma_prev = hma_s.shift(hma_slope_lookback).iloc[-1]
            hma_slope_bull = bool(hma_s.iloc[-1] > _hma_prev)
            hma_slope_bear = bool(hma_s.iloc[-1] < _hma_prev)
        if hma_fast_s is not None:
            hma_two_bars = _bars_since_cross(hma_fast_s, hma_s)

    ichimoku_df = _try(lambda: calculate_ichimoku(df, tenkan=ichimoku_tenkan, kijun=ichimoku_kijun, senkou=ichimoku_senkou))
    tk_cross_bars = 999
    ich_cloud_bullish = ich_cloud_bearish = None
    ich_tenkan_v = ich_kijun_v = ich_senkou_a_v = ich_senkou_b_v = None
    if ichimoku_df is not None:
        tk_cross_bars = _bars_since_cross(ichimoku_df["ICH_tenkan"], ichimoku_df["ICH_kijun"])
        ich_tenkan_v   = _safe_float(ichimoku_df["ICH_tenkan"].iloc[-1])
        ich_kijun_v    = _safe_float(ichimoku_df["ICH_kijun"].iloc[-1])
        ich_senkou_a_v = _safe_float(ichimoku_df["ICH_senkou_a"].iloc[-1])
        ich_senkou_b_v = _safe_float(ichimoku_df["ICH_senkou_b"].iloc[-1])
        _cloud_top    = ichimoku_df[["ICH_senkou_a", "ICH_senkou_b"]].max(axis=1)
        _cloud_bottom = ichimoku_df[["ICH_senkou_a", "ICH_senkou_b"]].min(axis=1)
        if not pd.isna(_cloud_top.iloc[-1]):
            ich_cloud_bullish = bool(close.iloc[-1] > _cloud_top.iloc[-1])
            ich_cloud_bearish = bool(close.iloc[-1] < _cloud_bottom.iloc[-1])

    donchian_df = _try(lambda: calculate_donchian(df, length=donchian_length))
    donchian_mid_bars = donchian_upper_bars = donchian_lower_bars = 999
    dc_upper_v = dc_mid_v = dc_lower_v = None
    if donchian_df is not None:
        donchian_mid_bars   = _bars_since_cross(close, donchian_df["DC_mid"])
        donchian_upper_bars = _bars_since_cross(close, donchian_df["DC_upper"])
        donchian_lower_bars = _bars_since_cross(close, donchian_df["DC_lower"])
        dc_upper_v = _safe_float(donchian_df["DC_upper"].iloc[-1])
        dc_mid_v   = _safe_float(donchian_df["DC_mid"].iloc[-1])
        dc_lower_v = _safe_float(donchian_df["DC_lower"].iloc[-1])

    keltner_df = _try(lambda: calculate_keltner(df, length=keltner_length, atr_length=keltner_atr_length, mult=keltner_mult))
    keltner_mid_bars = 999
    kc_upper_v = kc_mid_v = kc_lower_v = None
    kc_walking_upper = kc_walking_lower = kc_squeeze_on = kc_squeeze_bull = kc_squeeze_bear = False
    if keltner_df is not None:
        keltner_mid_bars = _bars_since_cross(close, keltner_df["KC_mid"])
        kc_upper_v = _safe_float(keltner_df["KC_upper"].iloc[-1])
        kc_mid_v   = _safe_float(keltner_df["KC_mid"].iloc[-1])
        kc_lower_v = _safe_float(keltner_df["KC_lower"].iloc[-1])
        walk = _try(lambda: calculate_bb_walking_band(
            close, keltner_df["KC_upper"], keltner_df["KC_lower"],
            min_consecutive=keltner_walk_min_consecutive, tolerance_pct=keltner_walk_tolerance_pct))
        if walk: kc_walking_upper, kc_walking_lower = bool(walk[0].iloc[-1]), bool(walk[1].iloc[-1])
        if bb_upper_s is not None:
            sq = _try(lambda: calculate_keltner_squeeze(
                close, bb_upper_s, bb_lower_s, keltner_df["KC_upper"], keltner_df["KC_lower"],
                breakout_window=keltner_squeeze_lookback))
            if sq: kc_squeeze_on, kc_squeeze_bull, kc_squeeze_bear = bool(sq[0].iloc[-1]), bool(sq[1].iloc[-1]), bool(sq[2].iloc[-1])

    stdev_s       = _try(lambda: calculate_stdev(df, length=stdev_length))
    chaikin_vol_s = _try(lambda: calculate_chaikin_volatility(df, ema_length=chaikin_vol_ema_length, roc_length=chaikin_vol_roc_length))
    hist_vol_s    = _try(lambda: calculate_historical_volatility(df, length=hist_vol_length))

    def _vol_expansion(s, trend_lb):
        """(value, is_expanding, bullish_expansion, bearish_expansion, is_contracting)"""
        if s is None or len(s) < 11:
            return None, None, False, False, None
        sma = s.rolling(10).mean()
        v, sma_v = _safe_float(s.iloc[-1]), _safe_float(sma.iloc[-1])
        expanding = bool(v is not None and sma_v is not None and v > sma_v)
        contracting = bool(v is not None and sma_v is not None and v < sma_v)
        bull = bear = False
        if expanding and len(close) > trend_lb:
            prev_close = close.shift(trend_lb).iloc[-1]
            bull = bool(close.iloc[-1] > prev_close)
            bear = bool(close.iloc[-1] < prev_close)
        return v, expanding, bull, bear, contracting

    _, _, atr_bull_exp, atr_bear_exp, atr_contracting = _vol_expansion(atr_s, atr_trend_lookback)
    stdev_v, stdev_expanding, stdev_bull_exp, stdev_bear_exp, stdev_contracting = _vol_expansion(stdev_s, stdev_trend_lookback)
    chaikin_vol_v, chaikin_vol_expanding, chaikin_vol_bull_exp, chaikin_vol_bear_exp, chaikin_vol_contracting = _vol_expansion(chaikin_vol_s, chaikin_vol_trend_lookback)
    hist_vol_v, hist_vol_expanding, hist_vol_bull_exp, hist_vol_bear_exp, hist_vol_contracting = _vol_expansion(hist_vol_s, hist_vol_trend_lookback)

    vwap_roll_s = _try(lambda: calculate_rolling_vwap(df, length=vwap_length, anchored=bool(vwap_anchored)))
    vwap_roll_v = vwap_bull = vwap_bear = vwap_band_touch = None
    if vwap_roll_s is not None:
        vwap_roll_v = _safe_float(vwap_roll_s.iloc[-1])
        if vwap_roll_v is not None:
            vwap_bull = close.iloc[-1] > vwap_roll_v
            vwap_bear = close.iloc[-1] < vwap_roll_v
            _band = vwap_roll_v * vwap_band_pct / 100
            vwap_band_touch = bool(close.iloc[-1] >= vwap_roll_v + _band or close.iloc[-1] <= vwap_roll_v - _band)

    ad_line_s = _try(lambda: calculate_ad_line(df))
    ad_line_v = ad_trend_bull = None
    ad_bull_div = ad_bear_div = False
    if ad_line_s is not None:
        ad_line_v = _safe_float(ad_line_s.iloc[-1])
        ad_sma = ad_line_s.rolling(ad_sma_length).mean()
        if not pd.isna(ad_sma.iloc[-1]):
            ad_trend_bull = bool(ad_line_s.iloc[-1] > ad_sma.iloc[-1])
        d = _try(lambda: calculate_price_divergence(close, ad_line_s, lookback=ad_div_lookback))
        if d: ad_bull_div, ad_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])

    cmf_s = _try(lambda: calculate_cmf(df, length=cmf_length))
    cmf_v = None
    cmf_centerline_bars = 999
    if cmf_s is not None:
        cmf_v = _safe_float(cmf_s.iloc[-1])
        cmf_centerline_bars = _bars_since_cross(cmf_s, pd.Series(0.0, index=cmf_s.index))

    tsi_df = _try(lambda: calculate_tsi(df, long=tsi_long, short=tsi_short, signal=tsi_signal))
    tsi_v = tsi_signal_v = None
    tsi_signal_cross_bars = tsi_centerline_bars = 999
    tsi_bull_div = tsi_bear_div = False
    if tsi_df is not None:
        _tsi_line, _tsi_sig = tsi_df.iloc[:, 0], tsi_df.iloc[:, 1]
        tsi_v = _safe_float(_tsi_line.iloc[-1])
        tsi_signal_v = _safe_float(_tsi_sig.iloc[-1])
        tsi_signal_cross_bars = _bars_since_cross(_tsi_line, _tsi_sig)
        tsi_centerline_bars   = _bars_since_cross(_tsi_line, pd.Series(0.0, index=_tsi_line.index))
        d = _try(lambda: calculate_price_divergence(close, _tsi_line, lookback=tsi_div_lookback))
        if d: tsi_bull_div, tsi_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])

    ao_s = _try(lambda: calculate_awesome_oscillator(df, fast=ao_fast, slow=ao_slow))
    ao_v = None
    ao_zero_bars = 999
    ao_bull_saucer = ao_bear_saucer = ao_bull_twin = ao_bear_twin = ao_bull_div = ao_bear_div = False
    if ao_s is not None:
        ao_v = _safe_float(ao_s.iloc[-1])
        ao_zero_bars = _bars_since_cross(ao_s, pd.Series(0.0, index=ao_s.index))
        sc = _try(lambda: calculate_ao_saucer(ao_s))
        if sc: ao_bull_saucer, ao_bear_saucer = bool(sc[0].iloc[-1]), bool(sc[1].iloc[-1])
        tw = _try(lambda: calculate_ao_twin_peaks(ao_s, lookback=ao_twin_peaks_lookback))
        if tw: ao_bull_twin, ao_bear_twin = bool(tw[0].iloc[-1]), bool(tw[1].iloc[-1])
        d = _try(lambda: calculate_price_divergence(close, ao_s, lookback=ao_div_lookback))
        if d: ao_bull_div, ao_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])

    obv_full_s = vol_df["OBV"]
    obv_trend_bull = None
    obv_bull_div = obv_bear_div = False
    if not obv_full_s.empty:
        obv_sma = obv_full_s.rolling(obv_sma_length).mean()
        if not pd.isna(obv_sma.iloc[-1]):
            obv_trend_bull = bool(obv_full_s.iloc[-1] > obv_sma.iloc[-1])
        d = _try(lambda: calculate_price_divergence(close, obv_full_s, lookback=obv_div_lookback))
        if d: obv_bull_div, obv_bear_div = bool(d[0].iloc[-1]), bool(d[1].iloc[-1])

    vp_s = _try(lambda: calculate_volume_profile_poc(df, lookback=vol_profile_lookback, bins=vol_profile_bins))
    vp_poc_v = vp_bullish = None
    vp_poc_bars = 999
    if vp_s is not None and not pd.isna(vp_s.iloc[-1]):
        vp_poc_v = _safe_float(vp_s.iloc[-1])
        vp_bullish = close.iloc[-1] > vp_poc_v
        vp_poc_bars = _bars_since_cross(close, vp_s)

    fib_df = _try(lambda: calculate_fibonacci_levels(df, lookback=fib_lookback))
    fib_levels = {}
    fib_any_touch = False
    if fib_df is not None:
        for col in fib_df.columns:
            fib_levels[col.lower()] = _safe_float(fib_df[col].iloc[-1])
        _cur = _safe_float(close.iloc[-1])
        for _k in ("fib_236", "fib_382", "fib_500", "fib_618", "fib_786"):
            _lvl = fib_levels.get(_k)
            if _cur is not None and _lvl:
                if abs(_cur - _lvl) / _lvl * 100 <= fib_tolerance_pct:
                    fib_any_touch = True
                    break

    # ── Combine for crossover tracking ────────────────────────────────────────
    frames = [df, mas, vol_df]
    if rsi_s   is not None: frames.append(rsi_s.rename("RSI"))
    if macd_df is not None: frames.append(macd_df)
    if bb_df   is not None: frames.append(bb_df)
    if stoch_df      is not None: frames.append(stoch_df)
    if stochrsi_df   is not None: frames.append(stochrsi_df)

    combined = pd.concat(frames, axis=1)
    combined.dropna(how="all", inplace=True)
    latest = combined.iloc[-1]

    macd_cols = list(macd_df.columns)   if macd_df is not None else []
    bb_cols   = list(bb_df.columns)     if bb_df   is not None else []

    # Crossovers
    ema_sn = _safe_float(latest.get(ema_sc))
    ema_ln = _safe_float(latest.get(ema_lc))
    ma20n  = _safe_float(latest.get("MA_20"))
    ma50n  = _safe_float(latest.get("MA_50"))
    ema_bars = _bars_since_cross(combined[ema_sc], combined[ema_lc])
    ma_bars  = _bars_since_cross(combined["MA_20"], combined["MA_50"])

    macd_bars = macd_line_n = macd_sig_n = 999
    if len(macd_cols) >= 3:
        macd_bars    = _bars_since_cross(combined[macd_cols[0]], combined[macd_cols[2]])
        macd_line_n  = _safe_float(latest.get(macd_cols[0]))
        macd_sig_n   = _safe_float(latest.get(macd_cols[2]))

    # Stochastic K/D
    stoch_cols = list(stoch_df.columns) if stoch_df is not None else []
    stoch_k_v = stoch_d_v = None
    stoch_bars = 999
    stoch_dir  = 0
    if len(stoch_cols) >= 2:
        stoch_k_v  = _safe_float(latest.get(stoch_cols[0]))
        stoch_d_v  = _safe_float(latest.get(stoch_cols[1]))
        stoch_bars = _bars_since_cross(combined[stoch_cols[0]], combined[stoch_cols[1]])
        stoch_dir  = 1 if (stoch_k_v and stoch_d_v and stoch_k_v > stoch_d_v) else -1

    # StochRSI K/D
    srsi_cols = list(stochrsi_df.columns) if stochrsi_df is not None else []
    srsi_k_v = srsi_d_v = None
    if len(srsi_cols) >= 2:
        srsi_k_v = _safe_float(latest.get(srsi_cols[0]))
        srsi_d_v = _safe_float(latest.get(srsi_cols[1]))

    # ADX
    adx_v = dmp_v = dmn_v = None
    if adx_df is not None:
        ac = list(adx_df.columns)
        adx_col = next((c for c in ac if c.upper().startswith("ADX")), None)
        dmp_col = next((c for c in ac if c.upper().startswith("DMP")), None)
        dmn_col = next((c for c in ac if c.upper().startswith("DMN")), None)
        if adx_col: adx_v = _safe_float(adx_df[adx_col].iloc[-1])
        if dmp_col: dmp_v = _safe_float(adx_df[dmp_col].iloc[-1])
        if dmn_col: dmn_v = _safe_float(adx_df[dmn_col].iloc[-1])

    # ATR + expansion flag
    atr_v = atr_expanding = None
    if atr_s is not None:
        atr_v = _safe_float(atr_s.iloc[-1])
        atr_sma = ta.sma(atr_s, length=10)
        if atr_sma is not None:
            atr_sma_v = _safe_float(atr_sma.iloc[-1])
            atr_expanding = bool(atr_v and atr_sma_v and atr_v > atr_sma_v)

    # PSAR
    psar_v = psar_bull = None
    if psar_df is not None:
        pc = list(psar_df.columns)
        pl_col = next((c for c in pc if c.upper().startswith("PSARL")), None)
        ps_col = next((c for c in pc if c.upper().startswith("PSARS")), None)
        if pl_col:
            pl_val = psar_df[pl_col].iloc[-1]
            psar_bull = not pd.isna(pl_val)
            psar_v = _safe_float(pl_val) if psar_bull else (
                _safe_float(psar_df[ps_col].iloc[-1]) if ps_col else None
            )

    # Supertrend
    st_v = st_bull = None
    if supertrend_df is not None:
        sc = list(supertrend_df.columns)
        st_val_col = next((c for c in sc if c.upper().startswith("SUPERT_")), None)
        st_dir_col = next((c for c in sc if c.upper().startswith("SUPERTD")), None)
        if st_val_col: st_v = _safe_float(supertrend_df[st_val_col].iloc[-1])
        if st_dir_col:
            dv = supertrend_df[st_dir_col].iloc[-1]
            st_bull = bool(dv == 1) if not pd.isna(dv) else None

    # Aroon
    ar_up = ar_dn = ar_osc = None
    if aroon_df is not None:
        arc = list(aroon_df.columns)
        ar_up_col  = next((c for c in arc if c.upper().startswith("AROONU")), None)
        ar_dn_col  = next((c for c in arc if c.upper().startswith("AROOND") and "OSC" not in c.upper()), None)
        ar_osc_col = next((c for c in arc if "OSC" in c.upper()), None)
        if ar_up_col:  ar_up  = _safe_float(aroon_df[ar_up_col].iloc[-1])
        if ar_dn_col:  ar_dn  = _safe_float(aroon_df[ar_dn_col].iloc[-1])
        if ar_osc_col: ar_osc = _safe_float(aroon_df[ar_osc_col].iloc[-1])

    # ── Build result ──────────────────────────────────────────────────────────
    return {
        "rsi": _safe_float(latest.get("RSI")),
        "macd": {
            "macd":      _safe_float(latest.get(macd_cols[0]) if macd_cols else None),
            "histogram": _safe_float(latest.get(macd_cols[1]) if len(macd_cols) > 1 else None),
            "signal":    _safe_float(latest.get(macd_cols[2]) if len(macd_cols) > 2 else None),
        },
        "bollinger_bands": {
            "lower":     _safe_float(latest.get(bb_cols[0]) if bb_cols else None),
            "mid":       _safe_float(latest.get(bb_cols[1]) if len(bb_cols) > 1 else None),
            "upper":     _safe_float(latest.get(bb_cols[2]) if len(bb_cols) > 2 else None),
            "bandwidth": _safe_float(latest.get(bb_cols[3]) if len(bb_cols) > 3 else None),
            "percent_b": _safe_float(latest.get(bb_cols[4]) if len(bb_cols) > 4 else None),
        },
        "moving_averages": {
            "ma_20":    ma20n,
            "ma_50":    ma50n,
            "ma_200":   _safe_float(latest.get("MA_200")),
            "ema_short": ema_sn,
            "ema_long":  ema_ln,
            "wma":  _safe_float(wma_s.iloc[-1]) if wma_s is not None else None,
            "hma":  _safe_float(hma_s.iloc[-1]) if hma_s is not None else None,
        },
        "volume": {
            "current": _safe_float(latest.get("Volume")),
            "sma_20":  _safe_float(latest.get("Vol_SMA_20")),
            "obv":     _safe_float(latest.get("OBV")),
            "ratio":   _safe_float(
                latest.get("Volume") / latest.get("Vol_SMA_20")
                if latest.get("Vol_SMA_20") and latest.get("Vol_SMA_20") != 0 else None
            ),
        },
        "price": {
            "close": _safe_float(latest.get("Close")),
            "open":  _safe_float(latest.get("Open")),
            "high":  _safe_float(latest.get("High")),
            "low":   _safe_float(latest.get("Low")),
        },
        "crossovers": {
            "ema_bars_since_cross":   ema_bars,
            "ema_direction":          1 if (ema_sn and ema_ln and ema_sn > ema_ln) else -1,
            "ma_bars_since_cross":    ma_bars,
            "ma_direction":           1 if (ma20n and ma50n and ma20n > ma50n) else -1,
            "macd_bars_since_cross":  macd_bars,
            "macd_direction":         1 if (macd_line_n and macd_sig_n and macd_line_n > macd_sig_n) else -1,
            "stoch_bars_since_cross": stoch_bars,
            "stoch_direction":        stoch_dir,
        },
        # ── New ───────────────────────────────────────────────────────────────
        "stochastic": {"k": stoch_k_v, "d": stoch_d_v},
        "stochrsi":   {"k": srsi_k_v,  "d": srsi_d_v},
        "cci":        _safe_float(cci_s.iloc[-1])   if cci_s   is not None else None,
        "willr":      _safe_float(willr_s.iloc[-1]) if willr_s is not None else None,
        "adx":        {"adx": adx_v, "dmp": dmp_v, "dmn": dmn_v},
        "atr":        atr_v,
        "atr_expanding": atr_expanding,
        "mfi":        _safe_float(mfi_s.iloc[-1])   if mfi_s   is not None else None,
        "vwap":       _safe_float(vwap_s.iloc[-1])  if vwap_s  is not None else None,
        "psar":       {"value": psar_v, "is_bull": psar_bull},
        "supertrend": {"value": st_v,   "is_bull": st_bull},
        "aroon":      {"up": ar_up, "down": ar_dn, "osc": ar_osc},
        "roc":        _safe_float(roc_s.iloc[-1])   if roc_s   is not None else None,
        "inverse_hs": inverse_hs,
        # ── Extended (ported from Backtester) ───────────────────────────────
        "rsi_centerline_bars_since_cross": rsi_centerline_bars,
        "rsi_bullish_divergence": rsi_bull_div, "rsi_bearish_divergence": rsi_bear_div,
        "rsi_failure_swing_bull": rsi_bull_fs,  "rsi_failure_swing_bear": rsi_bear_fs,
        "macd_centerline_bars_since_cross": macd_centerline_bars,
        "macd_bullish_divergence": macd_bull_div, "macd_bearish_divergence": macd_bear_div,
        "macd_histogram_reversal_bull": macd_bull_hr, "macd_histogram_reversal_bear": macd_bear_hr,
        "macd_zscore": macd_zscore_v,
        "bb_volatility_breakout_bull": bb_bull_breakout, "bb_volatility_breakout_bear": bb_bear_breakout,
        "bb_walking_upper": bb_walking_upper, "bb_walking_lower": bb_walking_lower,
        "bb_w_bottom": bb_w_bottom, "bb_m_top": bb_m_top,
        "ma_price_cross_bars_since_cross": price_ma_short_bars,
        "ma_two_bars_since_cross": two_ma_bars,
        "ma_three_bull": three_ma_bull, "ma_three_bear": three_ma_bear,
        "ma_multi": {"short": ma_short_v, "medium": ma_medium_v, "long": ma_long_v, "hma_fast": hma_fast_v},
        "adx_di_cross_bars_since_cross": di_cross_bars,
        "psar_flip_bars_since_cross": psar_flip_bars, "psar_narrowing": psar_narrowing,
        "supertrend_flip_bars_since_cross": st_flip_bars, "supertrend_narrowing": st_narrowing,
        "stoch_signal_bars_since_cross": stoch_signal_bars,
        "stochrsi_signal_bars_since_cross": stochrsi_signal_bars,
        "stochrsi_bullish_divergence": stochrsi_bull_div, "stochrsi_bearish_divergence": stochrsi_bear_div,
        "cci_centerline_bars_since_cross": cci_centerline_bars,
        "cci_breakout_bull": cci_breakout_bull, "cci_breakout_bear": cci_breakout_bear,
        "willr_midline_bars_since_cross": willr_midline_bars,
        "willr_bullish_divergence": willr_bull_div, "willr_bearish_divergence": willr_bear_div,
        "willr_trend_confirmation_bull": willr_bull_conf, "willr_trend_confirmation_bear": willr_bear_conf,
        "willr_failure_swing_bull": willr_bull_fs, "willr_failure_swing_bear": willr_bear_fs,
        "roc_centerline_bars_since_cross": roc_centerline_bars,
        "roc_bull_momentum": roc_bull_momentum, "roc_bear_momentum": roc_bear_momentum,
        "roc_bullish_divergence": roc_bull_div, "roc_bearish_divergence": roc_bear_div,
        "mfi_centerline_bars_since_cross": mfi_centerline_bars,
        "mfi_bullish_divergence": mfi_bull_div, "mfi_bearish_divergence": mfi_bear_div,
        "hma_slope_bull": hma_slope_bull, "hma_slope_bear": hma_slope_bear,
        "hma_price_bars_since_cross": hma_price_bars, "hma_two_bars_since_cross": hma_two_bars,
        "atr_bullish_expansion": atr_bull_exp, "atr_bearish_expansion": atr_bear_exp, "atr_contracting": atr_contracting,
        "ichimoku": {
            "tenkan": ich_tenkan_v, "kijun": ich_kijun_v,
            "senkou_a": ich_senkou_a_v, "senkou_b": ich_senkou_b_v,
            "cloud_bullish": ich_cloud_bullish, "cloud_bearish": ich_cloud_bearish,
            "tk_cross_bars_since_cross": tk_cross_bars,
        },
        "donchian": {
            "upper": dc_upper_v, "mid": dc_mid_v, "lower": dc_lower_v,
            "mid_bars_since_cross": donchian_mid_bars,
            "upper_bars_since_cross": donchian_upper_bars,
            "lower_bars_since_cross": donchian_lower_bars,
        },
        "keltner": {
            "upper": kc_upper_v, "mid": kc_mid_v, "lower": kc_lower_v,
            "mid_bars_since_cross": keltner_mid_bars,
            "walking_upper": kc_walking_upper, "walking_lower": kc_walking_lower,
            "squeeze_on": kc_squeeze_on, "squeeze_release_bull": kc_squeeze_bull, "squeeze_release_bear": kc_squeeze_bear,
        },
        "stdev": {"value": stdev_v, "expanding": stdev_expanding, "bullish_expansion": stdev_bull_exp,
                  "bearish_expansion": stdev_bear_exp, "contracting": stdev_contracting},
        "chaikin_vol": {"value": chaikin_vol_v, "expanding": chaikin_vol_expanding, "bullish_expansion": chaikin_vol_bull_exp,
                         "bearish_expansion": chaikin_vol_bear_exp, "contracting": chaikin_vol_contracting},
        "hist_vol": {"value": hist_vol_v, "expanding": hist_vol_expanding, "bullish_expansion": hist_vol_bull_exp,
                     "bearish_expansion": hist_vol_bear_exp, "contracting": hist_vol_contracting},
        "vwap_rolling": {"value": vwap_roll_v, "bullish": vwap_bull, "bearish": vwap_bear, "band_touch": vwap_band_touch},
        "ad_line": {"value": ad_line_v, "trend_bull": ad_trend_bull,
                    "bullish_divergence": ad_bull_div, "bearish_divergence": ad_bear_div},
        "cmf": {"value": cmf_v, "centerline_bars_since_cross": cmf_centerline_bars},
        "tsi": {"value": tsi_v, "signal": tsi_signal_v,
                "signal_cross_bars_since_cross": tsi_signal_cross_bars,
                "centerline_bars_since_cross": tsi_centerline_bars,
                "bullish_divergence": tsi_bull_div, "bearish_divergence": tsi_bear_div},
        "ao": {"value": ao_v, "zero_cross_bars_since_cross": ao_zero_bars,
               "bull_saucer": ao_bull_saucer, "bear_saucer": ao_bear_saucer,
               "bull_twin_peaks": ao_bull_twin, "bear_twin_peaks": ao_bear_twin,
               "bullish_divergence": ao_bull_div, "bearish_divergence": ao_bear_div},
        "obv_trend_bull": obv_trend_bull,
        "obv_bullish_divergence": obv_bull_div, "obv_bearish_divergence": obv_bear_div,
        "volume_profile": {"poc": vp_poc_v, "bullish": vp_bullish, "poc_bars_since_cross": vp_poc_bars},
        "fibonacci": {**fib_levels, "any_touch": fib_any_touch},
        "history":    _recent_ohlcv(combined),
    }


# ── Extended indicator set (Backtester) ───────────────────────────────────────
# Thin wrappers around proven pandas_ta calls (same calls already used above),
# plus hand-rolled pandas/numpy calcs for indicators pandas_ta doesn't expose
# in a form that lines up cleanly with per-bar backtesting (Ichimoku, Donchian,
# Keltner, stdev, Chaikin volatility, historical volatility, VWAP, A/D line,
# CMF, TSI, Awesome Oscillator, volume profile, Fibonacci retracement).

def calculate_adx(df: pd.DataFrame, length: int = 14) -> pd.DataFrame:
    return ta.adx(df["High"], df["Low"], df["Close"], length=length)


def calculate_psar(df: pd.DataFrame, start: float = 0.02, inc: float = 0.02, max_af: float = 0.2) -> pd.DataFrame:
    return ta.psar(df["High"], df["Low"], df["Close"], af0=start, af=inc, max_af=max_af)


def calculate_supertrend(df: pd.DataFrame, length: int = 10, mult: float = 3.0) -> pd.DataFrame:
    return ta.supertrend(df["High"], df["Low"], df["Close"], length=length, multiplier=mult)


def calculate_stochastic(df: pd.DataFrame, k: int = 14, d: int = 3, smooth: int = 3) -> pd.DataFrame:
    return ta.stoch(df["High"], df["Low"], df["Close"], k=k, d=d, smooth_k=smooth)


def calculate_stochrsi(df: pd.DataFrame, length: int = 14, k: int = 3, d: int = 3) -> pd.DataFrame:
    return ta.stochrsi(df["Close"], length=length, rsi_length=length, k=k, d=d)


def calculate_cci(df: pd.DataFrame, length: int = 20) -> pd.Series:
    return ta.cci(df["High"], df["Low"], df["Close"], length=length)


def calculate_williams_r(df: pd.DataFrame, length: int = 14) -> pd.Series:
    return ta.willr(df["High"], df["Low"], df["Close"], length=length)


def calculate_roc(df: pd.DataFrame, length: int = 12) -> pd.Series:
    return ta.roc(df["Close"], length=length)


def calculate_mfi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    return ta.mfi(df["High"], df["Low"], df["Close"], df["Volume"], length=length)


def calculate_atr(df: pd.DataFrame, length: int = 14) -> pd.Series:
    return ta.atr(df["High"], df["Low"], df["Close"], length=length)


def calculate_hma(df: pd.DataFrame, length: int = 20) -> pd.Series:
    return ta.hma(df["Close"], length=length)


def calculate_ichimoku(df: pd.DataFrame, tenkan: int = 9, kijun: int = 26, senkou: int = 52) -> pd.DataFrame:
    """Manual calc (not pandas_ta) so cloud values line up with the bar they apply
    to at backtest time — senkou spans are shifted forward by `kijun` bars, matching
    how the cloud plotted "today" was actually computed from `kijun` bars ago."""
    high, low = df["High"], df["Low"]
    tenkan_sen = (high.rolling(tenkan).max() + low.rolling(tenkan).min()) / 2
    kijun_sen  = (high.rolling(kijun).max()  + low.rolling(kijun).min())  / 2
    senkou_a   = ((tenkan_sen + kijun_sen) / 2).shift(kijun)
    senkou_b   = ((high.rolling(senkou).max() + low.rolling(senkou).min()) / 2).shift(kijun)
    return pd.DataFrame({
        "ICH_tenkan": tenkan_sen, "ICH_kijun": kijun_sen,
        "ICH_senkou_a": senkou_a, "ICH_senkou_b": senkou_b,
    })


def calculate_donchian(df: pd.DataFrame, length: int = 20) -> pd.DataFrame:
    upper = df["High"].rolling(length).max()
    lower = df["Low"].rolling(length).min()
    return pd.DataFrame({"DC_upper": upper, "DC_mid": (upper + lower) / 2, "DC_lower": lower})


def calculate_keltner(df: pd.DataFrame, length: int = 20, atr_length: int = 10, mult: float = 2.0) -> pd.DataFrame:
    basis   = ta.ema(df["Close"], length=length)
    atr_val = ta.atr(df["High"], df["Low"], df["Close"], length=atr_length)
    return pd.DataFrame({"KC_upper": basis + mult * atr_val, "KC_mid": basis, "KC_lower": basis - mult * atr_val})


def calculate_keltner_squeeze(
    close: pd.Series, bb_upper: pd.Series, bb_lower: pd.Series,
    kc_upper: pd.Series, kc_lower: pd.Series, breakout_window: int = 10,
) -> tuple[pd.Series, pd.Series, pd.Series]:
    """
    TTM-style squeeze: Bollinger Bands compressed inside the Keltner Channel (bb_upper <
    kc_upper and bb_lower > kc_lower) signals a volatility contraction — a breakout is
    building. Returns (squeeze_on, bullish_release, bearish_release): the latter two fire
    when a squeeze was active within the last `breakout_window` bars and price has now
    closed beyond a Keltner band.
    """
    squeeze_on = (bb_upper < kc_upper) & (bb_lower > kc_lower)
    was_squeezed = squeeze_on.rolling(breakout_window).max().fillna(0).astype(bool)
    bullish_release = was_squeezed & (close > kc_upper)
    bearish_release = was_squeezed & (close < kc_lower)
    return squeeze_on.fillna(False), bullish_release.fillna(False), bearish_release.fillna(False)


def calculate_stdev(df: pd.DataFrame, length: int = 20) -> pd.Series:
    return df["Close"].rolling(length).std()


def calculate_chaikin_volatility(df: pd.DataFrame, ema_length: int = 10, roc_length: int = 10) -> pd.Series:
    hl_range  = df["High"] - df["Low"]
    ema_range = hl_range.ewm(span=ema_length, adjust=False).mean()
    prior     = ema_range.shift(roc_length)
    return (ema_range - prior) / prior.replace(0, np.nan) * 100


def calculate_historical_volatility(df: pd.DataFrame, length: int = 20) -> pd.Series:
    log_ret = np.log(df["Close"] / df["Close"].shift(1))
    return log_ret.rolling(length).std() * (252 ** 0.5) * 100


def calculate_rolling_vwap(df: pd.DataFrame, length: int = 20, anchored: bool = False) -> pd.Series:
    """By default a rolling N-bar VWAP. When anchored=True, ignores `length` and
    instead cumulatively sums from the start of `df` — a classic anchored VWAP
    that never rolls off older bars, only growing wider over the series."""
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    tp_vol  = typical * df["Volume"]
    if anchored:
        return tp_vol.cumsum() / df["Volume"].cumsum().replace(0, np.nan)
    return tp_vol.rolling(length).sum() / df["Volume"].rolling(length).sum().replace(0, np.nan)


def calculate_ad_line(df: pd.DataFrame) -> pd.Series:
    rng = (df["High"] - df["Low"]).replace(0, np.nan)
    clv = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / rng
    return (clv.fillna(0) * df["Volume"]).cumsum()


def calculate_cmf(df: pd.DataFrame, length: int = 20) -> pd.Series:
    rng = (df["High"] - df["Low"]).replace(0, np.nan)
    clv = ((df["Close"] - df["Low"]) - (df["High"] - df["Close"])) / rng
    mfv = clv.fillna(0) * df["Volume"]
    return mfv.rolling(length).sum() / df["Volume"].rolling(length).sum().replace(0, np.nan)


def calculate_tsi(df: pd.DataFrame, long: int = 25, short: int = 13, signal: int = 13) -> pd.DataFrame:
    mom       = df["Close"].diff()
    ema1      = mom.ewm(span=long, adjust=False).mean()
    ema2      = ema1.ewm(span=short, adjust=False).mean()
    abs_ema1  = mom.abs().ewm(span=long, adjust=False).mean()
    abs_ema2  = abs_ema1.ewm(span=short, adjust=False).mean()
    tsi       = 100 * ema2 / abs_ema2.replace(0, np.nan)
    return pd.DataFrame({"TSI": tsi, "TSI_signal": tsi.ewm(span=signal, adjust=False).mean()})


def calculate_awesome_oscillator(df: pd.DataFrame, fast: int = 5, slow: int = 34) -> pd.Series:
    median_price = (df["High"] + df["Low"]) / 2
    return median_price.rolling(fast).mean() - median_price.rolling(slow).mean()


def calculate_ao_saucer(ao: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Bill Williams' AO saucer: a 3-bar momentum-dip-and-recover confirmed while the
    oscillator stays on one side of zero. Bull saucer — three bars above zero where the
    middle bar dips (lower than the first) and the current bar turns back up (higher than
    the middle), signaling fading-then-returning bullish momentum. Bear saucer mirrors
    this below zero.
    """
    a, b, c = ao.shift(2), ao.shift(1), ao
    bull = (a > 0) & (b > 0) & (c > 0) & (b < a) & (c > b)
    bear = (a < 0) & (b < 0) & (c < 0) & (b > a) & (c < b)
    return bull.fillna(False), bear.fillna(False)


def calculate_ao_twin_peaks(ao: pd.Series, lookback: int = 5) -> tuple[pd.Series, pd.Series]:
    """
    Bill Williams' AO twin peaks: two troughs (bull) or peaks (bear) on the same side of
    zero, where the oscillator holds that side for the entire stretch between them, and
    the second extreme is shallower than the first — confirming momentum is fading before
    price actually reverses. Pivots are trailing-confirmed the same way as
    calculate_price_divergence: bar j = i - lookback is a pivot if it's the min/max of the
    (2*lookback+1)-bar window ending at i, so there's no lookahead.
    """
    n = len(ao)
    bull = np.zeros(n, dtype=bool)
    bear = np.zeros(n, dtype=bool)

    win = 2 * lookback + 1
    a = ao.values

    last_trough_idx = last_trough_val = None
    last_peak_idx = last_peak_val = None

    for i in range(win - 1, n):
        j = i - lookback
        window = a[i - win + 1: i + 1]
        if np.isnan(window).any():
            continue

        if a[j] == window.min() and a[j] < 0:
            if (last_trough_val is not None and a[j] > last_trough_val
                    and (a[last_trough_idx:j + 1] < 0).all()):
                bull[i] = True
            last_trough_idx, last_trough_val = j, a[j]

        if a[j] == window.max() and a[j] > 0:
            if (last_peak_val is not None and a[j] < last_peak_val
                    and (a[last_peak_idx:j + 1] > 0).all()):
                bear[i] = True
            last_peak_idx, last_peak_val = j, a[j]

    return pd.Series(bull, index=ao.index), pd.Series(bear, index=ao.index)


def calculate_volume_profile_poc(df: pd.DataFrame, lookback: int = 50, bins: int = 24) -> pd.Series:
    """Rolling point-of-control: the price bin with the most traded volume in each lookback window."""
    high, low, close, vol = df["High"].values, df["Low"].values, df["Close"].values, df["Volume"].values
    n = len(df)
    poc = np.full(n, np.nan)
    for i in range(lookback - 1, n):
        lo_i = i - lookback + 1
        w_high, w_low, w_vol = high[lo_i:i + 1], low[lo_i:i + 1], vol[lo_i:i + 1]
        typical = (w_high + w_low + close[lo_i:i + 1]) / 3
        window_low, window_high = w_low.min(), w_high.max()
        if window_high <= window_low:
            continue
        edges = np.linspace(window_low, window_high, bins + 1)
        bucket_vol = np.zeros(bins)
        idxs = np.clip(np.digitize(typical, edges) - 1, 0, bins - 1)
        for b, v in zip(idxs, w_vol):
            bucket_vol[b] += v
        best_bin = int(np.argmax(bucket_vol))
        poc[i] = (edges[best_bin] + edges[best_bin + 1]) / 2
    return pd.Series(poc, index=df.index)


def calculate_fibonacci_levels(df: pd.DataFrame, lookback: int = 50) -> pd.DataFrame:
    swing_high = df["High"].rolling(lookback).max()
    swing_low  = df["Low"].rolling(lookback).min()
    rng = swing_high - swing_low
    return pd.DataFrame({
        "FIB_high": swing_high, "FIB_low": swing_low,
        "FIB_236": swing_high - rng * 0.236,
        "FIB_382": swing_high - rng * 0.382,
        "FIB_500": swing_high - rng * 0.5,
        "FIB_618": swing_high - rng * 0.618,
        "FIB_786": swing_high - rng * 0.786,
    })


# ── RSI trigger modes (Backtester) ────────────────────────────────────────────
# Lets the RSI indicator fire on something other than plain overbought/oversold.

def calculate_rsi_centerline_cross(rsi: pd.Series) -> pd.Series:
    """+1 the bar RSI crosses above 50, -1 the bar it crosses below 50, else 0."""
    above       = rsi > 50
    prev_above  = above.shift(1, fill_value=False)
    crossed_up  = above & ~prev_above
    crossed_dn  = ~above & prev_above
    signal = pd.Series(0, index=rsi.index)
    signal[crossed_up] = 1
    signal[crossed_dn] = -1
    return signal


def calculate_price_divergence(close: pd.Series, indicator: pd.Series, lookback: int = 5) -> tuple[pd.Series, pd.Series]:
    """
    Regular divergence between price and any oscillator series, detected off
    trailing-confirmed pivots: bar j = i - lookback is a pivot if it's the min/max
    of the (2*lookback+1)-bar window ending at i — using only data up to i, so
    there's no lookahead. Returns (bullish, bearish) boolean Series, True on the
    bar a divergence is confirmed (the second pivot).
    """
    n = len(close)
    bullish = np.zeros(n, dtype=bool)
    bearish = np.zeros(n, dtype=bool)

    win = 2 * lookback + 1
    c = close.values
    r = indicator.values

    last_low_price = last_low_ind = None
    last_high_price = last_high_ind = None

    for i in range(win - 1, n):
        j = i - lookback
        window_c = c[i - win + 1: i + 1]
        window_r = r[i - win + 1: i + 1]
        if np.isnan(window_c).any() or np.isnan(window_r).any():
            continue

        if c[j] == window_c.min():
            if last_low_price is not None and c[j] < last_low_price and r[j] > last_low_ind:
                bullish[i] = True
            last_low_price, last_low_ind = c[j], r[j]

        if c[j] == window_c.max():
            if last_high_price is not None and c[j] > last_high_price and r[j] < last_high_ind:
                bearish[i] = True
            last_high_price, last_high_ind = c[j], r[j]

    return pd.Series(bullish, index=close.index), pd.Series(bearish, index=close.index)


def calculate_rsi_divergence(close: pd.Series, rsi: pd.Series, lookback: int = 5) -> tuple[pd.Series, pd.Series]:
    return calculate_price_divergence(close, rsi, lookback)


def calculate_macd_divergence(close: pd.Series, macd_line: pd.Series, lookback: int = 5) -> tuple[pd.Series, pd.Series]:
    return calculate_price_divergence(close, macd_line, lookback)


def calculate_macd_histogram_reversal(histogram: pd.Series) -> tuple[pd.Series, pd.Series]:
    """
    Bullish: the prior bar was a local trough in the histogram (it was falling, now rising).
    Bearish: the prior bar was a local peak (it was rising, now falling).
    Confirmed on the turn, using only data up to the current bar (no lookahead).
    """
    prev1 = histogram.shift(1)
    prev2 = histogram.shift(2)
    bullish = (prev2 > prev1) & (histogram > prev1)
    bearish = (prev2 < prev1) & (histogram < prev1)
    return bullish.fillna(False), bearish.fillna(False)


def calculate_macd_zscore(macd_line: pd.Series, length: int = 100) -> pd.Series:
    mean = macd_line.rolling(length).mean()
    std  = macd_line.rolling(length).std()
    return (macd_line - mean) / std.replace(0, np.nan)


def calculate_failure_swings(series: pd.Series, oversold: float, overbought: float) -> tuple[pd.Series, pd.Series]:
    """
    Wilder's failure swings, generic over any bounded oscillator with an oversold/overbought
    zone (RSI 0-100, Williams %R -100-0, etc). Returns (bullish, bearish) boolean Series, True
    on the bar the swing is confirmed (the series breaks the high/low set during its pullback
    from the zone).
    """
    n = len(series)
    r = series.values
    bull = np.zeros(n, dtype=bool)
    bear = np.zeros(n, dtype=bool)

    # Bullish: idle -> armed (dipped below oversold) -> peaking (recovered, tracking high)
    #          -> pullback (declining, must stay above oversold) -> break above the peak.
    state, peak, prev = 0, None, None
    for i in range(n):
        v = r[i]
        if v != v:
            prev = v
            continue
        if state == 0:
            if v < oversold:
                state = 1
        elif state == 1:
            if v > oversold:
                state, peak = 2, v
        elif state == 2:
            if v < oversold:
                state = 1
            elif prev is not None and v < prev:
                peak, state = prev, 3
            else:
                peak = max(peak, v)
        elif state == 3:
            if v < oversold:
                state = 1
            elif v > peak:
                bull[i] = True
                state = 0
        prev = v

    # Bearish: mirror image.
    state, trough, prev = 0, None, None
    for i in range(n):
        v = r[i]
        if v != v:
            prev = v
            continue
        if state == 0:
            if v > overbought:
                state = 1
        elif state == 1:
            if v < overbought:
                state, trough = 2, v
        elif state == 2:
            if v > overbought:
                state = 1
            elif prev is not None and v > prev:
                trough, state = prev, 3
            else:
                trough = min(trough, v)
        elif state == 3:
            if v > overbought:
                state = 1
            elif v < trough:
                bear[i] = True
                state = 0
        prev = v

    return pd.Series(bull, index=series.index), pd.Series(bear, index=series.index)


def calculate_rsi_failure_swings(rsi: pd.Series, oversold: float = 30, overbought: float = 70) -> tuple[pd.Series, pd.Series]:
    return calculate_failure_swings(rsi, oversold, overbought)


def calculate_willr_failure_swings(willr: pd.Series, oversold: float = -80, overbought: float = -20) -> tuple[pd.Series, pd.Series]:
    return calculate_failure_swings(willr, oversold, overbought)


def calculate_trend_confirmation(close: pd.Series, indicator: pd.Series, lookback: int = 5) -> tuple[pd.Series, pd.Series]:
    """
    The mirror image of calculate_price_divergence: detected off the same trailing-confirmed
    pivots, but flags the bar a new price extreme is echoed by a same-direction extreme in the
    oscillator (both higher highs, or both lower lows) — confirming the trend is still backed by
    momentum, rather than warning that it's fading.
    """
    n = len(close)
    bull = np.zeros(n, dtype=bool)
    bear = np.zeros(n, dtype=bool)

    win = 2 * lookback + 1
    c = close.values
    r = indicator.values

    last_low_price = last_low_ind = None
    last_high_price = last_high_ind = None

    for i in range(win - 1, n):
        j = i - lookback
        window_c = c[i - win + 1: i + 1]
        window_r = r[i - win + 1: i + 1]
        if np.isnan(window_c).any() or np.isnan(window_r).any():
            continue

        if c[j] == window_c.min():
            if last_low_price is not None and c[j] < last_low_price and r[j] < last_low_ind:
                bear[i] = True
            last_low_price, last_low_ind = c[j], r[j]

        if c[j] == window_c.max():
            if last_high_price is not None and c[j] > last_high_price and r[j] > last_high_ind:
                bull[i] = True
            last_high_price, last_high_ind = c[j], r[j]

    return pd.Series(bull, index=close.index), pd.Series(bear, index=close.index)


# ── Bollinger Band trigger modes (Backtester) ─────────────────────────────────

def calculate_bb_squeeze_breakout(
    close: pd.Series, upper: pd.Series, lower: pd.Series, bandwidth: pd.Series,
    squeeze_lookback: int = 100, squeeze_percentile: float = 20.0, breakout_window: int = 10,
) -> tuple[pd.Series, pd.Series]:
    """
    Bullish/bearish volatility breakout: bandwidth was in the bottom
    `squeeze_percentile`% of its trailing `squeeze_lookback`-bar range (a "squeeze")
    at some point in the last `breakout_window` bars, and price has now closed
    beyond a band.
    """
    bw_rank = bandwidth.rolling(squeeze_lookback).rank(pct=True) * 100
    was_squeezed = (bw_rank <= squeeze_percentile).rolling(breakout_window).max().fillna(0).astype(bool)
    bullish = was_squeezed & (close > upper)
    bearish = was_squeezed & (close < lower)
    return bullish.fillna(False), bearish.fillna(False)


def calculate_bb_walking_band(
    close: pd.Series, upper: pd.Series, lower: pd.Series,
    min_consecutive: int = 3, tolerance_pct: float = 0.5,
) -> tuple[pd.Series, pd.Series]:
    """
    "Walking the band": price has stayed at/beyond a band for `min_consecutive`
    consecutive bars — a trend-continuation signal (not mean-reversion).
    """
    near_upper = close >= upper * (1 - tolerance_pct / 100)
    near_lower = close <= lower * (1 + tolerance_pct / 100)

    def _streak(mask: pd.Series) -> pd.Series:
        groups = (~mask).cumsum()
        return mask.astype(int).groupby(groups).cumsum()

    walking_upper = _streak(near_upper) >= min_consecutive
    walking_lower = _streak(near_lower) >= min_consecutive
    return walking_upper, walking_lower


def calculate_bb_double_patterns(
    close: pd.Series, low: pd.Series, high: pd.Series,
    lower_band: pd.Series, mid_band: pd.Series, upper_band: pd.Series, lookback: int = 5,
) -> tuple[pd.Series, pd.Series]:
    """
    W-bottom: a pivot low touches/pierces the lower band, price rallies back above
    the middle band (a real "W" shape, not just noise), then a later, HIGHER pivot
    low forms without touching the lower band — confirms a reversal rather than a
    continuation. M-top mirrors this at the upper band. Uses the same
    trailing-confirmed pivot approach as calculate_price_divergence (no lookahead).
    """
    n = len(close)
    w_bottom = np.zeros(n, dtype=bool)
    m_top = np.zeros(n, dtype=bool)

    win = 2 * lookback + 1
    c, l, h = close.values, low.values, high.values
    lb, mb, ub = lower_band.values, mid_band.values, upper_band.values

    last_low_price = last_low_touched = last_low_idx = None
    last_high_price = last_high_touched = last_high_idx = None

    for i in range(win - 1, n):
        j = i - lookback
        window_l = l[i - win + 1: i + 1]
        window_h = h[i - win + 1: i + 1]
        if (np.isnan(window_l).any() or np.isnan(window_h).any()
                or lb[j] != lb[j] or ub[j] != ub[j] or mb[j] != mb[j]):
            continue

        if l[j] == window_l.min():
            touched = l[j] <= lb[j]
            if (last_low_idx is not None and l[j] > last_low_price
                    and last_low_touched and not touched
                    and c[last_low_idx:j + 1].max() >= mb[j]):
                w_bottom[i] = True
            last_low_price, last_low_touched, last_low_idx = l[j], touched, j

        if h[j] == window_h.max():
            touched = h[j] >= ub[j]
            if (last_high_idx is not None and h[j] < last_high_price
                    and last_high_touched and not touched
                    and c[last_high_idx:j + 1].min() <= mb[j]):
                m_top[i] = True
            last_high_price, last_high_touched, last_high_idx = h[j], touched, j

    return pd.Series(w_bottom, index=close.index), pd.Series(m_top, index=close.index)


# ── Configurable MA type (Backtester — MA Cross trigger modes) ───────────────
# Separate from calculate_moving_averages (which stays fixed EMA/SMA for the
# live Signal page) so these can vary by user-selected MA type.

def calculate_sma(df: pd.DataFrame, length: int = 20) -> pd.Series:
    return df["Close"].rolling(length).mean()


def calculate_smma(df: pd.DataFrame, length: int = 20) -> pd.Series:
    """Smoothed moving average (aka Wilder's RMA)."""
    return df["Close"].ewm(alpha=1 / length, adjust=False).mean()


def calculate_wma(df: pd.DataFrame, length: int = 20) -> pd.Series:
    return ta.wma(df["Close"], length=length)


def calculate_vwma(df: pd.DataFrame, length: int = 20) -> pd.Series:
    pv = df["Close"] * df["Volume"]
    return pv.rolling(length).sum() / df["Volume"].rolling(length).sum()


def calculate_ma_by_type(df: pd.DataFrame, length: int = 20, ma_type: str = "exponential") -> pd.Series:
    if ma_type == "simple":
        return calculate_sma(df, length)
    if ma_type == "smoothed":
        return calculate_smma(df, length)
    if ma_type == "weighted":
        return calculate_wma(df, length)
    if ma_type == "volume_weighted":
        return calculate_vwma(df, length)
    return ta.ema(df["Close"], length=length)  # "exponential" (default)
