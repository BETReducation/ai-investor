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


def calculate_moving_averages(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    result["MA_20"] = ta.sma(df["Close"], length=20)
    result["MA_50"] = ta.sma(df["Close"], length=50)
    result["MA_200"] = ta.sma(df["Close"], length=200)
    result["EMA_9"] = ta.ema(df["Close"], length=9)
    result["EMA_21"] = ta.ema(df["Close"], length=21)
    return result


def calculate_volume_indicators(df: pd.DataFrame) -> pd.DataFrame:
    result = pd.DataFrame(index=df.index)
    result["Volume"] = df["Volume"]
    result["Vol_SMA_20"] = ta.sma(df["Volume"], length=20)
    result["OBV"] = ta.obv(df["Close"], df["Volume"])
    return result


def calculate_all(df: pd.DataFrame) -> dict:
    rsi = calculate_rsi(df)
    macd = calculate_macd(df)
    bbands = calculate_bollinger_bands(df)
    mas = calculate_moving_averages(df)
    vol = calculate_volume_indicators(df)

    combined = pd.concat([df, mas, vol, rsi.rename("RSI"), macd, bbands], axis=1)
    combined.dropna(how="all", inplace=True)

    latest = combined.iloc[-1]

    macd_cols = [c for c in macd.columns]
    bb_cols = [c for c in bbands.columns]

    return {
        "rsi": _safe_float(latest.get("RSI")),
        "macd": {
            "macd": _safe_float(latest.get(macd_cols[0]) if macd_cols else None),
            "histogram": _safe_float(latest.get(macd_cols[1]) if len(macd_cols) > 1 else None),
            "signal": _safe_float(latest.get(macd_cols[2]) if len(macd_cols) > 2 else None),
        },
        "bollinger_bands": {
            "upper": _safe_float(latest.get(bb_cols[0]) if bb_cols else None),
            "mid": _safe_float(latest.get(bb_cols[1]) if len(bb_cols) > 1 else None),
            "lower": _safe_float(latest.get(bb_cols[2]) if len(bb_cols) > 2 else None),
            "bandwidth": _safe_float(latest.get(bb_cols[3]) if len(bb_cols) > 3 else None),
            "percent_b": _safe_float(latest.get(bb_cols[4]) if len(bb_cols) > 4 else None),
        },
        "moving_averages": {
            "ma_20": _safe_float(latest.get("MA_20")),
            "ma_50": _safe_float(latest.get("MA_50")),
            "ma_200": _safe_float(latest.get("MA_200")),
            "ema_9": _safe_float(latest.get("EMA_9")),
            "ema_21": _safe_float(latest.get("EMA_21")),
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
        "history": _recent_ohlcv(combined),
    }


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
