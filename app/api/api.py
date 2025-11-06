from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Literal, Optional
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from app.config.config import logger, K_RESULTS
from app.services.vector_store import get_vector_store
from pathlib import Path


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
            # Use the new vector store for search
            vector_store = get_vector_store()
            results = vector_store.search_episodes(search_query, limit=k or K_RESULTS)
            
            # Convert to the expected format
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "episode": f"S{result['season']:02d}E{result['episode']}",
                    "title": result['title'],
                    "airdate": result['airdate'],
                    "summary": result['text'],
                    "score": result['score']
                })

            return SearchResponse(
                status="success", result=formatted_results, message="Search successful."
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

@router.get("/health/model", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def model_health_check():
    """Health check endpoint to verify the embedding model is loaded."""
    try:
        # Test model by encoding a simple string using vector store's embedder
        vector_store = get_vector_store()
        vector_store.embedder.encode("test")
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
