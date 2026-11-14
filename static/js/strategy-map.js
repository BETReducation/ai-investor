// Shared Signals <-> Backtester strategy translation tables. Loaded by signal_config.html and the
// Backtester pages (strategy-lab*.html). Backtester indicator toggle + trigger-chip mode -> Signals condition types;
// Signals import it directly, the Backtester inverts it for "Copy strategy from Signals".
const BT_INDICATOR_MAP = {
  togRsi:        { group: 'RSI',                  chips: 'rsiTriggerChips',       modes: {
    overbought_oversold: ['rsi_below', 'rsi_above'], overbought: ['rsi_above'], oversold: ['rsi_below'],
    centerline_cross: ['rsi_centerline_up', 'rsi_centerline_down'],
    bullish_divergence: ['rsi_bull_divergence'], bearish_divergence: ['rsi_bear_divergence'],
    failure_swings: ['rsi_failure_swing_bull', 'rsi_failure_swing_bear'],
  }},
  togMacd:       { group: 'MACD',                 chips: 'macdTriggerChips',      modes: {
    signal_cross: ['macd_bull_cross', 'macd_bear_cross'],
    bullish_signal_cross: ['macd_bull_cross'], bearish_signal_cross: ['macd_bear_cross'],
    centerline_cross: ['macd_centerline_up', 'macd_centerline_down'],
    bullish_divergence: ['macd_bull_divergence'], bearish_divergence: ['macd_bear_divergence'],
    histogram_reversal: ['macd_histogram_reversal_bull', 'macd_histogram_reversal_bear'],
    overbought: ['macd_zscore_overbought'], oversold: ['macd_zscore_oversold'],
  }},
  togBb:         { group: 'Bollinger',            chips: 'bbTriggerChips',        modes: {
    percent_b: ['bb_lower', 'bb_upper'], upper_touch: ['bb_broke_upper'], lower_touch: ['bb_broke_lower'],
    volatility_breakout: ['bb_volatility_breakout_bull', 'bb_volatility_breakout_bear'],
    walking_upper: ['bb_walking_upper'], walking_lower: ['bb_walking_lower'],
    w_bottom: ['bb_w_bottom'], m_top: ['bb_m_top'],
    breakout_margin: [], pct_below_high: [], pct_above_low: [],
  }},
  togMa:         { group: 'MA',                   chips: 'maTriggerChips',        modes: {
    dual_cross: ['ma_golden', 'ma_death'], price_cross: ['ma_price_cross_bull', 'ma_price_cross_bear'],
    two_ma_bull: ['ma_two_bull'], two_ma_bear: ['ma_two_bear'],
    three_ma_bull: ['ma_three_bull'], three_ma_bear: ['ma_three_bear'],
  }},
  togAdx:        { group: 'ADX',                  chips: 'adxTriggerChips',       modes: {
    trend_threshold: ['adx_above'], above_25: ['adx_above'], above_50: ['adx_above'], above_75: ['adx_above'],
    bull_di_cross: ['adx_di_bull_cross'], bear_di_cross: ['adx_di_bear_cross'],
    strong_di_plus: ['adx_di_bull'], strong_di_minus: ['adx_di_bear'],
  }},
  togPsar:       { group: 'Parabolic SAR',        chips: 'psarTriggerChips',      modes: {
    flip: ['psar_bull_flip', 'psar_bear_flip'], bull_flip: ['psar_bull_flip'], bear_flip: ['psar_bear_flip'],
    trend_state: ['psar_bull', 'psar_bear'], trailing_stop: ['psar_narrowing'],
  }},
  togIchimoku:   { group: 'Ichimoku',             chips: 'ichimokuTriggerChips',  modes: {
    cloud_position: ['ichimoku_cloud_bullish', 'ichimoku_cloud_bearish'],
    bullish: ['ichimoku_cloud_bullish'], bearish: ['ichimoku_cloud_bearish'],
    tk_cross: ['ichimoku_tk_bull_cross', 'ichimoku_tk_bear_cross'],
  }},
  togSupertrend: { group: 'Supertrend',           chips: 'supertrendTriggerChips', modes: {
    flip: ['supertrend_bull_flip', 'supertrend_bear_flip'], bull_flip: ['supertrend_bull_flip'], bear_flip: ['supertrend_bear_flip'],
    trend_state: ['supertrend_bull', 'supertrend_bear'], trailing_stop: ['supertrend_narrowing'],
  }},
  togDonchian:   { group: 'Donchian',             chips: 'donchianTriggerChips',  modes: {
    breakout: ['donchian_breakout_bull', 'donchian_breakout_bear'],
    bullish: ['donchian_breakout_bull'], bearish: ['donchian_breakout_bear'],
    middle_cross: ['donchian_mid_cross_bull', 'donchian_mid_cross_bear'],
    two_channel_bull: [], two_channel_bear: [], resistance_retest: [], support_retest: [],
  }},
  togHma:        { group: 'HMA',                  chips: 'hmaTriggerChips',       modes: {
    slope: ['hma_slope_bull', 'hma_slope_bear'], bullish_slope: ['hma_slope_bull'], bearish_slope: ['hma_slope_bear'],
    price_cross: ['hma_price_cross_bull', 'hma_price_cross_bear'],
    two_hma_bull: ['hma_two_cross_bull'], two_hma_bear: ['hma_two_cross_bear'],
  }},
  togStoch:      { group: 'Stochastic',           chips: 'stochTriggerChips',     modes: {
    overbought_oversold: ['stoch_k_below', 'stoch_k_above'], overbought: ['stoch_k_above'], oversold: ['stoch_k_below'],
    signal_cross: ['stoch_bull_cross', 'stoch_bear_cross'],
  }},
  togStochrsi:   { group: 'StochRSI',             chips: 'stochrsiTriggerChips',  modes: {
    overbought_oversold: ['stochrsi_below', 'stochrsi_above'], overbought: ['stochrsi_above'], oversold: ['stochrsi_below'],
    signal_cross: ['stochrsi_bull_cross', 'stochrsi_bear_cross'],
    bullish_divergence: ['stochrsi_bull_divergence'], bearish_divergence: ['stochrsi_bear_divergence'],
  }},
  togCci:        { group: 'CCI',                  chips: 'cciTriggerChips',       modes: {
    overbought_oversold: ['cci_below', 'cci_above'], overbought: ['cci_above'], oversold: ['cci_below'],
    centerline_cross: ['cci_centerline_up', 'cci_centerline_down'],
    breakout_bull: ['cci_breakout_bull'], breakout_bear: ['cci_breakout_bear'],
  }},
  togWillr:      { group: 'Williams %R',          chips: 'willrTriggerChips',     modes: {
    overbought_oversold: ['willr_below', 'willr_above'], overbought: ['willr_above'], oversold: ['willr_below'],
    midline_cross: ['willr_midline_bull', 'willr_midline_bear'],
    momentum_failure_bull: ['willr_failure_swing_bull'], momentum_failure_bear: ['willr_failure_swing_bear'],
    trend_confirmation_bull: ['willr_trend_confirm_bull'], trend_confirmation_bear: ['willr_trend_confirm_bear'],
    bullish_divergence: ['willr_bull_divergence'], bearish_divergence: ['willr_bear_divergence'],
  }},
  togRoc:        { group: 'ROC',                  chips: 'rocTriggerChips',       modes: {
    threshold: [], bullish: ['roc_positive'], bearish: ['roc_negative'],
    centerline_cross: ['roc_positive', 'roc_negative'],
    bull_momentum: ['roc_bull_momentum'], bear_momentum: ['roc_bear_momentum'],
    bullish_divergence: ['roc_bull_divergence'], bearish_divergence: ['roc_bear_divergence'],
  }},
  togMfi:        { group: 'MFI',                  chips: 'mfiTriggerChips',       modes: {
    overbought_oversold: ['mfi_below', 'mfi_above'], overbought: ['mfi_above'], oversold: ['mfi_below'],
    centerline_cross: ['mfi_centerline_up', 'mfi_centerline_down'],
    bullish_divergence: ['mfi_bull_divergence'], bearish_divergence: ['mfi_bear_divergence'],
  }},
  togTsi:        { group: 'TSI',                  chips: 'tsiTriggerChips',       modes: {
    signal_cross: ['tsi_bull_cross', 'tsi_bear_cross'], bullish: ['tsi_bull_cross'], bearish: ['tsi_bear_cross'],
    centerline_cross: ['tsi_centerline_up', 'tsi_centerline_down'],
    overbought: [], oversold: [],
    bullish_divergence: ['tsi_bull_divergence'], bearish_divergence: ['tsi_bear_divergence'],
  }},
  togAo:         { group: 'Awesome Oscillator',   chips: 'aoTriggerChips',        modes: {
    zero_state: ['ao_zero_cross_bull', 'ao_zero_cross_bear'], bullish: ['ao_zero_cross_bull'], bearish: ['ao_zero_cross_bear'],
    zero_cross: ['ao_zero_cross_bull', 'ao_zero_cross_bear'],
    bull_saucer: ['ao_bull_saucer'], bear_saucer: ['ao_bear_saucer'],
    bull_twin_peaks: ['ao_bull_twin_peaks'], bear_twin_peaks: ['ao_bear_twin_peaks'],
    bull_divergence: ['ao_bull_divergence'], bear_divergence: ['ao_bear_divergence'],
  }},
  togAtr:        { group: 'ATR',                  chips: 'atrTriggerChips',       modes: {
    expansion: ['atr_expanding'], bullish_expansion: ['atr_bullish_expansion'], bearish_expansion: ['atr_bearish_expansion'],
    contraction: ['atr_contracting'],
  }},
  togKeltner:    { group: 'Keltner',              chips: 'keltnerTriggerChips',   modes: {
    breakout: ['keltner_breakout_bull', 'keltner_breakout_bear'],
    bullish: ['keltner_breakout_bull'], bearish: ['keltner_breakout_bear'],
    middle_cross: [], bull_band_riding: ['keltner_walking_upper'], bear_band_riding: ['keltner_walking_lower'],
    bull_mean_reversion: [], bear_mean_reversion: [], keltner_squeeze: ['keltner_squeeze'],
  }},
  togStdev:      { group: 'Stdev',                chips: 'stdevTriggerChips',     modes: {
    expansion: ['stdev_bullish_expansion', 'stdev_bearish_expansion'],
    bullish_expansion: ['stdev_bullish_expansion'], bearish_expansion: ['stdev_bearish_expansion'],
    contraction: ['stdev_contracting'],
  }},
  togChaikinVol: { group: 'Chaikin Volatility',   chips: 'chaikinVolTriggerChips', modes: {
    expansion: ['chaikin_vol_bullish_expansion', 'chaikin_vol_bearish_expansion'],
    bullish_expansion: ['chaikin_vol_bullish_expansion'], bearish_expansion: ['chaikin_vol_bearish_expansion'],
    contraction: ['chaikin_vol_contracting'],
  }},
  togHistVol:    { group: 'Historical Volatility', chips: 'histVolTriggerChips',  modes: {
    expansion: ['hist_vol_bullish_expansion', 'hist_vol_bearish_expansion'],
    bullish_expansion: ['hist_vol_bullish_expansion'], bearish_expansion: ['hist_vol_bearish_expansion'],
    contraction: ['hist_vol_contracting'],
  }},
  togObv:        { group: 'OBV',                  chips: 'obvTriggerChips',       modes: {
    trend: ['obv_trend_bull', 'obv_trend_bear'], bullish: ['obv_trend_bull'], bearish: ['obv_trend_bear'],
    divergence: ['obv_bull_divergence', 'obv_bear_divergence'],
  }},
  togVwap:       { group: 'VWAP',                 chips: 'vwapTriggerChips',      modes: {
    position: ['price_above_vwap', 'price_below_vwap'], bullish: ['price_above_vwap'], bearish: ['price_below_vwap'],
    band_touch: ['vwap_rolling_band_touch'], pullback_buy: [], pullback_sell: [],
  }},
  togAd:         { group: 'A/D Line',             chips: 'adTriggerChips',        modes: {
    trend: ['ad_line_trend_bull', 'ad_line_trend_bear'], bullish: ['ad_line_trend_bull'], bearish: ['ad_line_trend_bear'],
    divergence: ['ad_line_bull_divergence', 'ad_line_bear_divergence'],
  }},
  togCmf:        { group: 'CMF',                  chips: 'cmfTriggerChips',       modes: {
    threshold: ['cmf_above', 'cmf_below'], bullish: ['cmf_above'], bearish: ['cmf_below'],
    centerline_cross: ['cmf_centerline_up', 'cmf_centerline_down'],
  }},
  togVolProfile: { group: 'Volume Profile',       chips: 'volProfileTriggerChips', modes: {
    position: ['vp_poc_bullish'], bullish: ['vp_poc_bullish'], bearish: [],
    poc_breakout: ['vp_poc_breakout_bull', 'vp_poc_breakout_bear'],
  }},
  togFib:        { group: 'Fibonacci',            chips: 'fibTriggerChips',       modes: {
    bounce_reject: ['fib_any_touch'], bullish_bounce: ['fib_any_touch'], bearish_reject: ['fib_any_touch'], any_touch: ['fib_any_touch'],
  }},
  togInvHs:      { group: 'Inverse H&S',          chips: 'invHsTriggerChips',     modes: {
    neckline_touch: ['inv_hs_neckline'], neckline_break: ['inv_hs_neckline'],
  }},
  // Volume has no trigger-mode chip row in the Backtester (it's a plain on/off
  // confirmation filter, not a multi-mode indicator) — CONDITION_VALUE_KEYS
  // below carries its surge multiplier across the same way as any other
  // condition's threshold.
  togVol:        { group: 'Volume', modes: { spike: ['volume_spike'] } },
};

