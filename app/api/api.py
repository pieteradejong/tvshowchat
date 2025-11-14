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


@router.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend React app."""
    static_index = Path(__file__).parent.parent.absolute() / "static" / "index.html"
    if static_index.exists():
        return FileResponse(static_index)
    else:
        # Return a simple HTML response if static files aren't available
        logger.warning("Static files not found, returning fallback HTML")
        return HTMLResponse(content="<html><body><h1>TV Show Chat API</h1><p>Frontend not available. API is running.</p><p>Try <a href='/health'>/health</a> or <a href='/api/search'>/api/search</a></p></body></html>")


@router.get("/vite.svg")
async def vite_svg():
    """Serve the Vite SVG icon."""
    static_dir = Path(__file__).parent.parent.absolute() / "static"
    vite_svg_path = static_dir / "vite.svg"
    if vite_svg_path.exists():
        return FileResponse(vite_svg_path)
    else:
        from fastapi.responses import Response
        return Response(status_code=404, content="Not found")


@router.get("/vite", response_class=HTMLResponse)
async def index():
    """Legacy endpoint - redirects to root."""
    static_index = Path(__file__).parent.parent.absolute() / "static" / "index.html"
    if static_index.exists():
        return FileResponse(static_index)
    else:
        # Return a simple HTML response if static files aren't available
        return HTMLResponse(content="<html><body><h1>TV Show Chat API</h1><p>Static files not available. API is running.</p></body></html>")

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
