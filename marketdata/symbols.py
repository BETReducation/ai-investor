"""Symbol classification and provider-specific instrument-name mapping.

Deliberately independent of app.py (no imports from it) to avoid a circular import —
app.py imports from marketdata, not the other way around. The classification rules
here mirror static/signal_config.html's categoryFromQuoteType() fallback heuristic,
since /api/prices gets a bare symbol with no category param.
"""

_METALS = {"XAU", "XAG"}


def _strip_x_suffix(symbol: str) -> str:
    s = symbol.upper()
    return s[:-2] if s.endswith("=X") else s


def parse_forex_pair(symbol: str) -> tuple[str, str] | None:
    """Returns (base, quote) for any 6-letter '=X'-style pair — plain FX or
    metal-in-currency alike (e.g. 'EURUSD=X' -> ('EUR','USD'), 'XAUGBP=X' ->
    ('XAU','GBP')) — or None if the symbol isn't shaped like one."""
    core = _strip_x_suffix(symbol)
    if len(core) == 6 and core.isalpha():
        return core[:3], core[3:]
    return None


def classify_symbol(symbol: str) -> str:
    """Best-effort category purely from the symbol string: 'metal-fx', 'forex',
    'crypto', 'futures', 'index', or 'stock' (the fallback)."""
    s = symbol.upper()
    if s.endswith("-USD"):
        return "crypto"
    if s.startswith("^"):
        return "index"
    if s.endswith("=X"):
        pair = parse_forex_pair(s)
        if pair and pair[0] in _METALS:
            return "metal-fx"
        return "forex"
    if s.endswith("=F"):
        return "futures"
    return "stock"


def yfinance_to_oanda_instrument(symbol: str, known_instruments: set[str] | None = None) -> str | None:
    """Maps a yfinance-style forex/metal symbol to OANDA's '<BASE>_<QUOTE>' instrument
    naming. If `known_instruments` (OANDA's own real, fetched instrument list) is
    given, returns None for anything OANDA doesn't actually list — this is what lets
    OANDA's real coverage be the source of truth rather than app.py's
    _METAL_FX_CURRENCIES set, which was derived from Yahoo's (different) coverage."""
    pair = parse_forex_pair(symbol)
    if not pair:
        return None
    instrument = f"{pair[0]}_{pair[1]}"
    if known_instruments is not None and instrument not in known_instruments:
        return None
    return instrument


# Yahoo uses '-' for share classes (e.g. 'BRK-B'), Alpaca/most US brokers use '.'
# ('BRK.B'). Extend this table as specific mismatches turn up; default is passthrough.
_ALPACA_SYMBOL_OVERRIDES: dict[str, str] = {}


def yfinance_to_alpaca_symbol(symbol: str) -> str:
    s = symbol.upper()
    if s in _ALPACA_SYMBOL_OVERRIDES:
        return _ALPACA_SYMBOL_OVERRIDES[s]
    return s.replace("-", ".")
