import pandas as pd
import pandas_ta as ta


def calculate_rsi(df: pd.DataFrame, length: int = 14) -> pd.Series:
    return ta.rsi(df["Close"], length=length)


def calculate_macd(df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    macd = ta.macd(df["Close"], fast=fast, slow=slow, signal=signal)
    return macd  # columns: MACD_f_s_sig, MACDh_f_s_sig, MACDs_f_s_sig


def calculate_bollinger_bands(df: pd.DataFrame, length: int = 20, std: float = 2.0) -> pd.DataFrame:
    bbands = ta.bbands(df["Close"], length=length, std=std)
    return bbands  # columns: BBL, BBM, BBU, BBB, BBP


def calculate_moving_averages(df: pd.DataFrame, ema_short: int = 9, ema_long: int = 21) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    result["MA_20"] = ta.sma(df["Close"], length=20)
    result["MA_50"] = ta.sma(df["Close"], length=50)
    result["MA_200"] = ta.sma(df["Close"], length=200)
    result[f"EMA_{ema_short}"] = ta.ema(df["Close"], length=ema_short)
    result[f"EMA_{ema_long}"] = ta.ema(df["Close"], length=ema_long)
    return result


def calculate_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    result["Volume"] = df["Volume"]
    result["Vol_SMA_20"] = ta.sma(df["Volume"], length=20)
    result["OBV"] = ta.obv(df["Close"], df["Volume"])
    return result


def calculate_all(
    df: pd.DataFrame,
    rsi_length: int = 14,
    macd_fast: int = 12,
    macd_slow: int = 26,
    macd_signal: int = 9,
    bb_length: int = 20,
    bb_std: float = 2.0,
    ema_short: int = 9,
    ema_long: int = 21,
) -> dict:
    rsi = calculate_rsi(df, length=rsi_length)
    macd = calculate_macd(df, fast=macd_fast, slow=macd_slow, signal=macd_signal)
    bbands = calculate_bollinger_bands(df, length=bb_length, std=bb_std)
    mas = calculate_moving_averages(df, ema_short=ema_short, ema_long=ema_long)
    vol = calculate_volume_indicators(df)

    combined = pd.concat([df, mas, vol, rsi.rename("RSI"), macd, bbands], axis=1)
    combined.dropna(how="all", inplace=True)

    latest = combined.iloc[-1]

    macd_cols = [c for c in macd.columns]
    bb_cols = [c for c in bbands.columns]

    ema_short_col = f"EMA_{ema_short}"
    ema_long_col = f"EMA_{ema_long}"
    ema_bars = _bars_since_cross(combined[ema_short_col], combined[ema_long_col])
    ma_bars = _bars_since_cross(combined["MA_20"], combined["MA_50"])
    ema_short_now = latest.get(ema_short_col)
    ema_long_now = latest.get(ema_long_col)
    ma20_now = latest.get("MA_20")
    ma50_now = latest.get("MA_50")

    macd_line_col = macd_cols[0] if macd_cols else None
    macd_sig_col = macd_cols[2] if len(macd_cols) > 2 else None
    if macd_line_col and macd_sig_col:
        macd_bars = _bars_since_cross(combined[macd_line_col], combined[macd_sig_col])
        macd_line_now = latest.get(macd_line_col)
        macd_sig_now = latest.get(macd_sig_col)
    else:
        macd_bars = 999
        macd_line_now = macd_sig_now = None

    return {
        "rsi": _safe_float(latest.get("RSI")),
        "macd": {
            "macd": _safe_float(latest.get(macd_cols[0]) if macd_cols else None),
            "histogram": _safe_float(latest.get(macd_cols[1]) if len(macd_cols) > 1 else None),
            "signal": _safe_float(latest.get(macd_cols[2]) if len(macd_cols) > 2 else None),
        },
        "bollinger_bands": {
            # pandas_ta order: BBL, BBM, BBU, BBB, BBP
            "lower": _safe_float(latest.get(bb_cols[0]) if bb_cols else None),
            "mid":   _safe_float(latest.get(bb_cols[1]) if len(bb_cols) > 1 else None),
            "upper": _safe_float(latest.get(bb_cols[2]) if len(bb_cols) > 2 else None),
            "bandwidth": _safe_float(latest.get(bb_cols[3]) if len(bb_cols) > 3 else None),
            "percent_b": _safe_float(latest.get(bb_cols[4]) if len(bb_cols) > 4 else None),
        },
        "moving_averages": {
            "ma_20": _safe_float(ma20_now),
            "ma_50": _safe_float(ma50_now),
            "ma_200": _safe_float(latest.get("MA_200")),
            "ema_short": _safe_float(ema_short_now),
            "ema_long": _safe_float(ema_long_now),
        },
        "volume": {
            "current": _safe_float(latest.get("Volume")),
            "sma_20": _safe_float(latest.get("Vol_SMA_20")),
            "obv": _safe_float(latest.get("OBV")),
            "ratio": _safe_float(
                latest.get("Volume") / latest.get("Vol_SMA_20")
                if latest.get("Vol_SMA_20") and latest.get("Vol_SMA_20") != 0
                else None
            ),
        },
        "price": {
            "close": _safe_float(latest.get("Close")),
            "open": _safe_float(latest.get("Open")),
            "high": _safe_float(latest.get("High")),
            "low": _safe_float(latest.get("Low")),
        },
        "crossovers": {
            "ema_bars_since_cross": ema_bars,
            "ema_direction": 1 if (ema_short_now and ema_long_now and ema_short_now > ema_long_now) else -1,
            "ma_bars_since_cross": ma_bars,
            "ma_direction": 1 if (ma20_now and ma50_now and ma20_now > ma50_now) else -1,
            "macd_bars_since_cross": macd_bars,
            "macd_direction": 1 if (macd_line_now and macd_sig_now and macd_line_now > macd_sig_now) else -1,
        },
        "history": _recent_ohlcv(combined),
    }


def _bars_since_cross(a: pd.Series, b: pd.Series) -> int:
    """Returns how many bars ago series a last crossed series b. Returns 999 if no cross found."""
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


def _safe_float(val):
    try:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return None
        return round(float(val), 6)
    except Exception:
        return None


def _recent_ohlcv(df: pd.DataFrame, n: int = 100) -> list:
    cols = [c for c in ["Open", "High", "Low", "Close", "Volume"] if c in df.columns]
    subset = df[cols].tail(n).copy()
    subset = subset.loc[:, ~subset.columns.duplicated()]
    subset.index = subset.index.astype(str)
    records = subset.reset_index()
    records.rename(columns={records.columns[0]: "date"}, inplace=True)
    return records.to_dict(orient="records")
