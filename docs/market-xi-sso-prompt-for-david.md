# Market XI single sign-on: what David needs to build

Growth Capital Group (GCG) is the identity provider. Members click "Play Market XI" on GCG and arrive on
playmarketxi.com already signed in. A shared secret (`MARKET_XI_SHARED_SECRET`, we'll send it privately) is set
in both Vercel and Railway.

## Prompt to paste into your AI coding tool (Next.js + Supabase)

```
Add GCG single sign-on to this Next.js + Supabase app.

First check whether the project uses the App Router (app/) or Pages Router (pages/) and write the routes to match.
Use the existing server-side Supabase service-role client and env var (SUPABASE_SERVICE_ROLE_KEY or whatever this
project already calls it); never expose it to the browser. Add MARKET_XI_SHARED_SECRET to the env as well.

1. Route GET /auth/gcg?token=<jwt>. The token is HS256, signed with env MARKET_XI_SHARED_SECRET.
   Verify: signature, exp not passed, iss == "growthcapitalgroup.co", aud == "playmarketxi.com".
   Reject a reused jti (store seen jti values for ~2 minutes, e.g. a small Supabase table or KV).
   Claims: sub (GCG username), email, email_verified (bool), tier (free|beginner|intermediate|pro|founder).

2. Using the Supabase service-role client (server-side only), find the auth user by email. If none, create
   one with email_confirm: true and no password. Then upsert a profile row with gcg_username = sub and
   gcg_tier = tier (add those two columns). Do this on every sign-in so tier changes carry over.

3. Only link to an existing Market XI account if its email is confirmed in Supabase and the token's
   email_verified is true. Otherwise show "verify your email on GCG first" instead of signing in.

4. Start a Supabase session for that user (admin.generateLink type "magiclink", then verify the
   hashed token server-side with verifyOtp, and set the session cookies) and redirect to the game home.

5. Access rule (launch phase): Market XI is gated. Only users whose gcg_tier is beginner, intermediate, pro or
   founder may play. Gary grants Beginner manually in the GCG admin panel. Everyone else (gcg_tier "free",
   missing/null, or an account with no GCG link, including anyone who signed up directly on Market XI) sees a
   "Market XI is currently for Growth Capital Group Beginner members and above" page with a link to
   https://www.growthcapitalgroup.co/arena/market-xi, and cannot enter the game or any game API route.
   Enforce this server-side (middleware and every API route), not just in the UI.
   Tier is only refreshed when someone comes through /auth/gcg, so also store gcg_tier_checked_at and, if it is
   older than 24 hours, send the user back through https://www.growthcapitalgroup.co/arena/market-xi/play to
   refresh (so a revoked member loses access within a day). Existing Market XI users with no GCG link are blocked
   until they sign in through GCG once; tell Gary how many there are.

6. After any new Market XI signup (email or other), POST from the server to
   https://www.growthcapitalgroup.co/api/market-xi/link-user
   with header Authorization: Bearer <MARKET_XI_SHARED_SECRET> and JSON
   {"email": "...", "username": "...", "first_name": "...", "email_verified": true|false}.
   Response: {"created": bool, "username": "...", "tier": "..."}. New accounts come back as tier "free"; that is expected, they are not allowed in until Gary upgrades them. Store username/tier on the profile.
   Failure of this call must not block signup; retry later.
```
