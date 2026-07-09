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


def calculate_rolling_vwap(df: pd.DataFrame, length: int = 20) -> pd.Series:
    typical = (df["High"] + df["Low"] + df["Close"]) / 3
    tp_vol  = typical * df["Volume"]
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
