"""Admin Planner: Gary's GCG to-do list and Google Calendar view.

Only the dedicated GCG calendar (its ID is set in the UI) is read or written, never the
personal calendar. Tasks with a due date get an all-day entry on it; entries added
directly in Google show up in the to-do list too.

Owner-only (PLANNER_OWNERS, default "garybyatt,admin"), not every admin. Google
access is plain OAuth 2.0 over `requests`: the refresh token is stored in the
planner document, scoped to calendar events only. Set GOOGLE_CLIENT_ID and
GOOGLE_CLIENT_SECRET; the redirect URI to register in Google Cloud is
{PUBLIC_BASE_URL}/api/planner/google/callback (override with GOOGLE_REDIRECT_URI).
"""
import datetime as _dt
import os
import secrets
import time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from urllib.parse import quote, urlencode

import requests
from flask import Blueprint, jsonify, redirect, request, session
from flask_login import current_user

from docstore import DocStore

bp = Blueprint("gcg_planner", __name__)

SCOPE = "https://www.googleapis.com/auth/calendar.events"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CAL_BASE = "https://www.googleapis.com/calendar/v3/calendars"
DEFAULT_TZ = "Europe/London"

store = DocStore("gcg_planner", lambda: {"next_id": 1, "todos": [], "google": {}, "calendar_id": "", "done_events": []})
_token_cache = {"token": "", "exp": 0.0}


def init(db_conn, database_url: str) -> None:
    store.init(db_conn, database_url)


def _owners() -> set:
    return {u.strip() for u in os.environ.get("PLANNER_OWNERS", "garybyatt,admin").split(",") if u.strip()}


def _denied():
    if not (current_user.is_authenticated and current_user.id in _owners()):
        return jsonify({"error": "Not allowed"}), 403
    return None


def _client():
    return os.environ.get("GOOGLE_CLIENT_ID", ""), os.environ.get("GOOGLE_CLIENT_SECRET", "")


def _redirect_uri() -> str:
    base = os.environ.get("PUBLIC_BASE_URL", "https://www.growthcapitalgroup.co").rstrip("/")
    return os.environ.get("GOOGLE_REDIRECT_URI", f"{base}/api/planner/google/callback")


def _access_token() -> str:
    """A valid access token from the stored refresh token, or "" if not connected."""
    if _token_cache["token"] and _token_cache["exp"] > time.time() + 60:
        return _token_cache["token"]
    refresh = store.read()["google"].get("refresh_token")
    cid, secret = _client()
    if not (refresh and cid and secret):
        return ""
    r = requests.post(TOKEN_URL, data={"client_id": cid, "client_secret": secret,
                                       "refresh_token": refresh, "grant_type": "refresh_token"}, timeout=15)
    if r.status_code != 200:
        # Revoked or expired grant: drop it so the UI offers Connect again.
        if r.json().get("error") == "invalid_grant":
            with store.txn() as doc:
                doc["google"] = {}
        return ""
    data = r.json()
    _token_cache.update(token=data["access_token"], exp=time.time() + data.get("expires_in", 3600))
    return _token_cache["token"]


@bp.before_request
def _guard():
    # The OAuth callback is a browser redirect from Google, but still needs the owner's session.
    return _denied()


@bp.route("/api/planner/state", methods=["GET"])
def state():
    doc = store.read()
    cid, secret = _client()
    g = doc["google"]
    return jsonify({"todos": doc["todos"], "done_events": doc.get("done_events", []),
                    "google": {"configured": bool(cid and secret), "connected": bool(g.get("refresh_token")),
                               "email": g.get("email", ""), "redirect_uri": _redirect_uri(),
                               "calendar_id": doc.get("calendar_id", "")}})


@bp.route("/api/planner/calendar-id", methods=["POST"])
def set_calendar_id():
    cal = ((request.get_json(silent=True) or {}).get("id") or "").strip()[:200]
    with store.txn() as doc:
        doc["calendar_id"] = cal
    return jsonify({"ok": True})


def _events_url(event_id: str = "") -> str:
    cal = store.read().get("calendar_id", "")
    return f"{CAL_BASE}/{quote(cal, safe='')}/events" + (f"/{quote(event_id, safe='')}" if event_id else "")


def _calendar_ready():
    """(auth headers, None) when the GCG calendar is usable, else (None, error response)."""
    if not store.read().get("calendar_id"):
        return None, (jsonify({"error": "Set the GCG calendar ID first"}), 400)
    token = _access_token()
    if not token:
        return None, (jsonify({"error": "Google Calendar not connected"}), 400)
    return {"Authorization": f"Bearer {token}"}, None


