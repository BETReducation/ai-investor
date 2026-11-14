import datetime as dt

import app as A
import plans


def test_promo_gives_registered_free_accounts_beginner_until_year_end():
    assert plans.access_tier("free", today=dt.date(2026, 12, 31)) == "beginner"
    assert plans.access_tier("free", today=dt.date(2027, 1, 1)) == "free"
    assert plans.access_tier("free", authenticated=False, today=dt.date(2026, 12, 1)) == "free"
    assert plans.access_tier("pro", today=dt.date(2026, 12, 1)) == "pro"


def test_tier_order_and_names():
    assert [t for t, _ in sorted(plans.PLAN_RANK.items(), key=lambda kv: kv[1])] == ["free", "beginner", "intermediate", "pro", "founder"]
    assert plans.PLAN_NAMES["beginner"] == "Beginner"
    assert [(p["id"], p["monthly"], p["annual"]) for p in plans.PLANS if p["monthly"]] == [
        ("beginner", 500, 5000), ("intermediate", 1000, 10000), ("pro", 2000, 20000)]


def test_compare_rows_have_a_cell_per_plan():
    assert all(len(r) == 1 + len(plans.PLANS) for r in plans.COMPARE)


def test_lesson_gates_by_level_with_one_free_sample_each():
    gates = A._gate_map()
    for level, need in (("beginner", "beginner"), ("intermediate", "intermediate"), ("pro", "pro")):
        lessons = [l for l in A.LESSON_PAGES if l["level"] == level]
        samples = [l for l in lessons if f"/learn/{level}/{l['slug']}" not in gates]
        assert len(samples) == 1, level
        assert all(gates[f"/learn/{level}/{l['slug']}"] == need for l in lessons if l not in samples)


def test_every_data_viz_page_needs_beginner_or_above():
    assert set(plans.DATAVIZ_MIN_PLAN.values()) == {"beginner"}


def test_entitlements_per_tier():
    e = A.default_entitlements
    assert e("beginner")["backtester"] == "basic" and e("beginner")["market_xi"] == "entered"
    assert e("intermediate")["backtester"] == "pro" and e("intermediate")["signals"] == "basic"
    assert e("pro")["signals"] == "pro" and e("free")["market_xi"] == "not_entered"


def test_tools_are_gated_by_plan():
    gates = A._gate_map()
    assert gates["/tools/signals"] == "pro" and gates["/tools/ai-chart-analysis"] == "pro"
    assert gates["/backtester"] == "intermediate" and gates["/tools/portfolio"] == "intermediate"
    assert gates["/tools/dividend-calculator"] == "beginner" and gates["/tools/calculator"] == "beginner"


def test_every_tool_page_in_the_menu_has_a_plan_and_nav_labels_match():
    import re
    nav = open("static/js/nav.js", encoding="utf-8").read()
    labels = dict(re.findall(r"'(/[^']+)':\s*'(Beginner|Intermediate|Pro)'", nav.split("TOOL_TIER")[1].split("};")[0]))
    assert labels == {path: plans.PLAN_NAMES[need] for path, need in plans.TOOL_MIN_PLAN.items()}
    for page in A._SEED_DATAVIZ_PAGES:
        if page.get("kind") == "tool":
            assert f"/tools/{page['slug']}" in plans.TOOL_MIN_PLAN


def test_backtester_and_signals_apis_lock_out_lower_plans(monkeypatch):
    c = A.app.test_client()
    r = c.get("/api/backtest?symbol=AAPL")
    assert r.status_code == 403 and r.get_json().get("locked")
    assert c.get("/api/backtest/quota").status_code == 403


def test_plan_read_from_intermediate_price_key():
    assert A._plan_from_price({"price": {"lookup_key": "gcg_intermediate_month_1000_exclusive"}}) == "intermediate"
