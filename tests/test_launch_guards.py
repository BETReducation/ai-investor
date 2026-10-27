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
