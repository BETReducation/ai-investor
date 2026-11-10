"""Plans, prices and what each plan unlocks. Edit this file to change the offer;
the pricing page, lock icons, upgrade prompts and server-side gating all read from it.

Prices are USD cents. Annual = ten months' price (two months free).
"""

PLAN_RANK = {"free": 0, "beginner": 1, "pro": 2, "founder": 3}  # founder is partner-only, never sold
PLAN_NAMES = {"free": "Free", "beginner": "Beginner", "pro": "Pro", "founder": "Founder"}
PAID_TIERS = ("beginner", "pro", "founder")

PLANS = [
    {"id": "free", "name": "Free", "monthly": 0, "annual": 0,
     "blurb": "Explore the basics and see how everything works."},
    {"id": "beginner", "name": "Beginner", "monthly": 500, "annual": 5000,
     "blurb": "Full Alpha posts, intermediate lessons and the community chat."},
    {"id": "pro", "name": "Pro", "monthly": 2000, "annual": 20000,
     "blurb": "Everything, including the full Backtester and Signals suite."},
]

# Rows of the comparison table: (label, free, beginner, pro). True/False render as tick/dash.
COMPARE = [
    ("Beginner lessons", True, True, True),
    ("Intermediate lessons", False, True, True),
    ("Pro lessons", False, False, True),
    ("Alpha posts", "Preview only", "Full posts", "Full posts"),
    ("Explainers", "The basics", "Basics and in-depth", "Basics and in-depth"),
    ("Data visualisations", "Selected", "Most", "All"),
    ("GCG Chat", "Read only", "Read and post", "Read and post"),
    ("Backtester", "Capped symbols and daily runs", "Capped symbols and daily runs", "All symbols, unlimited runs"),
    ("Signals", "Basic", "Basic", "Full suite and saved symbols"),
    ("Lesson Q&A assistant", "3 a day", "3 a day", "Unlimited"),
    ("Market XI dashboard", "With Market XI code", "With Market XI code", "With Market XI code"),
]

# Lessons are gated by level.
LESSON_LEVEL_MIN_PLAN = {"beginner": "free", "intermediate": "beginner", "pro": "pro"}

# Explainers are gated by their "part" field.
EXPLAINER_PART_MIN_PLAN = {"basics": "free", "in-depth": "beginner"}

# Data visualisation pages, by slug. Anything not listed is free.
DATAVIZ_MIN_PLAN = {
    "nasdaq-wagon-wheel": "beginner", "ftse-wagon-wheel": "beginner", "russell-compass": "beginner",
    "league-compass": "beginner", "bitcoin-dashboard": "beginner", "crypto-compass": "beginner",
    "reit-map": "beginner", "barrel-map": "beginner", "finance-map": "beginner",
    "etf-tracker": "pro", "ai-tracker": "pro", "mining-globe": "pro",
}

# Free readers see this much of an Alpha post before the paywall.
ALPHA_PREVIEW_CHARS = 700
ALPHA_FULL_MIN_PLAN = "beginner"
CHAT_POST_MIN_PLAN = "beginner"
