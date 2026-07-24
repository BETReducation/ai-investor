from flask import Flask, jsonify, request, send_from_directory, Response, session
from flask_cors import CORS
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from functools import wraps
import yfinance as yf
import pandas as pd
import bcrypt
import json
import os
import secrets
import hashlib
import hmac
import time
import re
import smtplib
import requests
from bs4 import BeautifulSoup
from email.mime.text import MIMEText
try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    psycopg2 = None
from datetime import timedelta
import datetime as _dt
import base64
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

from api.indicators import calculate_all
from api.signals import score_signals
from api.backtest import run_backtest
from api.metrics import calculate_metrics

app = Flask(__name__, static_folder="static")
app.secret_key = os.environ.get("SECRET_KEY", "gca-dev-key-change-in-production")
# Railway (and most PaaS hosts) terminate TLS at an edge proxy and forward requests
# over plain HTTP, so without this Flask sees every request as insecure — which
# breaks Secure-cookie handling (session + remember-me) behind the proxy.
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

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
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

# ── Alpha content ────────────────────────────────────────────────────────────
ALPHA_ROLES = {"tom", "dave", "gary", "connor"}
ALPHA_CONTENT_KINDS = {"post", "video", "link", "watchlist"}
ALPHA_STANCES = {"bullish", "neutral", "bearish"}
ALPHA_CONTENT_FILE = os.path.join(os.path.dirname(__file__), "alpha_content.json")
ALPHA_ATTACHMENTS_FILE = os.path.join(os.path.dirname(__file__), "alpha_attachments.json")
ALLOWED_DOC_EXTENSIONS = {"docx", "pdf", "xlsx", "xls"}
MAX_UPLOAD_TEXT_CHARS = 40000  # cap extracted text sent to the normalize step

# Each partner's 3 nominated topics — must match the topic-pill labels
# hardcoded on their public page (static/alpha-<name>.html).
ALPHA_TOPICS = {
    "tom":    ["Stocks", "Metals", "ETFs"],
    "dave":   ["Chart Breakdowns", "Setups Watchlist", "Pre-Market"],
    "gary":   ["Long-Term Investing", "Technical Analysis", "Impact of AI"],
    "connor": ["Macro & Micro", "Quant Statistics", "Finance & Formulae"],
}


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
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS alpha_role TEXT")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_file BYTEA")
        cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar_filename TEXT")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alpha_content (
                id              SERIAL PRIMARY KEY,
                author          TEXT NOT NULL,
                kind            TEXT NOT NULL,
                status          TEXT NOT NULL DEFAULT 'draft',
                topic           TEXT,
                title           TEXT,
                snippet         TEXT,
                body            TEXT,
                stance          TEXT,
                url             TEXT,
                source_kind     TEXT,
                source_filename TEXT,
                source_file     BYTEA,
                source_text     TEXT,
                created_at      TIMESTAMP NOT NULL DEFAULT now(),
                updated_at      TIMESTAMP NOT NULL DEFAULT now(),
                published_at    TIMESTAMP
            )
        """)
        cur.execute("ALTER TABLE alpha_content ADD COLUMN IF NOT EXISTS subtitle TEXT")
        cur.execute("ALTER TABLE alpha_content ADD COLUMN IF NOT EXISTS image_url TEXT")
        cur.execute("ALTER TABLE alpha_content ADD COLUMN IF NOT EXISTS image_filename TEXT")
        cur.execute("ALTER TABLE alpha_content ADD COLUMN IF NOT EXISTS image_file BYTEA")
        cur.execute("ALTER TABLE alpha_content ADD COLUMN IF NOT EXISTS staged_edits JSONB")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS alpha_content_attachment (
                id          SERIAL PRIMARY KEY,
                content_id  INTEGER NOT NULL,
                filename    TEXT,
                file        BYTEA NOT NULL,
                created_at  TIMESTAMP NOT NULL DEFAULT now()
            )
        """)

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
    "hs_pivot": 3, "hs_lookback": 90,
    # ── Extended set (calculate_all now exposes the same indicators/trigger-modes
    # Backtester does — same keys as _BT_INT_CALC_KEYS below, plus a few that only
    # this endpoint needs since Backtester computes them from `thresholds` instead).
    "rsi_div_lookback": 5,
    "macd_div_lookback": 5, "macd_zscore_length": 100,
    "stochrsi_div_lookback": 5,
    "willr_div_lookback": 5, "willr_confirm_lookback": 5,
    "roc_div_lookback": 5, "roc_momentum_lookback": 3,
    "mfi_div_lookback": 5,
    "tsi_div_lookback": 5,
    "ao_div_lookback": 5, "ao_twin_peaks_lookback": 5,
    "ichimoku_tenkan": 9, "ichimoku_kijun": 26, "ichimoku_senkou": 52,
    "donchian_length": 20,
    "keltner_length": 20, "keltner_atr_length": 10,
    "keltner_walk_min_consecutive": 3, "keltner_squeeze_lookback": 10,
    "stdev_length": 20,
    "chaikin_vol_ema_length": 10, "chaikin_vol_roc_length": 10,
    "hist_vol_length": 20,
    "vwap_length": 20, "vwap_anchored": 0,
    "ad_sma_length": 20, "ad_div_lookback": 5,
    "cmf_length": 20,
    "tsi_long": 25, "tsi_short": 13, "tsi_signal": 13,
    "ao_fast": 5, "ao_slow": 34,
    "obv_sma_length": 20, "obv_div_lookback": 5,
    "vol_profile_lookback": 50, "vol_profile_bins": 24,
    "fib_lookback": 50,
    "hma_slope_lookback": 3, "hma_fast_length": 9,
    "bb_squeeze_lookback": 100, "bb_breakout_window": 10,
    "bb_walk_min_consecutive": 3, "bb_pattern_lookback": 5,
    "ma_short_length": 9, "ma_medium_length": 20, "ma_long_length": 50,
    "psar_gap_lookback": 3, "supertrend_gap_lookback": 3,
    "atr_trend_lookback": 5, "stdev_trend_lookback": 5,
    "chaikin_vol_trend_lookback": 5, "hist_vol_trend_lookback": 5,
}
_FLOAT_CALC_KEYS = {
    "bb_std": 2.0, "supertrend_mult": 3.0,
    "psar_start": 0.02, "psar_inc": 0.02, "psar_max": 0.2,
    # ── Extended set ──────────────────────────────────────────────────────
    "rsi_oversold": 30.0, "rsi_overbought": 70.0,
    "willr_oversold": -80.0, "willr_overbought": -20.0,
    "keltner_mult": 2.0, "keltner_walk_tolerance_pct": 0.5,
    "bb_squeeze_percentile": 20.0, "bb_walk_tolerance_pct": 0.5,
    "vwap_band_pct": 1.0, "fib_tolerance_pct": 0.5,
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
    ma_type = args.get("ma_type", "").strip().lower()
    if ma_type in ("simple", "smoothed", "exponential", "weighted", "volume_weighted"):
        params["ma_type"] = ma_type
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

_TRIGGER_WHITELISTS = {
    "rsi_trigger":         {"overbought_oversold", "overbought", "oversold", "centerline_cross",
                             "bullish_divergence", "bearish_divergence", "failure_swings"},
    "macd_trigger":        {"signal_cross", "bullish_signal_cross", "bearish_signal_cross", "centerline_cross",
                             "bullish_divergence", "bearish_divergence", "histogram_reversal", "overbought", "oversold"},
    "bb_trigger":          {"percent_b", "upper_touch", "lower_touch", "volatility_breakout",
                             "walking_upper", "walking_lower", "w_bottom", "m_top",
                             "breakout_margin", "pct_below_high", "pct_above_low"},
    "ma_trigger":          {"dual_cross", "price_cross", "two_ma_bull", "two_ma_bear", "three_ma_bull", "three_ma_bear"},
    "adx_trigger":         {"trend_threshold", "bull_di_cross", "bear_di_cross", "above_25", "above_50", "above_75",
                             "strong_di_plus", "strong_di_minus"},
    "psar_trigger":        {"flip", "bull_flip", "bear_flip", "trend_state", "trailing_stop"},
    "ichimoku_trigger":    {"cloud_position", "bullish", "bearish", "tk_cross"},
    "supertrend_trigger":  {"flip", "bull_flip", "bear_flip", "trend_state", "trailing_stop"},
    "donchian_trigger":    {"breakout", "bullish", "bearish", "middle_cross", "two_channel_bull", "two_channel_bear",
                             "resistance_retest", "support_retest"},
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
    "inv_hs_trigger":      {"neckline_touch", "neckline_break"},
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


VALID_PERIODS = {"1d", "5d", "60d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"}

TIER_RANKS = {"basic": 0, "signal_tester": 1, "power_user": 2}


# ── User model ───────────────────────────────────────────────────────────────

class User(UserMixin):
    def __init__(self, username: str, tier: str = "basic", alpha_role: str | None = None):
        self.id = username
        self.tier = tier
        self.alpha_role = alpha_role


@login_manager.user_loader
def load_user(username: str):
    users = _load_users()
    if username in users:
        u = users[username]
        return User(username, u.get("tier", "basic"), u.get("alpha_role"))
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


def alpha_author_required(f):
    """Gates an endpoint to users with an assigned alpha_role (one of the 4 partners)."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Login required"}), 401
        if not getattr(current_user, "alpha_role", None):
            return jsonify({"error": "This account has no Alpha author access"}), 403
        return f(*args, **kwargs)
    return wrapped


# ── User-store helpers ───────────────────────────────────────────────────────

def _load_users() -> dict:
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT username, password_hash, preferences, tier, profile, alpha_role FROM users")
            return {
                row["username"]: {
                    "password_hash": row["password_hash"],
                    "preferences":   row["preferences"] or {},
                    "tier":          row.get("tier", "basic"),
                    "profile":       row.get("profile") or {},
                    "alpha_role":    row.get("alpha_role"),
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
                    INSERT INTO users (username, password_hash, preferences, tier, profile, alpha_role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ON CONFLICT (username) DO UPDATE
                        SET password_hash = EXCLUDED.password_hash,
                            preferences   = EXCLUDED.preferences,
                            tier          = EXCLUDED.tier,
                            profile       = EXCLUDED.profile,
                            alpha_role    = EXCLUDED.alpha_role
                """, (username, data["password_hash"], json.dumps(data.get("preferences", {})), data.get("tier", "basic"), json.dumps(data.get("profile", {})), data.get("alpha_role")))
        return
    with open(USERS_FILE, "w") as f:
        json.dump({"users": users}, f, indent=2)


def get_user_avatar(username: str):
    """Returns (filename, bytes) or (None, None). Kept out of _load_users()'s
    Postgres SELECT so that hot path (hit on every authenticated request)
    never has to move an image blob around."""
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT avatar_filename, avatar_file FROM users WHERE username = %s", (username,))
            row = cur.fetchone()
            if not row or row["avatar_file"] is None:
                return None, None
            return row["avatar_filename"], bytes(row["avatar_file"])
    users = _load_users()
    user = users.get(username)
    if not user or not user.get("avatar_file"):
        return None, None
    return user.get("avatar_filename"), base64.b64decode(user["avatar_file"])


def set_user_avatar(username: str, filename: str, file_bytes: bytes) -> None:
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET avatar_file = %s, avatar_filename = %s WHERE username = %s",
                (psycopg2.Binary(file_bytes), filename, username),
            )
        return
    users = _load_users()
    if username not in users:
        return
    users[username]["avatar_file"] = base64.b64encode(file_bytes).decode("ascii")
    users[username]["avatar_filename"] = filename
    _save_users(users)


