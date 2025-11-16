from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.config.config import logger
import json
from app.services.series_vis_data import build_v1_datasets


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
        raise HTTPException(status_code=500, detail="Failed to load episodes")


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
        raise HTTPException(status_code=500, detail="Failed to load character arcs")

