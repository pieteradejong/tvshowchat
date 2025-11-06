from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Literal
from fastapi.responses import HTMLResponse, FileResponse
from app.config.config import logger
from app.services.vector_store import get_vector_store
from pathlib import Path


router = APIRouter()


class SuccessResponse(BaseModel):
    status: Literal["success"]
    message: str


@router.get("/", response_model=SuccessResponse, status_code=status.HTTP_200_OK)
async def root():
    logger.info("Received root request")
    return SuccessResponse(
        status="success", message="This application is a TV Show Q&A engine."
    )


@router.get("/vite", response_class=HTMLResponse)
async def index():
    return FileResponse(Path(__file__).parent.parent.absolute() / "static" / "index.html")

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