# ── Alpha content store ──────────────────────────────────────────────────────
# Mirrors the _load_users/_save_users dual-path pattern above: Postgres when
# DATABASE_URL is set, a local JSON file otherwise. source_file (the original
# uploaded document) is never included in list/get results — only
# alpha_content_get_file() fetches it, so listing drafts never has to move a
# binary blob around.

_ALPHA_CONTENT_FIELDS = [
    "author", "kind", "status", "topic", "title", "subtitle", "snippet", "body", "stance", "url",
    "source_kind", "source_filename", "source_text",
    "image_url", "image_filename",
    # Pending edits to a *published* item, held back from the live page until the
    # author unpublishes (which folds them in) and re-publishes. Studio-only —
    # the public endpoints whitelist their output via _ALPHA_PUBLIC_FIELDS, so
    # this never leaks. Shape: {title, subtitle, snippet, body, topic, url,
    # stance, image_url} — a subset, only the fields that were edited.
    "staged_edits",
]


def _alpha_row_to_dict(row: dict) -> dict:
    d = {k: row.get(k) for k in ["id", *_ALPHA_CONTENT_FIELDS]}
    for key in ("created_at", "updated_at", "published_at"):
        val = row.get(key)
        d[key] = val.isoformat() if val is not None else None
    return d


def _load_alpha_content_json() -> dict:
    if not os.path.exists(ALPHA_CONTENT_FILE):
        return {"items": [], "next_id": 1}
    with open(ALPHA_CONTENT_FILE, "r") as f:
        return json.load(f)


def _save_alpha_content_json(data: dict) -> None:
    with open(ALPHA_CONTENT_FILE, "w") as f:
        json.dump(data, f, indent=2)


def alpha_content_list(author: str | None = None, status: str | None = None) -> list:
    if DATABASE_URL:
        query = f"SELECT id, {', '.join(_ALPHA_CONTENT_FIELDS)}, created_at, updated_at, published_at FROM alpha_content WHERE 1=1"
        params = []
        if author:
            query += " AND author = %s"
            params.append(author)
        if status:
            query += " AND status = %s"
            params.append(status)
        query += " ORDER BY created_at DESC"
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            return [_alpha_row_to_dict(row) for row in cur.fetchall()]
    data = _load_alpha_content_json()
    items = data["items"]
    if author:
        items = [i for i in items if i.get("author") == author]
    if status:
        items = [i for i in items if i.get("status") == status]
    items = sorted(items, key=lambda i: i.get("created_at") or "", reverse=True)
    return [{k: v for k, v in i.items() if k not in ("source_file", "image_file")} for i in items]


def alpha_content_get(item_id: int) -> dict | None:
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"SELECT id, {', '.join(_ALPHA_CONTENT_FIELDS)}, created_at, updated_at, published_at "
                f"FROM alpha_content WHERE id = %s", (item_id,)
            )
            row = cur.fetchone()
            return _alpha_row_to_dict(row) if row else None
    data = _load_alpha_content_json()
    for item in data["items"]:
        if item.get("id") == item_id:
            return {k: v for k, v in item.items() if k not in ("source_file", "image_file")}
    return None


def alpha_content_get_file(item_id: int):
    """Returns (filename, bytes) or (None, None) if there's no attached file."""
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT source_filename, source_file FROM alpha_content WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if not row or row["source_file"] is None:
                return None, None
            return row["source_filename"], bytes(row["source_file"])
    data = _load_alpha_content_json()
    for item in data["items"]:
        if item.get("id") == item_id:
            b64 = item.get("source_file")
            if not b64:
                return None, None
            return item.get("source_filename"), base64.b64decode(b64)
    return None, None


def alpha_content_get_image(item_id: int):
    """Returns (filename, bytes) or (None, None) if there's no uploaded image file."""
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT image_filename, image_file FROM alpha_content WHERE id = %s", (item_id,))
            row = cur.fetchone()
            if not row or row["image_file"] is None:
                return None, None
            return row["image_filename"], bytes(row["image_file"])
    data = _load_alpha_content_json()
    for item in data["items"]:
        if item.get("id") == item_id:
            b64 = item.get("image_file")
            if not b64:
                return None, None
            return item.get("image_filename"), base64.b64decode(b64)
    return None, None


def alpha_content_set_image(item_id: int, filename: str, file_bytes: bytes) -> dict | None:
    """Sets the uploaded image file, clearing image_url to enforce file-vs-URL exclusivity."""
    now = _dt.datetime.utcnow()
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"UPDATE alpha_content SET image_file = %s, image_filename = %s, image_url = NULL, "
                f"updated_at = %s WHERE id = %s "
                f"RETURNING id, {', '.join(_ALPHA_CONTENT_FIELDS)}, created_at, updated_at, published_at",
                (psycopg2.Binary(file_bytes), filename, now, item_id),
            )
            row = cur.fetchone()
            return _alpha_row_to_dict(row) if row else None
    data = _load_alpha_content_json()
    for item in data["items"]:
        if item.get("id") == item_id:
            item["image_file"] = base64.b64encode(file_bytes).decode("ascii")
            item["image_filename"] = filename
            item["image_url"] = None
            item["updated_at"] = now.isoformat()
            _save_alpha_content_json(data)
            return {k: v for k, v in item.items() if k not in ("source_file", "image_file")}
    return None


# ── Inline post attachments ──────────────────────────────────────────────────
# A post's main image is a single slot on the alpha_content row itself; these
# are additional images a writer drops into the middle of a post's body via
# the Studio's Insert Image button, so a post can hold more than one.

def _load_alpha_attachments_json() -> dict:
    if not os.path.exists(ALPHA_ATTACHMENTS_FILE):
        return {"items": [], "next_id": 1}
    with open(ALPHA_ATTACHMENTS_FILE, "r") as f:
        return json.load(f)


def _save_alpha_attachments_json(data: dict) -> None:
    with open(ALPHA_ATTACHMENTS_FILE, "w") as f:
        json.dump(data, f, indent=2)


def alpha_attachment_create(content_id: int, filename: str, file_bytes: bytes) -> int:
    """Returns the new attachment's id."""
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO alpha_content_attachment (content_id, filename, file) VALUES (%s, %s, %s) RETURNING id",
                (content_id, filename, psycopg2.Binary(file_bytes)),
            )
            return cur.fetchone()[0]
    data = _load_alpha_attachments_json()
    new_id = data.get("next_id", 1)
    data["items"].append({
        "id": new_id,
        "content_id": content_id,
        "filename": filename,
        "file": base64.b64encode(file_bytes).decode("ascii"),
    })
    data["next_id"] = new_id + 1
    _save_alpha_attachments_json(data)
    return new_id


