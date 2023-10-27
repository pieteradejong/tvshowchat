from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Literal
import redis
from fastapi.responses import JSONResponse
from app.config import logger

router = APIRouter()


class SuccessResponse(BaseModel):
    status: Literal["success"]
    message: str


class SearchResponse(BaseModel):
    status: Literal["success"]
    result: list


def get_redis_client():
    client = redis.Redis(host="localhost", port=6379, db=0)
    return client


@router.get("/", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def root():
    logger.info("Received root request")
    return {"status": "success", "message": "This application is a TV Show Q&A engine."}


@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search(request: Request):
    try:
        body_as_json = await request.json()
        search_query = body_as_json.get("query", None)

        if not search_query:
            raise HTTPException(status_code=400, detail="Invalid or empty query string")

        results = ["result one", "result two", search_query]
        return {"status": "success", "result": results}

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "data": str(e)}
        )
