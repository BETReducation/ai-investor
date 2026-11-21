import base64, json, time

import bcrypt
import pytest

import app as gcg


def _jwt(claims):
    body = base64.urlsafe_b64encode(json.dumps(claims).encode()).rstrip(b"=").decode()
    return f"x.{body}.y"


@pytest.fixture
def env(monkeypatch):
    users = {}
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "cid")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "sec")
    monkeypatch.setattr(gcg, "DATABASE_URL", "")
    monkeypatch.setattr(gcg, "_load_users", lambda: users)
    monkeypatch.setattr(gcg, "_load_user", lambda u: users.get(u))
    monkeypatch.setattr(gcg, "_save_user", lambda u, d: users.__setitem__(u, d))
    monkeypatch.setattr(gcg, "_find_user_by_login", lambda i, case_insensitive=False: next(
        ((n, d) for n, d in users.items() if n.lower() == i.lower() or d["profile"].get("email", "").lower() == i.lower()), (None, None)))
    monkeypatch.setattr(gcg, "log_event", lambda *a, **k: None)
    monkeypatch.setattr(gcg.gcg_notify, "record", lambda *a, **k: None)
    return users


def _user(email, verified, **profile):
    pw = bcrypt.hashpw(b"secret1", bcrypt.gensalt()).decode()
    return {"password_hash": pw, "tier": "free", "preferences": {}, "profile": {"email": email, "email_verified": verified, **profile}}


def _google(monkeypatch, client, sub="g1", email="a@gmail.com", verified=True):
    client.get("/auth/google/start")
    with client.session_transaction() as s:
        st = s["google_oauth"]

    class R:
        def raise_for_status(self): pass
        def json(self): return {"id_token": _jwt({"iss": "accounts.google.com", "aud": "cid", "exp": time.time() + 99,
                                                   "nonce": st["nonce"], "sub": sub, "email": email, "email_verified": verified,
                                                   "given_name": "Al"})}
    monkeypatch.setattr(gcg.requests, "post", lambda *a, **k: R())
    return client.get(f"/auth/google/callback?code=c&state={st['state']}")


def test_verified_email_links_and_logs_in(env, monkeypatch):
    env["al"] = _user("a@gmail.com", True)
    r = _google(monkeypatch, gcg.app.test_client())
    assert "gok=" in r.headers["Location"]
    assert env["al"]["profile"]["google_sub"] == "g1"


def test_unverified_account_email_needs_password(env, monkeypatch):
    env["al"] = _user("a@gmail.com", False)
    c = gcg.app.test_client()
    assert "gpending=1" in _google(monkeypatch, c).headers["Location"]
    assert "google_sub" not in env["al"]["profile"]
    assert c.post("/api/google/link", json={"identifier": "al", "password": "wrong"}).status_code == 401
    r = c.post("/api/google/link", json={"identifier": "al", "password": "secret1"})
    assert r.status_code == 200 and env["al"]["profile"]["google_sub"] == "g1"


def test_unknown_email_confirms_before_creating(env, monkeypatch):
    c = gcg.app.test_client()
    assert "gpending=1" in _google(monkeypatch, c, email="new@gmail.com").headers["Location"]
    assert env == {}
    r = c.post("/api/google/create", json={"username": "newbie", "first_name": "Al"})
    assert r.status_code == 200 and env["newbie"]["profile"]["has_password"] is False


def test_account_linked_to_other_google_is_refused(env, monkeypatch):
    env["al"] = _user("a@gmail.com", True, google_sub="other", google_email="o@gmail.com")
    r = _google(monkeypatch, gcg.app.test_client())
    assert "gerror=linked_other" in r.headers["Location"] and "o%2A%2A%2A" in r.headers["Location"]


def test_unverified_google_email_rejected(env, monkeypatch):
    assert "gerror=unverified" in _google(monkeypatch, gcg.app.test_client(), verified=False).headers["Location"]


def test_bad_state_rejected(env):
    c = gcg.app.test_client()
    c.get("/auth/google/start")
    assert "gerror=expired" in c.get("/auth/google/callback?code=c&state=nope").headers["Location"]


def test_login_messages_are_descriptive(env):
    env["g"] = _user("g@gmail.com", True, has_password=False)
    c = gcg.app.test_client()
    assert c.post("/api/login", json={"username": "g", "password": "x"}).get_json()["code"] == "google_only"
    assert c.post("/api/login", json={"username": "nobody", "password": "x"}).get_json()["code"] == "no_account"