def alpha_attachment_get(attachment_id: int):
    """Returns (content_id, filename, bytes) or (None, None, None)."""
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT content_id, filename, file FROM alpha_content_attachment WHERE id = %s", (attachment_id,))
            row = cur.fetchone()
            if not row:
                return None, None, None
            return row["content_id"], row["filename"], bytes(row["file"])
    data = _load_alpha_attachments_json()
    for item in data["items"]:
        if item.get("id") == attachment_id:
            return item.get("content_id"), item.get("filename"), base64.b64decode(item["file"])
    return None, None, None


def alpha_content_create(fields: dict, file_bytes: bytes | None = None) -> dict:
    now = _dt.datetime.utcnow()
    if DATABASE_URL:
        cols = [*_ALPHA_CONTENT_FIELDS, "source_file", "created_at", "updated_at"]
        vals = [fields.get(k) for k in _ALPHA_CONTENT_FIELDS] + [
            psycopg2.Binary(file_bytes) if file_bytes else None, now, now
        ]
        placeholders = ", ".join(["%s"] * len(vals))
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"INSERT INTO alpha_content ({', '.join(cols)}) VALUES ({placeholders}) "
                f"RETURNING id, {', '.join(_ALPHA_CONTENT_FIELDS)}, created_at, updated_at, published_at",
                vals,
            )
            row = cur.fetchone()
            return _alpha_row_to_dict(row)
    data = _load_alpha_content_json()
    new_id = data.get("next_id", 1)
    item = {k: fields.get(k) for k in _ALPHA_CONTENT_FIELDS}
    item["id"] = new_id
    item["created_at"] = now.isoformat()
    item["updated_at"] = now.isoformat()
    item["published_at"] = None
    if file_bytes:
        item["source_file"] = base64.b64encode(file_bytes).decode("ascii")
    data["items"].append(item)
    data["next_id"] = new_id + 1
    _save_alpha_content_json(data)
    return {k: v for k, v in item.items() if k not in ("source_file", "image_file")}


def alpha_content_update(item_id: int, updates: dict) -> dict | None:
    now = _dt.datetime.utcnow()
    allowed = set(_ALPHA_CONTENT_FIELDS) | {"published_at", "image_file"}
    updates = {k: v for k, v in updates.items() if k in allowed}
    if DATABASE_URL:
        if not updates:
            return alpha_content_get(item_id)
        set_clauses = [f"{k} = %s" for k in updates] + ["updated_at = %s"]
        # staged_edits is a JSONB column — wrap the dict so psycopg2 adapts it.
        vals = [
            psycopg2.extras.Json(v) if k == "staged_edits" and v is not None else v
            for k, v in updates.items()
        ] + [now, item_id]
        with _db_conn() as conn, conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(
                f"UPDATE alpha_content SET {', '.join(set_clauses)} WHERE id = %s "
                f"RETURNING id, {', '.join(_ALPHA_CONTENT_FIELDS)}, created_at, updated_at, published_at",
                vals,
            )
            row = cur.fetchone()
            return _alpha_row_to_dict(row) if row else None
    data = _load_alpha_content_json()
    json_updates = dict(updates)
    if "published_at" in json_updates:
        val = json_updates["published_at"]
        json_updates["published_at"] = val.isoformat() if hasattr(val, "isoformat") else val
    for item in data["items"]:
        if item.get("id") == item_id:
            item.update(json_updates)
            item["updated_at"] = now.isoformat()
            _save_alpha_content_json(data)
            return {k: v for k, v in item.items() if k not in ("source_file", "image_file")}
    return None


def alpha_content_delete(item_id: int) -> bool:
    if DATABASE_URL:
        with _db_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM alpha_content_attachment WHERE content_id = %s", (item_id,))
            cur.execute("DELETE FROM alpha_content WHERE id = %s", (item_id,))
            return cur.rowcount > 0
    attachments = _load_alpha_attachments_json()
    attachments["items"] = [a for a in attachments["items"] if a.get("content_id") != item_id]
    _save_alpha_attachments_json(attachments)
    data = _load_alpha_content_json()
    before = len(data["items"])
    data["items"] = [i for i in data["items"] if i.get("id") != item_id]
    _save_alpha_content_json(data)
    return len(data["items"]) < before


# ── Alpha content: extraction & normalization ────────────────────────────────

def extract_text_from_upload(file_storage) -> str:
    """Extracts plain text from an uploaded .docx/.pdf/.xlsx/.xls FileStorage.
    Raises ValueError with a user-facing message on failure."""
    filename = file_storage.filename or ""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ALLOWED_DOC_EXTENSIONS:
        raise ValueError(f"Unsupported file type .{ext or '?'} — please upload a Word, PDF or Excel file")
    try:
        if ext == "docx":
            import docx
            from docx.table import Table as DocxTable
            from docx.text.paragraph import Paragraph as DocxParagraph
            document = docx.Document(file_storage)
            # Walk paragraphs and tables in actual document order (python-docx's
            # .paragraphs/.tables only give each kind separately, losing where a
            # table sits relative to the surrounding text) and render each table
            # as a real markdown table (header + `---` separator row) so it's
            # unambiguous downstream — see auto_section_tables(), which wraps a
            # block matching this exact shape into its own Table section.
            parts = []
            for child in document.element.body.iterchildren():
                if child.tag.endswith("}p"):
                    p = DocxParagraph(child, document)
                    if p.text.strip():
                        parts.append(p.text.strip())
                elif child.tag.endswith("}tbl"):
                    table = DocxTable(child, document)
                    rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
                    rows = [r for r in rows if any(c for c in r)]
                    if not rows:
                        continue
                    md = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(" --- " for _ in rows[0]) + "|"]
                    for r in rows[1:]:
                        md.append("| " + " | ".join(r) + " |")
                    parts.append("\n".join(md))
            text = "\n\n".join(parts)
        elif ext == "pdf":
            from pypdf import PdfReader
            reader = PdfReader(file_storage)
            text = "\n".join((page.extract_text() or "") for page in reader.pages)
        else:  # xlsx / xls
            import openpyxl
            wb = openpyxl.load_workbook(file_storage, data_only=True)
            parts = []
            for sheet in wb.worksheets:
                parts.append(f"[Sheet: {sheet.title}]")
                for row in sheet.iter_rows(values_only=True):
                    cells = [str(c) for c in row if c is not None]
                    if cells:
                        parts.append(" | ".join(cells))
            text = "\n".join(parts)
    except ValueError:
        raise
    except Exception:
        raise ValueError("Couldn't read that file — it may be corrupted, password-protected, or an unsupported format")
    text = text.strip()
    if not text:
        raise ValueError("No readable text found in that file")
    return text[:MAX_UPLOAD_TEXT_CHARS]


def extract_text_from_url(url: str) -> str:
    """Fetches a URL and strips it down to readable text. Best-effort — many
    sites (paywalls, JS-rendered pages, bot protection) won't work well; the
    'paste text' input mode is the reliable fallback for those."""
    if not url.startswith(("http://", "https://")):
        raise ValueError("Please enter a valid http(s) link")
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0 (GCA-AlphaBot)"})
        resp.raise_for_status()
    except Exception:
        raise ValueError("Couldn't fetch that link — try pasting the text directly instead")
    try:
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "nav", "header", "footer", "noscript"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
        lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
        text = "\n".join(lines)
    except Exception:
        raise ValueError("Couldn't read the content at that link")
    if not text:
        raise ValueError("No readable text found at that link")
    return text[:MAX_UPLOAD_TEXT_CHARS]


def normalize_content(raw_text: str, author: str, topics: list) -> dict:
    """Turns raw extracted text into {title, subtitle, topic, snippet, body} for a draft post.

    STUB — no ANTHROPIC_API_KEY is wired in yet. This does a naive extractive
    pass (first sentence as title, second sentence as a subtitle suggestion,
    next couple of sentences as snippet, raw text reflowed into paragraphs as
    the body, first nominated topic as the default) so the rest of the
    pipeline — upload, draft review, edit, publish, public rendering — is
    fully testable right now.

    To make this real: call the Claude API (see the claude-api skill for the
    current model id and Messages API usage) with a prompt that gives it
    `author`, the exact `topics` list (it must pick one of these three, not
    invent a new one), and `raw_text`, instructing it to return JSON
    {title, subtitle, topic, snippet, body} — allowed to tighten/condense
    wording (per the earlier scoping decision) but not invent facts absent
    from raw_text. Keep the same return shape so no caller needs to change.
    """
    text = " ".join(raw_text.split())
    sentences = re.split(r"(?<=[.!?])\s+", text)
    title = (sentences[0] if sentences else text)[:100].strip() or "Untitled note"
    subtitle_source = sentences[1] if len(sentences) > 1 else (sentences[0] if sentences else text)
    subtitle = subtitle_source.strip()[:140]
    if len(subtitle_source) > 140:
        subtitle += "…"
    snippet_source = " ".join(sentences[1:3]) if len(sentences) > 1 else text
    snippet_words = snippet_source.split()
    snippet = " ".join(snippet_words[:40])
    if len(snippet_words) > 40:
        snippet += "…"
    paragraphs = [p.strip() for p in raw_text.split("\n") if p.strip()]
    body_parts = []
    for i, p in enumerate(paragraphs):
        if i > 0:
            # Keep consecutive markdown-table-row lines tight (single \n) so a
            # table survives this reflow intact — the normal blank-line-per-
            # paragraph spacing would otherwise pull each row apart, breaking
            # the table shape auto_section_tables() looks for below.
            prev_is_row = _looks_like_table_row(paragraphs[i - 1])
            this_is_row = _looks_like_table_row(p)
            body_parts.append("\n" if (prev_is_row and this_is_row) else "\n\n")
        body_parts.append(p)
    body = "".join(body_parts) if body_parts else text
    topic = topics[0] if topics else None
    return {"title": title, "subtitle": subtitle, "topic": topic, "snippet": snippet, "body": body}


