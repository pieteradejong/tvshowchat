import os
import glob
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Optional
from app.services.vector_store import get_vector_store
from app.config.config import logger

# --- Data Loading ---
CONTENT_DIR = "app/content"
MODEL_NAME = "all-MiniLM-L6-v2"

# Find the latest season 1 data file
def get_latest_data_file():
    files = sorted(glob.glob(os.path.join(CONTENT_DIR, "buffy_all_seasons_*.json")), reverse=True)
    for f in files:
        with open(f, "r") as file:
            data = json.load(file)
            if "season_1" in data:
                return f
    raise FileNotFoundError("No season 1 data file found.")

# Load data and model at startup
DATA_FILE = get_latest_data_file()
with open(DATA_FILE, "r") as f:
    DATA = json.load(f)["season_1"]

MODEL = SentenceTransformer(MODEL_NAME)

# --- API Schema ---
class SearchQuery(BaseModel):
    query: str
    limit: Optional[int] = 5
    season: Optional[int] = None

class SearchResult(BaseModel):
    season: int
    episode: str
    title: str
    airdate: str
    content_type: str
    text: str
    score: float
    characters: List[str]
    themes: List[str]
    context: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

# --- Cosine Similarity ---
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# --- Router ---
router = APIRouter()
vector_store = get_vector_store()

@router.post("/search")
async def search_episodes(query: SearchQuery) -> List[SearchResult]:
    """Search episodes using advanced semantic search."""
    try:
        results = vector_store.search_episodes(
            query=query.query,
            limit=query.limit,
            season=query.season
        )
        return [SearchResult(**result) for result in results]
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search failed: {str(e)}"
        )

@router.get("/test-search")
async def test_search(query: str = "Willow uses magic", limit: int = 3) -> dict:
    """Test endpoint for search functionality."""
    try:
        results = vector_store.search_episodes(
            query=query,
            limit=limit
        )
        return {
            "query": query,
            "limit": limit,
            "results": results
        }
    except Exception as e:
        logger.error(f"Test search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Test search failed: {str(e)}"
        )

@router.get("/test")
async def test_system():
    """Test endpoint to verify system state."""
    try:
        # Get vector store stats
        stats = vector_store.get_stats()
        
        # Get a sample episode
        sample_episode = None
        if stats["total_episodes"] > 0:
            sample_episode = vector_store.get_episode(1, "01")
        
        # Test a simple search
        test_query = "Buffy fights vampires"
        search_results = vector_store.search_episodes(test_query, limit=1)
        
        return {
            "status": "healthy",
            "vector_store": {
                "total_episodes": stats["total_episodes"],
                "seasons": stats["seasons"],
                "collection_name": stats["collection_name"],
                "model": stats["embedding_model"]
            },
            "sample_episode": {
                "season": sample_episode["season"] if sample_episode else None,
                "episode": sample_episode["episode"] if sample_episode else None,
                "title": sample_episode["title"] if sample_episode else None,
                "has_text": bool(sample_episode["text"]) if sample_episode else False
            } if sample_episode else None,
            "test_search": {
                "query": test_query,
                "results": search_results
            }
        }
        
    except Exception as e:
        logger.error(f"System test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"System test failed: {str(e)}"
        ) 