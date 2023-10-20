from fastapi.testclient import TestClient
import pytest
from app.api.api import router


client = TestClient(router)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "This application is a TV Show Q&A engine."
    }
