from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import yfinance as yf
import pandas as pd
import bcrypt
import json
import os

from api.indicators import calculate_all
from api.signals import score_signals

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "apex-trader-dev-key-change-in-production")

_is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")
_allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
_allowed_origins = (
    [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
    if _allowed_origins_env
    else ["http://localhost:5000", "http://127.0.0.1:5000"]
)

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(_is_production),
)
CORS(app, supports_credentials=True, origins=_allowed_origins)

login_manager = LoginManager(app)
login_manager.session_protection = "basic"

USERS_FILE = os.path.join(os.path.dirname(__file__), "users.json")

VALID_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}
VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}


# ── User model ───────────────────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, username: str):
        self.id = username


@login_manager.user_loader
def load_user(username: str):
    if username in _load_users():
        return User(username)
    return None


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Authentication required"}), 401


# ── User-store helpers ───────────────────────────────────────────────────────

def _load_users() -> dict:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f).get("users", {})


def _save_users(users: dict) -> None:
    with open(USERS_FILE, "w") as f:
        json.dump({"users": users}, f, indent=2)


def _ensure_default_user() -> None:
    if os.path.exists(USERS_FILE):
        return
    pw_hash = bcrypt.hashpw(b"apex2024", bcrypt.gensalt()).decode("utf-8")
    _save_users({"admin": {"password_hash": pw_hash, "preferences": {}}})
    print("\n  ✓ Created default user  →  username: admin  |  password: apex2024\n")


# ── OHLCV helper ─────────────────────────────────────────────────────────────

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


# ── Static ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "trading-dashboard.html")


# ── Auth endpoints ───────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    users = _load_users()
    if username in users:
        return jsonify({"error": "Username already taken"}), 409

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
    users[username] = {"password_hash": pw_hash, "preferences": {}}
    _save_users(users)

    login_user(User(username), remember=data.get("remember", False))
    return jsonify({"success": True, "username": username, "preferences": {}})


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    remember = bool(data.get("remember", False))

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    users = _load_users()
    user_data = users.get(username)
    if not user_data:
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user_data["password_hash"].encode("utf-8")):
        return jsonify({"error": "Invalid credentials"}), 401

    login_user(User(username), remember=remember)
    return jsonify({
        "success": True,
        "username": username,
        "preferences": user_data.get("preferences", {}),
    })


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return jsonify({"success": True})


@app.route("/api/save-preferences", methods=["POST"])
@login_required
def save_preferences():
    prefs = request.get_json() or {}
    users = _load_users()
    if current_user.id not in users:
        return jsonify({"error": "User not found"}), 404
    users[current_user.id]["preferences"] = prefs
    _save_users(users)
    return jsonify({"success": True})


@app.route("/api/load-preferences", methods=["GET"])
@login_required
def load_preferences():
    users = _load_users()
    user_data = users.get(current_user.id, {})
    return jsonify({
        "username": current_user.id,
        "preferences": user_data.get("preferences", {}),
    })


# ── Market data endpoints (login required) ───────────────────────────────────

@app.route("/api/prices", methods=["GET"])
@login_required
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
@login_required
def indicators():
    symbol = request.args.get("symbol", "").strip()
    period = request.args.get("period", "6mo")
    interval = request.args.get("interval", "1d")

    if not symbol:
        return jsonify({"error": "symbol parameter is required"}), 400
    try:
        df = _fetch_ohlcv(symbol, period, interval)
        result = calculate_all(df)
        return jsonify({"symbol": symbol.upper(), "period": period, "interval": interval, **result})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to calculate indicators: {str(e)}"}), 500


@app.route("/api/signals", methods=["GET"])
@login_required
def signals():
    symbol = request.args.get("symbol", "").strip()
    period = request.args.get("period", "6mo")
    interval = request.args.get("interval", "1d")

    if not symbol:
        return jsonify({"error": "symbol parameter is required"}), 400

    thresholds = {}
    float_keys = [
        "rsi_oversold", "rsi_overbought", "volume_surge",
        "macd_threshold", "bb_oversold", "bb_overbought",
        "rsi_on", "macd_on", "bb_on", "ma_on", "vol_on",
        "ema_short", "ema_long", "macd_cross_lookback", "ema_cross_lookback", "ma_cross_lookback",
    ]
    for key in float_keys:
        val = request.args.get(key)
        if val is not None:
            try:
                thresholds[key] = float(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for threshold '{key}'"}), 400

    calc_params = {}
    int_calc_keys = {"macd_fast": 12, "macd_slow": 26, "macd_signal": 9, "bb_length": 20, "ema_short": 9, "ema_long": 21}
    float_calc_keys = {"bb_std": 2.0}
    for key, default in int_calc_keys.items():
        val = request.args.get(key)
        if val is not None:
            try:
                calc_params[key] = int(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for '{key}'"}), 400
    for key, default in float_calc_keys.items():
        val = request.args.get(key)
        if val is not None:
            try:
                calc_params[key] = float(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for '{key}'"}), 400

    try:
        df = _fetch_ohlcv(symbol, period, interval)
        indicator_data = calculate_all(df, **calc_params)
        signal_result = score_signals(indicator_data, thresholds or None)
        return jsonify({
            "symbol": symbol.upper(),
            "period": period,
            "interval": interval,
            "indicators": {k: v for k, v in indicator_data.items() if k != "history"},
            **signal_result,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to generate signals: {str(e)}"}), 500


# ── Startup ───────────────────────────────────────────────────────────────────

_ensure_default_user()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=not _is_production, port=port)