def _looks_like_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.endswith("|") and s.count("|") >= 2


def _is_table_separator_row(line: str) -> bool:
    """`| --- | :--- | ---: |` — a markdown table's header/body divider row.
    Checked cell-by-cell rather than with one big character class, since a
    naive `^\\|[\\s:-]+\\|$` also has to reject the '|' *between* cells."""
    s = line.strip()
    if not (s.startswith("|") and s.endswith("|")):
        return False
    cells = [c.strip() for c in s.strip("|").split("|")]
    return len(cells) >= 1 and all(re.match(r"^:?-{2,}:?$", c) for c in cells)


# Matches the SECTION_JOIN / type-marker microsyntax the studio's section
# editor uses (static/alpha-studio.html — keep in sync with SECTION_JOIN and
# the type marker patterns there).
_SECTION_JOIN = "<!--section-->"


def auto_section_tables(body: str) -> str:
    """Wraps any markdown-table-shaped block (a `| ... |` row, a `|---|---|`
    separator row, then more `| ... |` rows) in its own Table section, so a
    table detected in an uploaded document lands directly in a Table section
    for editing instead of as garbled pipe-delimited text in a Normal one.
    No-op if the body has no such block.
    """
    lines = body.split("\n")
    out_lines = []
    i = 0
    found_any = False
    while i < len(lines):
        line = lines[i]
        if _looks_like_table_row(line) and i + 1 < len(lines) and _is_table_separator_row(lines[i + 1]):
            # Found a table: header row + separator row, then consume further row lines.
            table_lines = [line, lines[i + 1]]
            j = i + 2
            while j < len(lines) and _looks_like_table_row(lines[j]):
                table_lines.append(lines[j])
                j += 1
            while out_lines and not out_lines[-1].strip():
                out_lines.pop()
            if out_lines:
                out_lines.append("")
                out_lines.append(_SECTION_JOIN)
                out_lines.append("")
            out_lines.append("<!--type:table-->")
            out_lines.extend(table_lines)
            while j < len(lines) and not lines[j].strip():
                j += 1
            if j < len(lines):
                out_lines.append("")
                out_lines.append(_SECTION_JOIN)
                out_lines.append("")
            found_any = True
            i = j
            continue
        out_lines.append(line)
        i += 1
    return "\n".join(out_lines) if found_any else body


# ── Structured Word template ──────────────────────────────────────────────
# Convention (see the "Alpha Post Template" doc): every section starts with a
# "Heading 2" paragraph. Plain heading text = a Normal section. A bracket tag
# at the start of that heading picks a different type — "[TIP] Careful with
# leverage", "[QUOTE] Warren Buffett", "[TABLE] Key Metrics" (tables are also
# auto-detected from a real Word table regardless of any heading — see
# auto_section_tables above, which this mirrors), "[IMAGE LEFT] Our Office" /
# "[IMAGE RIGHT] Our Office" (the first inline picture in that section becomes
# the image). Content between one Heading 2 and the next belongs to that
# section. Keep these tags in sync with stripTypeMarker()'s marker strings in
# static/alpha-studio.html and static/alpha-post.html.
#
# Two more tags don't create a section at all — they fill the draft's own
# Subtitle/Snippet fields instead: "[SUBTITLE] ..." and "[SNIPPET] ...". Put
# the text right on the heading line, or leave the heading bare and write it
# as the paragraph(s) underneath — either works (see flush()'s "meta:" case).
_TYPE_MARKERS = {"tip": "<!--type:tip-->", "quote": "<!--type:quote-->", "table": "<!--type:table-->"}
_HEADING_TAG_RE = re.compile(r"^\[(TIP|QUOTE|TABLE|IMAGE\s+LEFT|IMAGE\s+RIGHT|IMAGE|SUBTITLE|SNIPPET)\]\s*", re.IGNORECASE)
_BLIP_TAG = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
_R_EMBED_ATTR = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed"


def _paragraph_image(paragraph, document):
    """Returns (bytes, extension) for the first inline picture in this
    paragraph's runs, or (None, None) if it has none."""
    for run in paragraph.runs:
        for blip in run._element.iter(_BLIP_TAG):
            rid = blip.get(_R_EMBED_ATTR)
            if rid and rid in document.part.related_parts:
                part = document.part.related_parts[rid]
                ext = (part.content_type.split("/")[-1] or "png").lower()
                if ext == "jpeg":
                    ext = "jpg"
                if ext not in ALLOWED_IMAGE_EXTENSIONS:
                    ext = "png"
                return part.blob, ext
    return None, None


def extract_structured_docx(file_storage):
    """Parses a docx built from the section template into (sections, meta),
    or returns None if the doc has no "Heading 2" paragraph at all (i.e. it
    wasn't built from the template) — callers should fall back to the plain
    extract_text_from_upload() + normalize_content() path then.

    sections: list of {type, heading, body_lines: [str, ...],
    rows: [[str,...],...] or None, image: (bytes, ext) or None,
    side: 'left'|'right'}. Images aren't uploaded here (no content row/id
    exists yet at extraction time — see _serialize_structured_sections,
    called after alpha_content_create).

    meta: {"subtitle": str or None, "snippet": str or None} — filled from any
    "[SUBTITLE]"/"[SNIPPET]" tagged block instead of becoming a section.
    """
    import docx
    from docx.table import Table as DocxTable
    from docx.text.paragraph import Paragraph as DocxParagraph
    document = docx.Document(file_storage)

    def blank_section():
        return {"type": "normal", "heading": "", "body_lines": [], "rows": None, "image": None, "side": "left"}

    children = list(document.element.body.iterchildren())
    has_heading = any(
        c.tag.endswith("}p") and DocxParagraph(c, document).style and DocxParagraph(c, document).style.name == "Heading 2"
        for c in children
    )
    if not has_heading:
        return None

    sections = []
    meta = {"subtitle": None, "snippet": None}
    cur = blank_section()

    def flush():
        nonlocal cur
        if cur["type"].startswith("meta:"):
            field = cur["type"].split(":", 1)[1]
            value = (cur["heading"] or "").strip() or "\n".join(cur["body_lines"]).strip()
            if value:
                meta[field] = value
        elif cur["heading"] or cur["body_lines"] or cur["rows"] or cur["image"]:
            sections.append(cur)
        cur = blank_section()

    for child in children:
        if child.tag.endswith("}p"):
            p = DocxParagraph(child, document)
            style_name = p.style.name if p.style else ""
            text = p.text.strip()
            if style_name == "Heading 2":
                flush()
                m = _HEADING_TAG_RE.match(text)
                if m:
                    tag = re.sub(r"\s+", " ", m.group(1).upper())
                    remainder = text[m.end():].strip()
                    if tag == "TIP":
                        cur["type"] = "tip"
                    elif tag == "QUOTE":
                        cur["type"] = "quote"
                    elif tag == "TABLE":
                        cur["type"] = "table"
                    elif tag == "SUBTITLE":
                        cur["type"] = "meta:subtitle"
                    elif tag == "SNIPPET":
                        cur["type"] = "meta:snippet"
                    elif tag.startswith("IMAGE"):
                        cur["type"] = "image"
                        cur["side"] = "right" if "RIGHT" in tag else "left"
                    cur["heading"] = remainder
                else:
                    cur["heading"] = text
                continue
            if cur["type"] == "image" and not cur["image"]:
                img_bytes, img_ext = _paragraph_image(p, document)
                if img_bytes:
                    cur["image"] = (img_bytes, img_ext)
                    continue
            if text:
                cur["body_lines"].append(text)
        elif child.tag.endswith("}tbl"):
            table = DocxTable(child, document)
            rows = [[cell.text.strip() for cell in row.cells] for row in table.rows]
            rows = [r for r in rows if any(c for c in r)]
            if not rows:
                continue
            if cur["type"] == "table" and cur["rows"] is None:
                cur["rows"] = rows
            else:
                # A table with no preceding "[TABLE]" heading still gets its
                # own section automatically, same rule as auto_section_tables()
                # for a non-template upload.
                flush()
                cur["type"] = "table"
                cur["rows"] = rows
                flush()
    flush()
    return sections, meta


