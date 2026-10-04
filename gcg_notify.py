"""Notification panel: a shared activity feed with a per-user read marker.

Partners see chat and Alpha activity; admins also see member joins and logins.
Nobody is notified of their own actions. Recording is best-effort so a feed
failure can never break the request it rides on.
"""
import datetime as _dt

from flask import Blueprint, jsonify
from flask_login import current_user

from docstore import DocStore

bp = Blueprint("gcg_notify", __name__)
store = DocStore("gcg_notifications", lambda: {"next_id": 1, "events": [], "seen": {}})

MAX_EVENTS = 400
ADMIN_ONLY = {"member_joined", "login"}
_is_admin = lambda user: False


def init(db_conn, database_url: str, is_admin) -> None:
    global _is_admin
    _is_admin = is_admin
    store.init(db_conn, database_url)


def record(kind: str, actor: str, summary: str, url: str = "") -> None:
    try:
        with store.txn() as doc:
            doc["events"].append({"id": doc["next_id"], "kind": kind, "actor": actor, "summary": summary[:240],
                                  "url": url, "at": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")})
            doc["next_id"] += 1
            del doc["events"][:-MAX_EVENTS]
    except Exception as e:
        print(f"[notify record failed] {kind}: {e}")


def _viewer_access():
    """None if the viewer gets no panel, else whether they also see admin-only events."""
    if not current_user.is_authenticated:
        return None
    admin = _is_admin(current_user)
    if admin or getattr(current_user, "alpha_role", None):
        return admin
    return None


def _visible(doc, me, admin):
    return [e for e in reversed(doc["events"]) if e["actor"] != me and (admin or e["kind"] not in ADMIN_ONLY)]


@bp.route("/api/notifications", methods=["GET"])
def notifications():
    admin = _viewer_access()
    if admin is None:
        return jsonify({"enabled": False, "unread": 0, "events": []})
    doc = store.read()
    me = current_user.id
    events = _visible(doc, me, admin)[:60]
    seen = doc["seen"].get(me, 0)
    for e in events:
        e["unread"] = e["id"] > seen
    return jsonify({"enabled": True, "admin": admin, "unread": sum(e["unread"] for e in events), "events": events})


@bp.route("/api/notifications/read", methods=["POST"])
def mark_read():
    if _viewer_access() is None:
        return jsonify({"error": "Not allowed"}), 403
    with store.txn() as doc:
        doc["seen"][current_user.id] = doc["next_id"] - 1
    return jsonify({"ok": True})
