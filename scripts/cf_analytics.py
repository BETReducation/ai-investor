"""Print Cloudflare zone traffic for the last N days (default 30).

Needs CF_API_TOKEN (Zone > Analytics > Read) and CF_ZONE_ID in .env.
Usage: python scripts/cf_analytics.py [days]
"""
import os
import sys
from collections import Counter
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.environ.get("CF_API_TOKEN", "")
ZONE = os.environ.get("CF_ZONE_ID", "")
if not (TOKEN and ZONE):
    sys.exit("Set CF_API_TOKEN and CF_ZONE_ID in .env")

days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
since = (date.today() - timedelta(days=days)).isoformat()

query = """
query($zone: String!, $since: Date!) {
  viewer { zones(filter: {zoneTag: $zone}) {
    httpRequests1dGroups(limit: 400, orderBy: [date_ASC], filter: {date_geq: $since}) {
      dimensions { date }
      uniq { uniques }
      sum { requests cachedRequests bytes
            countryMap { clientCountryName requests }
            responseStatusMap { edgeResponseStatus requests } }
    }
  } }
}"""

r = requests.post(
    "https://api.cloudflare.com/client/v4/graphql",
    headers={"Authorization": f"Bearer {TOKEN}"},
    json={"query": query, "variables": {"zone": ZONE, "since": since}},
    timeout=30,
)
r.raise_for_status()
body = r.json()
if body.get("errors"):
    sys.exit(f"API error: {body['errors']}")

rows = body["data"]["viewer"]["zones"][0]["httpRequests1dGroups"]
countries, statuses = Counter(), Counter()
print(f"{'date':<11}{'visitors':>9}{'requests':>10}{'cached%':>9}{'req/visitor':>13}")
for g in rows:
    s, u = g["sum"], g["uniq"]["uniques"]
    for c in s["countryMap"]:
        countries[c["clientCountryName"]] += c["requests"]
    for c in s["responseStatusMap"]:
        statuses[c["edgeResponseStatus"]] += c["requests"]
    cached = 100 * s["cachedRequests"] / s["requests"] if s["requests"] else 0
    per = s["requests"] / u if u else 0
    print(f"{g['dimensions']['date']:<11}{u:>9}{s['requests']:>10}{cached:>8.0f}%{per:>13.1f}")

total = sum(countries.values()) or 1
print("\nTop countries by requests")
for name, n in countries.most_common(10):
    print(f"  {name:<6}{n:>8}  {100 * n / total:.0f}%")
print("\nResponse codes")
for code, n in statuses.most_common(8):
    print(f"  {code}  {n:>8}  {100 * n / total:.0f}%")