def _serialize_structured_sections(sections, upload_image) -> str:
    """Builds the SECTION_JOIN-delimited body string from
    extract_structured_docx() output. `upload_image(bytes, ext) -> url` is
    called once per section that has an extracted image."""
    parts = []
    for sec in sections:
        t = sec["type"]
        heading = (sec.get("heading") or "").strip()
        if t == "table":
            rows = sec.get("rows") or []
            if not rows:
                continue
            md = ["| " + " | ".join(rows[0]) + " |", "|" + "|".join(" --- " for _ in rows[0]) + "|"]
            for r in rows[1:]:
                md.append("| " + " | ".join(r) + " |")
            chunk = "<!--type:table-->"
            if heading:
                chunk += "\n## " + heading
            chunk += "\n" + "\n".join(md)
            parts.append(chunk)
            continue
        if t == "image":
            body = "\n".join(sec.get("body_lines") or [])
            img = sec.get("image")
            url = upload_image(*img) if img else None
            if not heading and not body and not url:
                continue
            chunk = "<!--type:image:" + sec.get("side", "left") + "-->"
            if heading:
                chunk += "\n## " + heading
            if url:
                chunk += "\n![" + heading.replace("[", "").replace("]", "") + "](" + url + ")"
            if body:
                chunk += ("\n\n" if (heading or url) else "\n") + body
            parts.append(chunk)
            continue
        # normal / tip / quote
        body = "\n\n".join(sec.get("body_lines") or [])
        chunk = _TYPE_MARKERS.get(t, "")
        if heading:
            chunk += ("\n" if chunk else "") + "## " + heading
        if body:
            chunk += ("\n\n" if chunk else "") + body
        if chunk.strip():
            parts.append(chunk)
    return ("\n\n" + _SECTION_JOIN + "\n\n").join(parts)


def _send_email(to_addr: str, subject: str, body: str) -> None:
    smtp_host = os.environ.get("SMTP_HOST", "")
    if not smtp_host:
        # No SMTP configured — log so it's still usable during setup/testing.
        print(f"\n  ✉️  [email not configured] To: {to_addr}  Subject: {subject}\n{body}\n")
        return
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = os.environ.get("SMTP_USER", "")
    smtp_pass = os.environ.get("SMTP_PASS", "")
    from_addr = os.environ.get("SMTP_FROM", smtp_user)
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = from_addr
    msg["To"] = to_addr
    with smtplib.SMTP(smtp_host, smtp_port) as server:
        server.starttls()
        if smtp_user:
            server.login(smtp_user, smtp_pass)
        server.sendmail(from_addr, [to_addr], msg.as_string())


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


# yfinance/Yahoo occasionally throws transient errors (rate limiting, connection resets,
# brief service hiccups) that have nothing to do with the symbol or params being wrong —
# retrying a couple of times with a short backoff clears most of them before a user ever
# sees a failure. Only exhausted retries bubble up, as a ValueError clearly labeled
# "temporarily unavailable" so callers/UI can tell that apart from "bad symbol/params".
_YF_RETRY_ATTEMPTS = 3
_YF_RETRY_BACKOFF_SECONDS = 0.75


def _yf_history_with_retry(ticker: "yf.Ticker", **kwargs) -> pd.DataFrame:
    last_err: Exception | None = None
    for attempt in range(_YF_RETRY_ATTEMPTS):
        try:
            return ticker.history(auto_adjust=False, **kwargs)
        except Exception as e:
            last_err = e
            if attempt < _YF_RETRY_ATTEMPTS - 1:
                time.sleep(_YF_RETRY_BACKOFF_SECONDS * (attempt + 1))
    raise ValueError(f"Yahoo Finance data temporarily unavailable — try again in a moment ({last_err})")


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
        # auto_adjust=False: keep raw (split-adjusted only, not dividend-adjusted) closes.
        # yfinance's auto_adjust=True folds dividends into every historical Close, which
        # can badly skew RSI/MACD/etc. for anything with a meaningful dividend/distribution
        # history — and it's also what our own price chart plots, so indicators computed
        # here always line up with what's on screen.
        df = _yf_history_with_retry(ticker, start=start_date, end=end_date or None, interval=fetch_interval)
    else:
        if period not in VALID_PERIODS:
            raise ValueError(f"Invalid period: {period}")
        df = _yf_history_with_retry(ticker, period=period, interval=fetch_interval)
    if df.empty:
        raise ValueError(f"No data returned for symbol: {symbol} — check the ticker is correct")
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

@app.route("/backtester/forex")
def backtester_forex():
    return send_from_directory("static", "strategy-lab-forex.html")

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

@app.route("/learn/beginner/invest-consistently")
def learn_beginner_invest_consistently(): return send_from_directory("static", "lesson-invest-consistently.html")

@app.route("/learn/beginner/keep-costs-low")
def learn_beginner_keep_costs_low(): return send_from_directory("static", "lesson-keep-costs-low.html")

@app.route("/learn/beginner/think-in-decades")
def learn_beginner_think_in_decades(): return send_from_directory("static", "lesson-think-in-decades.html")

@app.route("/learn/beginner/stocks")
def learn_beginner_stocks(): return send_from_directory("static", "lesson-stocks.html")

@app.route("/learn/beginner/etfs")
def learn_beginner_etfs(): return send_from_directory("static", "lesson-etfs.html")

@app.route("/learn/beginner/bonds")
def learn_beginner_bonds(): return send_from_directory("static", "lesson-bonds.html")

@app.route("/learn/beginner/cash")
def learn_beginner_cash(): return send_from_directory("static", "lesson-cash.html")

@app.route("/learn/beginner/alternatives")
def learn_beginner_alternatives(): return send_from_directory("static", "lesson-alternatives.html")

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

@app.route("/tools/calculator")
def tools_calculator(): return send_from_directory("static", "calculator.html")

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

@app.route("/social-post-studio")
def social_post_studio(): return send_from_directory("static", "social-post-studio.html")


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

    session.permanent = True
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

    stay_signed_in = user_data.get("preferences", {}).get("stay_signed_in", True)
    session.permanent = bool(stay_signed_in)
    login_user(User(username, user_data.get("tier", "basic")), remember=bool(stay_signed_in))
    return jsonify({
        "success": True,
        "username": username,
        "tier": user_data.get("tier", "basic"),
        "preferences": user_data.get("preferences", {}),
        "landing_page": user_data.get("profile", {}).get("landing_page", "/"),
    })


@app.route("/api/forgot-password", methods=["POST"])
def api_forgot_password():
    data = request.get_json() or {}
    identifier = data.get("identifier", "").strip().lower()
    generic = {"success": True, "message": "If an account matches that username or email, we've sent a reset link."}
    if not identifier:
        return jsonify(generic)

    users = _load_users()
    match_username = None
    for username, user_data in users.items():
        email = (user_data.get("profile", {}) or {}).get("email", "").strip().lower()
        if username.lower() == identifier or (email and email == identifier):
            match_username = username
            break

    if match_username:
        user_data = users[match_username]
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        profile = dict(user_data.get("profile", {}) or {})
        profile["reset_token_hash"] = token_hash
        profile["reset_token_expires"] = time.time() + 3600  # 1 hour
        user_data["profile"] = profile
        users[match_username] = user_data
        _save_users(users)

        reset_link = f"{request.host_url.rstrip('/')}/reset-password?u={match_username}&t={token}"
        to_addr = profile.get("email") or match_username
        _send_email(
            to_addr,
            "Reset your Growth Capital Academy password",
            f"Someone requested a password reset for the account \"{match_username}\".\n\n"
            f"Reset your password here (valid for 1 hour):\n{reset_link}\n\n"
            f"If you didn't request this, you can safely ignore this email.",
        )

    return jsonify(generic)


@app.route("/api/reset-password", methods=["POST"])
def api_reset_password():
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    token = data.get("token", "")
    new_password = data.get("new_password", "")

    if not username or not token or not new_password:
        return jsonify({"error": "Missing required fields"}), 400
    if len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400

    users = _load_users()
    user_data = users.get(username)
    profile = (user_data.get("profile", {}) or {}) if user_data else {}
    stored_hash = profile.get("reset_token_hash")
    expires = profile.get("reset_token_expires", 0)

    if not user_data or not stored_hash or time.time() > expires:
        return jsonify({"error": "This reset link is invalid or has expired. Please request a new one."}), 400

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    if not hmac.compare_digest(token_hash, stored_hash):
        return jsonify({"error": "This reset link is invalid or has expired. Please request a new one."}), 400

    user_data["password_hash"] = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
    profile.pop("reset_token_hash", None)
    profile.pop("reset_token_expires", None)
    user_data["profile"] = profile
    users[username] = user_data
    _save_users(users)

    return jsonify({"success": True})


