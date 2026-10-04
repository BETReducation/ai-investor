import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin, login_user

import gcg_chat


class U(UserMixin):
    def __init__(self, role):
        self.id, self.alpha_role, self.tier = role, role, "founder"


@pytest.fixture
def clients(tmp_path, monkeypatch):
    monkeypatch.setattr(gcg_chat, "CHAT_FILE", str(tmp_path / "chat.json"))
    gcg_chat.init(None, "")
    app = Flask(__name__)
    app.secret_key = "x"
    lm = LoginManager(app)
    lm.user_loader(lambda uid: U(uid))
    app.register_blueprint(gcg_chat.bp)

    @app.route("/_login/<role>")
    def _login(role):
        login_user(U(role))
        return "ok"

    def as_(role):
        c = app.test_client()
        c.get(f"/_login/{role}")
        return c
    return as_


def test_branching_move_copy_permissions(clients):
    gary, tom = clients("gary"), clients("tom")
    tid = gary.post("/api/chat/topic", json={"title": "Japan carry", "body": "Thoughts?"}).get_json()["thread_id"]
    assert tom.post(f"/api/chat/thread/{tid}/reply", json={"kind": "text", "body": "unwind risk"}).status_code == 200
    assert tom.post(f"/api/chat/thread/{tid}/reply", json={"kind": "link", "url": "javascript:x", "body": "e"}).status_code == 400
    assert tom.post(f"/api/chat/thread/{tid}/reply", json={"kind": "question", "body": "why?"}).status_code == 400
    b = tom.post(f"/api/chat/thread/{tid}/reply", json={"kind": "question", "body": "France bonds?", "heading": "JGB sales"}).get_json()["thread_id"]
    s = gary.get("/api/chat").get_json()
    branch = next(t for t in s["threads"] if t["id"] == b)
    assert branch["root_id"] == tid
    # a question asked inside a branch forks a sibling under the same topic
    b2 = gary.post(f"/api/chat/thread/{b}/reply", json={"kind": "question", "body": "q", "heading": "second"}).get_json()["thread_id"]
    assert next(t for t in gary.get("/api/chat").get_json()["threads"] if t["id"] == b2)["root_id"] == tid
    # only the author can delete or move
    text_id = next(m["id"] for m in s["messages"] if m["kind"] == "text")
    assert gary.delete(f"/api/chat/message/{text_id}").status_code == 403
    assert gary.post(f"/api/chat/message/{text_id}/copy", json={"to_thread": b}).status_code == 200
    assert tom.post(f"/api/chat/message/{text_id}/move", json={"to_thread": b}).status_code == 200
    # moving a topic under another keeps its branches attached to the new parent
    t2 = gary.post("/api/chat/topic", json={"title": "Other", "body": "x"}).get_json()["thread_id"]
    assert gary.post(f"/api/chat/thread/{tid}/move", json={"to_topic": t2}).status_code == 200
    threads = gary.get("/api/chat").get_json()["threads"]
    assert {t["root_id"] for t in threads if t["id"] in (tid, b, b2)} == {t2}
    # closing blocks replies
    gary.post(f"/api/chat/thread/{t2}/close", json={"closed": True})
    assert gary.post(f"/api/chat/thread/{t2}/reply", json={"kind": "text", "body": "hi"}).status_code == 400
    gary.delete(f"/api/chat/thread/{t2}")
    assert {t["id"] for t in gary.get("/api/chat").get_json()["threads"]} == set()


def test_partners_only(clients):
    app_client = clients("gary").application.test_client()
    assert app_client.get("/api/chat").get_json()["me"] is None
    assert app_client.post("/api/chat/topic", json={"title": "t", "body": "b"}).status_code == 401
