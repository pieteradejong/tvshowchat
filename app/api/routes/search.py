import os
import glob
import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Optional
from app.services.storage.document_store import get_store
from app.config.config import logger
from redis import Redis

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
class SearchRequest(BaseModel):
    query: str
    top_k: int = 3

class SearchResult(BaseModel):
    season_number: int
    episode_number: str
    title: str
    airdate: str
    summary: List[str]
    score: float
    synopsis: Optional[List[str]] = None
    quotes: Optional[List[str]] = None
    trivia: Optional[List[str]] = None

class SearchResponse(BaseModel):
    results: List[SearchResult]

# --- Cosine Similarity ---
def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))

# --- Router ---
router = APIRouter()

@router.post("/search", response_model=SearchResponse)
def search_episodes(req: SearchRequest):
    try:
        store = get_store()
        results = store.search_episodes(req.query, limit=req.top_k)
        
        # Convert results to response format
        search_results = []
        for result in results:
            episode_data = result['data']
            search_results.append(SearchResult(
                season_number=result['season'],
                episode_number=episode_data['episode_number'],
                title=episode_data['title'],
                airdate=episode_data['airdate'],
                summary=episode_data['summary'],
                score=result['score'],
                synopsis=episode_data.get('synopsis'),
                quotes=episode_data.get('quotes'),
                trivia=episode_data.get('trivia')
            ))
        
        return SearchResponse(results=search_results)
        
    except Exception as e:
        logger.error(f"Search failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search operation failed: {str(e)}"
        )

@router.get("/test")
async def test_system():
    """Test endpoint to verify system state."""
    try:
        store = get_store()
        client = Redis(host='localhost', port=6379, db=0)
        
        # Get Redis info
        redis_info = {
            "total_keys": len(client.keys("buffy:*")),
            "sample_keys": client.keys("buffy:*")[:5],  # First 5 keys
            "index_info": client.ft("idx:buffy_vss").info() if client.exists("idx:buffy_vss") else None
        }
        
        # Get document store info
        store_info = {
            "total_seasons": len(list(store.episodes_path.glob("season_*.json"))),
            "total_episodes": sum(1 for _ in store.episodes_path.rglob("*.json")),
            "sample_episode": None
        }
        
        # Get a sample episode
        for season_file in store.episodes_path.glob("season_*.json"):
            with open(season_file, 'r') as f:
                season_data = json.load(f)
                if season_data:
                    first_episode = next(iter(season_data.values()))
                    store_info["sample_episode"] = {
                        "season": season_file.stem.split('_')[1],
                        "episode": first_episode.get("episode_number"),
                        "title": first_episode.get("episode_title"),
                        "has_synopsis": bool(first_episode.get("episode_synopsis")),
                        "has_summary": bool(first_episode.get("episode_summary")),
                        "has_embedding": bool(first_episode.get("summary_embedding"))
                    }
                    break
        
        # Test a simple search
        test_query = "Buffy fights vampires"
        search_results = store.search_episodes(test_query, limit=1)
        
        return {
            "status": "healthy",
            "redis": redis_info,
            "store": store_info,
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

@router.get("/test-search")
async def test_search(query: str = "Buffy fights vampires", limit: int = 3):
    """Test endpoint for simple search queries."""
    try:
        store = get_store()
        results = store.search_episodes(query, limit=limit)
        
        return {
            "query": query,
            "limit": limit,
            "results": results
        }
        
    except Exception as e:
        logger.error(f"Search test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Search test failed: {str(e)}"
        ) 