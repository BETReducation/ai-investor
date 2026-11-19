import base64, hashlib, hmac, json, os, time

os.environ["MARKET_XI_SHARED_SECRET"] = "test-secret"
import app as gcg


def _decode(token):
    head, body, sig = token.split(".")
    expected = base64.urlsafe_b64encode(hmac.new(b"test-secret", f"{head}.{body}".encode(), hashlib.sha256).digest()).rstrip(b"=").decode()
    assert hmac.compare_digest(sig, expected)
    return json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))


def test_token_carries_effective_tier_and_expires_soon():
    user = {"tier": "free", "profile": {"email": "a@b.co", "email_verified": True}}
    p = _decode(gcg._market_xi_token("gary", user))
    assert p["email"] == "a@b.co" and p["sub"] == "gary"
    assert p["tier"] in ("free", "beginner")  # beginner while the promo runs
    assert 0 < p["exp"] - time.time() <= gcg.MARKET_XI_TOKEN_TTL


def test_link_user_rejects_bad_secret():
    c = gcg.app.test_client()
    r = c.post("/api/market-xi/link-user", json={"email": "x@y.co"}, headers={"Authorization": "Bearer nope"})
    assert r.status_code == 401


def test_play_redirects_to_login_when_signed_out():
    r = gcg.app.test_client().get("/arena/market-xi/play")
    assert r.status_code == 302 and "/login?next=" in r.headers["Location"]


import pytest


@pytest.fixture
def store(monkeypatch):
    users = {}
    monkeypatch.setattr(gcg, "_load_user", lambda u: users.get(u))
    monkeypatch.setattr(gcg, "_save_user", lambda u, d: users.__setitem__(u, d))
    monkeypatch.setattr(gcg, "_find_user_by_login",
                        lambda ident, case_insensitive=False: next(
                            ((n, d) for n, d in users.items()
                             if n.lower() == ident.lower() or (d.get("profile", {}).get("email", "").lower() == ident.lower())),
                            (None, None)))
    monkeypatch.setattr(gcg, "_send_email", lambda *a, **k: None)
    monkeypatch.setattr(gcg.gcg_notify, "record", lambda *a, **k: None)
    return users


def _login(client, name):
    with client.session_transaction() as s:
        s["_user_id"] = name
        s["_fresh"] = True


def _member(store, name="gary", tier="pro", verified=True):
    store[name] = {"tier": tier, "password_hash": "x", "profile": {"email": f"{name}@x.co", "email_verified": verified}}


def test_play_blocks_unverified_email(store):
    _member(store, verified=False)
    c = gcg.app.test_client()
    _login(c, "gary")
    r = c.get("/arena/market-xi/play")
    assert r.status_code == 403 and r.headers["Cache-Control"] == "no-store"


def test_play_redirects_with_token_from_server_data(store):
    _member(store, tier="pro")
    c = gcg.app.test_client()
    _login(c, "gary")
    r = c.get("/arena/market-xi/play?tier=founder&email=evil@x.co")
    assert r.status_code == 302 and r.headers["Referrer-Policy"] == "no-referrer"
    from urllib.parse import urlparse, parse_qs
    p = _decode(parse_qs(urlparse(r.headers["Location"]).query)["token"][0])
    assert p["sub"] == "gary" and p["email"] == "gary@x.co" and p["tier"] == "pro"
    assert p["iss"] == "growthcapitalgroup.co" and p["aud"] == "playmarketxi.com"


def test_jti_unique_and_all_tiers_map():
    for tier in ("beginner", "intermediate", "pro", "founder"):
        assert _decode(gcg._market_xi_token("a", {"tier": tier, "profile": {}}))["tier"] == tier
    a = _decode(gcg._market_xi_token("a", {"tier": "pro", "profile": {}}))
    b = _decode(gcg._market_xi_token("a", {"tier": "pro", "profile": {}}))
    assert a["jti"] != b["jti"]


def test_unmapped_tier_fails_closed():
    with pytest.raises(ValueError):
        gcg._market_xi_token("a", {"tier": "platinum", "profile": {}})


def _link(c, **body):
    return c.post("/api/market-xi/link-user", json=body, headers={"Authorization": "Bearer test-secret"})


def test_link_user_creates_then_is_idempotent_and_never_downgrades(store):
    c = gcg.app.test_client()
    r = _link(c, email="new@x.co", username="newbie", first_name="N", email_verified=True)
    assert r.status_code == 201 and r.get_json() == {"created": True, "username": "newbie", "tier": "beginner"}
    r2 = _link(c, email="new@x.co", username="other", first_name="N", email_verified=True)
    assert r2.get_json() == {"created": False, "username": "newbie", "tier": "beginner"} and len(store) == 1
    _member(store, "paid", tier="pro")
    r3 = _link(c, email="paid@x.co", username="paid", first_name="P", email_verified=False)
    assert r3.get_json() == {"created": False, "username": "paid", "tier": "pro"} and store["paid"]["tier"] == "pro"


def test_link_user_rejects_non_boolean_verified(store):
    assert _link(gcg.app.test_client(), email="a@x.co", email_verified="yes").status_code == 400
