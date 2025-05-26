from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Literal, Optional
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from app.config.config import logger, K_RESULTS
from app.services import embed
from pathlib import Path
from redis import Redis


router = APIRouter()


class SuccessResponse(BaseModel):
    status: Literal["success"]
    message: str


class SearchResponse(BaseModel):
    status: Literal["success", "error"]
    result: Optional[list]
    message: Optional[str]


@router.get("/", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def root():
    logger.info("Received root request")
    return SuccessResponse(
        status="success", message="This application is a TV Show Q&A engine."
    )


@router.get("/vite", response_class=HTMLResponse)
async def index():
    return FileResponse(Path(__file__).parent.parent.absolute() / "static" / "index.html")

@router.post("/search", response_model=SearchResponse, status_code=status.HTTP_200_OK)
async def search(request: Request, k: Optional[int] = None):
    try:
        body_as_json = await request.json()
        search_query = body_as_json.get("query", None)
        if search_query is None:
            logger.error(f"No value for search query submitted: [{search_query}]")
            raise HTTPException(
                status_code=400, detail="Search query parameter is required."
            )
        elif search_query == "":
            logger.info(f"Empty search qeury submitted: [{search_query}]")

            return SearchResponse(
                status="success", result=[], message="Empty query string submitted."
            )
        else:
            results = embed.fetch_search_results(search_query, k or K_RESULTS)

            return SearchResponse(
                status="success", result=results, message="Search successful."
            )

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "data": str(e)}
        )

@router.get("/health", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint to verify the backend is running."""
    logger.info("Health check request received")
    return SuccessResponse(
        status="success",
        message="Backend is healthy"
    )

@router.get("/health/redis", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def redis_health_check():
    """Health check endpoint to verify Redis connection."""
    try:
        # Test Redis connection
        client = Redis(host='localhost', port=6379, db=0)
        client.ping()
        logger.info("Redis health check successful")
        return SuccessResponse(
            status="success",
            message="Redis connection is healthy"
        )
    except Exception as e:
        logger.error(f"Redis health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Redis connection failed: {str(e)}"
        )

@router.get("/health/model", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def model_health_check():
    """Health check endpoint to verify the embedding model is loaded."""
    try:
        # Test model by encoding a simple string
        from app.services.embed import embedder
        embedder.encode("test")
        logger.info("Model health check successful")
        return SuccessResponse(
            status="success",
            message="Embedding model is healthy"
        )
    except Exception as e:
        logger.error(f"Model health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Model check failed: {str(e)}"
        )
