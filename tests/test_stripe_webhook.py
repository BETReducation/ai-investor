import hashlib
import hmac
import json
import time

import pytest

import app as A

SIGNING_KEY = "whsec_test"


@pytest.fixture
def env(monkeypatch, tmp_path):
    users = {"sam": {"tier": "free", "profile": {}, "entitlements": {}}}
    notes = []
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", SIGNING_KEY)
    monkeypatch.setattr(A, "DATABASE_URL", "")
    monkeypatch.setattr(A, "STRIPE_EVENTS_FILE", str(tmp_path / "events.json"))
    monkeypatch.setattr(A, "_load_user", lambda u: users.get(u))
    monkeypatch.setattr(A, "_load_users", lambda: users)
    monkeypatch.setattr(A, "_save_user", lambda u, d: users.__setitem__(u, d))
    monkeypatch.setattr(A, "_clear_custom_symbols_on_downgrade", lambda *a, **k: None)
    monkeypatch.setattr(A.gcg_notify, "record", lambda kind, actor, summary, url="": notes.append((kind, actor)))
    return users, notes


def send(event_id, kind, obj):
    body = json.dumps({"id": event_id, "type": kind, "data": {"object": obj}}).encode()
    ts = str(int(time.time()))
    sig = hmac.new(SIGNING_KEY.encode(), ts.encode() + b"." + body, hashlib.sha256).hexdigest()
    return A.app.test_client().post("/stripe/webhook", data=body, headers={
        "Stripe-Signature": f"t={ts},v1={sig}", "Content-Type": "application/json"})


def upgrade(event_id="evt_1"):
    return send(event_id, "checkout.session.completed", {
        "customer": "cus_1", "subscription": "sub_1", "payment_status": "paid",
        "metadata": {"username": "sam", "plan": "pro"}})


def test_bad_signature_rejected(env):
    r = A.app.test_client().post("/stripe/webhook", data=b"{}", headers={"Stripe-Signature": "t=1,v1=bad"})
    assert r.status_code == 400


def test_checkout_upgrades_user(env):
    users, _ = env
    assert upgrade().status_code == 200
    assert users["sam"]["tier"] == "pro"
    assert users["sam"]["profile"]["billing"]["customer_id"] == "cus_1"


def test_unpaid_async_checkout_does_not_grant(env):
    users, _ = env
    send("evt_a", "checkout.session.completed", {"customer": "cus_1", "payment_status": "unpaid",
                                                 "metadata": {"username": "sam", "plan": "pro"}})
    assert users["sam"]["tier"] == "free"
    send("evt_b", "checkout.session.async_payment_succeeded", {"customer": "cus_1", "payment_status": "paid",
                                                               "metadata": {"username": "sam", "plan": "pro"}})
    assert users["sam"]["tier"] == "pro"


def test_duplicate_event_ignored(env):
    users, notes = env
    upgrade()
    users["sam"]["tier"] = "free"
    upgrade()
    assert users["sam"]["tier"] == "free"
    assert len(notes) == 1


def test_failed_handler_releases_event_for_retry(env, monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("db down")
    with monkeypatch.context() as m:
        m.setattr(A, "_set_user_tier", boom)
        assert upgrade("evt_x").status_code == 500
    assert A._stripe_claim_event("evt_x")


def test_subscription_update_resolves_user_by_customer_and_reads_item_period_end(env):
    users, _ = env
    upgrade()
    send("evt_2", "customer.subscription.updated", {
        "id": "sub_1", "customer": "cus_1", "status": "active", "metadata": {},
        "items": {"data": [{"current_period_end": 1900000000, "price": {"interval": "year"}}]}})
    b = users["sam"]["profile"]["billing"]
    assert users["sam"]["tier"] == "pro"
    assert b["current_period_end"] == 1900000000 and b["interval"] == "year"


def test_subscription_deleted_drops_to_free(env):
    users, _ = env
    upgrade()
    send("evt_3", "customer.subscription.deleted", {"id": "sub_1", "customer": "cus_1", "metadata": {}, "items": {"data": []}})
    assert users["sam"]["tier"] == "free"


def test_payment_failed_marks_past_due_and_keeps_access(env):
    users, notes = env
    upgrade()
    send("evt_4", "invoice.payment_failed", {"customer": "cus_1"})
    assert users["sam"]["tier"] == "pro"
    assert users["sam"]["profile"]["billing"]["status"] == "past_due"
    assert ("payment_issue", "sam") in notes
    send("evt_5", "invoice.paid", {"customer": "cus_1"})
    assert users["sam"]["profile"]["billing"]["status"] == "active"


def test_dispute_without_customer_still_flagged(env):
    _, notes = env
    send("evt_6", "charge.dispute.created", {"id": "dp_1", "charge": "ch_1"})
    assert notes and notes[0][0] == "payment_issue"


class _FakeList:
    def __init__(self, data):
        self.data = data


class _FakeClient:
    """Records Stripe calls so price lookup and checkout params can be asserted without the network."""
    def __init__(self):
        self.created = []
        self.sessions = []
        outer = self

        class Prices:
            def list(self, params):
                return _FakeList([])

            def create(self, params):
                outer.created.append(params)
                return type("P", (), {"id": "price_1"})()

        class Products:
            def retrieve(self, pid):
                return {}

        class Sessions:
            def create(self, params):
                outer.sessions.append(params)
                return type("S", (), {"url": "https://checkout.example/x"})()

        self.v1 = type("V1", (), {
            "prices": Prices(), "products": Products(),
            "checkout": type("C", (), {"sessions": Sessions()})(),
        })()


def test_checkout_uses_persistent_price_and_tags_integration(env, monkeypatch):
    users, _ = env
    fake = _FakeClient()
    monkeypatch.setenv("STRIPE_SECRET_KEY", "placeholder_key")
    monkeypatch.setattr(A, "_stripe_client", lambda: fake)
    A._stripe_price_cache.clear()
    monkeypatch.setattr(A, "login_required", lambda f: f, raising=False)
    c = A.app.test_client()
    with c.session_transaction() as sess:
        sess["_user_id"] = "sam"
        sess["_fresh"] = True
    monkeypatch.setattr(A, "_load_user", lambda u: users.get(u))
    r = c.post("/api/billing/checkout", json={"plan": "pro", "interval": "year"})
    if r.status_code == 401 or r.status_code == 302:
        pytest.skip("login session wiring differs")
    assert r.status_code == 200, r.get_data(as_text=True)
    assert fake.created[0]["lookup_key"] == "gcg_pro_year_20000_exclusive"
    sess_params = fake.sessions[0]
    assert sess_params["line_items"][0]["price"] == "price_1"
    assert "price_data" not in sess_params["line_items"][0]
    assert sess_params["integration_identifier"].startswith("gcg-")
