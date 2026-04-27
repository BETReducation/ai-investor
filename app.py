from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import yfinance as yf
import pandas as pd
import os

from api.indicators import calculate_all
from api.signals import score_signals

app = Flask(__name__, static_folder="static")
CORS(app)

VALID_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}
VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}


def _fetch_ohlcv(symbol: str, period: str = "3mo", interval: str = "1d") -> pd.DataFrame:
    if interval not in VALID_INTERVALS:
        raise ValueError(f"Invalid interval: {interval}")
    if period not in VALID_PERIODS:
        raise ValueError(f"Invalid period: {period}")

    ticker = yf.Ticker(symbol.upper())
    df = ticker.history(period=period, interval=interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for symbol: {symbol}")
    return df


@app.route("/")
def index():
    return send_from_directory("static", "trading-dashboard.html")


@app.route("/api/prices", methods=["GET"])
def prices():
    symbol = request.args.get("symbol", "").strip()
    period = request.args.get("period", "3mo")
    interval = request.args.get("interval", "1d")

    if not symbol:
        return jsonify({"error": "symbol parameter is required"}), 400

    try:
        df = _fetch_ohlcv(symbol, period, interval)
        df.index = df.index.astype(str)
        records = df[["Open", "High", "Low", "Close", "Volume"]].reset_index()
        records.rename(columns={"Date": "date", "Datetime": "date"}, inplace=True)
        if "date" not in records.columns:
            records.rename(columns={records.columns[0]: "date"}, inplace=True)
        return jsonify({
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "count": len(records),
            "data": records.to_dict(orient="records"),
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to fetch prices: {str(e)}"}), 500


@app.route("/api/indicators", methods=["GET"])
def indicators():
    symbol = request.args.get("symbol", "").strip()
    period = request.args.get("period", "6mo")
    interval = request.args.get("interval", "1d")

    if not symbol:
        return jsonify({"error": "symbol parameter is required"}), 400

    try:
        df = _fetch_ohlcv(symbol, period, interval)
        result = calculate_all(df)
        return jsonify({
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            **result,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate indicators: {str(e)}"}), 500


@app.route("/api/signals", methods=["GET"])
def signals():
    symbol = request.args.get("symbol", "").strip()
    period = request.args.get("period", "6mo")
    interval = request.args.get("interval", "1d")

    if not symbol:
        return jsonify({"error": "symbol parameter is required"}), 400

    # Optional threshold overrides from query params
    thresholds = {}
    threshold_keys = ["rsi_oversold", "rsi_overbought", "volume_surge", "macd_threshold", "bb_oversold", "bb_overbought"]
    for key in threshold_keys:
        val = request.args.get(key)
        if val is not None:
            try:
                thresholds[key] = float(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for threshold '{key}'"}), 400

    try:
        df = _fetch_ohlcv(symbol, period, interval)
        indicator_data = calculate_all(df)
        signal_result = score_signals(indicator_data, thresholds or None)
        return jsonify({
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "indicators": {
                k: v for k, v in indicator_data.items() if k != "history"
            },
            **signal_result,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to generate signals: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=True, port=port)
