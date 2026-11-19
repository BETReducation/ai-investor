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
