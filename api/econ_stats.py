from __future__ import annotations
import json
import os
import time
import urllib.request

# Same weekly-cache-on-first-visit pattern as api.news — see get_cached_news().
STATS_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "econ_stats_cache.json")
REFRESH_INTERVAL_SECONDS = 7 * 24 * 60 * 60  # 1 week

# Curated set of major economies (not every country the World Bank tracks) so the
# gallery stays focused rather than cycling through 200 countries.
COUNTRIES = [
    ("USA", "United States", "\U0001F1FA\U0001F1F8"),
    ("GBR", "United Kingdom", "\U0001F1EC\U0001F1E7"),
    ("EMU", "Euro Area", "\U0001F1EA\U0001F1FA"),
    ("JPN", "Japan", "\U0001F1EF\U0001F1F5"),
    ("CHN", "China", "\U0001F1E8\U0001F1F3"),
]

# World Bank indicator codes. Central bank policy interest rates are deliberately
# excluded — there's no single free, no-API-key source for them across countries
# (unlike these three, which the World Bank publishes cleanly for everyone).
INDICATORS = {
    "gdp_growth": "NY.GDP.MKTP.KD.ZG",     # GDP growth (annual %)
    "inflation": "FP.CPI.TOTL.ZG",         # Inflation, consumer prices (annual %)
    "unemployment": "SL.UEM.TOTL.ZS",      # Unemployment (% of total labor force)
}

_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GrowthCapitalAcademyBot/1.0)"}
_REQUEST_TIMEOUT = 10


def _fetch_indicator(codes: str, indicator: str) -> dict:
    """Returns {country_iso3: (value, year)}. mrv=3 asks the World Bank for each
    country's 3 most recent years (the latest is often still null — data lags
    real time), grouped by country and sorted most-recent-year-first, so keeping
    only the first non-null value seen per country gives the latest observation
    actually available."""
    url = (
        f"https://api.worldbank.org/v2/country/{codes}/indicator/{indicator}"
        "?format=json&mrv=3"
    )
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
        data = json.loads(resp.read())
    result = {}
    if not isinstance(data, list) or len(data) < 2 or not data[1]:
        return result
    for row in data[1]:
        iso3 = row.get("countryiso3code")
        value = row.get("value")
        year = row.get("date")
        if not iso3 or value is None:
            continue
        if iso3 not in result:
            result[iso3] = (value, year)
    return result


def _fetch_all_stats() -> list[dict]:
    codes = "%3B".join(code for code, _, _ in COUNTRIES)
    per_indicator = {}
    for key, indicator in INDICATORS.items():
        try:
            per_indicator[key] = _fetch_indicator(codes, indicator)
        except Exception:
            per_indicator[key] = {}

    stats = []
    for code, name, flag in COUNTRIES:
        gdp = per_indicator.get("gdp_growth", {}).get(code)
        infl = per_indicator.get("inflation", {}).get(code)
        unemp = per_indicator.get("unemployment", {}).get(code)
        if not (gdp or infl or unemp):
            continue  # World Bank had nothing usable for this country this run
        stats.append({
            "kind": "stat",
            "country": name,
            "flag": flag,
            "gdp_growth": round(gdp[0], 1) if gdp else None,
            "gdp_year": gdp[1] if gdp else None,
            "inflation": round(infl[0], 1) if infl else None,
            "inflation_year": infl[1] if infl else None,
            "unemployment": round(unemp[0], 1) if unemp else None,
            "unemployment_year": unemp[1] if unemp else None,
        })
    return stats


def get_cached_stats() -> dict:
    """Refetches if the cache is missing, empty, or a week or older — refreshes
    itself on the first homepage visit after a week has passed, no scheduler
    needed. Keeps the previous (stale) cache if a refetch attempt fails."""
    cache = None
    if os.path.exists(STATS_CACHE_FILE):
        try:
            with open(STATS_CACHE_FILE, "r", encoding="utf-8") as f:
                cache = json.load(f)
        except (json.JSONDecodeError, OSError):
            cache = None

    is_stale = (
        cache is None
        or "fetched_at" not in cache
        or not cache.get("items")
        or (time.time() - cache["fetched_at"]) > REFRESH_INTERVAL_SECONDS
    )
    if is_stale:
        fresh_items = _fetch_all_stats()
        if fresh_items:
            cache = {"fetched_at": time.time(), "items": fresh_items}
            try:
                with open(STATS_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
            except OSError:
                pass
        elif cache is None:
            cache = {"fetched_at": time.time(), "items": []}
    return cache
