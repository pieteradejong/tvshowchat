from pathlib import Path
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from app.config.config import logger
import json
from typing import Optional
from app.services.series_vis_data import build_v1_datasets, build_quotes_dataset, build_character_moments_dataset, build_season_stats
from app.services.grid_data import build_grid_episodes_dataset


router = APIRouter()

# __file__ is app/api/routes/series.py
# parents[0]=.../routes, [1]=.../api, [2]=.../app, [3]=project root
ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "app" / "data" / "episodes"


@router.get("/series/episodes")
async def get_series_episodes():
    """Return compact episode list for visualization."""
    try:
        episodes_path = DATA_DIR / "episodes.json"
        if not episodes_path.exists():
            logger.warning("episodes.json not found at %s; building datasets...", episodes_path)
            # Attempt to build on-demand
            build_v1_datasets(
                episodes_dir=DATA_DIR,
                output_dir=DATA_DIR,
            )
            if not episodes_path.exists():
                raise HTTPException(status_code=404, detail="episodes.json not found")
        with episodes_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load episodes.json: {e}")
        raise HTTPException(status_code=500, detail="Failed to load episodes") from e


@router.get("/series/character-arcs")
async def get_character_arcs():
    """Return character arcs time series."""
    try:
        arcs_path = DATA_DIR / "character_arcs.json"
        if not arcs_path.exists():
            logger.warning("character_arcs.json not found at %s; building datasets...", arcs_path)
            # Attempt to build on-demand
            build_v1_datasets(
                episodes_dir=DATA_DIR,
                output_dir=DATA_DIR,
            )
            if not arcs_path.exists():
                raise HTTPException(status_code=404, detail="character_arcs.json not found")
        with arcs_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load character_arcs.json: {e}")
        raise HTTPException(status_code=500, detail="Failed to load character arcs") from e


@router.get("/reminiscence/quotes")
async def get_quotes(
    character: Optional[str] = Query(None, description="Filter by character name"),
    season: Optional[int] = Query(None, description="Filter by season number"),
    search: Optional[str] = Query(None, description="Search text in quotes"),
):
    """Return quotes with optional filters for character, season, and text search."""
    try:
        quotes_path = DATA_DIR / "quotes.json"
        if not quotes_path.exists():
            logger.warning("quotes.json not found at %s; building dataset...", quotes_path)
            build_quotes_dataset()
            if not quotes_path.exists():
                raise HTTPException(status_code=404, detail="quotes.json not found")
        
        with quotes_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        quotes = data.get("quotes", [])
        
        # Apply filters
        if character:
            character_quote_ids = set(data.get("by_character", {}).get(character, []))
            quotes = [q for q in quotes if q["id"] in character_quote_ids]
        
        if season:
            season_quote_ids = set(data.get("by_season", {}).get(str(season), []))
            quotes = [q for q in quotes if q["id"] in season_quote_ids]
        
        if search:
            search_lower = search.lower()
            quotes = [q for q in quotes if search_lower in q["text"].lower()]
        
        return JSONResponse(content={"quotes": quotes, "total": len(quotes)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load quotes: {e}")
        raise HTTPException(status_code=500, detail="Failed to load quotes") from e


@router.get("/reminiscence/character-moments")
async def get_character_moments(
    character: Optional[str] = Query(None, description="Filter by character name"),
):
    """Return character moments (first appearances, last appearances, deaths)."""
    try:
        moments_path = DATA_DIR / "character_moments.json"
        if not moments_path.exists():
            logger.warning("character_moments.json not found at %s; building dataset...", moments_path)
            build_character_moments_dataset()
            if not moments_path.exists():
                raise HTTPException(status_code=404, detail="character_moments.json not found")
        
        with moments_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        moments = data.get("moments", [])
        
        # Apply character filter
        if character:
            character_moment_ids = set(data.get("by_character", {}).get(character, []))
            moments = [m for m in moments if m["id"] in character_moment_ids]
        
        return JSONResponse(content={"moments": moments, "total": len(moments)})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load character moments: {e}")
        raise HTTPException(status_code=500, detail="Failed to load character moments") from e


@router.get("/reminiscence/season-comparison")
async def get_season_comparison():
    """Return season comparison statistics."""
    try:
        stats_path = DATA_DIR / "season_stats.json"
        if not stats_path.exists():
            logger.warning("season_stats.json not found at %s; building dataset...", stats_path)
            build_season_stats()
            if not stats_path.exists():
                raise HTTPException(status_code=404, detail="season_stats.json not found")
        
        with stats_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load season stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to load season stats") from e


@router.get("/grid/quotes-density")
async def get_quotes_density():
    """Return quote counts per episode for grid visualization."""
    try:
        quotes_path = DATA_DIR / "quotes.json"
        if not quotes_path.exists():
            logger.warning("quotes.json not found at %s; building dataset...", quotes_path)
            build_quotes_dataset()
            if not quotes_path.exists():
                raise HTTPException(status_code=404, detail="quotes.json not found")
        
        with quotes_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        quotes = data.get("quotes", [])
        
        # Aggregate quote counts by episode_id
        quote_counts: dict[str, int] = {}
        for quote in quotes:
            episode_id = quote.get("episode_id", "")
            quote_counts[episode_id] = quote_counts.get(episode_id, 0) + 1
        
        return JSONResponse(content=quote_counts)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load quotes density: {e}")
        raise HTTPException(status_code=500, detail="Failed to load quotes density") from e


@router.get("/grid/episodes")
async def get_grid_episodes():
    """Return grid-optimized episode data with all metrics precomputed."""
    try:
        grid_path = DATA_DIR / "grid_episodes.json"
        if not grid_path.exists():
            logger.warning("grid_episodes.json not found at %s; building dataset...", grid_path)
            # Ensure prerequisite datasets exist
            episodes_path = DATA_DIR / "episodes.json"
            arcs_path = DATA_DIR / "character_arcs.json"
            quotes_path = DATA_DIR / "quotes.json"
            moments_path = DATA_DIR / "character_moments.json"
            
            if not episodes_path.exists() or not arcs_path.exists():
                build_v1_datasets(episodes_dir=DATA_DIR, output_dir=DATA_DIR)
            if not quotes_path.exists():
                build_quotes_dataset()
            if not moments_path.exists():
                build_character_moments_dataset()
            
            # Build grid dataset
            build_grid_episodes_dataset(
                episodes_path=episodes_path,
                arcs_path=arcs_path,
                quotes_path=quotes_path,
                moments_path=moments_path if moments_path.exists() else None,
                output_dir=DATA_DIR,
            )
            
            if not grid_path.exists():
                raise HTTPException(status_code=404, detail="grid_episodes.json not found")
        
        with grid_path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to load grid episodes: {e}")
        raise HTTPException(status_code=500, detail="Failed to load grid episodes") from e

