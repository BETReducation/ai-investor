from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
import yfinance as yf
import pandas as pd
import bcrypt
import json
import os
import secrets
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None
from datetime import timedelta
from werkzeug.utils import secure_filename

from api.indicators import calculate_all
from api.signals import score_signals
from api.backtest import run_backtest
from api.metrics import calculate_metrics

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "gca-dev-key-change-in-production")

_is_production = os.environ.get("RAILWAY_ENVIRONMENT") or os.environ.get("PRODUCTION")
_allowed_origins_env = os.environ.get("ALLOWED_ORIGINS", "")
_allowed_origins = (
    [o.strip() for o in _allowed_origins_env.split(",") if o.strip()]
    if _allowed_origins_env
    else ["http://localhost:5000", "http://127.0.0.1:5000"]
)

app.config.update(
    MAX_CONTENT_LENGTH=5 * 1024 * 1024,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=bool(_is_production),
    PERMANENT_SESSION_LIFETIME=timedelta(days=30),
    REMEMBER_COOKIE_DURATION=timedelta(days=30),
    REMEMBER_COOKIE_HTTPONLY=True,
    REMEMBER_COOKIE_SECURE=bool(_is_production),
)
CORS(app, supports_credentials=True, origins=_allowed_origins)

login_manager = LoginManager(app)
login_manager.session_protection = "basic"

USERS_FILE  = os.path.join(os.path.dirname(__file__), "users.json")
DATABASE_URL = os.environ.get("DATABASE_URL", "")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "static", "uploads", "avatars")
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _db_conn():
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return psycopg2.connect(url)


