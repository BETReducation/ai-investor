"""Admin Finances: cost evidence uploads, income, profit levels, ratios, budget + votes.

Ledger state is one JSON document (see docstore). Receipt files live outside it —
a Postgres BYTEA table, or a local folder without DATABASE_URL — so the ledger
row stays small. Amounts are integer pence.

Income is meant to fill itself from the shopping cart: point the cart's webhook at
POST /api/finance/income-webhook with the FINANCE_WEBHOOK_SECRET header and each
sale lands in the ledger (deduped on its reference). Manual entries stay possible.
"""
import datetime as _dt
import hmac
import os
import re
import uuid
from decimal import Decimal, InvalidOperation

from flask import Blueprint, Response, jsonify, request
from flask_login import current_user, login_required

from docstore import DocStore

bp = Blueprint("gcg_finance", __name__)

COST_TYPES = {
    "cost_of_sales": "Cost of sales",
    "operating": "Operating expense",
    "finance": "Interest & finance",
    "tax": "Tax",
}
BALANCE_FIELDS = ["cash", "receivables", "inventory", "other_current_assets", "fixed_assets",
                  "current_liabilities", "long_term_liabilities"]
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_EVIDENCE = 2
ALLOWED_EXT = {"pdf", "png", "jpg", "jpeg", "webp", "heic", "csv", "xlsx", "txt"}
DEFAULT_BIG_THRESHOLD = 50000  # pence: spend at/above this goes to a partner vote

_is_admin = lambda user: False
_load_users = dict
_db_conn = None
_use_db = False
FILES_DIR = os.path.join(os.path.dirname(__file__), "finance_files")


def _empty() -> dict:
    return {"next_id": 1, "costs": [], "income": [], "balance": {}, "budget": {"total": 0, "period": "", "notes": ""},
            "proposals": [], "big_threshold": DEFAULT_BIG_THRESHOLD}


store = DocStore("gcg_finance", _empty)


def init(db_conn, database_url: str, is_admin, load_users) -> None:
    global _is_admin, _db_conn, _use_db, _load_users
    _is_admin, _db_conn, _use_db, _load_users = is_admin, db_conn, bool(database_url), load_users
    store.init(db_conn, database_url)
    if _use_db:
        with db_conn() as conn, conn.cursor() as cur:
            cur.execute("CREATE TABLE IF NOT EXISTS finance_files (id TEXT PRIMARY KEY, name TEXT NOT NULL, "
                        "mime TEXT NOT NULL, data BYTEA NOT NULL)")


class FinError(Exception):
    def __init__(self, msg, code=400):
        super().__init__(msg)
        self.code = code


@bp.errorhandler(FinError)
def _fin_error(e):
    return jsonify({"error": str(e)}), e.code


def _admin_required():
    if not (current_user.is_authenticated and _is_admin(current_user)):
        raise FinError("Admin only", 403)


def _now() -> str:
    return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _pence(raw, label="Amount", allow_zero=False) -> int:
    try:
        p = int((Decimal(str(raw).replace(",", "").replace("£", "").strip()) * 100).to_integral_value())
    except (InvalidOperation, ValueError):
        raise FinError(f"{label} must be a number")
    if p < 0 or (p == 0 and not allow_zero):
        raise FinError(f"{label} must be greater than zero")
    return p


def _date(raw) -> str:
    try:
        return _dt.date.fromisoformat((raw or "").strip()).isoformat()
    except ValueError:
        raise FinError("Date must be YYYY-MM-DD")


def _text(raw, limit, label, required=True) -> str:
    v = (raw or "").strip()
    if required and not v:
        raise FinError(f"{label} is required")
    if len(v) > limit:
        raise FinError(f"{label} is too long (max {limit})")
    return v


def _new_id(doc) -> int:
    n = doc["next_id"]
    doc["next_id"] = n + 1
    return n


# ---- receipt files -------------------------------------------------------------