def _push_todo(todo: dict) -> str:
    """Create/update/remove the all-day GCG calendar entry for a task. Returns its event id ("" if none)."""
    headers, err = _calendar_ready()
    if err:
        return todo.get("event_id", "")
    event_id = todo.get("event_id", "")
    if not todo.get("due"):
        if event_id:
            requests.delete(_events_url(event_id), headers=headers, timeout=15)
        return ""
    day = _dt.date.fromisoformat(todo["due"])
    payload = {"summary": ("✓ " if todo["done"] else "") + todo["text"],
               "start": {"date": todo["due"]}, "end": {"date": (day + _dt.timedelta(days=1)).isoformat()}}
    if event_id:
        r = requests.patch(_events_url(event_id), headers=headers, json=payload, timeout=15)
        if r.status_code != 404:
            return event_id
    r = requests.post(_events_url(), headers=headers, json=payload, timeout=15)
    return r.json().get("id", "") if r.status_code == 200 else ""


def _valid_due(due: str) -> str:
    try:
        return _dt.date.fromisoformat(due).isoformat() if due else ""
    except ValueError:
        return ""


@bp.route("/api/planner/todos", methods=["POST"])
def add_todo():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()[:300]
    if not text:
        return jsonify({"error": "Task text required"}), 400
    with store.txn() as doc:
        todo = {"id": doc["next_id"], "text": text, "due": _valid_due((body.get("due") or "").strip()), "done": False}
        doc["next_id"] += 1
        doc["todos"].append(todo)
    if todo["due"]:
        todo["event_id"] = _push_todo(todo)
        with store.txn() as doc:
            next(t for t in doc["todos"] if t["id"] == todo["id"])["event_id"] = todo["event_id"]
    return jsonify(todo)


@bp.route("/api/planner/todos/<int:tid>", methods=["PATCH", "DELETE"])
def change_todo(tid):
    body = request.get_json(silent=True) or {}
    with store.txn() as doc:
        todo = next((t for t in doc["todos"] if t["id"] == tid), None)
        if not todo:
            return jsonify({"error": "Not found"}), 404
        if request.method == "DELETE":
            doc["todos"].remove(todo)
        else:
            if "done" in body:
                todo["done"] = bool(body["done"])
            if "text" in body and str(body["text"]).strip():
                todo["text"] = str(body["text"]).strip()[:300]
            if "due" in body:
                todo["due"] = _valid_due(str(body["due"] or "").strip())
        snapshot = dict(todo)
    try:
        if request.method == "DELETE":
            snapshot["due"] = ""  # removes the calendar entry
        event_id = _push_todo(snapshot)
    except Exception as e:
        print(f"[planner calendar sync failed] {e}")
        event_id = snapshot.get("event_id", "")
    if request.method == "PATCH":
        with store.txn() as doc:
            t = next((t for t in doc["todos"] if t["id"] == tid), None)
            if t:
                t["event_id"] = event_id
                snapshot = dict(t)
    return jsonify({"ok": True} if request.method == "DELETE" else snapshot)


@bp.route("/api/planner/events/<event_id>/done", methods=["POST"])
def mark_event_done(event_id):
    done = bool((request.get_json(silent=True) or {}).get("done"))
    with store.txn() as doc:
        ids = set(doc.setdefault("done_events", []))
        ids.add(event_id) if done else ids.discard(event_id)
        doc["done_events"] = sorted(ids)[-500:]
    return jsonify({"ok": True})


@bp.route("/api/planner/google/connect", methods=["GET"])
def google_connect():
    cid, secret = _client()
    if not (cid and secret):
        return jsonify({"error": "GOOGLE_CLIENT_ID / GOOGLE_CLIENT_SECRET not set"}), 400
    session["planner_oauth_state"] = state_token = secrets.token_urlsafe(24)
    return redirect(AUTH_URL + "?" + urlencode({
        "client_id": cid, "redirect_uri": _redirect_uri(), "response_type": "code", "scope": SCOPE + " email",
        "access_type": "offline", "prompt": "consent", "state": state_token}))


