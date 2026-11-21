"""Create (or find) the Stripe Products and Prices for every paid plan and interval.

Uses the same lookup as checkout (app._stripe_price_id), so Prices made here are the ones the
site finds later. Safe to re-run: existing Prices are reused, nothing is duplicated.

    STRIPE_SECRET_KEY=rk_live_... venv/bin/python scripts/seed_stripe_prices.py          # dry run
    STRIPE_SECRET_KEY=rk_live_... venv/bin/python scripts/seed_stripe_prices.py --apply  # create

The key needs write on Products and Prices. Set STRIPE_TAX_BEHAVIOR=inclusive first if the live
site will use it, because tax behaviour is part of the Price's lookup key.
"""
import os
import sys

os.environ.setdefault("GCG_SKIP_WARM", "1")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app
import plans

key = os.environ.get("STRIPE_SECRET_KEY", "")
if not key:
    sys.exit("Set STRIPE_SECRET_KEY in the environment first.")
mode = "LIVE" if key.startswith(("sk_live_", "rk_live_")) else "test/sandbox"
apply = "--apply" in sys.argv
behavior = "inclusive" if os.environ.get("STRIPE_TAX_BEHAVIOR") == "inclusive" else "exclusive"
print(f"Mode: {mode}, tax behaviour: {behavior}, {'APPLY' if apply else 'dry run'}")

client = app._stripe_client()
for plan in (p for p in plans.PLANS if p["monthly"]):
    for interval, amount in (("month", plan["monthly"]), ("year", plan["annual"])):
        lookup = f"gcg_{plan['id']}_{interval}_{amount}_{behavior}"
        found = client.v1.prices.list({"lookup_keys": [lookup], "active": True, "limit": 1}).data
        if found:
            print(f"  exists  {lookup}  {found[0].id}")
        elif apply:
            print(f"  created {lookup}  {app._stripe_price_id(plan, interval)}")
        else:
            print(f"  would create {lookup}  (${amount / 100:.2f}/{interval})")
