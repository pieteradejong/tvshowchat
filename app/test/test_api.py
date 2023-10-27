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
        json={"query": "What is the name of the main character in Breaking Bad?"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert isinstance(response.json()["result"], list)
