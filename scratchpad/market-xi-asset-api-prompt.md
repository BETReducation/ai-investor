# For your dev: what this is

Growth Capital Academy auto-links assets that Alpha authors mention (e.g. "NVDA", "Cardano")
to Market XI. Right now we're guessing the asset list from our own data — we'd rather pull it
live from Market XI itself, so if an asset is added or removed there, our links update
automatically.

We looked at Market XI's app and found it already has one public API route
(`/api/gameweek-timeline`) but no equivalent for the asset/player list yet. Below is a
ready-to-paste prompt for whichever AI coding tool your dev uses (Claude Code, Cursor, etc.)
inside the Market XI codebase — it explains exactly what to build. He doesn't need to
understand the details, just paste it in and run it.

Once it's live, send us the endpoint URL and we'll wire it in — should be a small change on
our side.

---

## Prompt to paste

```
I need a new public API route in this Next.js app that exposes our asset/player catalogue
as JSON, so an external partner site can read our current asset list and keep their own
links in sync automatically (an asset added or removed here should be reflected there
without anyone manually updating anything).

Context: this app already has a public, unauthenticated JSON route at
GET /api/gameweek-timeline — I want the new route to follow the same pattern (same auth
posture: public, no login required, plain JSON response, similar to how that route is
implemented).

Please:

1. Find wherever our asset/player catalogue data currently lives (I believe it's used by
   something like `assetMarketAssets` / `assetMarketCatalogue` in the frontend — find the
   underlying Supabase table(s) or data source those pull from).

2. Add a new route, GET /api/asset-catalogue (app/api/asset-catalogue/route.ts if this is
   the App Router, or pages/api/asset-catalogue.ts if it's the Pages Router — check which
   this project uses), that:
   - Requires no authentication — publicly readable, same as /api/gameweek-timeline.
   - Returns every asset currently available/active in the game (exclude anything removed,
     delisted, or not yet live).
   - Responds with this exact JSON shape:

     {
       "assets": [
         {
           "slug": "nvda",
           "name": "NVIDIA",
           "ticker": "NVDA",
           "url": "/players/nvda"
         }
       ]
     }

     Field notes:
     - "slug": whatever unique identifier/slug we already use for the asset's own page.
     - "name": the asset's display/company name.
     - "ticker": its trading ticker/symbol, if we have one (null or omit if not applicable,
       e.g. for something without a ticker).
     - "url": the relative path to that asset's own profile page on this site (e.g.
       "/players/nvda") — if per-asset profile pages don't exist yet, just return the slug
       and name/ticker for now and set "url" to null; we'll ask again once those pages
       exist.

   - Set a short cache header (e.g. Cache-Control: public, max-age=300 — 5 minutes) since
     this will be polled periodically by an external server, not on every page load.

3. Don't add CORS headers unless they're already the norm for this app's API routes — the
   consumer calls this from their own backend server, not from a browser, so CORS isn't
   required.

4. After building it, tell me the exact deployed URL of the new route (e.g.
   https://market-xi-live.vercel.app/api/asset-catalogue) so I can pass it along.

Please ask me if anything about our current data model is ambiguous rather than guessing —
I can go look things up if needed.
```
