"""Fix the .section-badge breadcrumb wrapping badly on mobile across every
page that duplicates this component in its own <style> block: drop the
decorative dash and let the text wrap cleanly as a centered block instead
of an inline-flex row that splits the text away from the dash.
"""
import glob
import sys

INSERT = (
    "\n@media (max-width: 600px) {\n"
    "  .section-badge { display: block; white-space: normal; text-align: center; }\n"
    "  .section-badge::before { display: none; }\n"
    "}\n"
)

FILES = sys.argv[1:] or sorted(glob.glob("static/*.html"))
touched = []

for path in FILES:
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    idx = content.find(".section-badge::before")
    if idx == -1:
        continue
    if "@media (max-width: 600px) {\n  .section-badge { display: block;" in content:
        continue  # already fixed

    brace_idx = content.find("}", idx)
    if brace_idx == -1:
        print("  SKIP (no closing brace found):", path)
        continue

    insert_at = brace_idx + 1
    new_content = content[:insert_at] + INSERT + content[insert_at:]
    with open(path, "w", encoding="utf-8") as f:
        f.write(new_content)
    touched.append(path)

print(f"Fixed {len(touched)} files")
for t in touched:
    print(" ", t)
