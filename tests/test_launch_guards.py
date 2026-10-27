import app as A


def test_rate_limiter_blocks_after_limit():
    key = "test-key-rl"
    assert not any(A._rate_limited("t", key, 3, 60) for _ in range(3))
    assert A._rate_limited("t", key, 3, 60)


def test_login_rate_limited():
    c = A.app.test_client()
    codes = [c.post("/api/login", json={"username": "nobody-rl", "password": "x"}).status_code for _ in range(12)]
    assert codes[-1] == 429


def test_404_pages():
    c = A.app.test_client()
    assert c.get("/definitely-not-a-page").status_code == 404
    assert c.get("/api/definitely-not-a-route").is_json


def test_sitemap_and_robots():
    c = A.app.test_client()
    assert b"/learn/beginner/stocks" in c.get("/sitemap.xml").data
    assert b"Sitemap:" in c.get("/robots.txt").data


def test_yf_history_cache_collapses_calls(monkeypatch):
    import pandas as pd
    calls = []

    def fake(ticker, **kw):
        calls.append(kw)
        return pd.DataFrame({"Close": [1.0]}, index=pd.to_datetime(["2024-01-02"]))

    monkeypatch.setattr(A, "_yf_history_with_retry", fake)
    A._ohlcv_cache.clear()
    for _ in range(3):
        A._fetch_yf_history_cached(None, "ZZTEST", "6mo", "1d")
        A._fetch_yf_history_cached(None, "ZZTEST", "6mo", "1d", start="2024-01-01", end="2024-06-01")
    assert len(calls) == 2


def test_backtest_busy_cap(monkeypatch):
    c = A.app.test_client()
    monkeypatch.setattr(A, "MAX_CONCURRENT_BACKTESTS", 0)
    r = c.get("/api/backtest?symbol=AAPL")
    assert r.status_code == 429 and r.get_json()["busy"]


def test_backtest_slots_released(monkeypatch):
    c = A.app.test_client()
    monkeypatch.setattr(A, "_backtest_impl", lambda: ("ok", 200))
    for _ in range(5):
        assert c.get("/api/backtest?symbol=AAPL").status_code == 200
    assert A._backtest_active == {"total": 0}


def test_save_users_writes_only_changed_rows(monkeypatch):
    writes = []

    class FakeCur:
        def execute(self, sql, params=None):
            writes.append(params[0])
        def __enter__(self): return self
        def __exit__(self, *a): return False

    class FakeConn:
        def cursor(self, **kw): return FakeCur()
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(A, "DATABASE_URL", "postgres://x")
    monkeypatch.setattr(A, "_db_conn", lambda: FakeConn())
    u = A._UserDict({"a": {"password_hash": "h", "tier": "free"}, "b": {"password_hash": "h2", "tier": "free"}})
    u._snapshot = {k: A._user_fingerprint(v) for k, v in u.items()}
    u["b"]["tier"] = "pro"
    A._save_users(u)
    assert writes == ["b"]


def test_pooled_conn_commits_and_returns(monkeypatch):
    events = []

    class FakeConn:
        closed = 0
        def commit(self): events.append("commit")
        def rollback(self): events.append("rollback")
        def cursor(self):
            class Cur:
                def __enter__(s): return s
                def __exit__(s, *a): return False
                def execute(s, q): pass
            return Cur()

    class FakePool:
        def __init__(self): self.c = FakeConn()
        def getconn(self): return self.c
        def putconn(self, conn, close=False): events.append(("put", close))

    pool = FakePool()
    monkeypatch.setattr(A, "_db_pool", pool)
    A._db_last_used.clear()
    with A._db_conn() as conn:
        assert conn is pool.c
    assert events == ["rollback", "commit", ("put", False)]  # rollback = idle ping
    events.clear()
    try:
        with A._db_conn():
            raise ValueError
    except ValueError:
        pass
    assert events == ["rollback", ("put", False)]
