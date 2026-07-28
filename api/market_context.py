from __future__ import annotations
import datetime as _dt
import threading
import yfinance as yf

# ── Sector classification ────────────────────────────────────────────────
# Maps yfinance's GICS-ish 'sector' string to a user-facing label, a
# representative sector ETF (the day's sector-performance benchmark), and a
# curated peer basket of well-known large caps in that sector — used to
# surface "notable movers" alongside each Backtester trade. Industry-level
# overrides (checked first) let a distinct group like "Defence" — which
# yfinance files under the broader "Industrials" sector — get its own label
# instead of being buried there.

SECTOR_MAP: dict[str, tuple[str, str, list[str]]] = {
    "Technology": ("Technology", "XLK",
        ["AAPL", "MSFT", "NVDA", "GOOGL", "META", "AVGO", "AMD", "INTC"]),
    "Communication Services": ("Communication Services", "XLC",
        ["GOOGL", "META", "NFLX", "DIS", "CMCSA", "T", "VZ", "TMUS"]),
    "Financial Services": ("Financials", "XLF",
        ["JPM", "BAC", "WFC", "GS", "MS", "C", "BLK", "SCHW"]),
    "Energy": ("Commodities — Energy", "XLE",
        ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "OXY"]),
    "Basic Materials": ("Commodities — Materials", "XLB",
        ["LIN", "SHW", "FCX", "NEM", "APD", "ECL", "NUE", "DOW"]),
    "Industrials": ("Industrials", "XLI",
        ["HON", "UPS", "CAT", "DE", "GE", "MMM", "UNP", "EMR"]),
    "Healthcare": ("Healthcare", "XLV",
        ["UNH", "JNJ", "LLY", "PFE", "ABBV", "MRK", "TMO", "ABT"]),
    "Consumer Cyclical": ("Consumer Discretionary", "XLY",
        ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "LOW", "BKNG"]),
    "Consumer Defensive": ("Consumer Staples", "XLP",
        ["PG", "KO", "PEP", "WMT", "COST", "PM", "MO", "CL"]),
    "Real Estate": ("Real Estate", "XLRE",
        ["PLD", "AMT", "EQIX", "PSA", "SPG", "O", "WELL", "DLR"]),
    "Utilities": ("Utilities", "XLU",
        ["NEE", "DUK", "SO", "D", "AEP", "EXC", "SRE", "XEL"]),
}

# Checked against yfinance's 'industry' field before falling back to the
# sector-level map above — first keyword match wins.
INDUSTRY_OVERRIDES: list[tuple[str, tuple[str, str, list[str]]]] = [
    ("aerospace", ("Defence", "ITA", ["LMT", "RTX", "NOC", "GD", "BA", "LHX", "TXT", "HII"])),
    ("defense",   ("Defence", "ITA", ["LMT", "RTX", "NOC", "GD", "BA", "LHX", "TXT", "HII"])),
    ("gold",      ("Commodities — Metals", "GDX", ["NEM", "GOLD", "AEM", "FNV", "WPM", "KGC"])),
    ("copper",    ("Commodities — Metals", "COPX", ["FCX", "SCCO", "TECK"])),
    ("oil & gas", ("Commodities — Energy", "XLE", ["XOM", "CVX", "COP", "SLB", "EOG", "MPC", "PSX", "OXY"])),
]

