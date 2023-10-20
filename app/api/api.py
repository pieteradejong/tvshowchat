from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Literal
import redis

router = APIRouter()


class SuccessResponse(BaseModel):
    status: Literal["success"]
    message: str


def get_redis_client():
    client = redis.Redis(host="localhost", port=6379, db=0)
    return client


@router.get("/", response_model=SuccessResponse, status_code=200)
def root():
    return {"status": "success", "message": "This application is a TV Show Q&A engine."}


@router.get("/fetch/{key}", response_model=SuccessResponse, status_code=200)
def fetch_key(key: str, redis_client: redis.Redis = Depends(get_redis_client)):
    value = redis_client.get(key)
    if value is None:
        return {"status": "failure", "message": f"No value found for key: {key}"}
    return {"status": "success", "message": f"Value for key {key}: {value.decode()}"}
