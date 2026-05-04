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
        "history":    _recent_ohlcv(combined),
    }
