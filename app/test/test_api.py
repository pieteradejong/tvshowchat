from fastapi.testclient import TestClient
from app.api.api import router

client = TestClient(router)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "This application is a TV Show Q&A engine.",
    }


def test_search():
    response = client.post(
        "/search",
        json={"query": "What do Buffy and Giles say to each other?"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert isinstance(response.json()["result"], list)


def test_search_empty_query():
    response = client.post(
        "/search",
        json={"query": ""},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["result"] == []
    assert response.json()["message"] == "Empty query string submitted."