@app.route("/reset-password")
def reset_password_page():
    return send_from_directory("static", "reset-password.html")


@app.route("/api/logout", methods=["POST"])
@login_required
def api_logout():
    logout_user()
    return jsonify({"success": True})


@app.route("/api/me", methods=["GET"])
def api_me():
    if not current_user.is_authenticated:
        return jsonify({"authenticated": False, "username": None, "tier": "basic", "alpha_role": None})
    return jsonify({
        "authenticated": True,
        "username": current_user.id,
        "tier": getattr(current_user, "tier", "basic"),
        "alpha_role": getattr(current_user, "alpha_role", None),
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


@app.route("/api/admin/users", methods=["GET"])
@login_required
def admin_list_users():
    if current_user.id != "admin":
        return jsonify({"error": "Admin only"}), 403
    users = _load_users()
    return jsonify({"users": [
        {"username": u, "alpha_role": data.get("alpha_role"), "tier": data.get("tier", "basic")}
        for u, data in sorted(users.items())
    ]})


@app.route("/api/admin/set-alpha-role", methods=["POST"])
@login_required
def admin_set_alpha_role():
    if current_user.id != "admin":
        return jsonify({"error": "Admin only"}), 403
    data = request.get_json() or {}
    username = data.get("username", "").strip()
    role = data.get("alpha_role")
    role = role.strip() if isinstance(role, str) else role
    if role not in ALPHA_ROLES and role not in (None, ""):
        return jsonify({"error": f"Invalid alpha_role. Valid options: {sorted(ALPHA_ROLES)} or null to unassign"}), 400
    users = _load_users()
    if username not in users:
        return jsonify({"error": "User not found"}), 404
    role = role or None
    if role:
        holder = next(
            (u for u, data in users.items() if u != username and data.get("alpha_role") == role),
            None,
        )
        if holder:
            return jsonify({"error": f'Role "{role}" is already assigned to "{holder}". Unassign it there first.'}), 409
    users[username]["alpha_role"] = role
    _save_users(users)
    return jsonify({"success": True, "username": username, "alpha_role": role})


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
    "/tools", "/tools/signals", "/backtester", "/tools/portfolio", "/tools/calculator",
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
        "preferences":    user_data.get("preferences", {}),
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
    users = _load_users()
    if current_user.id not in users:
        return jsonify({"error": "User not found"}), 404
    filename = secure_filename(f"{current_user.id}.{ext}")
    avatar_url = f"/api/profile/avatar/{current_user.id}"
    profile = users[current_user.id].get("profile", {})
    profile["profile_picture"] = avatar_url
    users[current_user.id]["profile"] = profile
    _save_users(users)
    # set_user_avatar() does its own load/save cycle in the local-JSON-fallback
    # path — must run after the profile_picture save above, not before, or its
    # internal _save_users() call would clobber this one's write and vice versa.
    set_user_avatar(current_user.id, filename, file.read())
    return jsonify({"success": True, "avatar_url": avatar_url})


@app.route("/api/profile/avatar/<username>", methods=["GET"])
def api_get_avatar(username):
    filename, file_bytes = get_user_avatar(username)
    if file_bytes is None:
        return jsonify({"error": "No avatar"}), 404
    import mimetypes
    mimetype = mimetypes.guess_type(filename or "")[0] or "image/jpeg"
    return Response(file_bytes, mimetype=mimetype, headers={"Cache-Control": "public, max-age=3600"})


# ── Alpha content API ─────────────────────────────────────────────────────────

def _alpha_can_touch(item) -> bool:
    return item is not None and item.get("author") == current_user.alpha_role


@app.route("/api/alpha/upload", methods=["POST"])
@login_required
@alpha_author_required
def api_alpha_upload():
    author = current_user.alpha_role
    kind = (request.form.get("kind") or "post").strip()
    if kind not in ALPHA_CONTENT_KINDS:
        return jsonify({"error": f"Invalid kind. Valid options: {sorted(ALPHA_CONTENT_KINDS)}"}), 400
    requested_topic = (request.form.get("topic") or "").strip() or None

    file_bytes = None
    source_filename = None
    structured_sections = None
    structured_meta = {}
    try:
        if "file" in request.files and request.files["file"].filename:
            f = request.files["file"]
            source_filename = secure_filename(f.filename)
            file_bytes = f.read()
            f.seek(0)
            raw_text = extract_text_from_upload(f)
            source_kind = "file"
            file_ext = source_filename.rsplit(".", 1)[-1].lower() if "." in source_filename else ""
            if file_ext == "docx" and kind == "post":
                f.seek(0)
                try:
                    result = extract_structured_docx(f)
                    if result is not None:
                        structured_sections, structured_meta = result
                except Exception:
                    structured_sections = None  # not a template doc, or unreadable structure — fall back below
        elif (request.form.get("link") or "").strip():
            raw_text = extract_text_from_url(request.form.get("link").strip())
            source_kind = "link"
        elif (request.form.get("paste") or "").strip():
            raw_text = request.form.get("paste").strip()[:MAX_UPLOAD_TEXT_CHARS]
            source_kind = "paste"
        else:
            return jsonify({"error": "Provide a file, a link, or pasted text"}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    author_topics = ALPHA_TOPICS.get(author, [])
    normalized = normalize_content(raw_text, author, author_topics)
    topic = requested_topic if requested_topic in author_topics else normalized["topic"]
    body = auto_section_tables(normalized["body"]) if kind == "post" else normalized["body"]
    # normalize_content's title/subtitle/snippet are a naive split of the
    # whole flattened document — a structured upload has much better
    # candidates: the first Normal section's own heading for the title, and
    # any explicit "[SUBTITLE]"/"[SNIPPET]" tagged block for those fields.
    if structured_sections and structured_sections[0].get("type") == "normal" and structured_sections[0].get("heading"):
        normalized["title"] = structured_sections[0]["heading"][:100]
    if structured_meta.get("subtitle"):
        normalized["subtitle"] = structured_meta["subtitle"][:140]
    if structured_meta.get("snippet"):
        normalized["snippet"] = structured_meta["snippet"][:280]

    fields = {
        "author": author, "kind": kind, "status": "draft", "topic": topic,
        "title": normalized["title"], "subtitle": normalized["subtitle"],
        "snippet": normalized["snippet"], "body": body,
        "stance": None, "url": None,
        "source_kind": source_kind, "source_filename": source_filename, "source_text": raw_text,
    }
    item = alpha_content_create(fields, file_bytes=file_bytes)

    if structured_sections:
        # Images inside a structured doc's [IMAGE] sections need the new
        # item's id to attach to, which only exists after the create above —
        # hence building this replacement body as a second step.
        def _upload_extracted_image(img_bytes, img_ext):
            attachment_id = alpha_attachment_create(item["id"], f"template-image.{img_ext}", img_bytes)
            return f"/api/alpha/content/{item['id']}/images/{attachment_id}"
        structured_body = _serialize_structured_sections(structured_sections, _upload_extracted_image)
        if structured_body.strip():
            item = alpha_content_update(item["id"], {"body": structured_body})

    return jsonify({"success": True, "item": item})


@app.route("/api/alpha/content", methods=["GET", "POST"])
@login_required
@alpha_author_required
def api_alpha_content():
    author = current_user.alpha_role
    if request.method == "GET":
        return jsonify({"items": alpha_content_list(author=author)})

    data = request.get_json() or {}
    kind = (data.get("kind") or "").strip()
    if kind not in ALPHA_CONTENT_KINDS:
        return jsonify({"error": f"Invalid kind. Valid options: {sorted(ALPHA_CONTENT_KINDS)}"}), 400
    if kind == "post":
        return jsonify({"error": "Posts are created via the upload endpoint, not this one"}), 400

    topic = (data.get("topic") or "").strip() or None
    if topic and topic not in ALPHA_TOPICS.get(author, []):
        return jsonify({"error": "Topic must be one of your nominated topics"}), 400

    title = (data.get("title") or "").strip()
    if not title:
        return jsonify({"error": "Title is required"}), 400

    fields = {
        "author": author, "kind": kind, "status": "draft", "topic": topic,
        "title": title,
        "snippet": (data.get("snippet") or "").strip() or None,
        "body": (data.get("body") or "").strip() or None,
        "stance": None, "url": None,
        "source_kind": "manual", "source_filename": None, "source_text": None,
    }
    if kind == "watchlist":
        stance = (data.get("stance") or "").strip().lower()
        if stance not in ALPHA_STANCES:
            return jsonify({"error": f"Stance must be one of {sorted(ALPHA_STANCES)}"}), 400
        fields["stance"] = stance
    if kind in ("video", "link"):
        url = (data.get("url") or "").strip()
        if not url:
            return jsonify({"error": f"A URL is required for a {kind}"}), 400
        fields["url"] = url

    item = alpha_content_create(fields)
    return jsonify({"success": True, "item": item})


@app.route("/api/alpha/content/<int:item_id>", methods=["PUT", "DELETE"])
@login_required
@alpha_author_required
def api_alpha_content_item(item_id):
    existing = alpha_content_get(item_id)
    if not _alpha_can_touch(existing):
        return jsonify({"error": "Not found"}), 404

    if request.method == "DELETE":
        alpha_content_delete(item_id)
        return jsonify({"success": True})

    data = request.get_json() or {}

    # Fields a staged edit can hold and fold back into the live item — shared by
    # the "save while published" path below, republish, and the unpublish fold.
    _stageable_fields = ("topic", "title", "subtitle", "snippet", "body", "url", "stance", "image_url", "image_filename")

    if data.get("republish"):
        # Push any pending staged edits live in one step, without a detour
        # through "draft" — an alternative to Unpublish-then-Publish when the
        # author just wants their saved edits to go live.
        if existing.get("status") != "published":
            return jsonify({"error": "Only a published item can be re-published"}), 400
        fold = {"staged_edits": None}
        for k, v in (existing.get("staged_edits") or {}).items():
            if k in _stageable_fields:
                fold[k] = v
        item = alpha_content_update(item_id, fold)
        return jsonify({"success": True, "item": item})

    updates = {}
    for field in ("topic", "title", "subtitle", "snippet", "body", "url"):
        if field in data:
            value = data[field]
            updates[field] = (str(value).strip() or None) if value is not None else None
    if data.get("clear_image"):
        # Remove the hero image entirely — both a pasted URL and any uploaded file.
        updates["image_url"] = None
        updates["image_file"] = None
        updates["image_filename"] = None
    elif "image_url" in data:
        image_url = (data["image_url"] or "").strip()
        updates["image_url"] = image_url or None
        if image_url:
            # Switching to URL mode clears any previously uploaded file.
            updates["image_file"] = None
            updates["image_filename"] = None
    if "stance" in data:
        stance = (data["stance"] or "").strip().lower()
        if stance and stance not in ALPHA_STANCES:
            return jsonify({"error": f"Stance must be one of {sorted(ALPHA_STANCES)}"}), 400
        updates["stance"] = stance or None
    if updates.get("topic") and updates["topic"] not in ALPHA_TOPICS.get(current_user.alpha_role, []):
        return jsonify({"error": "Topic must be one of your nominated topics"}), 400

    # ── Staged edits ────────────────────────────────────────────────────────
    # Editing a PUBLISHED item (a content change with no status change) saves to
    # a pending `staged_edits` copy and leaves the live page untouched. The edits
    # are folded into the item when it's next unpublished (see below), so the
    # path to make them live is: edit → Save (staged) → Unpublish → Publish.
    _content_edit_keys = ("topic", "title", "subtitle", "snippet", "body", "url", "stance", "image_url", "clear_image")
    if existing.get("status") == "published" and "status" not in data and any(k in data for k in _content_edit_keys):
        staged = dict(existing.get("staged_edits") or {})
        # image_filename is included so `clear_image` can stage removing an
        # uploaded hero image (setting it to None) — cheap, since it never holds
        # new binary data. A brand-new *upload* is blocked before it reaches here
        # (see /image endpoint below): only removal is staged, not replacement.
        for field in _stageable_fields:
            if field in updates:
                staged[field] = updates[field]
        item = alpha_content_update(item_id, {"staged_edits": staged})
        return jsonify({"success": True, "item": item})

    if "status" in data:
        status = data["status"]
        if status not in ("draft", "published"):
            return jsonify({"error": "Status must be 'draft' or 'published'"}), 400
        if status == "published":
            merged = {**existing, **updates}
            if merged.get("kind") == "post":
                missing = []
                if not (merged.get("title") or "").strip():
                    missing.append("title")
                if not (merged.get("subtitle") or "").strip():
                    missing.append("subtitle")
                if not ((merged.get("image_url") or "").strip() or merged.get("image_filename")):
                    missing.append("image")
                if missing:
                    return jsonify({
                        "error": "Missing before publishing: " + ", ".join(missing) + ".",
                        "missing_fields": missing,
                    }), 400
        updates["status"] = status
        updates["published_at"] = _dt.datetime.utcnow() if status == "published" else None
        # Unpublishing folds any staged edits into the (now draft) live fields so
        # they're preserved and ready to go live again on the next publish. A
        # field already present in `updates` (the studio sends the whole form,
        # not a diff) is the author's current on-screen text and wins over an
        # older staged copy of that same field.
        if status == "draft" and existing.get("staged_edits"):
            for k, v in existing["staged_edits"].items():
                if k in _stageable_fields and k not in updates:
                    updates[k] = v
            updates["staged_edits"] = None

    item = alpha_content_update(item_id, updates)
    return jsonify({"success": True, "item": item})


@app.route("/api/alpha/content/<int:item_id>/file", methods=["GET"])
@login_required
@alpha_author_required
def api_alpha_content_file(item_id):
    existing = alpha_content_get(item_id)
    if not _alpha_can_touch(existing):
        return jsonify({"error": "Not found"}), 404
    filename, file_bytes = alpha_content_get_file(item_id)
    if file_bytes is None:
        return jsonify({"error": "No file attached to this item"}), 404
    import mimetypes
    mimetype = mimetypes.guess_type(filename or "")[0] or "application/octet-stream"
    return Response(
        file_bytes, mimetype=mimetype,
        headers={"Content-Disposition": f"attachment; filename={secure_filename(filename or 'download')}"}
    )


@app.route("/api/alpha/content/<int:item_id>/image", methods=["GET"])
def api_alpha_content_image(item_id):
    item = alpha_content_get(item_id)
    if not item:
        return jsonify({"error": "Not found"}), 404
    is_owner = current_user.is_authenticated and getattr(current_user, "alpha_role", None) == item.get("author")
    if item.get("status") != "published" and not is_owner:
        return jsonify({"error": "Not found"}), 404
    filename, file_bytes = alpha_content_get_image(item_id)
    if file_bytes is None:
        return jsonify({"error": "No image attached"}), 404
    import mimetypes
    mimetype = mimetypes.guess_type(filename or "")[0] or "image/jpeg"
    cache = "public, max-age=3600" if item.get("status") == "published" else "private, no-store"
    return Response(file_bytes, mimetype=mimetype, headers={"Cache-Control": cache})


@app.route("/api/alpha/content/<int:item_id>/image", methods=["POST"])
@login_required
@alpha_author_required
def api_alpha_content_image_upload(item_id):
    existing = alpha_content_get(item_id)
    if not _alpha_can_touch(existing):
        return jsonify({"error": "Not found"}), 404
    if existing.get("kind") != "post":
        return jsonify({"error": "Images can only be attached to posts"}), 400
    if existing.get("status") == "published":
        # This is the single hero-image slot, served live at .../image — unlike
        # text/topic/URL edits it isn't staged, so replacing it here would go
        # straight to the website. Unpublish first, or use an Image URL, which
        # does stage.
        return jsonify({"error": "Unpublish this post first to upload a new hero image, or use an Image URL instead."}), 400
    if "image" not in request.files or not request.files["image"].filename:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["image"]
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "Allowed types: png, jpg, jpeg, gif, webp"}), 400
    item = alpha_content_set_image(item_id, secure_filename(file.filename), file.read())
    return jsonify({"success": True, "item": item})


@app.route("/api/alpha/content/<int:item_id>/images", methods=["POST"])
@login_required
@alpha_author_required
def api_alpha_content_attachment_upload(item_id):
    """Uploads an inline image to embed mid-post (distinct from the single main
    image slot on the row itself — a post can have any number of these)."""
    existing = alpha_content_get(item_id)
    if not _alpha_can_touch(existing):
        return jsonify({"error": "Not found"}), 404
    if existing.get("kind") != "post":
        return jsonify({"error": "Images can only be attached to posts"}), 400
    if "image" not in request.files or not request.files["image"].filename:
        return jsonify({"error": "No file provided"}), 400
    file = request.files["image"]
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        return jsonify({"error": "Allowed types: png, jpg, jpeg, gif, webp"}), 400
    attachment_id = alpha_attachment_create(item_id, secure_filename(file.filename), file.read())
    return jsonify({"success": True, "url": f"/api/alpha/content/{item_id}/images/{attachment_id}"})


@app.route("/api/alpha/content/<int:item_id>/images/<int:attachment_id>", methods=["GET"])
def api_alpha_content_attachment_get(item_id, attachment_id):
    content_id, filename, file_bytes = alpha_attachment_get(attachment_id)
    if content_id != item_id or file_bytes is None:
        return jsonify({"error": "Not found"}), 404
    item = alpha_content_get(item_id)
    is_owner = current_user.is_authenticated and getattr(current_user, "alpha_role", None) == (item or {}).get("author")
    if not item or (item.get("status") != "published" and not is_owner):
        return jsonify({"error": "Not found"}), 404
    import mimetypes
    mimetype = mimetypes.guess_type(filename or "")[0] or "image/jpeg"
    cache = "public, max-age=3600" if item.get("status") == "published" else "private, no-store"
    return Response(file_bytes, mimetype=mimetype, headers={"Cache-Control": cache})


def _alpha_public_image_url(item: dict) -> str | None:
    if item.get("image_filename"):
        return f"/api/alpha/content/{item['id']}/image"
    return item.get("image_url")


_ALPHA_PUBLIC_FIELDS = ["id", "kind", "topic", "title", "subtitle", "snippet", "body", "stance", "url", "published_at"]


@app.route("/api/alpha/<slug>/content", methods=["GET"])
def api_alpha_public_content(slug):
    if slug not in ALPHA_ROLES:
        return jsonify({"error": "Unknown author"}), 404
    topic = (request.args.get("topic") or "").strip() or None
    items = alpha_content_list(author=slug, status="published")
    if topic:
        items = [i for i in items if i.get("topic") == topic]
    grouped = {"watchlist": [], "video": [], "post": [], "link": []}
    for item in items:
        public_item = {k: item.get(k) for k in _ALPHA_PUBLIC_FIELDS}
        public_item["image_url"] = _alpha_public_image_url(item)
        grouped.setdefault(item["kind"], []).append(public_item)
    caps = {"watchlist": 3, "video": 4, "post": 4}
    for kind, cap in caps.items():
        grouped[kind] = grouped[kind][:cap]
    return jsonify(grouped)


@app.route("/api/alpha/<slug>/post/<int:post_id>", methods=["GET"])
def api_alpha_public_post(slug, post_id):
    if slug not in ALPHA_ROLES:
        return jsonify({"error": "Unknown author"}), 404
    item = alpha_content_get(post_id)
    if not item or item["author"] != slug or item["kind"] != "post" or item["status"] != "published":
        return jsonify({"error": "Post not found"}), 404
    public_item = {k: item.get(k) for k in _ALPHA_PUBLIC_FIELDS}
    public_item["image_url"] = _alpha_public_image_url(item)
    return jsonify(public_item)


@app.route("/alpha/<slug>/post/<int:post_id>")
def alpha_post_page(slug, post_id):
    return send_from_directory("static", "alpha-post.html")


@app.route("/alpha/studio")
def alpha_studio():
    # Client-side checks /api/me for alpha_role, same convention as /profile —
    # no server-side @login_required here since page routes in this app rely
    # on the JS auth check rather than a redirect-on-401 pattern.
    return send_from_directory("static", "alpha-studio.html")


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
        stop_loss_pct   = float(request.args.get("stop_loss",     100.0))
        take_profit_pct = float(request.args.get("take_profit",   200.0))
        min_confidence  = float(request.args.get("min_confidence", 60.0))
        trailing_stop      = request.args.get("trailing_stop", "0") in ("1", "true", "True")
        trail_distance_pct = float(request.args.get("trail_distance", 1.5))
        capital            = float(request.args.get("capital", 10000.0))
        trade_amount        = float(request.args.get("trade_amount", 100.0))
        trade_amount_mode   = request.args.get("trade_amount_mode", "percent").strip().lower()
        sl_tp_unit          = request.args.get("sl_tp_unit", "percent").strip().lower()
    except (ValueError, TypeError) as e:
        return jsonify({"error": f"Invalid parameter: {e}"}), 400

    if trade_amount_mode not in ("percent", "gbp"):
        return jsonify({"error": "trade_amount_mode must be 'percent' or 'gbp'"}), 400
    if sl_tp_unit not in ("percent", "pips"):
        return jsonify({"error": "sl_tp_unit must be 'percent' or 'pips'"}), 400

    # Forex pip size: 0.01 for JPY pairs (quoted to 2-3 decimal places),
    # 0.0001 for everything else (quoted to 4-5 decimal places).
    pip_size = 0.01 if "JPY" in symbol.upper() else 0.0001

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
        "inv_hs_on", "inv_hs_tolerance_pct",
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
        "bb_breakout_margin_pct", "bb_pct_below_high", "bb_pct_above_low",
        "donchian_retest_lookback", "donchian_retest_tolerance_pct",
    ]:
        val = request.args.get(key)
        if val is not None:
            try:
                thresholds[key] = float(val)
            except ValueError:
                return jsonify({"error": f"Invalid value for '{key}'"}), 400

    # Each indicator's trigger can now have several modes active at once — the
    # frontend sends one repeated query key per active mode (?rsi_trigger=a&rsi_trigger=b),
    # which Flask collects with getlist(). Falls back to DEFAULT_THRESHOLDS' single-mode
    # default (in score_signals) if the caller sends nothing for a given indicator.
    for trig_key, allowed in _TRIGGER_WHITELISTS.items():
        vals = request.args.getlist(trig_key)
        if vals:
            cleaned = []
            for v in vals:
                if v not in allowed:
                    return jsonify({"error": f"Invalid value for '{trig_key}'"}), 400
                if v not in cleaned:
                    cleaned.append(v)
            thresholds[trig_key] = cleaned

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
            capital=capital,
            trade_amount_mode=trade_amount_mode,
            trade_amount=trade_amount,
            sl_tp_unit=sl_tp_unit,
            pip_size=pip_size,
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


