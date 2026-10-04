"""GCG Chat — threaded partner discussion (Alpha section, partners only).

Structure: a topic is a thread with root_id None; its opening post is the first
message. Replies are one of three types: link (url + manual excerpt), text, or
question. A question forks a branch: a new thread (root_id = the topic) with its
own sub-heading. Branches are always one level under a topic, never nested.

State is one JSON document (a single Postgres row, or a local file without
DATABASE_URL). Volume is a handful of partners writing text, so whole-document
read-modify-write under a row lock is simpler than several relational tables.
"""
import datetime as _dt

from flask import Blueprint, jsonify, request
from flask_login import current_user

import gcg_notify
from docstore import DocStore

bp = Blueprint("gcg_chat", __name__)

QUIET_DAYS = 14
MAX_TITLE, MAX_BODY, MAX_EXCERPT = 160, 4000, 1200


def _empty() -> dict:
    return {"next_id": 1, "threads": [], "messages": []}


store = DocStore("gcg_chat", _empty)
_txn, _read, init = store.txn, store.read, store.init


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ChatError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.code = code


def _new_id(state) -> int:
    n = state["next_id"]
    state["next_id"] = n + 1
    return n


def _thread(state, tid):
    for t in state["threads"]:
        if t["id"] == tid:
            return t
    raise ChatError("Thread not found", 404)


def _message(state, mid):
    for m in state["messages"]:
        if m["id"] == mid:
            return m
    raise ChatError("Message not found", 404)


def _touch(thread, ts=None):
    thread["last_activity"] = ts or _now()


def _clean(value, limit, label, required=True) -> str:
    value = (value or "").strip()
    if required and not value:
        raise ChatError(f"{label} is required")
    if len(value) > limit:
        raise ChatError(f"{label} is too long (max {limit} characters)")
    return value


def _fields_for(kind, data) -> dict:
    """Validated content fields for a message of the given type."""
    if kind == "link":
        url = _clean(data.get("url"), 1000, "Link")
        if not url.lower().startswith(("http://", "https://")):
            raise ChatError("Link must start with http:// or https://")
        return {"url": url, "body": _clean(data.get("body"), MAX_EXCERPT, "Excerpt")}
    return {"url": None, "body": _clean(data.get("body"), MAX_BODY, "Text")}


def _open_thread(thread):
    if thread.get("closed"):
        raise ChatError("This thread is closed. Reopen it first.")


def _author_only(item):
    if item["author"] != current_user.alpha_role:
        raise ChatError("Only the author can do that", 403)


def _add_message(state, thread, kind, author, fields, opening=False, ts=None) -> dict:
    ts = ts or _now()
    msg = {"id": _new_id(state), "thread_id": thread["id"], "author": author, "kind": kind,
           "created_at": ts, "edited_at": None, "opening": opening, **fields}
    state["messages"].append(msg)
    _touch(thread, ts)
    return msg


def _copy_thread(state, src, root_id, title=None) -> dict:
    ts = _now()
    new = {"id": _new_id(state), "root_id": root_id, "title": title or src["title"], "author": src["author"],
           "created_at": ts, "forked_at": ts, "last_activity": ts, "closed": False}
    state["threads"].append(new)
    for m in [m for m in state["messages"] if m["thread_id"] == src["id"]]:
        state["messages"].append({**m, "id": _new_id(state), "thread_id": new["id"]})
    return new


def _topic_target(state, tid):
    t = _thread(state, tid)
    if t["root_id"] is not None:
        raise ChatError("Destination must be a topic")
    return t


def _notify(kind, summary):
    gcg_notify.record(kind, current_user.id, summary, "/alpha/chat")


def _api(fn):
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            return jsonify({"error": "Login required"}), 401
        if getattr(current_user, "tier", None) != "founder" or not getattr(current_user, "alpha_role", None):
            return jsonify({"error": "GCG Chat is for partners only"}), 403
        try:
            return fn(*args, **kwargs)
        except ChatError as e:
            return jsonify({"error": str(e)}), e.code
    wrapped.__name__ = fn.__name__
    return wrapped


@bp.route("/api/chat", methods=["GET"])
def chat_state():
    """Public read. Posting and every other endpoint stay partner-only."""
    state = _read()
    me = None
    if current_user.is_authenticated and current_user.tier == "founder":
        me = current_user.alpha_role
    return jsonify({"me": me, "quiet_days": QUIET_DAYS,
                    "threads": state["threads"], "messages": state["messages"]})


@bp.route("/api/chat/topic", methods=["POST"])
@_api
def chat_new_topic():
    data = request.get_json(silent=True) or {}
    title = _clean(data.get("title"), MAX_TITLE, "Title")
    fields = {"url": None, "body": _clean(data.get("body"), MAX_BODY, "Opening post")}
    with _txn() as state:
        ts = _now()
        t = {"id": _new_id(state), "root_id": None, "title": title, "author": current_user.alpha_role,
             "created_at": ts, "forked_at": None, "last_activity": ts, "closed": False}
        state["threads"].append(t)
        _add_message(state, t, "post", current_user.alpha_role, fields, opening=True, ts=ts)
    _notify("chat_topic", f"{current_user.alpha_role} started a topic: {title}")
    return jsonify({"thread_id": t["id"]})


