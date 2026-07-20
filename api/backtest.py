from __future__ import annotations
import numpy as np
import pandas as pd
from api.indicators import (
    calculate_rsi, calculate_macd, calculate_bollinger_bands,
    calculate_moving_averages, calculate_volume_indicators,
    calculate_adx, calculate_psar, calculate_supertrend,
    calculate_stochastic, calculate_stochrsi, calculate_cci, calculate_williams_r,
    calculate_roc, calculate_mfi, calculate_atr, calculate_hma,
    calculate_ichimoku, calculate_donchian, calculate_keltner, calculate_stdev,
    calculate_chaikin_volatility, calculate_historical_volatility,
    calculate_rolling_vwap, calculate_ad_line, calculate_cmf, calculate_tsi,
    calculate_awesome_oscillator, calculate_volume_profile_poc, calculate_fibonacci_levels,
    calculate_rsi_centerline_cross, calculate_rsi_divergence, calculate_rsi_failure_swings,
    calculate_macd_divergence, calculate_macd_histogram_reversal, calculate_macd_zscore,
    calculate_bb_squeeze_breakout, calculate_bb_walking_band, calculate_bb_double_patterns,
    calculate_ma_by_type, calculate_price_divergence,
    calculate_willr_failure_swings, calculate_trend_confirmation,
    calculate_ao_saucer, calculate_ao_twin_peaks, calculate_keltner_squeeze,
    _inverse_hs_series,
)
from api.signals import score_signals, DEFAULT_THRESHOLDS