def _save_file(f) -> dict:
    name = os.path.basename(f.filename or "file")
    ext = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if ext not in ALLOWED_EXT:
        raise FinError(f"File type .{ext or '?'} not allowed (use {', '.join(sorted(ALLOWED_EXT))})")
    data = f.read()
    if not data:
        raise FinError("Empty file")
    if len(data) > MAX_FILE_BYTES:
        raise FinError("File is over 5 MB")
    fid = uuid.uuid4().hex
    mime = f.mimetype or "application/octet-stream"
    if _use_db:
        with _db_conn() as conn, conn.cursor() as cur:
            cur.execute("INSERT INTO finance_files (id, name, mime, data) VALUES (%s, %s, %s, %s)",
                        (fid, name, mime, data))
    else:
        os.makedirs(FILES_DIR, exist_ok=True)
        with open(os.path.join(FILES_DIR, fid), "wb") as out:
            out.write(data)
        with open(os.path.join(FILES_DIR, fid + ".meta"), "w") as out:
            out.write(f"{name}\n{mime}")
    return {"file_id": fid, "file_name": name}


def _load_file(fid):
    if not re.fullmatch(r"[0-9a-f]{32}", fid):
        return None
    if _use_db:
        with _db_conn() as conn, conn.cursor() as cur:
            cur.execute("SELECT name, mime, data FROM finance_files WHERE id = %s", (fid,))
            row = cur.fetchone()
        return (row[0], row[1], bytes(row[2])) if row else None
    path = os.path.join(FILES_DIR, fid)
    if not os.path.exists(path):
        return None
    name, mime = open(path + ".meta").read().split("\n", 1)
    return name, mime, open(path, "rb").read()


def _delete_file(fid) -> None:
    if not fid:
        return
    if _use_db:
        with _db_conn() as conn, conn.cursor() as cur:
            cur.execute("DELETE FROM finance_files WHERE id = %s", (fid,))
    else:
        for p in (os.path.join(FILES_DIR, fid), os.path.join(FILES_DIR, fid + ".meta")):
            if os.path.exists(p):
                os.remove(p)


@bp.route("/api/admin/finance/file/<fid>")
@login_required
def finance_file(fid):
    _admin_required()
    found = _load_file(fid)
    if not found:
        raise FinError("File not found", 404)
    name, mime, data = found
    safe = re.sub(r'[^\w.\- ]', "_", name)
    return Response(data, mimetype=mime, headers={"Content-Disposition": f'inline; filename="{safe}"'})


# ---- costs ---------------------------------------------------------------------

def _cost_files(c) -> list:
    """Evidence list; entries saved before two-file support carry a single file_id."""
    return c.get("files") or ([{"file_id": c["file_id"], "file_name": c["file_name"]}] if c.get("file_id") else [])


def _uploads() -> list:
    return [f for f in request.files.getlist("file") if f and f.filename]


def _cost_fields(form) -> dict:
    kind = form.get("type", "operating")
    if kind not in COST_TYPES:
        raise FinError("Unknown cost type")
    paid = _date(form.get("date"))
    return {"date": paid, "invoice_date": _date(form["invoice_date"]) if form.get("invoice_date") else paid,
            "supplier": _text(form.get("supplier"), 120, "Supplier"),
            "description": _text(form.get("description"), 300, "Description", required=False),
            "type": kind, "amount": _pence(form.get("amount"))}


@bp.route("/api/admin/finance/costs", methods=["GET"])
@login_required
def list_costs():
    _admin_required()
    costs = [dict(c, files=_cost_files(c)) for c in store.read()["costs"]]
    return jsonify({"costs": sorted(costs, key=lambda c: (c["date"], c["id"]), reverse=True), "types": COST_TYPES})