PEER_NAMES: dict[str, str] = {
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "Nvidia", "GOOGL": "Alphabet",
    "META": "Meta", "AVGO": "Broadcom", "AMD": "AMD", "INTC": "Intel",
    "NFLX": "Netflix", "DIS": "Disney", "CMCSA": "Comcast", "T": "AT&T",
    "VZ": "Verizon", "TMUS": "T-Mobile",
    "JPM": "JPMorgan", "BAC": "Bank of America", "WFC": "Wells Fargo", "GS": "Goldman Sachs",
    "MS": "Morgan Stanley", "C": "Citigroup", "BLK": "BlackRock", "SCHW": "Charles Schwab",
    "XOM": "ExxonMobil", "CVX": "Chevron", "COP": "ConocoPhillips", "SLB": "SLB",
    "EOG": "EOG Resources", "MPC": "Marathon Petroleum", "PSX": "Phillips 66", "OXY": "Occidental",
    "LIN": "Linde", "SHW": "Sherwin-Williams", "FCX": "Freeport-McMoRan", "NEM": "Newmont",
    "APD": "Air Products", "ECL": "Ecolab", "NUE": "Nucor", "DOW": "Dow Inc.",
    "HON": "Honeywell", "UPS": "UPS", "CAT": "Caterpillar", "DE": "Deere & Co.",
    "GE": "GE Aerospace", "MMM": "3M", "UNP": "Union Pacific", "EMR": "Emerson",
    "UNH": "UnitedHealth", "JNJ": "Johnson & Johnson", "LLY": "Eli Lilly", "PFE": "Pfizer",
    "ABBV": "AbbVie", "MRK": "Merck", "TMO": "Thermo Fisher", "ABT": "Abbott",
    "AMZN": "Amazon", "TSLA": "Tesla", "HD": "Home Depot", "MCD": "McDonald's",
    "NKE": "Nike", "SBUX": "Starbucks", "LOW": "Lowe's", "BKNG": "Booking Holdings",
    "PG": "Procter & Gamble", "KO": "Coca-Cola", "PEP": "PepsiCo", "WMT": "Walmart",
    "COST": "Costco", "PM": "Philip Morris", "MO": "Altria", "CL": "Colgate-Palmolive",
    "PLD": "Prologis", "AMT": "American Tower", "EQIX": "Equinix", "PSA": "Public Storage",
    "SPG": "Simon Property", "O": "Realty Income", "WELL": "Welltower", "DLR": "Digital Realty",
    "NEE": "NextEra Energy", "DUK": "Duke Energy", "SO": "Southern Co.", "D": "Dominion Energy",
    "AEP": "American Electric Power", "EXC": "Exelon", "SRE": "Sempra", "XEL": "Xcel Energy",
    "LMT": "Lockheed Martin", "RTX": "RTX Corp.", "NOC": "Northrop Grumman", "GD": "General Dynamics",
    "BA": "Boeing", "LHX": "L3Harris", "TXT": "Textron", "HII": "Huntington Ingalls",
    "GOLD": "Barrick Gold", "AEM": "Agnico Eagle", "FNV": "Franco-Nevada",
    "WPM": "Wheaton Precious Metals", "KGC": "Kinross Gold",
    "SCCO": "Southern Copper", "TECK": "Teck Resources",
}

_NON_EQUITY_SUFFIXES = ("=X", "=F", "-USD")

# Sector/industry classification barely ever changes — cache for the process
# lifetime rather than re-hitting yfinance's slower `.info` endpoint on every
# backtest run for the same symbol.
_sector_cache: dict[str, dict | None] = {}
_sector_cache_lock = threading.Lock()


def _classify(sector: str | None, industry: str | None) -> tuple[str, str, list[str]] | None:
    industry_l = (industry or "").lower()
    for keyword, mapping in INDUSTRY_OVERRIDES:
        if keyword in industry_l:
            return mapping
    if sector and sector in SECTOR_MAP:
        return SECTOR_MAP[sector]
    return None


def get_symbol_sector(symbol: str) -> dict | None:
    """Best-effort sector classification for `symbol`. Returns None for
    non-equity instruments (forex, futures, crypto, indices) or when
    yfinance has no usable sector/industry data for it (most ETFs, some
    smaller listings) — callers treat that as "skip enrichment", not an
    error, since this is supplementary color, not core backtest output."""
    s = symbol.upper()
    if s.startswith("^") or any(s.endswith(suf) for suf in _NON_EQUITY_SUFFIXES):
        return None

    with _sector_cache_lock:
        if s in _sector_cache:
            return _sector_cache[s]

    result = None
    try:
        info = yf.Ticker(s).get_info()
        mapping = _classify(info.get("sector"), info.get("industry"))
        if mapping:
            label, benchmark, peers = mapping
            result = {
                "label": label,
                "benchmark": benchmark,
                "peers": [p for p in peers if p != s],
            }
    except Exception:
        result = None

    with _sector_cache_lock:
        _sector_cache[s] = result
    return result


