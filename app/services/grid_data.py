"""
Grid-optimized data layer for series visualization.

This module creates a unified data structure optimized for grid visualization,
aggregating all episode metrics and precomputing grid coordinates.
"""
from pathlib import Path
from typing import Dict, Any, List, Optional
import json
import logging
from collections import defaultdict

logger = logging.getLogger(__name__)

# Episode counts per season
SEASON_EPISODE_COUNTS = {
    1: 12,
    2: 22,
    3: 22,
    4: 22,
    5: 22,
    6: 22,
    7: 22,
}

MAIN_CHARACTERS = [
    "Buffy", "Willow", "Xander", "Giles", "Angel", "Spike", "Cordelia",
    "Oz", "Anya", "Faith", "Dawn", "Tara", "Riley", "Joyce",
]


def _episode_id(season: int, episode: int) -> str:
    """Generate episode ID in format sXXeYY."""
    return f"s{season:02d}e{episode:02d}"


def build_grid_episodes_dataset(
    episodes_path: Path = Path("app/data/episodes/episodes.json"),
    arcs_path: Path = Path("app/data/episodes/character_arcs.json"),
    quotes_path: Path = Path("app/data/episodes/quotes.json"),
    moments_path: Optional[Path] = None,
    output_dir: Path = Path("app/data/episodes"),
) -> Path:
    """
    Build a grid-optimized episode dataset with all metrics precomputed.
    
    Output structure:
    {
        "episodes": {
            "s01e01": {
                "id": "s01e01",
                "season": 1,
                "episode": 1,
                "title": "...",
                "airdate": "...",
                "logline": "...",
                "themes": [...],
                "grid_position": {"row": 0, "col": 0},
                "metrics": {
                    "quote_count": 5,
                    "character_presence": {
                        "Buffy": 10,
                        "Willow": 5,
                        ...
                    },
                    "death_count": 0,
                    "body_count": 0,
                    "character_moments": {
                        "first_appearances": [],
                        "deaths": [],
                        ...
                    }
                },
                "production": {
                    "director": "...",
                    "writer": "...",
                    ...
                }
            },
            ...
        },
        "metadata": {
            "total_episodes": 144,
            "season_counts": {1: 12, 2: 22, ...},
            "max_episodes_per_season": 22,
            "grid_dimensions": {"rows": 7, "cols": 22}
        }
    }
    """
    # Load base data
    if not episodes_path.exists():
        raise FileNotFoundError(f"Episodes file not found: {episodes_path}")
    
    with episodes_path.open("r", encoding="utf-8") as f:
        episodes = json.load(f)
    
    # Load character arcs
    character_arcs: Dict[str, List[Dict]] = {}
    if arcs_path.exists():
        with arcs_path.open("r", encoding="utf-8") as f:
            character_arcs = json.load(f)
    
    # Load quotes
    quotes_by_episode: Dict[str, int] = defaultdict(int)
    if quotes_path.exists():
        with quotes_path.open("r", encoding="utf-8") as f:
            quotes_data = json.load(f)
            for quote in quotes_data.get("quotes", []):
                episode_id = quote.get("episode_id", "")
                if episode_id:
                    quotes_by_episode[episode_id] += 1
    
    # Load character moments
    moments_by_episode: Dict[str, Dict[str, List[str]]] = defaultdict(lambda: {
        "first_appearances": [],
        "last_appearances": [],
        "deaths": [],
    })
    if moments_path and moments_path.exists():
        with moments_path.open("r", encoding="utf-8") as f:
            moments_data = json.load(f)
            for moment in moments_data.get("moments", []):
                episode_id = moment.get("episode_id", "")
                moment_type = moment.get("type", "")
                character = moment.get("character", "")
                if episode_id and character and moment_type:
                    if moment_type == "first_appearance":
                        moments_by_episode[episode_id]["first_appearances"].append(character)
                    elif moment_type == "last_appearance":
                        moments_by_episode[episode_id]["last_appearances"].append(character)
                    elif moment_type == "death":
                        moments_by_episode[episode_id]["deaths"].append(character)
    
    # Build character presence map
    character_presence_by_episode: Dict[str, Dict[str, int]] = defaultdict(dict)
    for character, arc_points in character_arcs.items():
        for point in arc_points:
            episode_id = point.get("episode_id", "")
            presence_score = point.get("presence_score", 0)
            if episode_id and presence_score > 0:
                character_presence_by_episode[episode_id][character] = presence_score
    
    # Build grid episodes
    grid_episodes: Dict[str, Dict[str, Any]] = {}
    
    for ep in episodes:
        episode_id = ep.get("id", "")
        if not episode_id:
            continue
        
        season = ep.get("season", 0)
        episode_num = ep.get("episode", 0)
        
        # Compute grid position
        grid_row = season - 1  # 0-indexed
        grid_col = episode_num - 1  # 0-indexed
        
        # Build metrics
        metrics: Dict[str, Any] = {
            "quote_count": quotes_by_episode.get(episode_id, 0),
            "character_presence": character_presence_by_episode.get(episode_id, {}),
            "character_moments": moments_by_episode.get(episode_id, {
                "first_appearances": [],
                "last_appearances": [],
                "deaths": [],
            }),
        }
        
        # Build episode data
        grid_episodes[episode_id] = {
            "id": episode_id,
            "season": season,
            "episode": episode_num,
            "title": ep.get("title", ""),
            "airdate": ep.get("airdate", ""),
            "logline": ep.get("logline", ""),
            "themes": ep.get("themes", []),
            "grid_position": {
                "row": grid_row,
                "col": grid_col,
            },
            "metrics": metrics,
        }
    
    # Build metadata
    metadata = {
        "total_episodes": len(grid_episodes),
        "season_counts": SEASON_EPISODE_COUNTS,
        "max_episodes_per_season": max(SEASON_EPISODE_COUNTS.values()),
        "grid_dimensions": {
            "rows": len(SEASON_EPISODE_COUNTS),
            "cols": max(SEASON_EPISODE_COUNTS.values()),
        },
    }
    
    # Write output
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "grid_episodes.json"
    
    output_data = {
        "episodes": grid_episodes,
        "metadata": metadata,
    }
    
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Built grid episodes dataset: {len(grid_episodes)} episodes")
    return output_path

