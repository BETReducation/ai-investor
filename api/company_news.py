from __future__ import annotations
import json
import os
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# Same weekly-cache-on-first-visit pattern as api.news — see get_cached_news().
COMPANY_NEWS_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "company_news_cache.json")
REFRESH_INTERVAL_SECONDS = 7 * 24 * 60 * 60  # 1 week

# Curated watchlist spanning banking, energy, defense, tech and autos — not an
# exhaustive index, just enough variety for the homepage gallery. Easy to extend.
COMPANIES = [
    "JPMorgan", "British Gas", "Rheinmetall", "Nvidia",
    "Apple", "Amazon", "Shell", "HSBC", "Tesla",
    "Microsoft", "Alphabet", "ExxonMobil", "Toyota", "Samsung",
]

# One query per company via Google News' free RSS search (no API key). Biased
# toward the kind of news the user actually asked for (mergers, product
# releases) and restricted to the last 2 weeks so the gallery stays current.
_QUERY_TEMPLATE = '"{company}" (merger OR acquisition OR "product launch" OR earnings OR partnership) when:14d'
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GrowthCapitalAcademyBot/1.0)"}
_REQUEST_TIMEOUT = 10


def _fetch_company(company: str, limit: int = 1) -> list[dict]:
    query = _QUERY_TEMPLATE.format(company=company)
    url = "https://news.google.com/rss/search?" + urllib.parse.urlencode({
        "q": query, "hl": "en-US", "gl": "US", "ceid": "US:en",
    })
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    items = []
    for item in root.iter("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        source_el = item.find("source")
        if title_el is None or link_el is None or not title_el.text or not (link_el.text or "").strip():
            continue
        title = title_el.text.strip()
        source_name = source_el.text.strip() if source_el is not None and source_el.text else None
        # Google News suffixes titles with " - <Source>" — strip it since the
        # source is already carried separately.
        if source_name and title.endswith(f" - {source_name}"):
            title = title[: -(len(source_name) + 3)].strip()
        items.append({
            "kind": "company",
            "company": company,
            "title": title,
            "link": link_el.text.strip(),
            "source": source_name,
        })
        if len(items) >= limit:
            break
    return items


def _fetch_all_company_news() -> list[dict]:
    items: list[dict] = []
    for company in COMPANIES:
        try:
            items.extend(_fetch_company(company))
        except Exception:
            continue  # one company query failing shouldn't blank the gallery
    return items


def get_cached_company_news() -> dict:
    """Refetches if the cache is missing, empty, or a week or older — refreshes
    itself on the first homepage visit after a week has passed, no scheduler
    needed. Keeps the previous (stale) cache if a refetch attempt fails."""
    cache = None
    if os.path.exists(COMPANY_NEWS_CACHE_FILE):
        try:
            with open(COMPANY_NEWS_CACHE_FILE, "r", encoding="utf-8") as f:
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
        fresh_items = _fetch_all_company_news()
        if fresh_items:
            cache = {"fetched_at": time.time(), "items": fresh_items}
            try:
                with open(COMPANY_NEWS_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
            except OSError:
                pass
        elif cache is None:
            cache = {"fetched_at": time.time(), "items": []}
    return cache