@bp.route("/api/admin/finance/costs", methods=["POST"])
@login_required
def add_cost():
    _admin_required()
    entry = _cost_fields(request.form)
    uploads = _uploads()
    if not uploads:
        raise FinError("Evidence file is required (receipt or invoice)")
    if len(uploads) > MAX_EVIDENCE:
        raise FinError(f"At most {MAX_EVIDENCE} evidence files")
    entry.update(added_by=current_user.id, at=_now(), files=[_save_file(f) for f in uploads])
    with store.txn() as doc:
        entry["id"] = _new_id(doc)
        doc["costs"].append(entry)
    return jsonify({"cost": entry})


@bp.route("/api/admin/finance/costs/<int:cid>", methods=["PUT"])
@login_required
def edit_cost(cid):
    _admin_required()
    fields = _cost_fields(request.form)
    drop = set(request.form.getlist("remove"))
    uploads = _uploads()
    with store.txn() as doc:
        c = next((x for x in doc["costs"] if x["id"] == cid), None)
        if not c:
            raise FinError("Cost not found", 404)
        kept = [f for f in _cost_files(c) if f["file_id"] not in drop]
        if not kept and not uploads:
            raise FinError("Keep or upload at least one evidence file")
        if len(kept) + len(uploads) > MAX_EVIDENCE:
            raise FinError(f"At most {MAX_EVIDENCE} evidence files")
        removed = [f for f in _cost_files(c) if f["file_id"] in drop]
        c.update(fields, files=kept + [_save_file(f) for f in uploads], edited_by=current_user.id, edited_at=_now())
        c.pop("file_id", None)
        c.pop("file_name", None)
    for f in removed:
        _delete_file(f["file_id"])
    return jsonify({"success": True})


@bp.route("/api/admin/finance/costs/<int:cid>", methods=["DELETE"])
@login_required
def delete_cost(cid):
    _admin_required()
    with store.txn() as doc:
        match = next((c for c in doc["costs"] if c["id"] == cid), None)
        if not match:
            raise FinError("Cost not found", 404)
        doc["costs"].remove(match)
    for f in _cost_files(match):
        _delete_file(f["file_id"])
    return jsonify({"success": True})


# ---- income --------------------------------------------------------------------

@bp.route("/api/admin/finance/income", methods=["GET"])
@login_required
def list_income():
    _admin_required()
    return jsonify({"income": sorted(store.read()["income"], key=lambda i: (i["date"], i["id"]), reverse=True)})


@bp.route("/api/admin/finance/income", methods=["POST"])
@login_required
def add_income():
    _admin_required()
    data = request.get_json() or {}
    entry = {"date": _date(data.get("date")), "description": _text(data.get("description"), 300, "Description"),
             "amount": _pence(data.get("amount")), "source": "manual", "ref": "",
             "added_by": current_user.id, "at": _now()}
    with store.txn() as doc:
        entry["id"] = _new_id(doc)
        doc["income"].append(entry)
    return jsonify({"income": entry})


@bp.route("/api/admin/finance/income/<int:iid>", methods=["DELETE"])
@login_required
def delete_income(iid):
    _admin_required()
    with store.txn() as doc:
        match = next((i for i in doc["income"] if i["id"] == iid), None)
        if not match:
            raise FinError("Income entry not found", 404)
        doc["income"].remove(match)
    return jsonify({"success": True})


@bp.route("/api/finance/income-webhook", methods=["POST"])
def income_webhook():
    """Cart sale -> income row. Body: {amount, description?, date?, ref}; ref dedupes retries."""
    secret = os.environ.get("FINANCE_WEBHOOK_SECRET", "")
    if not secret or not hmac.compare_digest(request.headers.get("X-Webhook-Secret", ""), secret):
        return jsonify({"error": "Unauthorized"}), 401
    data = request.get_json() or {}
    ref = _text(str(data.get("ref") or ""), 120, "ref")
    with store.txn() as doc:
        if any(i.get("ref") == ref for i in doc["income"]):
            return jsonify({"success": True, "duplicate": True})
        doc["income"].append({"id": _new_id(doc), "date": _date(data.get("date") or _dt.date.today().isoformat()),
                              "description": _text(data.get("description") or "Cart sale", 300, "Description"),
                              "amount": _pence(data.get("amount")), "source": "cart", "ref": ref,
                              "added_by": "cart", "at": _now()})
    return jsonify({"success": True})