def fetch_daily_pct_changes(tickers: list[str], start: str, end: str) -> dict[str, dict[str, float]]:
    """Daily % change for each ticker, keyed by 'YYYY-MM-DD'. Best-effort —
    returns {} on any fetch failure so callers can degrade gracefully rather
    than fail the whole backtest over an enrichment nice-to-have."""
    if not tickers:
        return {}
    try:
        end_buffered = (_dt.date.fromisoformat(end) + _dt.timedelta(days=2)).isoformat()
        data = yf.download(
            tickers=tickers, start=start, end=end_buffered, interval="1d",
            group_by="ticker", auto_adjust=True, progress=False, threads=True,
        )
    except Exception:
        return {}

    out: dict[str, dict[str, float]] = {}
    for ticker in tickers:
        try:
            closes = data[ticker]["Close"] if len(tickers) > 1 else data["Close"]
        except Exception:
            continue
        pct = closes.pct_change() * 100
        out[ticker] = {
            str(idx.date()): round(float(v), 2)
            for idx, v in pct.items() if v == v  # drop NaN
        }
    return out


def _fmt_pct(v: float) -> str:
    return f"{v:+.2f}%"


def _day_note(label: str, benchmark: str, peers: list[str], pct_by_ticker: dict, date_key: str) -> str | None:
    """A plain-English readout of how the sector and its peers moved on one
    calendar day — the sector benchmark's return plus the peer basket's best
    and worst performer that day, wherever data is actually available."""
    bench_pct = pct_by_ticker.get(benchmark, {}).get(date_key)
    movers = [(p, v) for p in peers if (v := pct_by_ticker.get(p, {}).get(date_key)) is not None]
    if bench_pct is None and not movers:
        return None

    parts = []
    if bench_pct is not None:
        parts.append(f"the {label} sector ({benchmark}) moved {_fmt_pct(bench_pct)}")
    if movers:
        best  = max(movers, key=lambda m: m[1])
        worst = min(movers, key=lambda m: m[1])
        name = lambda t: PEER_NAMES.get(t, t)
        if best[0] != worst[0]:
            parts.append(
                f"among peers, {name(best[0])} ({best[0]}) led at {_fmt_pct(best[1])} "
                f"while {name(worst[0])} ({worst[0]}) lagged at {_fmt_pct(worst[1])}"
            )
        else:
            parts.append(f"among peers, {name(best[0])} ({best[0]}) moved {_fmt_pct(best[1])}")
    return "; ".join(parts)


def enrich_trades_with_sector_context(trades: list[dict], symbol: str, data_start: str, data_end: str) -> None:
    """Mutates `trades` in place: attaches sector/peer market context for each
    trade's entry and exit day, and appends it to the trade's existing
    description strings. Silently no-ops for non-equity symbols or if the
    enrichment data can't be fetched — this is supplementary color, never
    load-bearing for the backtest result itself."""
    if not trades:
        return
    sector = get_symbol_sector(symbol)
    if not sector:
        return

    tickers = [sector["benchmark"]] + sector["peers"]
    pct_by_ticker = fetch_daily_pct_changes(tickers, data_start, data_end)
    if not pct_by_ticker:
        return

    for t in trades:
        entry_key = str(t["entry_date"])[:10]
        exit_key  = str(t["exit_date"])[:10]

        entry_note = _day_note(sector["label"], sector["benchmark"], sector["peers"], pct_by_ticker, entry_key)
        exit_note  = _day_note(sector["label"], sector["benchmark"], sector["peers"], pct_by_ticker, exit_key)

        t["sector"] = sector["label"]
        t["sector_benchmark"] = sector["benchmark"]
        t["entry_market_note"] = entry_note
        t["exit_market_note"] = exit_note

        if entry_note:
            t["description_detailed"] = t.get("description_detailed", "") + (
                f"\n\nMARKET — Entry day ({entry_key}): {entry_note}."
            )
            t["description_simple"] = t.get("description_simple", "") + (
                f" On the entry day, {entry_note}."
            )
        if exit_note:
            t["description_detailed"] = t.get("description_detailed", "") + (
                f"\nExit day ({exit_key}): {exit_note}."
            )
            t["description_simple"] = t.get("description_simple", "") + (
                f" On the exit day, {exit_note}."
            )
