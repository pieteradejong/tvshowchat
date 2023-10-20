from fastapi.testclient import TestClient
from app.api.api import router
import app.api.api as api
import redis

client = TestClient(router)


def test_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "status": "success",
        "message": "This application is a TV Show Q&A engine.",
    }


def test_redis_client_loading():
    redis_client = api.get_redis_client()
    assert redis_client is not None
    assert isinstance(redis_client, redis.Redis)
