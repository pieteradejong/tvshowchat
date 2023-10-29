from fastapi import APIRouter, HTTPException, status, Request
from pydantic import BaseModel
from typing import Literal, Optional
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse
from app.config import logger
from app.services import embed
from app import config
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
async def search(request: Request, k: Optional[int] = config.K_RESULTS):
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
            results = embed.fetch_search_results(search_query, k)

            return SearchResponse(
                status="success", result=results, message="Search successful."
            )

    except Exception as e:
        return JSONResponse(
            status_code=500, content={"status": "error", "data": str(e)}
        )
