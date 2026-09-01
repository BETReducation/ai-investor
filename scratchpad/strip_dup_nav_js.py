"""Remove the legacy duplicate theme/nav-scroll JS block from pages that
still hand-copy it — nav.js now owns toggleTheme/toggleMobileNav/the
scroll-background handler (including the arm-colour tint), and this
trailing duplicate ran after it and silently overwrote it every time.
"""
import sys

REPLACEMENT = (
    "// Theme toggle, mobile nav, and the nav-scroll background (incl. this\n"
    "// page's arm-coloured tint) all now live solely in /static/js/nav.js —\n"
    "// this used to duplicate all of it with a plain, non-arm-aware version\n"
    "// that ran after nav.js's and silently overwrote it, undoing the header\n"
    "// colour-match on every scroll and theme toggle. Removed rather than\n"
    "// kept in sync by hand.\n"
    "</script>\n</body>\n</html>\n"
)

FILES = sys.argv[1:]

for path in FILES:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    candidates = []
    for marker in ("function updateLogos", "function toggleMobileNav"):
        idx = content.find(marker)
        if idx != -1:
            candidates.append(idx)

    if not candidates:
        print("  SKIP (no marker found):", path)
        continue

    start = min(candidates)
    if not content.rstrip().endswith("</html>"):
        print("  SKIP (doesn't end with </html>, needs manual check):", path)
        continue

    new_content = content[:start] + REPLACEMENT
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("done:", path)