const CONDITION_VALUE_KEYS = {
  rsi_below:      { basic: 'rsiOversoldBasic',   detailed: 'rsiOversold' },
  rsi_above:      { basic: 'rsiOverboughtBasic', detailed: 'rsiOverbought' },
  volume_spike:   { basic: 'volSurgeBasic',      detailed: 'volSurge' },
  cci_below:      { detailed: 'cciOversold' },
  cci_above:      { detailed: 'cciOverbought' },
  willr_below:    { detailed: 'willrOversold' },
  willr_above:    { detailed: 'willrOverbought' },
  mfi_below:      { detailed: 'mfiOversold' },
  mfi_above:      { detailed: 'mfiOverbought' },
  stoch_k_below:  { detailed: 'stochOversold' },
  stoch_k_above:  { detailed: 'stochOverbought' },
  stochrsi_below: { detailed: 'stochrsiOversold' },
  stochrsi_above: { detailed: 'stochrsiOverbought' },
  adx_above:      { detailed: 'adxTrendThreshold' },
  cmf_above:      { detailed: 'cmfThreshold' },
  cmf_below:      { detailed: 'cmfThreshold', transform: v => -v },
};

const BT_BASIC_TOGGLE_MAP = {
  togRsiBasic:      { togId: 'togRsi',      chips: 'rsiTriggerChips',      defaultMode: 'overbought_oversold' },
  togMacdBasic:     { togId: 'togMacd',     chips: 'macdTriggerChips',     defaultMode: 'signal_cross' },
  togBbBasic:       { togId: 'togBb',       chips: 'bbTriggerChips',       defaultMode: 'percent_b' },
  togMaBasic:       { togId: 'togMa',       chips: 'maTriggerChips',       defaultMode: 'dual_cross' },
  togDonchianBasic: { togId: 'togDonchian', chips: 'donchianTriggerChips', defaultMode: 'breakout' },
  togVolBasic:      { togId: 'togVol',      chips: null,                  defaultMode: 'spike' },
};
// Signals condition param id -> Backtester sidebar field id, per indicator group (Signals INDICATOR_PARAMS apiKey, camelCased).
const SIGNALS_PARAM_FIELDS = {"RSI":{"period":"rsiLength","smoothing":"rsiSmoothing"},"Stochastic":{"k":"stochK","d":"stochD","smooth":"stochSmooth"},"StochRSI":{"length":"stochrsiLength","k":"stochrsiK","d":"stochrsiD"},"MACD":{"fast":"macdFast","slow":"macdSlow","signal":"macdSignal"},"CCI":{"length":"cciLength"},"Williams %R":{"length":"willrLength"},"Bollinger":{"length":"bbLength","std":"bbStd"},"ADX":{"length":"adxLength"},"ATR":{"length":"atrLength"},"MFI":{"length":"mfiLength"},"Supertrend":{"length":"supertrendLength","mult":"supertrendMult"},"Aroon":{"length":"aroonLength"},"Parabolic SAR":{"start":"psarStart","inc":"psarInc","max":"psarMax"},"ROC":{"length":"rocLength"},"MA":{"short":"emaShort","long":"emaLong","maType":"maType","maShort":"maShortLength","maMedium":"maMediumLength","maLong":"maLongLength"},"Inverse H&S":{"pivot":"hsPivot","lookback":"hsLookback"},"VWAP":{"length":"vwapLength","bandPct":"vwapBandPct"},"HMA":{"length":"hmaLength","fastLength":"hmaFastLength"},"Ichimoku":{"tenkan":"ichimokuTenkan","kijun":"ichimokuKijun","senkou":"ichimokuSenkou"},"Donchian":{"length":"donchianLength"},"Keltner":{"length":"keltnerLength","atrLength":"keltnerAtrLength","mult":"keltnerMult"},"Stdev":{"length":"stdevLength"},"Chaikin Volatility":{"emaLength":"chaikinVolEmaLength","rocLength":"chaikinVolRocLength"},"Historical Volatility":{"length":"histVolLength"},"A/D Line":{"smaLength":"adSmaLength"},"CMF":{"length":"cmfLength"},"TSI":{"long":"tsiLong","short":"tsiShort","signal":"tsiSignal"},"Awesome Oscillator":{"fast":"aoFast","slow":"aoSlow"},"OBV":{"smaLength":"obvSmaLength"},"Volume Profile":{"lookback":"volProfileLookback","bins":"volProfileBins"},"Fibonacci":{"lookback":"fibLookback","tolPct":"fibTolerancePct"}};