# ---- balance sheet inputs, profit, ratios --------------------------------------

@bp.route("/api/admin/finance/balance", methods=["PUT"])
@login_required
def set_balance():
    _admin_required()
    data = request.get_json() or {}
    bal = {k: _pence(data.get(k) or 0, k, allow_zero=True) for k in BALANCE_FIELDS}
    with store.txn() as doc:
        doc["balance"] = bal
    return jsonify({"balance": bal})


def _ratio(num, den):
    return round(num / den, 4) if den else None


def compute_summary(doc, start=None, end=None) -> dict:
    def inside(e):
        return (not start or e["date"] >= start) and (not end or e["date"] <= end)

    revenue = sum(i["amount"] for i in doc["income"] if inside(i))
    by_type = {k: 0 for k in COST_TYPES}
    for c in doc["costs"]:
        if inside(c):
            by_type[c["type"]] += c["amount"]
    gross = revenue - by_type["cost_of_sales"]
    operating = gross - by_type["operating"]
    npbt = operating - by_type["finance"]
    npat = npbt - by_type["tax"]

    b = {k: doc["balance"].get(k, 0) for k in BALANCE_FIELDS}
    current_assets = b["cash"] + b["receivables"] + b["inventory"] + b["other_current_assets"]
    total_assets = current_assets + b["fixed_assets"]
    total_liabilities = b["current_liabilities"] + b["long_term_liabilities"]
    equity = total_assets - total_liabilities
    have_balance = bool(doc["balance"])
    ratios = {
        "gross_margin": _ratio(gross, revenue),
        "operating_margin": _ratio(operating, revenue),
        "net_margin": _ratio(npat, revenue),
        "cost_to_income": _ratio(sum(by_type.values()), revenue),
        "current_ratio": _ratio(current_assets, b["current_liabilities"]) if have_balance else None,
        "quick_ratio": _ratio(current_assets - b["inventory"], b["current_liabilities"]) if have_balance else None,
        "cash_ratio": _ratio(b["cash"], b["current_liabilities"]) if have_balance else None,
        "debt_to_equity": _ratio(total_liabilities, equity) if have_balance and equity > 0 else None,
        "return_on_assets": _ratio(npat, total_assets) if have_balance else None,
        "return_on_equity": _ratio(npat, equity) if have_balance and equity > 0 else None,
    }
    return {"revenue": revenue, "costs_by_type": by_type, "gross": gross, "operating": operating, "npbt": npbt,
            "npat": npat, "ratios": ratios, "balance": doc["balance"],
            "working_capital": current_assets - b["current_liabilities"] if have_balance else None}


@bp.route("/api/admin/finance/summary", methods=["GET"])
@login_required
def summary():
    _admin_required()
    start = request.args.get("from") or None
    end = request.args.get("to") or None
    return jsonify(compute_summary(store.read(), start, end))


# ---- budget + votes ------------------------------------------------------------
# Partners (alpha_role set) vote on big items; every other signed-in member votes on small ones.

def _voter_group() -> str:
    return "partner" if getattr(current_user, "alpha_role", None) else "member"


def _eligible_voters(group):
    users = _load_users()
    partners = sum(1 for u in users.values() if u.get("alpha_role"))
    return partners if group == "partner" else len(users) - partners


def _proposal_view(p, threshold, me=None, include_voters=False) -> dict:
    group = "partner" if p["amount"] >= threshold else "member"
    tally = {"yes": 0, "no": 0, "abstain": 0}
    for v in p["votes"].values():
        if v["group"] == group:
            tally[v["choice"]] += 1
    out = {k: p[k] for k in ("id", "title", "description", "amount", "status", "created_by", "at")}
    out.update(group=group, tally=tally, eligible=_eligible_voters(group),
               my_vote=(p["votes"].get(me) or {}).get("choice") if me else None,
               can_vote=bool(me) and p["status"] == "open" and _voter_group() == group,
               outcome=p.get("outcome"))
    if include_voters:
        out["votes"] = {u: v for u, v in p["votes"].items() if v["group"] == group}
    return out