@bp.route("/api/planner/google/callback", methods=["GET"])
def google_callback():
    if request.args.get("state") != session.pop("planner_oauth_state", None) or not request.args.get("code"):
        return redirect("/admin#planner")
    cid, secret = _client()
    r = requests.post(TOKEN_URL, data={"code": request.args["code"], "client_id": cid, "client_secret": secret,
                                       "redirect_uri": _redirect_uri(), "grant_type": "authorization_code"}, timeout=15)
    if r.status_code == 200 and r.json().get("refresh_token"):
        data = r.json()
        email = ""
        try:
            info = requests.get("https://www.googleapis.com/oauth2/v3/userinfo",
                                headers={"Authorization": f"Bearer {data['access_token']}"}, timeout=10)
            email = info.json().get("email", "")
        except Exception:
            pass
        with store.txn() as doc:
            doc["google"] = {"refresh_token": data["refresh_token"], "email": email}
        _token_cache.update(token=data["access_token"], exp=time.time() + data.get("expires_in", 3600))
    return redirect("/admin#planner")


@bp.route("/api/planner/google/disconnect", methods=["POST"])
def google_disconnect():
    token = store.read()["google"].get("refresh_token")
    if token:
        try:
            requests.post("https://oauth2.googleapis.com/revoke", data={"token": token}, timeout=10)
        except Exception:
            pass
    with store.txn() as doc:
        doc["google"] = {}
    _token_cache.update(token="", exp=0.0)
    return jsonify({"ok": True})


@bp.route("/api/planner/events", methods=["GET"])
def list_events():
    headers, err = _calendar_ready()
    if err:
        return err
    days = min(max(request.args.get("days", 30, type=int), 1), 120)
    now = _dt.datetime.now(_dt.timezone.utc)
    r = requests.get(_events_url(), headers=headers, timeout=15, params={
        "timeMin": now.isoformat(), "timeMax": (now + _dt.timedelta(days=days)).isoformat(),
        "singleEvents": "true", "orderBy": "startTime", "maxResults": 100})
    if r.status_code != 200:
        return jsonify({"error": "Google Calendar request failed (check the calendar ID)"}), 502
    doc = store.read()
    linked = {t["event_id"] for t in doc["todos"] if t.get("event_id")}
    events = [{"id": e["id"], "title": e.get("summary", "(no title)"), "start": e["start"].get("dateTime") or e["start"].get("date"),
               "all_day": "date" in e["start"], "link": e.get("htmlLink", ""), "linked": e["id"] in linked}
              for e in r.json().get("items", [])]
    return jsonify({"events": events})


@bp.route("/api/planner/events", methods=["POST"])
def create_event():
    headers, err = _calendar_ready()
    if err:
        return err
    body = request.get_json(silent=True) or {}
    title, date, time_ = (body.get("title") or "").strip()[:200], body.get("date") or "", body.get("time") or ""
    try:
        day = _dt.date.fromisoformat(date)
        if time_:
            start = _dt.datetime.combine(day, _dt.time.fromisoformat(time_))
    except ValueError:
        return jsonify({"error": "Valid date (and time) required"}), 400
    if not title:
        return jsonify({"error": "Title required"}), 400
    try:
        tz = str(ZoneInfo(body.get("tz") or DEFAULT_TZ))  # times are entered in the browser's own zone
    except (ZoneInfoNotFoundError, ValueError):
        tz = DEFAULT_TZ
    if time_:
        mins = min(max(int(body.get("minutes") or 30), 5), 1440)
        end = start + _dt.timedelta(minutes=mins)
        payload = {"start": {"dateTime": start.isoformat(), "timeZone": tz},
                   "end": {"dateTime": end.isoformat(), "timeZone": tz}}
    else:
        payload = {"start": {"date": date}, "end": {"date": (day + _dt.timedelta(days=1)).isoformat()}}
    payload["summary"] = title
    if body.get("notes"):
        payload["description"] = str(body["notes"])[:2000]
    r = requests.post(_events_url(), headers=headers, json=payload, timeout=15)
    if r.status_code != 200:
        return jsonify({"error": "Google rejected the event"}), 502
    return jsonify({"ok": True, "link": r.json().get("htmlLink", "")})


@bp.route("/api/planner/events/<event_id>", methods=["DELETE"])
def delete_event(event_id):
    headers, err = _calendar_ready()
    if err:
        return err
    r = requests.delete(_events_url(event_id), headers=headers, timeout=15)
    if r.status_code in (200, 204, 410):
        with store.txn() as doc:
            for t in doc["todos"]:
                if t.get("event_id") == event_id:
                    t["event_id"] = ""
        return jsonify({"ok": True})
    return jsonify({"error": "Delete failed"}), 502
