# Railway -> Render migration (handoff)

Why: Railway builder (BuildKit) failing every deploy since 2026-10-26; 5 failures in a row. Site stuck on the 13:23 build.

Done:
- render.yaml in repo (web service ai-investor, starter; Postgres ai-investor-db basic-256mb, diskSizeGB 15 to match what Render created).
- Railway Postgres dumped (217 MB, pg_dump -Fc) and restored to Render with pg_restore --clean. 15/16 tables match exactly; user_events 812 vs 811 (live traffic since the dump).
- libpq installed via brew (/opt/homebrew/opt/libpq/bin).
- Render MCP server added at user scope.

Open:
- Blueprint sync "GCG Website" on Render was failing (first on disk shrink 15 -> 5 GB, fixed in render.yaml; user said still not working afterwards). Find the current error via Render MCP.
- Check the web service is running; restart it so it sees the restored data.
- Test the onrender.com URL (pages, /api, Alpha files, login). Add the Render URL to Google OAuth redirect URIs.
- At cutover: fresh pg_dump from Railway (DATABASE_PUBLIC_URL from `railway variables --service Postgres`), restore to Render, then DNS for growthcapitalgroup.co. User should not publish/edit during that window.
- Afterwards: rotate the Render DB password, delete the dump in the scratchpad dir (contains user data), keep Railway for ~1 week as fallback.
- Later, separately: move alpha_content source_file/image_file bytea blobs (189 MB) to object storage (R2/S3).