def run_backtest(
    df: pd.DataFrame,
    thresholds: dict | None = None,
    calc_params: dict | None = None,
    stop_loss_pct: float = 2.0,
    take_profit_pct: float = 4.0,
    min_confidence: float = 60.0,
    trailing_stop: bool = False,
    trail_distance_pct: float = 1.5,
    capital: float = 10000.0,
    trade_amount_mode: str = "percent",
    trade_amount: float = 100.0,
) -> tuple[list[dict], list[dict], list[dict]]:
    """
    Bar-by-bar backtest using the existing indicator + signal pipeline.
    Returns (trades, equity_curve, bah_curve) where bah = buy-and-hold baseline.
    Entry at close when BUY fires; exit at close on SELL, or intrabar SL/TP.

    trade_amount_mode="percent": each trade risks trade_amount% of CURRENT equity
    (compounds — matches trade_amount_mode="gbp" behaviour as the pot grows/shrinks).
    trade_amount_mode="gbp": each trade risks a fixed trade_amount, converted to a
    fraction of the current pot value at entry time, so it still compounds naturally.

    stop_loss_pct/take_profit_pct are a % of STARTING capital (a fixed £ target),
    not a % price move — e.g. take_profit_pct=34.5 with capital=10000 targets a
    £3,450 gain on that trade. That £ target is converted into the price move
    needed on the trade's actual invested amount (size_fraction * pot value at
    entry) to reach it. When trade_amount is small relative to capital, this can
    require a very large — even unreachable — price move; that's inherent to
    defining SL/TP against total capital rather than the position actually at risk.
    """
    t  = {**DEFAULT_THRESHOLDS, **(thresholds or {})}
    cp = calc_params or {}

    rsi_length      = int(cp.get("rsi_length",  14))
    rsi_div_lookback = int(cp.get("rsi_div_lookback", 5))
    macd_fast   = int(cp.get("macd_fast",   12))
    macd_slow   = int(cp.get("macd_slow",   26))
    macd_signal = int(cp.get("macd_signal",  9))
    macd_div_lookback  = int(cp.get("macd_div_lookback", 5))
    macd_zscore_length = int(cp.get("macd_zscore_length", 100))
    bb_length   = int(cp.get("bb_length",   20))
    bb_std      = float(cp.get("bb_std",    2.0))
    bb_squeeze_lookback   = int(cp.get("bb_squeeze_lookback", 100))
    bb_breakout_window    = int(cp.get("bb_breakout_window", 10))
    bb_walk_min_consecutive = int(cp.get("bb_walk_min_consecutive", 3))
    bb_pattern_lookback   = int(cp.get("bb_pattern_lookback", 5))
    bb_squeeze_percentile   = float(cp.get("bb_squeeze_percentile", 20.0))
    bb_walk_tolerance_pct   = float(cp.get("bb_walk_tolerance_pct", 0.5))
    ema_short   = int(cp.get("ema_short",    9))
    ema_long    = int(cp.get("ema_long",    21))
    ma_type          = str(cp.get("ma_type", "exponential"))
    ma_short_length  = int(cp.get("ma_short_length", 9))
    ma_medium_length = int(cp.get("ma_medium_length", 20))
    ma_long_length   = int(cp.get("ma_long_length", 50))

    # ── Extended indicator set: lengths/params (sensible defaults if unset) ──
    adx_length             = int(cp.get("adx_length", 14))
    psar_start             = float(cp.get("psar_start", 0.02))
    psar_inc               = float(cp.get("psar_inc", 0.02))
    psar_max               = float(cp.get("psar_max", 0.2))
    supertrend_length      = int(cp.get("supertrend_length", 10))
    supertrend_mult        = float(cp.get("supertrend_mult", 3.0))
    stoch_k                = int(cp.get("stoch_k", 14))
    stoch_d                = int(cp.get("stoch_d", 3))
    stoch_smooth           = int(cp.get("stoch_smooth", 3))
    stochrsi_length        = int(cp.get("stochrsi_length", 14))
    stochrsi_k             = int(cp.get("stochrsi_k", 3))
    stochrsi_d             = int(cp.get("stochrsi_d", 3))
    stochrsi_div_lookback  = int(cp.get("stochrsi_div_lookback", 5))
    cci_length             = int(cp.get("cci_length", 20))
    willr_length           = int(cp.get("willr_length", 14))
    willr_div_lookback     = int(cp.get("willr_div_lookback", 5))
    willr_confirm_lookback = int(cp.get("willr_confirm_lookback", 5))
    roc_length             = int(cp.get("roc_length", 12))
    roc_div_lookback       = int(cp.get("roc_div_lookback", 5))
    roc_momentum_lookback  = int(cp.get("roc_momentum_lookback", 3))
    mfi_length             = int(cp.get("mfi_length", 14))
    mfi_div_lookback       = int(cp.get("mfi_div_lookback", 5))
    atr_length             = int(cp.get("atr_length", 14))
    hma_length             = int(cp.get("hma_length", 20))
    hma_slope_lookback     = int(cp.get("hma_slope_lookback", 3))
    hma_fast_length        = int(cp.get("hma_fast_length", 9))
    ichimoku_tenkan        = int(cp.get("ichimoku_tenkan", 9))
    ichimoku_kijun         = int(cp.get("ichimoku_kijun", 26))
    ichimoku_senkou        = int(cp.get("ichimoku_senkou", 52))
    donchian_length        = int(cp.get("donchian_length", 20))
    donchian_exit_length   = int(cp.get("donchian_exit_length", 10))
    keltner_length         = int(cp.get("keltner_length", 20))
    keltner_atr_length     = int(cp.get("keltner_atr_length", 10))
    keltner_mult           = float(cp.get("keltner_mult", 2.0))
    keltner_walk_min_consecutive = int(cp.get("keltner_walk_min_consecutive", 3))
    keltner_walk_tolerance_pct   = float(cp.get("keltner_walk_tolerance_pct", 0.5))
    keltner_squeeze_lookback     = int(cp.get("keltner_squeeze_lookback", 10))
    stdev_length           = int(cp.get("stdev_length", 20))
    chaikin_vol_ema_length = int(cp.get("chaikin_vol_ema_length", 10))
    chaikin_vol_roc_length = int(cp.get("chaikin_vol_roc_length", 10))
    hist_vol_length        = int(cp.get("hist_vol_length", 20))
    vwap_length            = int(cp.get("vwap_length", 20))
    ad_sma_length          = int(cp.get("ad_sma_length", 20))
    cmf_length             = int(cp.get("cmf_length", 20))
    tsi_long               = int(cp.get("tsi_long", 25))
    tsi_short              = int(cp.get("tsi_short", 13))
    tsi_signal             = int(cp.get("tsi_signal", 13))
    tsi_div_lookback       = int(cp.get("tsi_div_lookback", 5))
    ao_fast                = int(cp.get("ao_fast", 5))
    ao_slow                = int(cp.get("ao_slow", 34))
    ao_div_lookback        = int(cp.get("ao_div_lookback", 5))
    ao_twin_peaks_lookback = int(cp.get("ao_twin_peaks_lookback", 5))
    obv_sma_length         = int(cp.get("obv_sma_length", 20))
    vol_profile_lookback   = int(cp.get("vol_profile_lookback", 50))
    vol_profile_bins       = int(cp.get("vol_profile_bins", 24))
    fib_lookback           = int(cp.get("fib_lookback", 50))
    vwap_band_pct          = float(cp.get("vwap_band_pct", 1.0))
    vwap_anchored          = bool(int(cp.get("vwap_anchored", 0)))
    obv_div_lookback       = int(cp.get("obv_div_lookback", 5))
    ad_div_lookback        = int(cp.get("ad_div_lookback", 5))
    hs_pivot               = int(cp.get("hs_pivot", 3))
    hs_lookback            = int(cp.get("hs_lookback", 90))

    # ── Compute full indicator series upfront (O(n), not O(n²)) ──────────
    rsi_s   = calculate_rsi(df, length=rsi_length)
    rsi_centerline       = calculate_rsi_centerline_cross(rsi_s)
    rsi_bull_div, rsi_bear_div = calculate_rsi_divergence(df["Close"], rsi_s, lookback=rsi_div_lookback)
    rsi_bull_fs, rsi_bear_fs   = calculate_rsi_failure_swings(
        rsi_s, oversold=float(t.get("rsi_oversold", 30)), overbought=float(t.get("rsi_overbought", 70)),
    )
    macd_df = calculate_macd(df, fast=macd_fast, slow=macd_slow, signal=macd_signal)
    macd_line_s = macd_df.iloc[:, 0]
    macd_hist_s = macd_df.iloc[:, 1]
    macd_centerline_bars = _bars_since_cross_series(macd_line_s, pd.Series(0.0, index=macd_line_s.index))
    macd_bull_div, macd_bear_div = calculate_macd_divergence(df["Close"], macd_line_s, lookback=macd_div_lookback)
    macd_bull_hr, macd_bear_hr   = calculate_macd_histogram_reversal(macd_hist_s)
    macd_zscore = calculate_macd_zscore(macd_line_s, length=macd_zscore_length)
    bb_df   = calculate_bollinger_bands(df, length=bb_length, std=bb_std)
    bb_lower_s, bb_mid_s, bb_upper_s, bb_bw_s = bb_df.iloc[:, 0], bb_df.iloc[:, 1], bb_df.iloc[:, 2], bb_df.iloc[:, 3]
    bb_bull_breakout, bb_bear_breakout = calculate_bb_squeeze_breakout(
        df["Close"], bb_upper_s, bb_lower_s, bb_bw_s,
        squeeze_lookback=bb_squeeze_lookback, squeeze_percentile=bb_squeeze_percentile,
        breakout_window=bb_breakout_window,
    )
    bb_walking_upper, bb_walking_lower = calculate_bb_walking_band(
        df["Close"], bb_upper_s, bb_lower_s,
        min_consecutive=bb_walk_min_consecutive, tolerance_pct=bb_walk_tolerance_pct,
    )
    bb_w_bottom, bb_m_top = calculate_bb_double_patterns(
        df["Close"], df["Low"], df["High"], bb_lower_s, bb_mid_s, bb_upper_s, lookback=bb_pattern_lookback,
    )
    mas_df  = calculate_moving_averages(df, ema_short=ema_short, ema_long=ema_long)
    vol_df  = calculate_volume_indicators(df)

    # Inverse head & shoulders — causal per-bar state (no lookahead). Aligned to df's
    # positional index, which `combined` preserves (concat with no row drops).
    hs_detected_s, hs_neckline_s, hs_pct_s, hs_broke_s = _inverse_hs_series(
        df["High"], df["Low"], df["Close"], pivot=hs_pivot, lookback=hs_lookback,
    )

    ma_short_s  = calculate_ma_by_type(df, ma_short_length,  ma_type)
    ma_medium_s = calculate_ma_by_type(df, ma_medium_length, ma_type)
    ma_long_s   = calculate_ma_by_type(df, ma_long_length,   ma_type)
    price_cross_bars = _bars_since_cross_series(df["Close"], ma_short_s)
    two_ma_bars       = _bars_since_cross_series(ma_short_s, ma_long_s)
    three_ma_bull_s = (ma_short_s > ma_medium_s) & (ma_medium_s > ma_long_s)
    three_ma_bear_s = (ma_short_s < ma_medium_s) & (ma_medium_s < ma_long_s)

    adx_df        = _try(lambda: calculate_adx(df, length=adx_length))
    psar_df       = _try(lambda: calculate_psar(df, start=psar_start, inc=psar_inc, max_af=psar_max))
    supertrend_df = _try(lambda: calculate_supertrend(df, length=supertrend_length, mult=supertrend_mult))
    stoch_df      = _try(lambda: calculate_stochastic(df, k=stoch_k, d=stoch_d, smooth=stoch_smooth))
    stochrsi_df   = _try(lambda: calculate_stochrsi(df, length=stochrsi_length, k=stochrsi_k, d=stochrsi_d))
    cci_s         = _try(lambda: calculate_cci(df, length=cci_length))
    willr_s       = _try(lambda: calculate_williams_r(df, length=willr_length))
    roc_s         = _try(lambda: calculate_roc(df, length=roc_length))
    mfi_s         = _try(lambda: calculate_mfi(df, length=mfi_length))
    atr_s         = _try(lambda: calculate_atr(df, length=atr_length))
    hma_s         = _try(lambda: calculate_hma(df, length=hma_length))
    hma_fast_s    = _try(lambda: calculate_hma(df, length=hma_fast_length))
    ichimoku_df   = _try(lambda: calculate_ichimoku(df, tenkan=ichimoku_tenkan, kijun=ichimoku_kijun, senkou=ichimoku_senkou))
    donchian_df   = _try(lambda: calculate_donchian(df, length=donchian_length))
    donchian_exit_df = _try(lambda: calculate_donchian(df, length=donchian_exit_length))
    if donchian_exit_df is not None:
        donchian_exit_df = donchian_exit_df.rename(
            columns={"DC_upper": "DC_exit_upper", "DC_mid": "DC_exit_mid", "DC_lower": "DC_exit_lower"}
        )
    keltner_df    = _try(lambda: calculate_keltner(df, length=keltner_length, atr_length=keltner_atr_length, mult=keltner_mult))
    stdev_s       = _try(lambda: calculate_stdev(df, length=stdev_length))
    chaikin_vol_s = _try(lambda: calculate_chaikin_volatility(df, ema_length=chaikin_vol_ema_length, roc_length=chaikin_vol_roc_length))
    hist_vol_s    = _try(lambda: calculate_historical_volatility(df, length=hist_vol_length))
    vwap_s        = _try(lambda: calculate_rolling_vwap(df, length=vwap_length, anchored=vwap_anchored))
    ad_line_s     = _try(lambda: calculate_ad_line(df))
    cmf_s         = _try(lambda: calculate_cmf(df, length=cmf_length))
    tsi_df        = _try(lambda: calculate_tsi(df, long=tsi_long, short=tsi_short, signal=tsi_signal))
    ao_s          = _try(lambda: calculate_awesome_oscillator(df, fast=ao_fast, slow=ao_slow))
    vp_s          = _try(lambda: calculate_volume_profile_poc(df, lookback=vol_profile_lookback, bins=vol_profile_bins))
    fib_df        = _try(lambda: calculate_fibonacci_levels(df, lookback=fib_lookback))

    frames = [df[["Open", "High", "Low", "Close", "Volume"]],
              mas_df, vol_df, rsi_s.rename("RSI"), macd_df, bb_df]
    for extra in (adx_df, psar_df, supertrend_df, stoch_df, stochrsi_df, ichimoku_df,
                  donchian_df, donchian_exit_df, keltner_df, tsi_df, fib_df):
        if extra is not None:
            frames.append(extra)
    for name, s in (("CCI", cci_s), ("WILLR", willr_s), ("ROC", roc_s), ("MFI", mfi_s),
                    ("ATR", atr_s), ("HMA", hma_s), ("HMA_FAST", hma_fast_s), ("STDEV", stdev_s),
                    ("CHAIKIN_VOL", chaikin_vol_s), ("HIST_VOL", hist_vol_s),
                    ("VWAP_ROLL", vwap_s), ("AD_LINE", ad_line_s), ("CMF", cmf_s),
                    ("AO", ao_s), ("VP_POC", vp_s)):
        if s is not None:
            frames.append(s.rename(name))

    combined = pd.concat(frames, axis=1).copy()
    combined = combined.loc[:, ~combined.columns.duplicated()]

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

    # ── Extended indicator set: resolve dynamic pandas_ta column names once ──
    adx_col = dmp_col = dmn_col = None
    if adx_df is not None:
        adx_cols = list(adx_df.columns)
        adx_col = _find_col(adx_cols, "ADX")
        dmp_col = _find_col(adx_cols, "DMP")
        dmn_col = _find_col(adx_cols, "DMN")
    di_cross_bars = (
        _bars_since_cross_series(combined[dmp_col], combined[dmn_col])
        if dmp_col and dmn_col
        else pd.Series(999, index=combined.index)
    )

    psar_long_col = psar_short_col = None
    if psar_df is not None:
        psar_cols = list(psar_df.columns)
        psar_long_col  = _find_col(psar_cols, "PSARL")
        psar_short_col = _find_col(psar_cols, "PSARS")
    if psar_long_col and psar_short_col:
        long_notna  = combined[psar_long_col].notna()
        short_notna = combined[psar_short_col].notna()
        psar_dir = pd.Series(np.where(long_notna, 1.0, np.where(short_notna, -1.0, np.nan)), index=combined.index)
        psar_value_s = combined[psar_long_col].where(long_notna, combined[psar_short_col])
    else:
        psar_dir = pd.Series(np.nan, index=combined.index)
        psar_value_s = pd.Series(np.nan, index=combined.index)
    psar_flip = _bars_since_flip_series(psar_dir)

    # "Trailing stop" trigger: the SAR dot IS a trailing stop, so its gap from price
    # narrowing (vs `psar_gap_lookback` bars ago) means momentum is decelerating toward
    # that stop — an early warning of a possible flip, ahead of the flip itself.
    psar_gap_lookback = int(t.get("psar_gap_lookback", 3))
    psar_gap_s = (df["Close"] - psar_value_s).abs()
    psar_narrowing_s = psar_gap_s < psar_gap_s.shift(psar_gap_lookback)

    st_dir_col = st_val_col = None
    if supertrend_df is not None:
        st_cols = list(supertrend_df.columns)
        st_dir_col = _find_col(st_cols, "SUPERTD")
        st_val_col = _find_col(st_cols, "SUPERT_")
    st_flip = _bars_since_flip_series(combined[st_dir_col]) if st_dir_col else pd.Series(999, index=combined.index)

    # "Trailing stop" trigger: the Supertrend line IS a trailing stop, so its gap from
    # price narrowing (vs `supertrend_gap_lookback` bars ago) means momentum is
    # decelerating toward that stop — an early warning ahead of the flip itself.
    supertrend_gap_lookback = int(t.get("supertrend_gap_lookback", 3))
    if st_val_col:
        st_gap_s = (combined["Close"] - combined[st_val_col]).abs()
        st_narrowing_s = st_gap_s < st_gap_s.shift(supertrend_gap_lookback)
    else:
        st_narrowing_s = pd.Series(False, index=combined.index)

    stoch_k_col = stoch_d_col = None
    if stoch_df is not None:
        sc = list(stoch_df.columns)
        stoch_k_col = sc[0] if len(sc) > 0 else None
        stoch_d_col = sc[1] if len(sc) > 1 else None

    srsi_k_col = srsi_d_col = None
    if stochrsi_df is not None:
        rc = list(stochrsi_df.columns)
        srsi_k_col = rc[0] if len(rc) > 0 else None
        srsi_d_col = rc[1] if len(rc) > 1 else None
    if srsi_k_col:
        stochrsi_bull_div, stochrsi_bear_div = calculate_price_divergence(
            combined["Close"], combined[srsi_k_col], lookback=stochrsi_div_lookback,
        )
    else:
        stochrsi_bull_div = stochrsi_bear_div = pd.Series(False, index=combined.index)

    if "WILLR" in combined:
        willr_bull_div, willr_bear_div = calculate_price_divergence(
            combined["Close"], combined["WILLR"], lookback=willr_div_lookback,
        )
        willr_bull_conf, willr_bear_conf = calculate_trend_confirmation(
            combined["Close"], combined["WILLR"], lookback=willr_confirm_lookback,
        )
        willr_bull_fs, willr_bear_fs = calculate_willr_failure_swings(
            combined["WILLR"], oversold=float(t.get("willr_oversold", -80)), overbought=float(t.get("willr_overbought", -20)),
        )
    else:
        willr_bull_div = willr_bear_div = pd.Series(False, index=combined.index)
        willr_bull_conf = willr_bear_conf = pd.Series(False, index=combined.index)
        willr_bull_fs = willr_bear_fs = pd.Series(False, index=combined.index)

    if "ROC" in combined:
        roc_bull_div, roc_bear_div = calculate_price_divergence(
            combined["Close"], combined["ROC"], lookback=roc_div_lookback,
        )
        roc_prev = combined["ROC"].shift(roc_momentum_lookback)
    else:
        roc_bull_div = roc_bear_div = pd.Series(False, index=combined.index)
        roc_prev = pd.Series(np.nan, index=combined.index)

    if "MFI" in combined:
        mfi_bull_div, mfi_bear_div = calculate_price_divergence(
            combined["Close"], combined["MFI"], lookback=mfi_div_lookback,
        )
    else:
        mfi_bull_div = mfi_bear_div = pd.Series(False, index=combined.index)

    if "TSI" in combined:
        tsi_bull_div, tsi_bear_div = calculate_price_divergence(
            combined["Close"], combined["TSI"], lookback=tsi_div_lookback,
        )
    else:
        tsi_bull_div = tsi_bear_div = pd.Series(False, index=combined.index)

    if "AO" in combined:
        ao_bull_saucer, ao_bear_saucer = calculate_ao_saucer(combined["AO"])
        ao_bull_twin, ao_bear_twin = calculate_ao_twin_peaks(combined["AO"], lookback=ao_twin_peaks_lookback)
        ao_bull_div, ao_bear_div = calculate_price_divergence(
            combined["Close"], combined["AO"], lookback=ao_div_lookback,
        )
    else:
        ao_bull_saucer = ao_bear_saucer = pd.Series(False, index=combined.index)
        ao_bull_twin = ao_bear_twin = pd.Series(False, index=combined.index)
        ao_bull_div = ao_bear_div = pd.Series(False, index=combined.index)

    if "KC_upper" in combined and "KC_lower" in combined:
        kc_walking_upper, kc_walking_lower = calculate_bb_walking_band(
            combined["Close"], combined["KC_upper"], combined["KC_lower"],
            min_consecutive=keltner_walk_min_consecutive, tolerance_pct=keltner_walk_tolerance_pct,
        )
        kc_squeeze_on, kc_squeeze_bull, kc_squeeze_bear = calculate_keltner_squeeze(
            combined["Close"], bb_upper_s, bb_lower_s, combined["KC_upper"], combined["KC_lower"],
            breakout_window=keltner_squeeze_lookback,
        )
    else:
        kc_walking_upper = kc_walking_lower = pd.Series(False, index=combined.index)
        kc_squeeze_on = kc_squeeze_bull = kc_squeeze_bear = pd.Series(False, index=combined.index)

    hma_prev = combined["HMA"].shift(hma_slope_lookback) if "HMA" in combined else pd.Series(np.nan, index=combined.index)

    # "Two HMA" cross triggers: crossover of a fast HMA (hma_fast_length) over/under the
    # (slower) primary HMA — same bull/bear-cross-event pattern as the two-MA trigger.
    hma_two_bars = (
        _bars_since_cross_series(combined["HMA_FAST"], combined["HMA"])
        if "HMA_FAST" in combined and "HMA" in combined
        else pd.Series(999, index=combined.index)
    )

    atr_trend_lb   = int(t.get("atr_trend_lookback", 5))
    stdev_trend_lb = int(t.get("stdev_trend_lookback", 5))
    cv_trend_lb    = int(t.get("chaikin_vol_trend_lookback", 5))
    hv_trend_lb    = int(t.get("hist_vol_trend_lookback", 5))

    atr_sma   = combined["ATR"].rolling(10).mean()         if "ATR" in combined else pd.Series(np.nan, index=combined.index)
    stdev_sma = combined["STDEV"].rolling(10).mean()       if "STDEV" in combined else pd.Series(np.nan, index=combined.index)
    cv_sma    = combined["CHAIKIN_VOL"].rolling(10).mean() if "CHAIKIN_VOL" in combined else pd.Series(np.nan, index=combined.index)
    hv_sma    = combined["HIST_VOL"].rolling(10).mean()    if "HIST_VOL" in combined else pd.Series(np.nan, index=combined.index)

    close_shift_atr   = combined["Close"].shift(atr_trend_lb)
    close_shift_stdev = combined["Close"].shift(stdev_trend_lb)
    close_shift_cv    = combined["Close"].shift(cv_trend_lb)
    close_shift_hv    = combined["Close"].shift(hv_trend_lb)

    obv_sma = combined["OBV"].rolling(obv_sma_length).mean()     if "OBV" in combined else pd.Series(np.nan, index=combined.index)
    ad_sma  = combined["AD_LINE"].rolling(ad_sma_length).mean()  if "AD_LINE" in combined else pd.Series(np.nan, index=combined.index)

    # ── Trigger-mode precomputes for the remaining extended indicators ──────
    # (bull/bear split + one discrete-cross-event variant per indicator, all built
    # from series already computed above via the same _bars_since_cross_series /
    # calculate_price_divergence primitives used for RSI/MACD/ADX.)
    def _cross_bars(col_a, col_b=None, level=None):
        if col_a not in combined:
            return pd.Series(999, index=combined.index)
        b = combined[col_b] if col_b else pd.Series(level, index=combined.index)
        return _bars_since_cross_series(combined[col_a], b)

    tk_cross_bars        = _cross_bars("ICH_tenkan", "ICH_kijun")
    donchian_mid_bars    = _bars_since_cross_series(combined["Close"], combined["DC_mid"]) if "DC_mid" in combined else pd.Series(999, index=combined.index)
    donchian_upper_bars  = _bars_since_cross_series(combined["Close"], combined["DC_upper"]) if "DC_upper" in combined else pd.Series(999, index=combined.index)
    donchian_lower_bars  = _bars_since_cross_series(combined["Close"], combined["DC_lower"]) if "DC_lower" in combined else pd.Series(999, index=combined.index)
    hma_price_bars       = _bars_since_cross_series(combined["Close"], combined["HMA"])    if "HMA"    in combined else pd.Series(999, index=combined.index)
    stoch_signal_bars    = _bars_since_cross_series(combined[stoch_k_col], combined[stoch_d_col]) if stoch_k_col and stoch_d_col else pd.Series(999, index=combined.index)
    stochrsi_signal_bars = _bars_since_cross_series(combined[srsi_k_col], combined[srsi_d_col])    if srsi_k_col and srsi_d_col   else pd.Series(999, index=combined.index)
    cci_centerline_bars  = _cross_bars("CCI", level=0.0)
    willr_midline_bars   = _cross_bars("WILLR", level=-50.0)
    roc_centerline_bars  = _cross_bars("ROC", level=0.0)
    mfi_centerline_bars  = _cross_bars("MFI", level=50.0)
    tsi_centerline_bars  = _cross_bars("TSI", level=0.0)
    ao_zero_bars         = _cross_bars("AO", level=0.0)
    keltner_mid_bars     = _bars_since_cross_series(combined["Close"], combined["KC_mid"]) if "KC_mid" in combined else pd.Series(999, index=combined.index)
    cmf_centerline_bars  = _cross_bars("CMF", level=0.0)
    vp_poc_bars          = _bars_since_cross_series(combined["Close"], combined["VP_POC"]) if "VP_POC" in combined else pd.Series(999, index=combined.index)

    obv_bull_div, obv_bear_div = calculate_price_divergence(df["Close"], combined["OBV"], lookback=obv_div_lookback)
    ad_bull_div, ad_bear_div = (
        calculate_price_divergence(df["Close"], combined["AD_LINE"], lookback=ad_div_lookback)
        if "AD_LINE" in combined
        else (pd.Series(False, index=combined.index), pd.Series(False, index=combined.index))
    )

    warmup = max(
        50, macd_slow + macd_signal + 5, bb_length + 5,
        ichimoku_kijun + ichimoku_senkou, vol_profile_lookback, fib_lookback,
    )

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

        # Ichimoku cloud position
        senkou_a  = _sf(row.get("ICH_senkou_a"))
        senkou_b  = _sf(row.get("ICH_senkou_b"))
        cloud_pos = 0
        if senkou_a is not None and senkou_b is not None:
            cloud_top, cloud_bot = max(senkou_a, senkou_b), min(senkou_a, senkou_b)
            cloud_pos = 1 if close > cloud_top else (-1 if close < cloud_bot else 0)

        # Fibonacci: nearest level + trend context
        fib_nearest = fib_dist_pct = fib_trend = None
        fib_high, fib_low = _sf(row.get("FIB_high")), _sf(row.get("FIB_low"))
        if fib_high is not None and fib_low is not None and close:
            levels = {
                "23.6%": _sf(row.get("FIB_236")), "38.2%": _sf(row.get("FIB_382")),
                "50%":   _sf(row.get("FIB_500")), "61.8%": _sf(row.get("FIB_618")),
                "78.6%": _sf(row.get("FIB_786")),
            }
            valid = {k: v for k, v in levels.items() if v is not None}
            if valid:
                fib_nearest  = min(valid, key=lambda k: abs(close - valid[k]))
                fib_dist_pct = abs(close - valid[fib_nearest]) / close * 100
                fib_trend    = "up" if close > (fib_high + fib_low) / 2 else "down"

        def _expanding(value_col, sma_series):
            v, s = row.get(value_col), sma_series.iloc[i]
            return bool(v > s) if (v == v and s == s) else None  # NaN-safe

        indicators = {
            "rsi": _sf(row.get("RSI")),
            "rsi_trigger": {
                "centerline_cross":     int(rsi_centerline.iloc[i]),
                "bullish_divergence":   bool(rsi_bull_div.iloc[i]),
                "bearish_divergence":   bool(rsi_bear_div.iloc[i]),
                "bullish_failure_swing": bool(rsi_bull_fs.iloc[i]),
                "bearish_failure_swing": bool(rsi_bear_fs.iloc[i]),
            },
            "macd": {
                "macd":      mln,
                "histogram": _sf(row.get(macd_cols[1]) if len(macd_cols) > 1 else None),
                "signal":    msn,
            },
            "macd_trigger": {
                "centerline_bars_since_cross": int(macd_centerline_bars.iloc[i]),
                "centerline_direction":        1 if (mln is not None and mln > 0) else -1,
                "bullish_divergence":          bool(macd_bull_div.iloc[i]),
                "bearish_divergence":          bool(macd_bear_div.iloc[i]),
                "bullish_histogram_reversal":  bool(macd_bull_hr.iloc[i]),
                "bearish_histogram_reversal":  bool(macd_bear_hr.iloc[i]),
                "zscore":                      _sf(macd_zscore.iloc[i]),
            },
            "bollinger_bands": {
                "lower":     _sf(row.get(bb_cols[0]) if bb_cols else None),
                "mid":       _sf(row.get(bb_cols[1]) if len(bb_cols) > 1 else None),
                "upper":     _sf(row.get(bb_cols[2]) if len(bb_cols) > 2 else None),
                "bandwidth": _sf(row.get(bb_cols[3]) if len(bb_cols) > 3 else None),
                "percent_b": _sf(row.get(bb_cols[4]) if len(bb_cols) > 4 else None),
            },
            "bb_trigger": {
                "bull_breakout":  bool(bb_bull_breakout.iloc[i]),
                "bear_breakout":  bool(bb_bear_breakout.iloc[i]),
                "walking_upper":  bool(bb_walking_upper.iloc[i]),
                "walking_lower":  bool(bb_walking_lower.iloc[i]),
                "w_bottom":       bool(bb_w_bottom.iloc[i]),
                "m_top":          bool(bb_m_top.iloc[i]),
            },
            "moving_averages": {
                "ma_20":    m20, "ma_50": m50,
                "ma_200":   _sf(row.get("MA_200")),
                "ema_short": esn, "ema_long": eln,
            },
            "ma_trigger": {
                "price_cross_bars_since": int(price_cross_bars.iloc[i]),
                "price_cross_direction":  1 if (close is not None and ma_short_s.iloc[i] == ma_short_s.iloc[i] and close > ma_short_s.iloc[i]) else -1,
                "two_ma_bars_since":      int(two_ma_bars.iloc[i]),
                "two_ma_direction":       1 if (ma_short_s.iloc[i] == ma_short_s.iloc[i] and ma_long_s.iloc[i] == ma_long_s.iloc[i] and ma_short_s.iloc[i] > ma_long_s.iloc[i]) else -1,
                "three_ma_bull":          bool(three_ma_bull_s.iloc[i]),
                "three_ma_bear":          bool(three_ma_bear_s.iloc[i]),
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
            "inverse_hs": {
                "detected":          bool(hs_detected_s[i]),
                "neckline":          _sf(hs_neckline_s[i]),
                "close":             close,
                "pct_from_neckline": _sf(hs_pct_s[i]),
                "broke_neckline":    bool(hs_broke_s[i]),
            },
            "crossovers": {
                "ema_bars_since_cross":  int(ema_cross.iloc[i]),
                "ema_direction":         1 if (esn and eln and esn > eln) else -1,
                "ma_bars_since_cross":   int(ma_cross.iloc[i]),
                "ma_direction":          1 if (m20 and m50 and m20 > m50) else -1,
                "macd_bars_since_cross": int(macd_cross.iloc[i]),
                "macd_direction":        1 if (mln and msn and mln > msn) else -1,
            },
            # ── Extended indicator set ────────────────────────────────────
            "adx": {
                "adx": _sf(row.get(adx_col)) if adx_col else None,
                "dmp": (dmp_v := _sf(row.get(dmp_col)) if dmp_col else None),
                "dmn": (dmn_v := _sf(row.get(dmn_col)) if dmn_col else None),
                "di_cross_bars_since": int(di_cross_bars.iloc[i]),
                "di_direction":        1 if (dmp_v is not None and dmn_v is not None and dmp_v > dmn_v) else -1,
            },
            "psar": {
                "is_bull":         (bool(psar_dir.iloc[i] == 1) if psar_dir.iloc[i] == psar_dir.iloc[i] else None),
                "bars_since_flip": int(psar_flip.iloc[i]),
                "gap_narrowing":   bool(psar_narrowing_s.iloc[i]),
            },
            "ichimoku": {
                "tenkan": _sf(row.get("ICH_tenkan")), "kijun": _sf(row.get("ICH_kijun")),
                "senkou_a": senkou_a, "senkou_b": senkou_b, "cloud_pos": cloud_pos,
                "tk_cross_bars_since": int(tk_cross_bars.iloc[i]),
                "tk_cross_direction":  1 if (row.get("ICH_tenkan") == row.get("ICH_tenkan") and row.get("ICH_kijun") == row.get("ICH_kijun") and row.get("ICH_tenkan") > row.get("ICH_kijun")) else -1,
            },
            "supertrend": {
                "is_bull":         (bool(row.get(st_dir_col) == 1) if st_dir_col and row.get(st_dir_col) == row.get(st_dir_col) else None),
                "bars_since_flip": int(st_flip.iloc[i]),
                "gap_narrowing":   bool(st_narrowing_s.iloc[i]),
            },
            "donchian": {
                "upper": _sf(row.get("DC_upper")), "mid": _sf(row.get("DC_mid")),
                "lower": _sf(row.get("DC_lower")), "close": close,
                "mid_cross_bars_since": int(donchian_mid_bars.iloc[i]),
                "mid_cross_direction":  1 if (close is not None and row.get("DC_mid") == row.get("DC_mid") and close > row.get("DC_mid")) else -1,
                "exit_upper": _sf(row.get("DC_exit_upper")), "exit_lower": _sf(row.get("DC_exit_lower")),
                "upper_cross_bars_since": int(donchian_upper_bars.iloc[i]),
                "lower_cross_bars_since": int(donchian_lower_bars.iloc[i]),
            },
            "hma": {
                "value": _sf(row.get("HMA")),
                "prev":  _sf(hma_prev.iloc[i]),
                "price_cross_bars_since": int(hma_price_bars.iloc[i]),
                "price_cross_direction":  1 if (close is not None and row.get("HMA") == row.get("HMA") and close > row.get("HMA")) else -1,
                "fast": (hma_fast_v := _sf(row.get("HMA_FAST"))),
                "two_cross_bars_since": int(hma_two_bars.iloc[i]),
                "two_cross_direction":  1 if (hma_fast_v is not None and row.get("HMA") == row.get("HMA") and hma_fast_v > row.get("HMA")) else -1,
            },
            "stochastic": {
                "k": (stoch_k_v := _sf(row.get(stoch_k_col)) if stoch_k_col else None),
                "d": (stoch_d_v := _sf(row.get(stoch_d_col)) if stoch_d_col else None),
                "signal_cross_bars_since": int(stoch_signal_bars.iloc[i]),
                "signal_cross_direction":  1 if (stoch_k_v is not None and stoch_d_v is not None and stoch_k_v > stoch_d_v) else -1,
            },
            "stochrsi": {
                "k": (srsi_k_v := _sf(row.get(srsi_k_col)) if srsi_k_col else None),
                "d": (srsi_d_v := _sf(row.get(srsi_d_col)) if srsi_d_col else None),
                "signal_cross_bars_since": int(stochrsi_signal_bars.iloc[i]),
                "signal_cross_direction":  1 if (srsi_k_v is not None and srsi_d_v is not None and srsi_k_v > srsi_d_v) else -1,
                "bullish_divergence": bool(stochrsi_bull_div.iloc[i]),
                "bearish_divergence": bool(stochrsi_bear_div.iloc[i]),
            },
            "cci": {
                "value": (cci_v := _sf(row.get("CCI"))),
                "centerline_bars_since": int(cci_centerline_bars.iloc[i]),
                "centerline_direction":  1 if (cci_v is not None and cci_v > 0) else -1,
            },
            "willr": {
                "value": (willr_v := _sf(row.get("WILLR"))),
                "midline_bars_since": int(willr_midline_bars.iloc[i]),
                "midline_direction":  1 if (willr_v is not None and willr_v > -50) else -1,
                "bullish_divergence": bool(willr_bull_div.iloc[i]),
                "bearish_divergence": bool(willr_bear_div.iloc[i]),
                "bullish_confirmation": bool(willr_bull_conf.iloc[i]),
                "bearish_confirmation": bool(willr_bear_conf.iloc[i]),
                "bullish_failure_swing": bool(willr_bull_fs.iloc[i]),
                "bearish_failure_swing": bool(willr_bear_fs.iloc[i]),
            },
            "roc": {
                "value": (roc_v := _sf(row.get("ROC"))),
                "centerline_bars_since": int(roc_centerline_bars.iloc[i]),
                "centerline_direction":  1 if (roc_v is not None and roc_v > 0) else -1,
                "prev": _sf(roc_prev.iloc[i]),
                "bullish_divergence": bool(roc_bull_div.iloc[i]),
                "bearish_divergence": bool(roc_bear_div.iloc[i]),
            },
            "mfi": {
                "value": (mfi_v := _sf(row.get("MFI"))),
                "centerline_bars_since": int(mfi_centerline_bars.iloc[i]),
                "centerline_direction":  1 if (mfi_v is not None and mfi_v > 50) else -1,
                "bullish_divergence": bool(mfi_bull_div.iloc[i]),
                "bearish_divergence": bool(mfi_bear_div.iloc[i]),
            },
            "tsi": {
                "value":  (tsi_v := _sf(row.get("TSI"))),
                "signal": _sf(row.get("TSI_signal")),
                "centerline_bars_since": int(tsi_centerline_bars.iloc[i]),
                "centerline_direction":  1 if (tsi_v is not None and tsi_v > 0) else -1,
                "bullish_divergence": bool(tsi_bull_div.iloc[i]),
                "bearish_divergence": bool(tsi_bear_div.iloc[i]),
            },
            "awesome_oscillator": {
                "value": (ao_v := _sf(row.get("AO"))),
                "zero_cross_bars_since": int(ao_zero_bars.iloc[i]),
                "zero_cross_direction":  1 if (ao_v is not None and ao_v > 0) else -1,
                "bull_saucer": bool(ao_bull_saucer.iloc[i]),
                "bear_saucer": bool(ao_bear_saucer.iloc[i]),
                "bull_twin_peaks": bool(ao_bull_twin.iloc[i]),
                "bear_twin_peaks": bool(ao_bear_twin.iloc[i]),
                "bullish_divergence": bool(ao_bull_div.iloc[i]),
                "bearish_divergence": bool(ao_bear_div.iloc[i]),
            },
            "atr": {
                "value":           _sf(row.get("ATR")),
                "expanding":       _expanding("ATR", atr_sma),
                "close_trend_ref": _sf(close_shift_atr.iloc[i]),
            },
            "keltner": {
                "upper": _sf(row.get("KC_upper")), "mid": _sf(row.get("KC_mid")), "lower": _sf(row.get("KC_lower")),
                "mid_cross_bars_since": int(keltner_mid_bars.iloc[i]),
                "mid_cross_direction":  1 if (close is not None and row.get("KC_mid") == row.get("KC_mid") and close > row.get("KC_mid")) else -1,
                "walking_upper": bool(kc_walking_upper.iloc[i]),
                "walking_lower": bool(kc_walking_lower.iloc[i]),
                "squeeze_on": bool(kc_squeeze_on.iloc[i]),
                "squeeze_bull_release": bool(kc_squeeze_bull.iloc[i]),
                "squeeze_bear_release": bool(kc_squeeze_bear.iloc[i]),
            },
            "stdev": {
                "value":           _sf(row.get("STDEV")),
                "expanding":       _expanding("STDEV", stdev_sma),
                "close_trend_ref": _sf(close_shift_stdev.iloc[i]),
            },
            "chaikin_vol": {
                "value":           _sf(row.get("CHAIKIN_VOL")),
                "expanding":       _expanding("CHAIKIN_VOL", cv_sma),
                "close_trend_ref": _sf(close_shift_cv.iloc[i]),
            },
            "hist_vol": {
                "value":           _sf(row.get("HIST_VOL")),
                "expanding":       _expanding("HIST_VOL", hv_sma),
                "close_trend_ref": _sf(close_shift_hv.iloc[i]),
            },
            "obv_trend": {
                "obv":     _sf(row.get("OBV")),
                "obv_sma": _sf(obv_sma.iloc[i]),
                "bullish_divergence": bool(obv_bull_div.iloc[i]),
                "bearish_divergence": bool(obv_bear_div.iloc[i]),
            },
            "vwap": {
                "value": (vwap_v := _sf(row.get("VWAP_ROLL"))),
                "upper_band": _sf(vwap_v * (1 + vwap_band_pct / 100)) if vwap_v is not None else None,
                "lower_band": _sf(vwap_v * (1 - vwap_band_pct / 100)) if vwap_v is not None else None,
                "prev_close": _sf(combined["Close"].iloc[i - 1]) if i > 0 else None,
                "prev_value": _sf(vwap_s.iloc[i - 1]) if i > 0 and vwap_s is not None else None,
            },
            "ad_trend": {
                "ad":     _sf(row.get("AD_LINE")),
                "ad_sma": _sf(ad_sma.iloc[i]),
                "bullish_divergence": bool(ad_bull_div.iloc[i]),
                "bearish_divergence": bool(ad_bear_div.iloc[i]),
            },
            "cmf": {
                "value": (cmf_v := _sf(row.get("CMF"))),
                "centerline_bars_since": int(cmf_centerline_bars.iloc[i]),
                "centerline_direction":  1 if (cmf_v is not None and cmf_v > 0) else -1,
            },
            "volume_profile": {
                "poc": (poc_v := _sf(row.get("VP_POC"))),
                "breakout_bars_since": int(vp_poc_bars.iloc[i]),
                "breakout_direction":  1 if (close is not None and poc_v is not None and close > poc_v) else -1,
            },
            "fibonacci": {
                "nearest_level": fib_nearest, "distance_pct": fib_dist_pct, "trend": fib_trend,
                "prev_close": _sf(combined["Close"].iloc[i - 1]) if i > 0 else None,
            },
        }

        result     = score_signals(indicators, t)
        overall    = result["overall"]
        confidence = result["confidence"]

        # ── Manage open position ──────────────────────────────────────────
        if position is not None:
            ep       = position["entry_price"]
            sl_price = position["sl_price"]
            tp_price = position["tp_price"]

            trail_price = None
            if trailing_stop:
                position["peak"] = max(position["peak"], high)
                trail_price = position["peak"] * (1 - trail_distance_pct / 100)

            # Trailing stop only ever tightens the floor set by the fixed stop.
            effective_sl   = max(sl_price, trail_price) if trail_price is not None else sl_price
            trail_is_tighter = trail_price is not None and effective_sl == trail_price and trail_price > sl_price

            exit_reason = exit_price = None

            if low <= effective_sl:
                exit_reason = "Trailing Stop" if trail_is_tighter else "Stop Loss"
                exit_price  = max(low, effective_sl)
            elif high >= tp_price:
                exit_reason = "Take Profit"
                exit_price  = min(high, tp_price)
            elif overall == "SELL" and confidence >= min_confidence:
                exit_reason = "Signal"
                exit_price  = close

            if exit_reason:
                ret           = (exit_price - ep) / ep * 100
                f             = position["size_fraction"]
                equity_before = equity
                equity       *= 1 + f * ret / 100
                trades.append({
                    "entry_date":  position["entry_date"],
                    "exit_date":   date_str,
                    "entry_price": round(ep, 4),
                    "exit_price":  round(exit_price, 4),
                    "return_pct":  round(ret, 2),
                    "exit_reason": exit_reason,
                    "size_pct":      round(f * 100, 2),
                    "equity_before": round(equity_before, 6),
                    "equity_after":  round(equity, 6),
                    "pnl_gbp":       round(capital * (equity - equity_before), 2),
                })
                position = None

        else:
            if overall == "BUY" and confidence >= min_confidence:
                pot_value = equity * capital
                if trade_amount_mode == "gbp":
                    size_fraction = min(max(trade_amount / pot_value, 0.0), 1.0) if pot_value > 0 else 0.0
                else:
                    size_fraction = min(max(trade_amount / 100, 0.01), 1.0)
                invested_gbp = size_fraction * pot_value

                # Stop Loss / Take Profit are a % of STARTING capital, not of the
                # entry price — convert that £ target into whatever price move on
                # THIS trade's actual invested amount is needed to reach it. With
                # a small Trade Amount relative to capital this can require a very
                # large price move (by design — see the £-vs-%-of-capital tradeoff
                # this was built for).
                if invested_gbp > 0:
                    tp_price_move_pct = (capital * take_profit_pct / 100) / invested_gbp * 100
                    sl_price_move_pct = (capital * stop_loss_pct   / 100) / invested_gbp * 100
                else:
                    tp_price_move_pct = take_profit_pct
                    sl_price_move_pct = stop_loss_pct

                position = {
                    "entry_price": close, "entry_date": date_str, "peak": close,
                    "size_fraction": size_fraction,
                    "sl_price": close * (1 - sl_price_move_pct / 100),
                    "tp_price": close * (1 + tp_price_move_pct / 100),
                }

        equity_curve.append({"date": date_str, "equity": round(equity, 6)})

    # Close any position still open at end of data
    if position is not None:
        lc            = _sf(combined.iloc[-1].get("Close")) or position["entry_price"]
        ret           = (lc - position["entry_price"]) / position["entry_price"] * 100
        f             = position["size_fraction"]
        equity_before = equity
        equity       *= 1 + f * ret / 100
        trades.append({
            "entry_date":  position["entry_date"],
            "exit_date":   str(combined.index[-1]),
            "entry_price": round(position["entry_price"], 4),
            "exit_price":  round(lc, 4),
            "return_pct":  round(ret, 2),
            "exit_reason": "End of Data",
            "size_pct":      round(f * 100, 2),
            "equity_before": round(equity_before, 6),
            "equity_after":  round(equity, 6),
            "pnl_gbp":       round(capital * (equity - equity_before), 2),
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


def _bars_since_flip_series(sign: pd.Series) -> pd.Series:
    """O(n) precomputation: how many bars since a single +1/-1 series last flipped sign."""
    result     = [999] * len(sign)
    bars_since = 999
    prev       = None
    for i in range(len(sign)):
        v = sign.iloc[i]
        if v != v:   # NaN
            result[i] = 999
            prev = None
            continue
        if prev is not None and v != prev:
            bars_since = 0
        result[i] = bars_since
        if bars_since < 999:
            bars_since += 1
        prev = v
    return pd.Series(result, index=sign.index, dtype=int)


def _find_col(cols: list[str], prefix: str) -> str | None:
    prefix = prefix.upper()
    return next((c for c in cols if c.upper().startswith(prefix)), None)


def _try(fn):
    try:
        return fn()
    except Exception:
        return None


def _sf(val):
    try:
        if val is None:
            return None
        v = float(val)
        return None if v != v else round(v, 6)  # NaN → None
    except Exception:
        return None