def _ensure_table() -> None:
    if not DATABASE_URL:
        return
    with _db_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                username      TEXT PRIMARY KEY,
                password_hash TEXT NOT NULL,
                preferences   JSONB NOT NULL DEFAULT '{}',
                tier          TEXT NOT NULL DEFAULT 'basic'
            )
        """)
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS tier TEXT NOT NULL DEFAULT 'basic'")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS profile JSONB NOT NULL DEFAULT '{}'::jsonb")
        cur.execute("UPDATE users SET tier = 'power_user' WHERE tier IN ('basic', 'signal_tester')")

VALID_INTERVALS = {"1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"}

# yfinance has no native 2-hour/4-hour bars — synthesized by fetching hourly data and
# resampling. Kept separate from VALID_INTERVALS since every other caller of that set
# (elsewhere in the codebase, if any) should keep seeing only intervals yfinance itself
# understands; only _fetch_ohlcv needs to know about the synthetic ones.
_RESAMPLE_INTERVALS = {"2h": "1h", "4h": "1h"}
ALL_VALID_INTERVALS = VALID_INTERVALS | set(_RESAMPLE_INTERVALS)

_INT_CALC_KEYS = {
    "rsi_length": 14, "macd_fast": 12, "macd_slow": 26, "macd_signal": 9,
    "bb_length": 20, "ema_short": 9, "ema_long": 21,
    "stoch_k": 14, "stoch_d": 3, "stoch_smooth": 3,
    "stochrsi_length": 14, "stochrsi_k": 3, "stochrsi_d": 3,
    "cci_length": 20, "willr_length": 14, "adx_length": 14,
    "atr_length": 14, "mfi_length": 14, "aroon_length": 25,
    "supertrend_length": 10, "wma_length": 20, "hma_length": 20, "roc_length": 12,
}
_FLOAT_CALC_KEYS = {
    "bb_std": 2.0, "supertrend_mult": 3.0,
    "psar_start": 0.02, "psar_inc": 0.02, "psar_max": 0.2,
}


def _extract_calc_params(args) -> dict:
    params = {}
    for key in _INT_CALC_KEYS:
        val = args.get(key)
        if val is not None:
            try:
                params[key] = int(val)
            except ValueError:
                pass
    for key in _FLOAT_CALC_KEYS:
        val = args.get(key)
        if val is not None:
            try:
                params[key] = float(val)
            except ValueError:
                pass
    smoothing = args.get("rsi_smoothing", "").strip().lower()
    if smoothing in ("wilder", "ema", "sma"):
        params["rsi_smoothing"] = smoothing
    return params


# Backtester-only calc params (kept separate from _INT_CALC_KEYS/_FLOAT_CALC_KEYS
# above so /api/indicators' calculate_all(**calc_params) never sees an unexpected kwarg).
_BT_INT_CALC_KEYS = {
    "rsi_div_lookback": 5,
    "macd_div_lookback": 5, "macd_zscore_length": 100,
    "stochrsi_div_lookback": 5,
    "willr_div_lookback": 5, "willr_confirm_lookback": 5,
    "roc_div_lookback": 5, "roc_momentum_lookback": 3,
    "mfi_div_lookback": 5,
    "tsi_div_lookback": 5,
    "ao_div_lookback": 5, "ao_twin_peaks_lookback": 5,
    "ichimoku_tenkan": 9, "ichimoku_kijun": 26, "ichimoku_senkou": 52,
    "donchian_length": 20, "donchian_exit_length": 10,
    "keltner_length": 20, "keltner_atr_length": 10,
    "keltner_walk_min_consecutive": 3, "keltner_squeeze_lookback": 10,
    "stdev_length": 20,
    "chaikin_vol_ema_length": 10, "chaikin_vol_roc_length": 10,
    "hist_vol_length": 20,
    "vwap_length": 20, "vwap_anchored": 0,
    "ad_sma_length": 20,
    "cmf_length": 20,
    "tsi_long": 25, "tsi_short": 13, "tsi_signal": 13,
    "ao_fast": 5, "ao_slow": 34,
    "obv_sma_length": 20,
    "vol_profile_lookback": 50, "vol_profile_bins": 24,
    "fib_lookback": 50,
    "hma_slope_lookback": 3, "hma_fast_length": 9,
    "bb_squeeze_lookback": 100, "bb_breakout_window": 10,
    "bb_walk_min_consecutive": 3, "bb_pattern_lookback": 5,
    "ma_short_length": 9, "ma_medium_length": 20, "ma_long_length": 50,
    "obv_div_lookback": 5, "ad_div_lookback": 5,
}
_BT_FLOAT_CALC_KEYS = {
    "keltner_mult": 2.0, "keltner_walk_tolerance_pct": 0.5,
    "bb_squeeze_percentile": 20.0, "bb_walk_tolerance_pct": 0.5,
    "vwap_band_pct": 1.0,
}

_VALID_RSI_TRIGGERS = {
    "overbought_oversold", "overbought", "oversold", "centerline_cross",
    "bullish_divergence", "bearish_divergence", "failure_swings",
}

_VALID_MACD_TRIGGERS = {
    "signal_cross", "bullish_signal_cross", "bearish_signal_cross", "centerline_cross",
    "bullish_divergence", "bearish_divergence", "histogram_reversal", "overbought", "oversold",
}

_VALID_BB_TRIGGERS = {
    "percent_b", "upper_touch", "lower_touch", "volatility_breakout",
    "walking_upper", "walking_lower", "w_bottom", "m_top",
}

_VALID_MA_TRIGGERS = {
    "dual_cross", "price_cross", "two_ma_bull", "two_ma_bear", "three_ma_bull", "three_ma_bear",
}

_VALID_ADX_TRIGGERS = {
    "trend_threshold", "bull_di_cross", "bear_di_cross", "above_25", "above_50", "above_75",
    "strong_di_plus", "strong_di_minus",
}

_TRIGGER_WHITELISTS = {
    "psar_trigger":        {"flip", "bull_flip", "bear_flip", "trend_state", "trailing_stop"},
    "ichimoku_trigger":    {"cloud_position", "bullish", "bearish", "tk_cross"},
    "supertrend_trigger":  {"flip", "bull_flip", "bear_flip", "trend_state", "trailing_stop"},
    "donchian_trigger":    {"breakout", "bullish", "bearish", "middle_cross", "two_channel_bull", "two_channel_bear"},
    "hma_trigger":         {"slope", "bullish_slope", "bearish_slope", "price_cross", "two_hma_bull", "two_hma_bear"},
    "stoch_trigger":       {"overbought_oversold", "overbought", "oversold", "signal_cross"},
    "stochrsi_trigger":    {"overbought_oversold", "overbought", "oversold", "signal_cross", "bullish_divergence", "bearish_divergence"},
    "cci_trigger":         {"overbought_oversold", "overbought", "oversold", "centerline_cross", "breakout_bull", "breakout_bear"},
    "willr_trigger":       {"overbought_oversold", "overbought", "oversold", "midline_cross",
                             "momentum_failure_bull", "momentum_failure_bear",
                             "trend_confirmation_bull", "trend_confirmation_bear",
                             "bullish_divergence", "bearish_divergence"},
    "roc_trigger":         {"threshold", "bullish", "bearish", "centerline_cross",
                             "bull_momentum", "bear_momentum",
                             "bullish_divergence", "bearish_divergence"},
    "mfi_trigger":         {"overbought_oversold", "overbought", "oversold", "centerline_cross",
                             "bullish_divergence", "bearish_divergence"},
    "tsi_trigger":         {"signal_cross", "bullish", "bearish", "centerline_cross",
                             "overbought", "oversold",
                             "bullish_divergence", "bearish_divergence"},
    "ao_trigger":          {"zero_state", "bullish", "bearish", "zero_cross",
                             "bull_saucer", "bear_saucer",
                             "bull_twin_peaks", "bear_twin_peaks",
                             "bull_divergence", "bear_divergence"},
    "atr_trigger":         {"expansion", "bullish_expansion", "bearish_expansion", "contraction"},
    "keltner_trigger":     {"breakout", "bullish", "bearish", "middle_cross",
                             "bull_band_riding", "bear_band_riding",
                             "bull_mean_reversion", "bear_mean_reversion",
                             "keltner_squeeze"},
    "stdev_trigger":       {"expansion", "bullish_expansion", "bearish_expansion", "contraction"},
    "chaikin_vol_trigger": {"expansion", "bullish_expansion", "bearish_expansion", "contraction"},
    "hist_vol_trigger":    {"expansion", "bullish_expansion", "bearish_expansion", "contraction"},
    "obv_trigger":         {"trend", "bullish", "bearish", "divergence"},
    "vwap_trigger":        {"position", "bullish", "bearish", "band_touch", "pullback_buy", "pullback_sell"},
    "ad_trigger":          {"trend", "bullish", "bearish", "divergence"},
    "cmf_trigger":         {"threshold", "bullish", "bearish", "centerline_cross"},
    "vol_profile_trigger": {"position", "bullish", "bearish", "poc_breakout"},
    "fib_trigger":         {"bounce_reject", "bullish_bounce", "bearish_reject", "any_touch"},
}


def _extract_backtest_calc_params(args) -> dict:
    params = {}
    for key in _BT_INT_CALC_KEYS:
        val = args.get(key)
        if val is not None:
            try:
                params[key] = int(val)
            except ValueError:
                pass
    for key in _BT_FLOAT_CALC_KEYS:
        val = args.get(key)
        if val is not None:
            try:
                params[key] = float(val)
            except ValueError:
                pass
    ma_type = args.get("ma_type", "").strip().lower()
    if ma_type in ("simple", "smoothed", "exponential", "weighted", "volume_weighted"):
        params["ma_type"] = ma_type
    return params


VALID_PERIODS = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}

TIER_RANKS = {"basic": 0, "signal_tester": 1, "power_user": 2}


# ── User model ───────────────────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, username: str, tier: str = "basic"):
        self.id = username
        self.tier = tier


@login_manager.user_loader
def load_user(username: str):
    users = _load_users()
    if username in users:
        return User(username, users[username].get("tier", "basic"))
    return None


@login_manager.unauthorized_handler
def unauthorized():
    return jsonify({"error": "Authentication required"}), 401


def tier_required(min_tier: str):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if not current_user.is_authenticated:
                return jsonify({"error": "Login required", "tier_required": min_tier}), 401
            user_rank = TIER_RANKS.get(getattr(current_user, "tier", "basic"), 0)
            if user_rank < TIER_RANKS.get(min_tier, 0):
                return jsonify({
                    "error": "Subscription upgrade required",
                    "tier_required": min_tier,
                    "current_tier": getattr(current_user, "tier", "basic"),
                }), 403
            return f(*args, **kwargs)
        return wrapped
    return decorator


# ── User-store helpers ───────────────────────────────────────────────────────

def _load_users() -> dict:
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT username, password_hash, preferences, tier, profile FROM users")
            return {
                row["username"]: {
                    "password_hash": row["password_hash"],
                    "preferences":   row["preferences"] or {},
                    "tier":          row.get("tier", "basic"),
                    "profile":       row.get("profile") or {},
                }
                for row in cur.fetchall()
            }
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return json.load(f).get("users", {})


def _save_users(users: dict) -> None:
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor() as cur:
            for username, data in users.items():
                cur.execute("""
                    INSERT INTO users (username, password_hash, preferences, tier, profile)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE
                        SET password_hash = EXCLUDED.password_hash,
                            preferences   = EXCLUDED.preferences,
                            tier          = EXCLUDED.tier,
                            profile       = EXCLUDED.profile
                """, (username, data["password_hash"], json.dumps(data.get("preferences", {})), data.get("tier", "basic"), json.dumps(data.get("profile", {}))))
        return
    with open(USERS_FILE, "w") as f:
        json.dump({"users": users}, f, indent=2)


def _save_preferences(username: str, preferences: dict) -> None:
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET preferences = %s WHERE username = %s",
                (json.dumps(preferences), username)
            )
        return
    users = _load_users()
    users[username]["preferences"] = preferences
    _save_users(users)


def _ensure_default_user() -> None:
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users LIMIT 1")
            if cur.fetchone():
                return
        password = secrets.token_urlsafe(12)
        pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        _save_users({"admin": {"password_hash": pw_hash, "preferences": {}, "tier": "power_user"}})
        print(f"\n  ✓ Created default user  →  username: admin  |  password: {password}  |  tier: power_user\n")
        return
    if os.path.exists(USERS_FILE):
        return
    password = secrets.token_urlsafe(12)
    pw_hash = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    _save_users({"admin": {"password_hash": pw_hash, "preferences": {}, "tier": "power_user"}})
    print(f"\n  ✓ Created default user  →  username: admin  |  password: {password}  |  tier: power_user\n")


# ── OHLCV helper ─────────────────────────────────────────────────────────────

def _resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {"Open": "first", "High": "max", "Low": "min", "Close": "last"}
    if "Volume" in df.columns:
        agg["Volume"] = "sum"
    resampled = df.resample(rule).agg(agg)
    return resampled.dropna(subset=["Open"])


def _fetch_ohlcv(
    symbol: str,
    period: str = "3mo",
    interval: str = "1d",
    start_date: str | None = None,
    end_date: str | None = None,
) -> pd.DataFrame:
    if interval not in ALL_VALID_INTERVALS:
        raise ValueError(f"Invalid interval: {interval}")
    fetch_interval = _RESAMPLE_INTERVALS.get(interval, interval)
    ticker = yf.Ticker(symbol.upper())
    if start_date:
        import datetime as _dt
        try:
            _dt.date.fromisoformat(start_date)
            if end_date:
                _dt.date.fromisoformat(end_date)
        except ValueError:
            raise ValueError("start_date / end_date must be YYYY-MM-DD")
        df = ticker.history(start=start_date, end=end_date or None, interval=fetch_interval, auto_adjust=True)
    else:
        if period not in VALID_PERIODS:
            raise ValueError(f"Invalid period: {period}")
        df = ticker.history(period=period, interval=fetch_interval, auto_adjust=True)
    if df.empty:
        raise ValueError(f"No data returned for symbol: {symbol}")
    if interval in _RESAMPLE_INTERVALS:
        df = _resample_ohlcv(df, interval)
        if df.empty:
            raise ValueError(f"No data returned for symbol: {symbol}")
    return df


# ── Static ───────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return send_from_directory("static", "index.html")


@app.route("/login")
def login_page():
    return send_from_directory("static", "login.html")

@app.route("/signal-config")
def signal_config():
    return send_from_directory("static", "signal_config.html")

@app.route("/portfolio-balancer")
def portfolio_balancer():
    return send_from_directory("static", "portfolio-balancer.html")

@app.route("/backtester")
def backtester():
    return send_from_directory("static", "strategy-lab.html")

@app.route("/stories")
def stories():
    return send_from_directory("static", "stories.html")

@app.route("/education-hub")
def education_hub():
    return send_from_directory("static", "EducationHub.html")

@app.route("/stories-podcasts")
def stories_podcasts():
    return send_from_directory("static", "StoriesPodcasts.html")

@app.route("/competitions-partnerships")
def competitions_partnerships():
    return send_from_directory("static", "CompetitionsPartnerships.html")

@app.route("/btc-swing-trade")
def btc_swing_trade():
    return send_from_directory("static", "btc-swing-trade.html")

# ── New nav routes ────────────────────────────────────────────────────────────

@app.route("/learn")
def learn(): return send_from_directory("static", "learn.html")

@app.route("/learn/beginner")
def learn_beginner(): return send_from_directory("static", "learn-beginner.html")

@app.route("/learn/beginner/start-early")
def learn_beginner_start_early(): return send_from_directory("static", "lesson-start-early.html")

@app.route("/learn/beginner/diversify")
def learn_beginner_diversify(): return send_from_directory("static", "lesson-diversify.html")

@app.route("/learn/intermediate")
def learn_intermediate(): return send_from_directory("static", "learn-intermediate.html")

@app.route("/learn/pro")
def learn_pro(): return send_from_directory("static", "learn-pro.html")

@app.route("/tools")
def tools(): return send_from_directory("static", "tools.html")

@app.route("/tools/signals")
def tools_signals(): return send_from_directory("static", "signal_config.html")

@app.route("/tools/portfolio")
def tools_portfolio(): return send_from_directory("static", "portfolio-balancer.html")

@app.route("/arena")
def arena(): return send_from_directory("static", "arena.html")

@app.route("/arena/market-xi")
def arena_market_xi(): return send_from_directory("static", "arena-market-xi.html")

@app.route("/arena/competitions")
def arena_competitions(): return send_from_directory("static", "arena-competitions.html")

@app.route("/arena/predictions")
def arena_predictions(): return send_from_directory("static", "arena-predictions.html")

@app.route("/alpha")
def alpha(): return send_from_directory("static", "alpha.html")

@app.route("/alpha/connor")
def alpha_connor(): return send_from_directory("static", "alpha-connor.html")

@app.route("/alpha/dave")
def alpha_dave(): return send_from_directory("static", "alpha-dave.html")

@app.route("/alpha/gary")
def alpha_gary(): return send_from_directory("static", "alpha-gary.html")

@app.route("/alpha/tom")
def alpha_tom(): return send_from_directory("static", "alpha-tom.html")

@app.route("/alpha/podcast")
def alpha_podcast(): return send_from_directory("static", "alpha-podcast.html")

@app.route("/partners")
def partners(): return send_from_directory("static", "partners.html")

@app.route("/sitemap")
def sitemap(): return send_from_directory("static", "sitemap.html")


# ── Portfolio Balancer — live price feed ──────────────────────────────────────

_PB_TICKERS = {
    # Safe (bonds & cash proxies)
    's_tbills': 'SHY',    # iShares 1-3yr Treasury Bond ETF
    's_gilts':  'IGLT.L', # iShares UK Gilts UCITS ETF
    's_euro':   'IBTE.L', # iShares € Govt Bond 1-3yr UCITS ETF
    's_corp':   'LQD',    # iShares iBoxx IG Corp Bond ETF
    's_cash':   'ERNS.L', # iShares GBP Ultrashort Bond ETF (cash proxy)
    # Hard Assets (property / land / infrastructure proxies)
    'h_ukres':  'IUKP.L', # iShares UK Property UCITS ETF
    'h_comre':  'REM',    # iShares Mortgage Real Estate ETF
    'h_agri':   'MOO',    # VanEck Agribusiness ETF
    'h_infra':  'IGF',    # iShares Global Infrastructure ETF
    'h_reits':  'VNQ',    # Vanguard Real Estate ETF
    # Stocks & Shares
    'k_sp500':  'SPY',    # SPDR S&P 500 ETF Trust
    'k_nas':    'QQQ',    # Invesco QQQ Trust (NASDAQ 100)
    'k_ftse':   'ISF.L',  # iShares Core FTSE 100 UCITS ETF
    'k_em':     'EEM',    # iShares MSCI Emerging Markets ETF
    'k_sc':     'VSS',    # Vanguard FTSE All-World ex-US Small-Cap ETF
    # Metals (ETFs — more reliable than futures via yfinance)
    'm_gold':   'GLD',    # SPDR Gold Shares ETF
    'm_silv':   'SLV',    # iShares Silver Trust ETF
    'm_plat':   'PPLT',   # Aberdeen Physical Platinum ETF
    'm_copp':   'CPER',   # United States Copper Index Fund
    'm_pall':   'PALL',   # Aberdeen Physical Palladium ETF
    # Crypto
    'c_btc':    'BTC-USD',
    'c_eth':    'ETH-USD',
    'c_ada':    'ADA-USD',
    'c_xrp':    'XRP-USD',
    'c_sol':    'SOL-USD',
}


@app.route("/api/portfolio-prices")
def portfolio_prices():
    """Return current prices for all 25 portfolio balancer assets."""
    unique = list(set(_PB_TICKERS.values()))
    price_map = {}
    try:
        raw = yf.download(unique, period='5d', interval='1d',
                          progress=False, auto_adjust=True, threads=True)
        close = raw['Close'] if isinstance(raw.columns, pd.MultiIndex) else raw
        for ticker in unique:
            try:
                s = close[ticker].dropna() if ticker in close.columns else pd.Series(dtype=float)
                if len(s):
                    price_map[ticker] = float(s.iloc[-1])
            except Exception:
                pass
    except Exception:
        pass

    result = {}
    for asset_id, ticker in _PB_TICKERS.items():
        price = price_map.get(ticker)
        result[asset_id] = {
            'ticker': ticker,
            'price':  round(price, 6) if price is not None else None,
            'live':   price is not None,
        }
    return jsonify({'prices': result, 'ts': pd.Timestamp.now().isoformat()})


@app.route("/profile")
def profile_page():
    return send_from_directory("static", "profile.html")


# ── Auth endpoints ───────────────────────────────────────────────────────────

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email    = data.get("email", "").strip()

    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    if not email:
        return jsonify({"error": "Email address required"}), 400
    if len(password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    users = _load_users()
    if username in users:
        return jsonify({"error": "Username already taken"}), 409

    pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode("utf-8")
    users[username] = {
        "password_hash": pw_hash,
        "preferences": {},
        "tier": "power_user",
        "profile": {
            "email": email,
            "display_name": username,
            "bio": "",
            "investor_type": "beginner",
            "profile_picture": "",
        },
    }
    _save_users(users)

    login_user(User(username, "power_user"), remember=True)
    return jsonify({"success": True, "username": username, "tier": "power_user", "preferences": {}, "landing_page": "/"})


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400

    users = _load_users()
    user_data = users.get(username)
    if not user_data:
        return jsonify({"error": "Invalid credentials"}), 401

    if not bcrypt.checkpw(password.encode("utf-8"), user_data["password_hash"].encode("utf-8")):
        return jsonify({"error": "Invalid credentials"}), 401

    login_user(User(username, user_data.get("tier", "basic")), remember=True)
    return jsonify({
        "success": True,
        "username": username,
        "tier": user_data.get("tier", "basic"),
        "preferences": user_data.get("preferences", {}),
        "landing_page": user_data.get("profile", {}).get("landing_page", "/"),
    })


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return jsonify({"success": True})


@app.route("/api/me", methods=["GET"])
def api_me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False, "username": None, "tier": "basic"})
    return jsonify({
        "authenticated": True,
        "username": current_user.id,
        "tier": getattr(current_user, "tier", "basic"),
    })


@app.route("/api/admin/set-tier", methods=["POST"])
@login_required
def admin_set_tier():
    if current_user.id != "admin":
        return jsonify({"error": "Admin only"}), 403
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    new_tier = data.get("tier", "").strip()
    if new_tier not in TIER_RANKS:
        return jsonify({"error": f"Invalid tier. Valid options: {list(TIER_RANKS.keys())}"}), 400
    users = _load_users()
    if username not in users:
        return jsonify({"error": "User not found"}), 404
    users[username]["tier"] = new_tier
    _save_users(users)
    return jsonify({"success": True, "username": username, "tier": new_tier})


@app.route("/api/save-preferences", methods=["POST"])
@login_required
def save_preferences():
    incoming = request.get_json() or {}
    users = _load_users()
    if current_user.id not in users:
        return jsonify({"error": "User not found"}), 404
    # Shallow-merge onto the existing preferences rather than replacing them outright,
    # so keys this caller doesn't know about (e.g. custom_symbols, saved by the
    # /api/custom-symbols endpoints) survive a save from a page that only manages its
    # own subset of settings.
    existing = users[current_user.id].get("preferences", {}) or {}
    merged = {**existing, **incoming}
    _save_preferences(current_user.id, merged)
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


LANDING_PAGE_CHOICES = {
    "/",
    "/learn", "/learn/beginner", "/learn/intermediate", "/learn/pro",
    "/tools", "/tools/signals", "/backtester", "/tools/portfolio",
    "/arena", "/arena/market-xi", "/arena/competitions", "/arena/predictions",
    "/alpha", "/alpha/connor", "/alpha/dave", "/alpha/gary", "/alpha/tom", "/alpha/podcast",
    "/partners", "/profile",
}


@app.route("/api/profile", methods=["GET"])
@login_required
def api_get_profile():
    users = _load_users()
    user_data = users.get(current_user.id, {})
    profile = user_data.get("profile", {})
    return jsonify({
        "username":       current_user.id,
        "tier":           user_data.get("tier", "basic"),
        "email":          profile.get("email", ""),
        "display_name":   profile.get("display_name", current_user.id),
        "bio":            profile.get("bio", ""),
        "investor_type":  profile.get("investor_type", "beginner"),
        "profile_picture": profile.get("profile_picture", ""),
        "landing_page":   profile.get("landing_page", "/"),
    })


PRESET_AVATARS = {"preset:beginner", "preset:intermediate", "preset:pro"}


@app.route("/api/profile/update", methods=["POST"])
@login_required
def api_update_profile():
    data = request.get_json() or {}
    users = _load_users()
    if current_user.id not in users:
        return jsonify({"error": "User not found"}), 404
    profile = users[current_user.id].get("profile", {})
    for field in ("email", "display_name", "bio", "investor_type"):
        if field in data:
            profile[field] = str(data[field]).strip()
    if "profile_picture" in data:
        value = str(data["profile_picture"]).strip()
        if value not in PRESET_AVATARS:
            return jsonify({"error": "Invalid avatar selection"}), 400
        profile["profile_picture"] = value
    if "landing_page" in data:
        value = str(data["landing_page"]).strip()
        if value not in LANDING_PAGE_CHOICES:
            return jsonify({"error": "Invalid landing page"}), 400
        profile["landing_page"] = value
    users[current_user.id]["profile"] = profile
    _save_users(users)
    return jsonify({"success": True, "profile": profile})


@app.route("/api/profile/avatar", methods=["POST"])
@login_required
def api_upload_avatar():
    if "avatar" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["avatar"]
    if not file.filename:
        return jsonify({"error": "No file selected"}), 400
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "Allowed types: png, jpg, jpeg, gif, webp"}), 400
    filename = secure_filename(f"{current_user.id}.{ext}")
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    avatar_url = f"/static/uploads/avatars/{filename}"
    users = _load_users()
    if current_user.id not in users:
        return jsonify({"error": "User not found"}), 404
    profile = users[current_user.id].get("profile", {})
    profile["profile_picture"] = avatar_url
    users[current_user.id]["profile"] = profile
    _save_users(users)
    return jsonify({"success": True, "avatar_url": avatar_url})


@app.route("/api/subscription/cancel", methods=["POST"])
@login_required
def api_cancel_subscription():
    users = _load_users()
    if current_user.id not in users:
        return jsonify({"error": "User not found"}), 404
    users[current_user.id]["tier"] = "basic"
    _save_users(users)
    return jsonify({"success": True, "message": "Subscription cancelled. You have been moved to the Basic (free) plan."})


@app.route("/api/account/cancel", methods=["POST"])
@login_required
def api_cancel_account():
    username = current_user.id
    if username == "admin":
        return jsonify({"error": "Cannot delete the admin account"}), 403
    users = _load_users()
    if username not in users:
        return jsonify({"error": "User not found"}), 404
    del users[username]
    _save_users(users)
    logout_user()
    return jsonify({"success": True})


# ── Market data endpoints (public) ───────────────────────────────────────────

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


@app.route("/api/symbol-search", methods=["GET"])
def symbol_search():
    """Ticker/company autocomplete, proxied through yfinance's Search (which itself
    wraps Yahoo's public search endpoint). Best-effort — degrades to an empty result
    list on any failure (missing yfinance.Search in an older pinned version, Yahoo
    throttling, network error, etc.) rather than surfacing a 500 to the picker UI."""
    query = request.args.get("q", "").strip()
    if len(query) < 1:
        return jsonify({"results": []})
    try:
        quotes = yf.Search(query, max_results=10).quotes
    except Exception:
        return jsonify({"results": []})
    results = []
    for q in quotes:
        symbol = q.get("symbol")
        if not symbol:
            continue
        results.append({
            "symbol": symbol,
            "name": q.get("shortname") or q.get("longname") or symbol,
            "exchange": q.get("exchDisp") or q.get("exchange") or "",
            "type": q.get("quoteType") or "",
        })
    return jsonify({"results": results})


_CUSTOM_SYMBOLS_MAX = 50


@app.route("/api/custom-symbols", methods=["GET"])
@login_required
def get_custom_symbols():
    users = _load_users()
    prefs = users.get(current_user.id, {}).get("preferences", {}) or {}
    return jsonify({"symbols": prefs.get("custom_symbols", [])})


@app.route("/api/custom-symbols", methods=["POST"])
@login_required
def add_custom_symbol():
    data = request.get_json() or {}
    symbol = (data.get("symbol") or "").strip().upper()
    if not symbol:
        return jsonify({"error": "symbol is required"}), 400
    label = (data.get("label") or symbol).strip()
    category = (data.get("category") or "stock").strip().lower()
    exchange = (data.get("exchange") or "").strip()

    users = _load_users()
    if current_user.id not in users:
        return jsonify({"error": "User not found"}), 404
    prefs = users[current_user.id].get("preferences", {}) or {}
    custom = prefs.get("custom_symbols", [])

    if not any(s["symbol"] == symbol for s in custom):
        if len(custom) >= _CUSTOM_SYMBOLS_MAX:
            return jsonify({"error": f"Custom symbol list is full (max {_CUSTOM_SYMBOLS_MAX})"}), 400
        try:
            df = _fetch_ohlcv(symbol, period="5d", interval="1d")
        except Exception:
            df = None
        if df is None or df.empty:
            return jsonify({"error": f"No data found for '{symbol}' — check the ticker"}), 400
        custom.append({"symbol": symbol, "label": label, "category": category, "exchange": exchange})

    prefs["custom_symbols"] = custom
    _save_preferences(current_user.id, prefs)
    return jsonify({"success": True, "symbols": custom})


@app.route("/api/custom-symbols", methods=["DELETE"])
@login_required
def remove_custom_symbol():
    symbol = (request.args.get("symbol") or "").strip().upper()
    users = _load_users()
    if current_user.id not in users:
        return jsonify({"error": "User not found"}), 404
    prefs = users[current_user.id].get("preferences", {}) or {}
    custom = [s for s in prefs.get("custom_symbols", []) if s["symbol"] != symbol]
    prefs["custom_symbols"] = custom
    _save_preferences(current_user.id, prefs)
    return jsonify({"success": True, "symbols": custom})


@app.route("/api/indicators", methods=["GET"])
def indicators():
    symbol = request.args.get("symbol", "").strip()
    period = request.args.get("period", "6mo")
    interval = request.args.get("interval", "1d")

    if not symbol:
        return jsonify({"error": "symbol parameter is required"}), 400
    try:
        df = _fetch_ohlcv(symbol, period, interval)
        calc_params = _extract_calc_params(request.args)
        result = calculate_all(df, **calc_params)
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

    calc_params = _extract_calc_params(request.args)

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


# ── Backtest endpoint (public) ───────────────────────────────────────────────

@app.route("/api/backtest", methods=["GET"])
def backtest():
    symbol     = request.args.get("symbol", "").strip()
    period     = request.args.get("period", "2y")
    interval   = request.args.get("interval", "1d")
    start_date = request.args.get("start_date", "").strip() or None
    end_date   = request.args.get("end_date", "").strip() or None

    if not symbol:
        return jsonify({"error": "symbol parameter is required"}), 400

    try:
        stop_loss_pct   = float(request.args.get("stop_loss",     2.0))
        take_profit_pct = float(request.args.get("take_profit",   4.0))
        min_confidence  = float(request.args.get("min_confidence", 60.0))
        trailing_stop      = request.args.get("trailing_stop", "0") in ("1", "true", "True")
        trail_distance_pct = float(request.args.get("trail_distance", 1.5))
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid parameter: {e}"}), 400

    thresholds = {}
    for key in [
        "rsi_oversold", "rsi_overbought", "volume_surge",
        "bb_oversold", "bb_overbought",
        "rsi_on", "macd_on", "bb_on", "ma_on", "vol_on",
        "macd_cross_lookback", "ema_cross_lookback", "ma_cross_lookback",
        # ── Extended indicator set (Backtester) ──────────────────────────
        "adx_on", "adx_trend_threshold",
        "psar_on", "psar_flip_lookback",
        "ichimoku_on",
        "supertrend_on", "supertrend_flip_lookback",
        "donchian_on",
        "hma_on",
        "stoch_on", "stoch_oversold", "stoch_overbought",
        "stochrsi_on", "stochrsi_oversold", "stochrsi_overbought",
        "cci_on", "cci_oversold", "cci_overbought",
        "willr_on", "willr_oversold", "willr_overbought",
        "roc_on", "roc_threshold",
        "mfi_on", "mfi_oversold", "mfi_overbought",
        "tsi_on", "tsi_oversold", "tsi_overbought",
        "ao_on",
        "atr_on", "atr_trend_lookback",
        "keltner_on",
        "stdev_on", "stdev_trend_lookback",
        "chaikin_vol_on", "chaikin_vol_trend_lookback",
        "hist_vol_on", "hist_vol_trend_lookback",
        "obv_on",
        "vwap_on",
        "ad_on",
        "cmf_on", "cmf_threshold",
        "vol_profile_on",
        "fib_on", "fib_tolerance_pct",
        "macd_centerline_lookback", "macd_zscore_overbought", "macd_zscore_oversold",
        "ma_trigger_lookback",
        "adx_di_cross_lookback",
        "psar_gap_lookback", "supertrend_gap_lookback",
        "ichimoku_tk_cross_lookback", "donchian_mid_cross_lookback", "hma_price_cross_lookback",
        "hma_two_cross_lookback",
        "stoch_signal_cross_lookback", "stochrsi_signal_cross_lookback",
        "cci_centerline_lookback", "willr_midline_lookback", "roc_centerline_lookback",
        "mfi_centerline_lookback", "tsi_centerline_lookback", "ao_zero_cross_lookback",
        "keltner_mid_cross_lookback", "cmf_centerline_lookback", "vol_profile_breakout_lookback",
    ]:
        val = request.args.get(key)
        if val is not None:
            try:
                thresholds[key] = float(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for '{key}'"}), 400

    rsi_trigger = request.args.get("rsi_trigger")
    if rsi_trigger is not None:
        if rsi_trigger not in _VALID_RSI_TRIGGERS:
            return jsonify({"error": "Invalid value for 'rsi_trigger'"}), 400
        thresholds["rsi_trigger"] = rsi_trigger

    macd_trigger = request.args.get("macd_trigger")
    if macd_trigger is not None:
        if macd_trigger not in _VALID_MACD_TRIGGERS:
            return jsonify({"error": "Invalid value for 'macd_trigger'"}), 400
        thresholds["macd_trigger"] = macd_trigger

    bb_trigger = request.args.get("bb_trigger")
    if bb_trigger is not None:
        if bb_trigger not in _VALID_BB_TRIGGERS:
            return jsonify({"error": "Invalid value for 'bb_trigger'"}), 400
        thresholds["bb_trigger"] = bb_trigger

    ma_trigger = request.args.get("ma_trigger")
    if ma_trigger is not None:
        if ma_trigger not in _VALID_MA_TRIGGERS:
            return jsonify({"error": "Invalid value for 'ma_trigger'"}), 400
        thresholds["ma_trigger"] = ma_trigger

    adx_trigger = request.args.get("adx_trigger")
    if adx_trigger is not None:
        if adx_trigger not in _VALID_ADX_TRIGGERS:
            return jsonify({"error": "Invalid value for 'adx_trigger'"}), 400
        thresholds["adx_trigger"] = adx_trigger

    for trig_key, allowed in _TRIGGER_WHITELISTS.items():
        val = request.args.get(trig_key)
        if val is not None:
            if val not in allowed:
                return jsonify({"error": f"Invalid value for '{trig_key}'"}), 400
            thresholds[trig_key] = val

    calc_params = _extract_calc_params(request.args)
    calc_params.update(_extract_backtest_calc_params(request.args))

    try:
        df = _fetch_ohlcv(symbol, period, interval, start_date=start_date, end_date=end_date)
        trades, equity_curve, bah_curve = run_backtest(
            df,
            thresholds=thresholds or None,
            calc_params=calc_params or None,
            stop_loss_pct=stop_loss_pct,
            take_profit_pct=take_profit_pct,
            min_confidence=min_confidence,
            trailing_stop=trailing_stop,
            trail_distance_pct=trail_distance_pct,
        )
        metrics = calculate_metrics(trades, equity_curve)
        period_label = f"{start_date} → {end_date or 'today'}" if start_date else period
        return jsonify({
            "symbol":       symbol.upper(),
            "period":       period_label,
            "interval":     interval,
            "metrics":      metrics,
            "trades":       trades,
            "equity_curve": equity_curve,
            "bah_curve":    bah_curve,
        })
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Backtest failed: {str(e)}"}), 500


# ── Startup ───────────────────────────────────────────────────────────────────

_ensure_table()
_ensure_default_user()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=not _is_production, port=port)
