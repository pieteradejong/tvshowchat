import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import Dict, List, Optional
from app.services.vector_store import get_vector_store
from app.config.config import logger
from pathlib import Path

# --- Data Loading ---
ROOT_DIR = Path(__file__).resolve().parents[3]
CONTENT_FILE = ROOT_DIR / "app/content/btvs_all_seasons.json"
MODEL_NAME = "all-MiniLM-L6-v2"

# Find the latest season 1 data file
def get_data_file() -> Path:
    if not CONTENT_FILE.exists():
        raise FileNotFoundError(
            f"No content data found at {CONTENT_FILE.relative_to(ROOT_DIR)}. "
            "Run scripts/crawl.sh to generate btvs_all_seasons.json."
        )
    with CONTENT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    if "season_1" not in data:
        raise FileNotFoundError(
            f"Content file {CONTENT_FILE.relative_to(ROOT_DIR)} does not contain season_1 data."
        )
    return CONTENT_FILE

# Load data and model at startup
DATA_FILE = get_data_file()
with DATA_FILE.open("r", encoding="utf-8") as f:
    DATA = json.load(f).get("season_1", {})

MODEL = SentenceTransformer(MODEL_NAME)


def load_content_metadata() -> Dict[int, int]:
    """Load season counts from the unified content file."""
    with CONTENT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)
    season_counts: Dict[int, int] = {}
    for season_key, episodes in data.items():
        if not season_key.startswith("season_"):
            continue
        try:
            season_num = int(season_key.split("_")[1])
        except (IndexError, ValueError):
            logger.warning("Skipping unrecognized season key in content file: %s", season_key)
            continue
        season_counts[season_num] = len(episodes)
    return season_counts


def get_content_summary() -> Dict[str, Dict[int, int]]:
    season_counts = load_content_metadata()
    total = sum(season_counts.values())
    return {
        "total_episodes": total,
        "season_counts": season_counts,
    }

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
        content_summary = get_content_summary()
        
        # Get a sample episode
        sample_episode = None
        if stats["total_episodes"] > 0:
            sample_episode = vector_store.get_episode(1, "01")
        
        # Test a simple search
        test_query = "Buffy fights vampires"
        search_results = vector_store.search_episodes(test_query, limit=1)
        
        return {
            "status": "healthy",
            "content": {
                "total_episodes": content_summary["total_episodes"],
                "season_counts": content_summary["season_counts"],
            },
            "vector_store": {
                "total_episodes": stats["total_episodes"],
                "seasons": stats["seasons"],
                "collection_name": stats["collection_name"],
                "model": stats["embedding_model"],
                "chromadb_episodes": stats.get("chromadb_episodes", 0)
            },
            "sample_episode": {
                "season": sample_episode.get("season_number") if sample_episode else None,
                "episode": sample_episode.get("episode_number") if sample_episode else None,
                "title": sample_episode.get("title") if sample_episode else None,
                "has_summary": bool(sample_episode.get("summary")) if sample_episode else False
            } if sample_episode else None,
            "test_search": {
                "query": test_query,
                "results_count": len(search_results),
                "first_result": search_results[0] if search_results else None
            }
        }
        
    except Exception as e:
        logger.error(f"System test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"System test failed: {str(e)}"
        ) 