@bp.route("/api/chat/thread/<int:tid>/reply", methods=["POST"])
@_api
def chat_reply(tid):
    data = request.get_json(silent=True) or {}
    kind = data.get("kind")
    if kind not in ("link", "text", "question"):
        raise ChatError("Reply type must be link, text or question")
    with _txn() as state:
        thread = _thread(state, tid)
        _open_thread(thread)
        fields = _fields_for(kind, data)
        topic_title = _thread(state, thread["root_id"] or tid)["title"]
        if kind != "question":
            msg = _add_message(state, thread, kind, current_user.alpha_role, fields)
            verb = "shared a link in" if kind == "link" else "replied in"
            _notify("chat_reply", f"{current_user.alpha_role} {verb} {topic_title}")
            return jsonify({"thread_id": tid, "message_id": msg["id"]})
        heading = _clean(data.get("heading"), MAX_TITLE, "Sub-heading")
        root = thread["root_id"] or thread["id"]
        ts = _now()
        branch = {"id": _new_id(state), "root_id": root, "title": heading, "author": current_user.alpha_role,
                  "created_at": ts, "forked_at": ts, "last_activity": ts, "closed": False}
        state["threads"].append(branch)
        _add_message(state, branch, "question", current_user.alpha_role, fields, opening=True, ts=ts)
        _touch(_thread(state, root), ts)
    _notify("chat_branch", f"{current_user.alpha_role} opened a branch \"{heading}\" in {topic_title}")
    return jsonify({"thread_id": branch["id"]})


@bp.route("/api/chat/message/<int:mid>", methods=["PATCH", "DELETE"])
@_api
def chat_message(mid):
    with _txn() as state:
        msg = _message(state, mid)
        thread = _thread(state, msg["thread_id"])
        _author_only(msg)
        if request.method == "DELETE":
            if msg["opening"]:
                raise ChatError("Delete the whole thread instead of its opening post")
            state["messages"].remove(msg)
        else:
            _open_thread(thread)
            data = request.get_json(silent=True) or {}
            msg.update(_fields_for(msg["kind"] if msg["kind"] == "link" else "text", {**data, "url": data.get("url")}))
            msg["edited_at"] = _now()
    return jsonify({"ok": True})


@bp.route("/api/chat/message/<int:mid>/<action>", methods=["POST"])
@_api
def chat_message_transfer(mid, action):
    if action not in ("copy", "move"):
        raise ChatError("Unknown action", 404)
    data = request.get_json(silent=True) or {}
    with _txn() as state:
        msg = _message(state, mid)
        if msg["opening"]:
            raise ChatError("Opening posts travel with their thread. Move or copy the whole thread.")
        dest = _thread(state, int(data.get("to_thread") or 0))
        _open_thread(dest)
        if dest["id"] == msg["thread_id"]:
            raise ChatError("Pick a different thread")
        if action == "move":
            _author_only(msg)
            msg["thread_id"] = dest["id"]
            _touch(dest)
        else:
            state["messages"].append({**msg, "id": _new_id(state), "thread_id": dest["id"], "created_at": _now()})
            _touch(dest)
    return jsonify({"ok": True})


@bp.route("/api/chat/thread/<int:tid>", methods=["PATCH", "DELETE"])
@_api
def chat_thread(tid):
    with _txn() as state:
        thread = _thread(state, tid)
        _author_only(thread)
        if request.method == "PATCH":
            data = request.get_json(silent=True) or {}
            thread["title"] = _clean(data.get("title"), MAX_TITLE, "Heading")
        else:
            doomed = {tid} | {t["id"] for t in state["threads"] if t["root_id"] == tid}
            state["threads"] = [t for t in state["threads"] if t["id"] not in doomed]
            state["messages"] = [m for m in state["messages"] if m["thread_id"] not in doomed]
    return jsonify({"ok": True})


@bp.route("/api/chat/thread/<int:tid>/<action>", methods=["POST"])
@_api
def chat_thread_transfer(tid, action):
    """copy/move a topic or branch to become a branch under another topic."""
    if action not in ("copy", "move"):
        raise ChatError("Unknown action", 404)
    data = request.get_json(silent=True) or {}
    with _txn() as state:
        thread = _thread(state, tid)
        target = _topic_target(state, int(data.get("to_topic") or 0))
        if target["id"] == tid or target["id"] == thread["root_id"]:
            raise ChatError("Pick a different topic")
        _open_thread(target)
        if action == "copy":
            _copy_thread(state, thread, target["id"])
        else:
            _author_only(thread)
            # a moved topic brings its own branches along as siblings under the new topic
            for child in [t for t in state["threads"] if t["root_id"] == tid]:
                child["root_id"] = target["id"]
            thread["root_id"] = target["id"]
            thread["forked_at"] = _now()
        _touch(target)
    return jsonify({"ok": True})


@bp.route("/api/chat/thread/<int:tid>/close", methods=["POST"])
@_api
def chat_close(tid):
    data = request.get_json(silent=True) or {}
    with _txn() as state:
        thread = _thread(state, tid)
        thread["closed"] = bool(data.get("closed", True))
    return jsonify({"ok": True})
