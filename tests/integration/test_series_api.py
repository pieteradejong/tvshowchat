from fastapi.testclient import TestClient
from app.api.main import app


def test_series_endpoints():
    with TestClient(app) as client:
        resp_ep = client.get("/api/series/episodes")
        assert resp_ep.status_code in (200, 404)
        if resp_ep.status_code == 200:
            data = resp_ep.json()
            assert isinstance(data, list)
            if data:
                assert "id" in data[0]
        resp_arcs = client.get("/api/series/character-arcs")
        assert resp_arcs.status_code in (200, 404)
        if resp_arcs.status_code == 200:
            arcs = resp_arcs.json()
            assert isinstance(arcs, dict)

