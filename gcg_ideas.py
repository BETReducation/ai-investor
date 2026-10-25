"""Topic ideas for the scheduled X drafting task.

Gary adds ideas in the Social Post Studio; each draft run fetches the pending ones
(token-authenticated, since the task isn't a logged-in browser), writes drafts around
them, then marks them used. X_IDEAS_TOKEN must match on the server and in the task's
local token file.
"""
import datetime as _dt
import hmac
import os

from flask import Blueprint, jsonify, request
from flask_login import current_user

from docstore import DocStore

bp = Blueprint("gcg_ideas", __name__)
store = DocStore("gcg_x_ideas", lambda: {"next_id": 1, "ideas": []})
MAX_IDEAS = 200
_is_admin = lambda user: False


def init(db_conn, database_url: str, is_admin) -> None:
    global _is_admin
    _is_admin = is_admin
    store.init(db_conn, database_url)


def _authorised() -> bool:
    token = os.environ.get("X_IDEAS_TOKEN", "")
    sent = request.headers.get("X-Ideas-Token", "")
    if token and sent and hmac.compare_digest(token, sent):
        return True
    return current_user.is_authenticated and _is_admin(current_user)


@bp.before_request
def _guard():
    if not _authorised():
        return jsonify({"error": "Not allowed"}), 403


@bp.route("/api/x-ideas", methods=["GET"])
def list_ideas():
    return jsonify({"ideas": store.read()["ideas"]})


@bp.route("/api/x-ideas", methods=["POST"])
def add_idea():
    text = ((request.get_json(silent=True) or {}).get("text") or "").strip()[:600]
    if not text:
        return jsonify({"error": "Idea text required"}), 400
    with store.txn() as doc:
        idea = {"id": doc["next_id"], "text": text, "used": False,
                "added": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
        doc["next_id"] += 1
        doc["ideas"].append(idea)
        del doc["ideas"][:-MAX_IDEAS]
    return jsonify(idea)


@bp.route("/api/x-ideas/<int:iid>", methods=["DELETE"])
def delete_idea(iid):
    with store.txn() as doc:
        doc["ideas"] = [i for i in doc["ideas"] if i["id"] != iid]
    return jsonify({"ok": True})


@bp.route("/api/x-ideas/<int:iid>/used", methods=["POST"])
def mark_used(iid):
    with store.txn() as doc:
        for i in doc["ideas"]:
            if i["id"] == iid:
                i["used"] = True
    return jsonify({"ok": True})
