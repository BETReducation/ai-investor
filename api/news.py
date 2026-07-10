from __future__ import annotations
import json
import os
import time
import urllib.request
import xml.etree.ElementTree as ET

# Cached alongside users.json at the project root — same "small local JSON state"
# pattern already used there, not a database table.
NEWS_CACHE_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), "news_cache.json")
REFRESH_INTERVAL_SECONDS = 7 * 24 * 60 * 60  # 1 week

# Free, no-API-key finance/banking/economy RSS feeds. Each is checked independently —
# one going down or dropping images doesn't take out the others. (investing.com was
# tried and dropped: its image CDN sends Cross-Origin-Resource-Policy: same-origin,
# which silently blocks the images from ever rendering as a background-image on our
# origin in Chromium-based browsers.)
FEEDS = [
    "https://feeds.bbci.co.uk/news/business/rss.xml",
    "https://feeds.content.dowjones.io/public/rss/mw_topstories",
    "https://www.theguardian.com/uk/business/rss",
]

_MEDIA_NS = "{http://search.yahoo.com/mrss/}"
_HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; GrowthCapitalAcademyBot/1.0)"}
_REQUEST_TIMEOUT = 10


def _extract_image(item: ET.Element) -> str | None:
    thumb = item.find(f"{_MEDIA_NS}thumbnail")
    if thumb is not None and thumb.get("url"):
        return thumb.get("url")
    content = item.find(f"{_MEDIA_NS}content")
    if content is not None and content.get("url") and content.get("medium") in (None, "image"):
        return content.get("url")
    enclosure = item.find("enclosure")
    if enclosure is not None and enclosure.get("url") and "image" in (enclosure.get("type") or ""):
        return enclosure.get("url")
    return None


def _parse_feed(url: str, limit: int = 8) -> list[dict]:
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=_REQUEST_TIMEOUT) as resp:
        data = resp.read()
    root = ET.fromstring(data)
    items = []
    for item in root.iter("item"):
        title_el = item.find("title")
        link_el = item.find("link")
        if title_el is None or link_el is None or not title_el.text or not (link_el.text or "").strip():
            continue
        image = _extract_image(item)
        if not image:
            continue  # the gallery needs a picture — skip text-only items
        items.append({
            "kind": "photo",
            "title": title_el.text.strip(),
            "link": link_el.text.strip(),
            "image": image,
        })
        if len(items) >= limit:
            break
    return items


def _fetch_all_news(limit_per_feed: int = 6) -> list[dict]:
    items: list[dict] = []
    for url in FEEDS:
        try:
            items.extend(_parse_feed(url, limit=limit_per_feed))
        except Exception:
            continue  # one broken/unreachable/rate-limited feed shouldn't blank the gallery
    return items


def get_cached_news() -> dict:
    """Return {"fetched_at": unix_ts, "items": [...]}. Refetches all feeds if the
    cache is missing, empty, or older than REFRESH_INTERVAL_SECONDS (~1 week) — so
    under normal traffic this refreshes itself on the first homepage visit after a
    week has passed, with no background scheduler needed. If a refetch is attempted
    but every feed fails, the previous (stale) cache is kept rather than wiped."""
    cache = None
    if os.path.exists(NEWS_CACHE_FILE):
        try:
            with open(NEWS_CACHE_FILE, "r", encoding="utf-8") as f:
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
        fresh_items = _fetch_all_news()
        if fresh_items:
            cache = {"fetched_at": time.time(), "items": fresh_items}
            try:
                with open(NEWS_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(cache, f)
            except OSError:
                pass
        elif cache is None:
            cache = {"fetched_at": time.time(), "items": []}
    return cache
