"""Admin Planner: Gary's personal to-do list and Google Calendar view.

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
from urllib.parse import urlencode

import requests
from flask import Blueprint, jsonify, redirect, request, session
from flask_login import current_user

from docstore import DocStore

bp = Blueprint("gcg_planner", __name__)

SCOPE = "https://www.googleapis.com/auth/calendar.events"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
CAL_URL = "https://www.googleapis.com/calendar/v3/calendars/primary/events"
DEFAULT_TZ = "Europe/London"

store = DocStore("gcg_planner", lambda: {"next_id": 1, "todos": [], "google": {}})
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
    return jsonify({"todos": doc["todos"],
                    "google": {"configured": bool(cid and secret), "connected": bool(g.get("refresh_token")),
                               "email": g.get("email", ""), "redirect_uri": _redirect_uri()}})


@bp.route("/api/planner/todos", methods=["POST"])
def add_todo():
    body = request.get_json(silent=True) or {}
    text = (body.get("text") or "").strip()[:300]
    if not text:
        return jsonify({"error": "Task text required"}), 400
    due = (body.get("due") or "").strip()
    with store.txn() as doc:
        todo = {"id": doc["next_id"], "text": text, "due": due, "done": False}
        doc["next_id"] += 1
        doc["todos"].append(todo)
    return jsonify(todo)


@bp.route("/api/planner/todos/<int:tid>", methods=["PATCH", "DELETE"])
def change_todo(tid):
    with store.txn() as doc:
        todo = next((t for t in doc["todos"] if t["id"] == tid), None)
        if not todo:
            return jsonify({"error": "Not found"}), 404
        if request.method == "DELETE":
            doc["todos"].remove(todo)
            return jsonify({"ok": True})
        body = request.get_json(silent=True) or {}
        if "done" in body:
            todo["done"] = bool(body["done"])
        if "text" in body and str(body["text"]).strip():
            todo["text"] = str(body["text"]).strip()[:300]
        if "due" in body:
            todo["due"] = str(body["due"] or "").strip()
        return jsonify(todo)


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


def _headers():
    token = _access_token()
    return {"Authorization": f"Bearer {token}"} if token else None


@bp.route("/api/planner/events", methods=["GET"])
def list_events():
    headers = _headers()
    if not headers:
        return jsonify({"error": "Google Calendar not connected"}), 400
    days = min(max(request.args.get("days", 30, type=int), 1), 120)
    now = _dt.datetime.now(_dt.timezone.utc)
    r = requests.get(CAL_URL, headers=headers, timeout=15, params={
        "timeMin": now.isoformat(), "timeMax": (now + _dt.timedelta(days=days)).isoformat(),
        "singleEvents": "true", "orderBy": "startTime", "maxResults": 100})
    if r.status_code != 200:
        return jsonify({"error": "Google Calendar request failed"}), 502
    events = [{"id": e["id"], "title": e.get("summary", "(no title)"), "start": e["start"].get("dateTime") or e["start"].get("date"),
               "all_day": "date" in e["start"], "link": e.get("htmlLink", "")} for e in r.json().get("items", [])]
    return jsonify({"events": events})


@bp.route("/api/planner/events", methods=["POST"])
def create_event():
    headers = _headers()
    if not headers:
        return jsonify({"error": "Google Calendar not connected"}), 400
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
    r = requests.post(CAL_URL, headers=headers, json=payload, timeout=15)
    if r.status_code != 200:
        return jsonify({"error": "Google rejected the event"}), 502
    return jsonify({"ok": True, "link": r.json().get("htmlLink", "")})


@bp.route("/api/planner/events/<event_id>", methods=["DELETE"])
def delete_event(event_id):
    headers = _headers()
    if not headers:
        return jsonify({"error": "Google Calendar not connected"}), 400
    r = requests.delete(f"{CAL_URL}/{event_id}", headers=headers, timeout=15)
    return (jsonify({"ok": True}) if r.status_code in (200, 204, 410) else (jsonify({"error": "Delete failed"}), 502))
