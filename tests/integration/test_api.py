"""The HTTP surface: health, search, input bounds, and what errors reveal."""
import pytest

pytestmark = pytest.mark.model

SECRET = "/very/secret/internal/path.json"


@pytest.mark.parametrize("path", ["/health", "/health/vector-store", "/health/model", "/health/store"])
def test_health_endpoints_are_up(client, path):
    assert client.get(path).status_code == 200


def test_pipeline_is_consistent_at_144(client):
    body = client.get("/health/pipeline").json()
    assert body["status"] == "healthy", body
    assert body["consistency"] == "all_stages_match"
    assert body["stages"]["vector_index"]["indexed_episodes"] == 144


def test_removed_endpoints_say_so(client):
    assert client.get("/health/chromadb").status_code == 410
    assert client.get("/health/redis").status_code == 410


def test_system_self_test(client):
    body = client.get("/api/test").json()
    assert body["status"] == "healthy"
    assert body["vector_store"]["indexed_episodes"] == 144


def test_search_returns_ranked_results(client):
    r = client.post("/api/search", json={"query": "Xander becomes a hyena", "limit": 3})
    assert r.status_code == 200
    results = r.json()
    assert len(results) == 3
    assert results[0]["season"] == 1 and results[0]["episode"] == "06"
    scores = [x["score"] for x in results]
    assert scores == sorted(scores, reverse=True)


def test_season_filter(client):
    r = client.post("/api/search", json={"query": "vampire", "limit": 5, "season": 3})
    assert r.status_code == 200
    assert {x["season"] for x in r.json()} == {3}


@pytest.mark.parametrize("payload", [
    {"query": "x" * 501},
    {"query": "vampire", "limit": 0},
    {"query": "vampire", "limit": 51},
    {"query": "vampire", "limit": None},
    {"query": "vampire", "season": 0},
    {"query": "vampire", "season": 8},
    {"limit": 5},
    {"query": ["not", "a", "string"]},
])
def test_search_rejects_out_of_bounds_input(client, payload):
    assert client.post("/api/search", json=payload).status_code == 422


def test_search_accepts_the_limits(client):
    assert client.post("/api/search", json={"query": "x" * 500, "limit": 50}).status_code == 200


def test_search_error_does_not_leak_internals(client, monkeypatch):
    from app.api.routes import search

    def boom(**_):
        raise RuntimeError(f"cannot open {SECRET}")

    monkeypatch.setattr(search.vector_store, "search_episodes", boom)
    r = client.post("/api/search", json={"query": "vampire"})
    assert r.status_code == 500
    assert SECRET not in r.text
    assert "RuntimeError" not in r.text


def test_series_error_does_not_leak_internals(client, monkeypatch):
    from app.api.routes import series

    def boom(*_, **__):
        raise OSError(f"permission denied: {SECRET}")

    monkeypatch.setattr(series.json, "load", boom)
    for path in ["/api/series/episodes", "/api/grid/episodes"]:
        r = client.get(path)
        assert SECRET not in r.text, path


def test_cors_allows_only_known_origins_without_credentials(client):
    ok = client.options("/api/search", headers={
        "Origin": "http://localhost:5173", "Access-Control-Request-Method": "POST"})
    assert ok.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert "access-control-allow-credentials" not in ok.headers

    evil = client.options("/api/search", headers={
        "Origin": "https://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in evil.headers


@pytest.mark.parametrize("path", ["/api/series/episodes", "/api/series/character-arcs"])
def test_series_endpoints(client, path):
    assert client.get(path).status_code == 200