# ── Social Post Studio — generate platform-ready posts via Claude ────────────

_SOCIAL_PLATFORMS = {
    "x": {
        "label": "X",
        "guidance": (
            "X (Twitter) post. HARD LIMIT: body + cta combined must be under 270 "
            "characters. Punchy, one clear idea, strong hook. 1-2 hashtags max. "
            "No title needed (set title to empty string)."
        ),
    },
    "instagram": {
        "label": "Instagram",
        "guidance": (
            "Instagram caption. First line must be a scroll-stopping hook (it gets "
            "truncated). Short paragraphs with line breaks, tasteful emojis. 5-8 "
            "relevant hashtags. No title (empty string)."
        ),
    },
    "facebook": {
        "label": "Facebook",
        "guidance": (
            "Facebook post. Conversational, 2-3 short paragraphs, invites "
            "comments/shares. 0-3 hashtags. No title (empty string)."
        ),
    },
    "substack": {
        "label": "Substack",
        "guidance": (
            "Substack note/post. Include a compelling title. Body 150-300 words, "
            "written like a mini-essay with a personal, direct voice. Hashtags "
            "array should be empty."
        ),
    },
    "email": {
        "label": "Email newsletter",
        "guidance": (
            "Email newsletter section. 'title' = the subject line (under 60 chars, "
            "curiosity-driven). Body 100-200 words, scannable, warm. CTA should "
            "read like button text + one supporting line. Hashtags empty."
        ),
    },
}

