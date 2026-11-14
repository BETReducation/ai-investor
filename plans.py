"""Plans, prices and what each plan unlocks. Edit this file to change the offer;
the pricing page, lock icons, upgrade prompts and server-side gating all read from it.

Prices are USD cents. Annual = ten months' price (two months free).
"""

PLAN_RANK = {"free": 0, "beginner": 1, "intermediate": 2, "pro": 3, "founder": 4}  # founder is partner-only, never sold
PLAN_NAMES = {"free": "Free", "beginner": "Beginner", "intermediate": "Intermediate", "pro": "Pro", "founder": "Founder"}
PAID_TIERS = ("beginner", "intermediate", "pro", "founder")

# Beginner is free for registered accounts until the end of this date (partner decision, Nov 2026).
# Worked out on each request rather than stored, so it ends by itself on 1 January 2027.
import datetime as _dt
PROMO_PLAN = "beginner"
PROMO_UNTIL = _dt.date(2026, 12, 31)


def promo_active(today=None) -> bool:
    return (today or _dt.datetime.now(_dt.timezone.utc).date()) <= PROMO_UNTIL


def access_tier(tier: str, authenticated: bool = True, today=None) -> str:
    """The tier used for access checks: free accounts get the promo plan while the promo runs."""
    tier = tier or "free"
    if authenticated and tier == "free" and promo_active(today):
        return PROMO_PLAN
    return tier


PLANS = [
    {"id": "free", "name": "Free", "monthly": 0, "annual": 0,
     "blurb": "Explore the basics and see how everything works."},
    {"id": "beginner", "name": "Beginner", "monthly": 500, "annual": 5000,
     "blurb": "Beginner lessons and Alpha research, every data visualisation and tool, and the community Discord."},
    {"id": "intermediate", "name": "Intermediate", "monthly": 1000, "annual": 10000,
     "blurb": "Everything in Beginner, plus intermediate lessons and Alpha, the Backtester and email support."},
    {"id": "pro", "name": "Pro", "monthly": 2000, "annual": 20000,
     "blurb": "Everything, including pro lessons and Alpha, the Signals suite, trading competitions and priority email."},
]

# Rows of the comparison table: (label, free, beginner, intermediate, pro). True/False render as tick/dash.
COMPARE = [
    ("Beginner lessons", True, True, True, True),
    ("Intermediate lessons", False, False, True, True),
    ("Pro lessons", False, False, False, True),
    ("Beginner Alpha posts", "Preview only", "Full posts", "Full posts", "Full posts"),
    ("Intermediate Alpha posts", "Preview only", "Preview only", "Full posts", "Full posts"),
    ("Pro Alpha posts", "Preview only", "Preview only", "Preview only", "Full posts"),
    ("Explainers", "The basics", "Basics and in-depth", "Basics and in-depth", "Basics and in-depth"),
    ("Data visualisations", "Selected", "All", "All", "All"),
    ("Calculators, donuts and trackers", False, True, True, True),
    ("Backtester and Portfolio Manager", False, False, True, True),
    ("Signals and AI Chart Analysis", False, False, False, True),
    ("Market XI dashboard", False, True, True, True),
    ("Trading competitions", False, False, False, True),
    ("Community Discord and FAQ", False, True, True, True),
    ("Email support", False, False, True, True),
    ("Priority email support", False, False, False, True),
    ("Lesson Q&A assistant", "3 a day", "3 a day", "3 a day", "Unlimited"),
]

# Lessons are gated by level.
LESSON_LEVEL_MIN_PLAN = {"beginner": "beginner", "intermediate": "intermediate", "pro": "pro"}  # Free accounts see FREE_LESSON_SAMPLES only

# Explainers are gated by their "part" field.
EXPLAINER_PART_MIN_PLAN = {"basics": "free", "in-depth": "beginner"}

# Data visualisation pages, by slug. Anything not listed is free.
DATAVIZ_MIN_PLAN = {
    "nasdaq-wagon-wheel": "beginner", "ftse-wagon-wheel": "beginner", "russell-compass": "beginner",
    "league-compass": "beginner", "bitcoin-dashboard": "beginner", "crypto-compass": "beginner",
    "reit-map": "beginner", "barrel-map": "beginner", "finance-map": "beginner",
    "etf-tracker": "beginner", "ai-tracker": "beginner", "mining-globe": "beginner",
}

# Free readers see this much of an Alpha post before the paywall.
ALPHA_PREVIEW_CHARS = 700
ALPHA_LEVEL_MIN_PLAN = {"beginner": "beginner", "intermediate": "intermediate", "pro": "pro"}  # by post level; unlevelled posts count as beginner
CHAT_POST_MIN_PLAN = "beginner"

# Tools, by page path: the plan each one needs. Free accounts see them locked with a plan label.
# static/js/nav.js carries a copy of this map (TOOL_TIER) for the labels; tests/test_plans.py keeps them in step.
TOOL_MIN_PLAN = {
    "/tools/signals": "pro",
    "/tools/ai-chart-analysis": "pro",
    "/backtester": "intermediate",
    "/tools/portfolio": "intermediate",
    "/tools/calculator": "beginner",
    "/tools/crypto-unit-calculator": "beginner",
    "/tools/crypto-portfolio-donut": "beginner",
    "/tools/metal-calculator": "beginner",
    "/tools/dividend-calculator": "beginner",
    "/tools/stock-donut": "beginner",
    "/tools/currency-calculator": "beginner",
    "/tools/freedom-clock": "beginner",
    "/tools/price-value-tracker": "beginner",
}

# Free-account samples (the "1 page / 3 tests / 3 pages" cells of the tier sheet).
FREE_LESSONS_PER_LEVEL = 1        # the first lesson of each level stays open to everyone
FREE_ALPHA_POSTS_PER_LEVEL = 1    # a free account can open one full Alpha post per level
FREE_DATAVIZ_PAGES = 3            # a free account can open three data visualisation pages