@bp.route("/api/admin/finance/budget", methods=["GET"])
@login_required
def get_budget():
    _admin_required()
    doc = store.read()
    spent = sum(p["amount"] for p in doc["proposals"] if p.get("outcome") == "approved")
    committed = sum(p["amount"] for p in doc["proposals"] if p["status"] == "open")
    return jsonify({"budget": doc["budget"], "big_threshold": doc["big_threshold"], "approved": spent,
                    "pending": committed,
                    "proposals": [_proposal_view(p, doc["big_threshold"], current_user.id, True)
                                  for p in sorted(doc["proposals"], key=lambda p: p["id"], reverse=True)]})


@bp.route("/api/admin/finance/budget", methods=["PUT"])
@login_required
def set_budget():
    _admin_required()
    data = request.get_json() or {}
    with store.txn() as doc:
        doc["budget"] = {"total": _pence(data.get("total") or 0, "Budget", allow_zero=True),
                         "period": _text(data.get("period"), 80, "Period", required=False),
                         "notes": _text(data.get("notes"), 1000, "Notes", required=False)}
        if data.get("big_threshold") not in (None, ""):
            doc["big_threshold"] = _pence(data["big_threshold"], "Threshold")
    return jsonify({"success": True})


@bp.route("/api/admin/finance/proposals", methods=["POST"])
@login_required
def add_proposal():
    _admin_required()
    data = request.get_json() or {}
    p = {"title": _text(data.get("title"), 160, "Title"), "description": _text(data.get("description"), 1000, "What it's for", required=False),
         "amount": _pence(data.get("amount")), "status": "open", "votes": {}, "created_by": current_user.id, "at": _now()}
    with store.txn() as doc:
        p["id"] = _new_id(doc)
        doc["proposals"].append(p)
    return jsonify({"success": True})


@bp.route("/api/finance/proposals/<int:pid>/vote", methods=["POST"])
@login_required
def vote(pid):
    choice = (request.get_json() or {}).get("choice")
    if choice not in ("yes", "no", "abstain"):
        raise FinError("choice must be yes, no or abstain")
    with store.txn() as doc:
        p = next((x for x in doc["proposals"] if x["id"] == pid), None)
        if not p:
            raise FinError("Proposal not found", 404)
        group = "partner" if p["amount"] >= doc["big_threshold"] else "member"
        if p["status"] != "open":
            raise FinError("Voting is closed")
        if _voter_group() != group:
            raise FinError(f"This is a {group} vote", 403)
        p["votes"][current_user.id] = {"choice": choice, "group": group, "at": _now()}
    return jsonify({"success": True})


@bp.route("/api/admin/finance/proposals/<int:pid>/close", methods=["POST"])
@login_required
def close_proposal(pid):
    _admin_required()
    with store.txn() as doc:
        p = next((x for x in doc["proposals"] if x["id"] == pid), None)
        if not p:
            raise FinError("Proposal not found", 404)
        group = "partner" if p["amount"] >= doc["big_threshold"] else "member"
        yes = sum(1 for v in p["votes"].values() if v["group"] == group and v["choice"] == "yes")
        no = sum(1 for v in p["votes"].values() if v["group"] == group and v["choice"] == "no")
        p["status"], p["outcome"] = "closed", "approved" if yes > no else "rejected"
    return jsonify({"success": True})


@bp.route("/api/admin/finance/proposals/<int:pid>", methods=["DELETE"])
@login_required
def delete_proposal(pid):
    _admin_required()
    with store.txn() as doc:
        doc["proposals"] = [p for p in doc["proposals"] if p["id"] != pid]
    return jsonify({"success": True})
