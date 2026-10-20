import io

import pytest
from flask import Flask
from flask_login import LoginManager, UserMixin, login_user

import gcg_finance

USERS = {"gary": {"alpha_role": "gary"}, "tom": {"alpha_role": "tom"}, "mem1": {}, "mem2": {}, "mem3": {}}


class U(UserMixin):
    def __init__(self, name):
        self.id, self.alpha_role = name, USERS[name].get("alpha_role")


@pytest.fixture
def client_for(tmp_path, monkeypatch):
    monkeypatch.setattr(gcg_finance.store, "file", str(tmp_path / "fin.json"))
    monkeypatch.setattr(gcg_finance, "FILES_DIR", str(tmp_path / "files"))
    gcg_finance.init(None, "", lambda u: u.id == "gary", lambda: USERS)
    app = Flask(__name__)
    app.secret_key = "x"
    lm = LoginManager(app)
    lm.user_loader(lambda uid: U(uid))
    app.register_blueprint(gcg_finance.bp)

    @app.route("/_login/<name>")
    def _login(name):
        login_user(U(name))
        return "ok"

    def as_(name):
        c = app.test_client()
        c.get(f"/_login/{name}")
        return c
    return as_


def add_cost(c, amount, kind="operating", date="2026-10-01"):
    return c.post("/api/admin/finance/costs", data={
        "date": date, "supplier": "Acme", "type": kind, "amount": amount,
        "file": (io.BytesIO(b"%PDF-1.4"), "inv.pdf")})


def test_costs_require_evidence_and_admin(client_for):
    gary, tom = client_for("gary"), client_for("tom")
    assert tom.get("/api/admin/finance/costs").status_code == 403
    r = gary.post("/api/admin/finance/costs", data={"date": "2026-10-01", "supplier": "A", "amount": "5"})
    assert r.status_code == 400
    r = add_cost(gary, "12.50")
    assert r.status_code == 200
    fid = r.get_json()["cost"]["files"][0]["file_id"]
    assert gary.get(f"/api/admin/finance/file/{fid}").data == b"%PDF-1.4"
    assert tom.get(f"/api/admin/finance/file/{fid}").status_code == 403


def test_profit_levels_and_ratios(client_for):
    gary = client_for("gary")
    gary.post("/api/admin/finance/income", json={"date": "2026-10-02", "description": "Sale", "amount": "1000"})
    add_cost(gary, "200", "cost_of_sales")
    add_cost(gary, "300", "operating")
    add_cost(gary, "50", "finance")
    add_cost(gary, "90", "tax")
    s = gary.get("/api/admin/finance/summary").get_json()
    assert (s["revenue"], s["gross"], s["operating"], s["npbt"], s["npat"]) == (100000, 80000, 50000, 45000, 36000)
    assert s["ratios"]["gross_margin"] == 0.8 and s["ratios"]["current_ratio"] is None
    gary.put("/api/admin/finance/balance", json={"cash": "500", "current_liabilities": "250"})
    assert gary.get("/api/admin/finance/summary").get_json()["ratios"]["current_ratio"] == 2.0
    assert gary.get("/api/admin/finance/summary?from=2027-01-01").get_json()["revenue"] == 0


def test_webhook_dedupes(client_for, monkeypatch):
    monkeypatch.setenv("FINANCE_WEBHOOK_SECRET", "s3")
    c = client_for("tom")
    body = {"amount": "9.99", "ref": "order-1"}
    assert c.post("/api/finance/income-webhook", json=body).status_code == 401
    h = {"X-Webhook-Secret": "s3"}
    c.post("/api/finance/income-webhook", json=body, headers=h)
    assert c.post("/api/finance/income-webhook", json=body, headers=h).get_json()["duplicate"]
    assert len(client_for("gary").get("/api/admin/finance/income").get_json()["income"]) == 1


def test_voting_groups(client_for):
    gary, tom, mem = client_for("gary"), client_for("tom"), client_for("mem1")
    gary.put("/api/admin/finance/budget", json={"total": "1000", "big_threshold": "500"})
    gary.post("/api/admin/finance/proposals", json={"title": "Big", "amount": "600"})
    gary.post("/api/admin/finance/proposals", json={"title": "Small", "amount": "40"})
    assert mem.post("/api/finance/proposals/1/vote", json={"choice": "yes"}).status_code == 403
    assert tom.post("/api/finance/proposals/2/vote", json={"choice": "yes"}).status_code == 403
    assert tom.post("/api/finance/proposals/1/vote", json={"choice": "yes"}).status_code == 200
    assert mem.post("/api/finance/proposals/2/vote", json={"choice": "no"}).status_code == 200
    gary.post("/api/admin/finance/proposals/1/close")
    gary.post("/api/admin/finance/proposals/2/close")
    b = gary.get("/api/admin/finance/budget").get_json()
    out = {p["title"]: p["outcome"] for p in b["proposals"]}
    assert out == {"Big": "approved", "Small": "rejected"} and b["approved"] == 60000


def test_edit_cost_and_two_evidence(client_for):
    gary = client_for("gary")
    pdf = lambda n: (io.BytesIO(b"x"), n)
    base = {"date": "2026-05-24", "supplier": "Railway", "type": "operating", "amount": "3.83"}
    r = gary.post("/api/admin/finance/costs", data=dict(base, file=[pdf("a.pdf"), pdf("b.pdf")]))
    cid = r.get_json()["cost"]["id"]
    assert len(r.get_json()["cost"]["files"]) == 2
    assert gary.post("/api/admin/finance/costs", data=dict(base, file=[pdf("a.pdf"), pdf("b.pdf"), pdf("c.pdf")])).status_code == 400
    # at the cap: a third file is refused, removing one first makes room
    assert gary.put(f"/api/admin/finance/costs/{cid}", data=dict(base, file=pdf("c.pdf")),
                    content_type="multipart/form-data").status_code == 400
    first = gary.get("/api/admin/finance/costs").get_json()["costs"][0]["files"][0]["file_id"]
    r = gary.put(f"/api/admin/finance/costs/{cid}", data=dict(base, amount="4.00", remove=first, file=pdf("c.pdf")),
                 content_type="multipart/form-data")
    assert r.status_code == 200
    c = gary.get("/api/admin/finance/costs").get_json()["costs"][0]
    assert c["amount"] == 400 and [f["file_name"] for f in c["files"]] == ["b.pdf", "c.pdf"]
    # removing everything without a replacement is refused
    ids = [f["file_id"] for f in c["files"]]
    assert gary.put(f"/api/admin/finance/costs/{cid}", data=dict(base, remove=ids),
                    content_type="multipart/form-data").status_code == 400
