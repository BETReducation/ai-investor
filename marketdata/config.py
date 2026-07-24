import os

# Same pattern as app.py's SMTP_* config: plain os.environ.get(), no framework, and
# presence of credentials is itself the on/off flag — no separate feature flag to
# forget to flip. Absent either provider's credentials, that provider's streamer is
# never started and every symbol falls straight back to the existing yfinance path.

OANDA_API_TOKEN = os.environ.get("OANDA_API_TOKEN", "")
OANDA_ACCOUNT_ID = os.environ.get("OANDA_ACCOUNT_ID", "")
OANDA_ENVIRONMENT = os.environ.get("OANDA_ENVIRONMENT", "practice")  # "practice" | "live"
OANDA_ENABLED = bool(OANDA_API_TOKEN and OANDA_ACCOUNT_ID)

OANDA_STREAM_HOSTS = {
    "practice": "stream-fxpractice.oanda.com",
    "live": "stream-fxtrade.oanda.com",
}
OANDA_REST_HOSTS = {
    "practice": "api-fxpractice.oanda.com",
    "live": "api-fxtrade.oanda.com",
}

ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY", "")
ALPACA_API_SECRET = os.environ.get("ALPACA_API_SECRET", "")
ALPACA_FEED = os.environ.get("ALPACA_FEED", "iex")  # free/paper tier; "sip" needs a paid plan
ALPACA_ENABLED = bool(ALPACA_API_KEY and ALPACA_API_SECRET)
