import json
import re
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from app.services.vector_store import get_vector_store
from app.config.config import logger
from pathlib import Path

# --- Data Loading ---
ROOT_DIR = Path(__file__).resolve().parents[3]
CONTENT_FILE = ROOT_DIR / "app/content/btvs_all_seasons.json"

# Removed unused DATA loading - saves memory at startup
# Data is accessed through vector_store when needed


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
    snippets: List[str] = Field(default_factory=list)
    score: float
    characters: List[str]
    themes: List[str]
    context: str

class SearchResponse(BaseModel):
    results: List[SearchResult]

# --- Router ---
router = APIRouter()
vector_store = get_vector_store()

@router.post("/search")
async def search_episodes(query: SearchQuery) -> List[SearchResult]:
    """Search episodes using advanced semantic search."""
    try:
        # Enhance query for memory-friendly searches
        enhanced_query = _enhance_memory_query(query.query)
        
        results = vector_store.search_episodes(
            query=enhanced_query,
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


def _enhance_memory_query(query: str) -> str:
    """
    Enhance query for memory-friendly searches.
    Expands common memory patterns like "episode where X" or "that episode with Y".
    """
    query_lower = query.lower().strip()
    
    # Pattern: "episode where X happens" -> extract X and search for it
    if "episode where" in query_lower or "episode in which" in query_lower:
        # Remove the "episode where" part and search for the actual content
        query = re.sub(r"episode\s+(where|in\s+which)\s+", "", query, flags=re.IGNORECASE)
    
    # Pattern: "that episode with X" -> search for X
    if "that episode with" in query_lower or "episode with" in query_lower:
        query = re.sub(r"(that\s+)?episode\s+with\s+", "", query, flags=re.IGNORECASE)
    
    # Pattern: "musical episode" -> add theme keywords
    if "musical" in query_lower:
        query = f"{query} singing song music"
    
    # Pattern: "first appearance" or "first time" -> add character context
    if "first appearance" in query_lower or "first time" in query_lower:
        # Keep original query but it will match first_appearances data
        pass
    
    return query

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

        expected_counts = content_summary["season_counts"]
        expected_total = content_summary["total_episodes"]

        vector_counts_raw = stats.get("season_counts", {})
        embedding_counts_raw = stats.get("embedding_counts", {})

        def normalize_counts(source: Dict[int, int], label: str) -> Dict[int, int]:
            normalized: Dict[int, int] = {}
            for key, value in source.items():
                try:
                    season_num = int(key)
                except (TypeError, ValueError):
                    logger.warning("Skipping invalid season key '%s' in %s", key, label)
                    continue
                normalized[season_num] = int(value)
            return normalized

        vector_counts = normalize_counts(vector_counts_raw, "vector store stats")
        embedding_counts = normalize_counts(embedding_counts_raw, "embedding stats")

        def validate_counts(label: str, counts: Dict[int, int]):
            missing = sorted(set(expected_counts.keys()) - set(counts.keys()))
            if missing:
                raise HTTPException(
                    status_code=500,
                    detail=f"{label} missing seasons: {missing}",
                )
            for season, expected in expected_counts.items():
                actual = counts.get(season)
                if actual != expected:
                    raise HTTPException(
                        status_code=500,
                        detail=(
                            f"{label} mismatch for season {season}: "
                            f"expected {expected}, found {actual}"
                        ),
                    )

        validate_counts("Vector store season counts", vector_counts)
        validate_counts("Embedding season counts", embedding_counts)

        vector_total = stats["total_episodes"]
        chroma_total = stats.get("chromadb_episodes", 0)
        embedding_total = stats.get("embedding_total", sum(embedding_counts.values()))

        if vector_total != expected_total:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Vector store total mismatch: expected {expected_total}, "
                    f"found {vector_total}"
                ),
            )

        if embedding_total != expected_total:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"Embedding total mismatch: expected {expected_total}, "
                    f"found {embedding_total}"
                ),
            )

        if chroma_total != expected_total:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"ChromaDB total mismatch: expected {expected_total}, "
                    f"found {chroma_total}"
                ),
            )

        # Get a sample episode
        sample_episode = None
        if vector_total > 0:
            sample_episode = vector_store.get_episode(1, "01")

        # Test a simple search
        test_query = "Buffy fights vampires"
        search_results = vector_store.search_episodes(test_query, limit=1)

        return {
            "status": "healthy",
            "expected_total_episodes": expected_total,
            "content": {
                "total_episodes": content_summary["total_episodes"],
                "season_counts": expected_counts,
            },
            "vector_store": {
                "total_episodes": vector_total,
                "seasons": stats["seasons"],
                "season_counts": vector_counts,
                "embedding_counts": embedding_counts,
                "collection_name": stats["collection_name"],
                "model": stats["embedding_model"],
                "chromadb_episodes": chroma_total,
            },
            "sample_episode": {
                "season": sample_episode.get("season_number") if sample_episode else None,
                "episode": sample_episode.get("episode_number") if sample_episode else None,
                "title": sample_episode.get("title") if sample_episode else None,
                "has_summary": bool(sample_episode.get("summary")) if sample_episode else False,
            }
            if sample_episode
            else None,
            "test_search": {
                "query": test_query,
                "results_count": len(search_results),
                "first_result": search_results[0] if search_results else None,
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"System test failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"System test failed: {str(e)}"
        )