_SOCIAL_POST_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "body": {"type": "string"},
        "cta": {"type": "string"},
        "hashtags": {"type": "array", "items": {"type": "string"}},
        "image_prompt": {"type": "string"},
    },
    "required": ["title", "body", "cta", "hashtags", "image_prompt"],
    "additionalProperties": False,
}


@app.route("/api/social-posts", methods=["POST"])
def social_posts():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return jsonify({"error": "No Anthropic API key is configured on the server "
                                 "(set the ANTHROPIC_API_KEY environment variable)."}), 503

    data = request.get_json(silent=True) or {}
    platform = _SOCIAL_PLATFORMS.get(data.get("platform"))
    if not platform:
        return jsonify({"error": "Unknown platform"}), 400
    ideas = (data.get("ideas") or "").strip()
    if not ideas:
        return jsonify({"error": "Add some ideas or bullet points first."}), 400

    prompt_parts = [
        "You are an expert social media copywriter.",
        "",
        f"Create a {platform['label']} post from the author's raw notes below.",
        "",
        "AUTHOR'S IDEAS / BULLET POINTS:",
        ideas[:8000],
    ]
    for field, heading in (("audience", "TARGET AUDIENCE"),
                           ("ctaGoal", "GOAL OF THE CALL TO ACTION"),
                           ("brandVoice", "BRAND VOICE NOTES")):
        value = (data.get(field) or "").strip()
        if value:
            prompt_parts.append(f"{heading}: {value[:500]}")
    prompt_parts += [
        f"TONE: {(data.get('tone') or 'Friendly')[:50]}",
        "",
        f"PLATFORM RULES: {platform['guidance']}",
        "",
        'Also write "image_prompt": a detailed prompt (40-70 words) the author can '
        "paste into an AI image generator (Midjourney, DALL-E, etc.) to create a "
        "matching visual. Describe subject, style, mood, colours, composition. "
        "No text in the image.",
    ]

    try:
        import anthropic
        client = anthropic.Anthropic()
        response = client.messages.create(
            model="claude-opus-4-8",
            max_tokens=2000,
            output_config={"format": {"type": "json_schema", "schema": _SOCIAL_POST_SCHEMA}},
            messages=[{"role": "user", "content": "\n".join(prompt_parts)}],
        )
        if response.stop_reason == "refusal":
            return jsonify({"error": "The model declined to write this post."}), 502
        text = next((b.text for b in response.content if b.type == "text"), "")
        return jsonify(json.loads(text))
    except Exception as e:
        return jsonify({"error": f"Generation failed: {e}"}), 502


# ── Startup ───────────────────────────────────────────────────────────────────

_ensure_table()
_ensure_default_user()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=not _is_production, port=port)
