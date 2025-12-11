from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.config.config import logger
from app.services.storage.document_store import get_store
from app.services.embedding_service import EmbeddingService
import json
import numpy as np
from collections import defaultdict, Counter
from typing import Dict, List, Tuple

router = APIRouter()

ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = ROOT / "app" / "data" / "episodes"
EMBEDDINGS_DIR = ROOT / "app" / "data" / "embeddings"


@router.get("/experiments/character-relationships")
async def get_character_relationships():
    """Compute character co-appearance network."""
    try:
        # Use character arcs data which we already have
        arcs_path = DATA_DIR / "character_arcs.json"
        episodes_path = DATA_DIR / "episodes.json"
        
        if not arcs_path.exists() or not episodes_path.exists():
            raise HTTPException(status_code=404, detail="Character arcs data not found")
        
        with open(arcs_path, 'r') as f:
            arcs = json.load(f)
        with open(episodes_path, 'r') as f:
            episodes = json.load(f)
        
        # Build episode map
        episode_map = {ep["id"]: ep for ep in episodes}
        
        # Build co-appearance matrix
        character_pairs = defaultdict(int)
        character_episodes = defaultdict(set)
        main_characters = ["Buffy", "Willow", "Xander", "Giles", "Angel", "Spike", "Cordelia", "Oz", "Tara", "Anya", "Dawn", "Faith", "Riley", "Joyce"]
        
        # For each episode, find which characters appear (presence_score > 0)
        for char_name, char_data in arcs.items():
            if char_name not in main_characters:
                continue
            for ep_data in char_data:
                if ep_data.get("presence_score", 0) > 0:
                    character_episodes[char_name].add(ep_data["episode_id"])
        
        # Build pairs: characters that appear together in episodes
        for ep_id in episode_map.keys():
            chars_in_ep = [
                char for char, char_data in arcs.items()
                if char in main_characters and any(d["episode_id"] == ep_id and d.get("presence_score", 0) > 5 for d in char_data)
            ]
            for i, char1 in enumerate(chars_in_ep):
                for char2 in chars_in_ep[i+1:]:
                    pair = tuple(sorted([char1, char2]))
                    character_pairs[pair] += 1
        
        # Convert to network format
        nodes = []
        node_set = set()
        for char, episodes in character_episodes.items():
            if len(episodes) >= 3:  # Only characters in 3+ episodes
                nodes.append({
                    "id": char,
                    "name": char,
                    "episode_count": len(episodes),
                    "size": min(50, len(episodes) * 2)
                })
                node_set.add(char)
        
        links = []
        for (char1, char2), count in character_pairs.items():
            if char1 in node_set and char2 in node_set and count >= 2:
                links.append({
                    "source": char1,
                    "target": char2,
                    "value": count,
                    "strength": min(1.0, count / 20.0)
                })
        
        return {"nodes": nodes, "links": links}
    except Exception as e:
        logger.error(f"Failed to compute character relationships: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/theme-cooccurrence")
async def get_theme_cooccurrence():
    """Compute theme co-occurrence matrix."""
    try:
        episodes_path = DATA_DIR / "episodes.json"
        if not episodes_path.exists():
            raise HTTPException(status_code=404, detail="Episodes data not found")
        
        with open(episodes_path, 'r') as f:
            episodes = json.load(f)
        
        theme_episodes = defaultdict(set)
        theme_pairs = defaultdict(int)
        all_themes = set()
        
        for episode in episodes:
            themes = episode.get("themes", [])
            if not themes:
                continue
            
            # Normalize themes
            themes = [t.lower().strip() for t in themes if t and len(t) > 2]  # Filter very short themes
            all_themes.update(themes)
            
            for theme in themes:
                theme_episodes[theme].add(episode["id"])
            
            # Count pairs
            for i, t1 in enumerate(themes):
                for t2 in themes[i+1:]:
                    pair = tuple(sorted([t1, t2]))
                    theme_pairs[pair] += 1
        
        # Filter to top themes
        top_themes = sorted(theme_episodes.items(), key=lambda x: len(x[1]), reverse=True)[:30]
        theme_list = [t[0] for t in top_themes]
        
        # Build matrix
        matrix = []
        for t1 in theme_list:
            row = []
            for t2 in theme_list:
                if t1 == t2:
                    row.append(len(theme_episodes[t1]))
                else:
                    pair = tuple(sorted([t1, t2]))
                    row.append(theme_pairs.get(pair, 0))
            matrix.append(row)
        
        # Build network links
        links = []
        for (t1, t2), count in theme_pairs.items():
            if t1 in theme_list and t2 in theme_list and count >= 3:
                links.append({
                    "source": t1,
                    "target": t2,
                    "value": count
                })
        
        return {
            "themes": theme_list,
            "matrix": matrix,
            "links": links,
            "episode_counts": {t: len(theme_episodes[t]) for t in theme_list}
        }
    except Exception as e:
        logger.error(f"Failed to compute theme co-occurrence: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/episode-similarity")
async def get_episode_similarity():
    """Compute episode similarity using embeddings."""
    try:
        embedding_service = EmbeddingService()
        store = get_store()
        episodes_dir = store.episodes_path
        
        episodes = []
        embeddings_list = []
        
        for season_file in sorted(episodes_dir.glob("season_*.json")):
            if season_file.name == "season_stats.json":
                continue
            try:
                season_num = int(season_file.stem.split('_')[1])
            except (ValueError, IndexError):
                continue
            with open(season_file, 'r') as f:
                season_data = json.load(f)
            
            for episode_num, episode in season_data.items():
                ep_id = f"s{season_num:02d}e{int(episode_num):02d}"
                emb = embedding_service.get_episode_embedding(season_num, episode_num)
                
                if emb is not None:
                    episodes.append({
                        "id": ep_id,
                        "season": season_num,
                        "episode": int(episode_num),
                        "title": episode.get("title", ""),
                    })
                    embeddings_list.append(emb)
        
        if len(embeddings_list) < 2:
            return {"episodes": [], "similarities": []}
        
        # Compute pairwise similarities
        embeddings_array = np.array(embeddings_list)
        similarities = []
        
        # Use cosine similarity
        norms = np.linalg.norm(embeddings_array, axis=1, keepdims=True)
        normalized = embeddings_array / (norms + 1e-8)
        similarity_matrix = np.dot(normalized, normalized.T)
        
        # Extract upper triangle (avoid duplicates)
        for i in range(len(episodes)):
            for j in range(i+1, len(episodes)):
                sim = float(similarity_matrix[i][j])
                if sim > 0.5:  # Only strong similarities
                    similarities.append({
                        "source": episodes[i]["id"],
                        "target": episodes[j]["id"],
                        "similarity": sim
                    })
        
        return {
            "episodes": episodes,
            "similarities": similarities
        }
    except Exception as e:
        logger.error(f"Failed to compute episode similarity: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/character-journey")
async def get_character_journey():
    """Compute character journey across seasons (Sankey data)."""
    try:
        arcs_path = DATA_DIR / "character_arcs.json"
        if not arcs_path.exists():
            raise HTTPException(status_code=404, detail="Character arcs data not found")
        
        with open(arcs_path, 'r') as f:
            arcs = json.load(f)
        
        # Character presence by season
        character_seasons = defaultdict(lambda: defaultdict(int))
        main_chars = ["Buffy", "Willow", "Xander", "Giles", "Angel", "Spike", "Cordelia", "Oz", "Tara", "Anya", "Dawn", "Faith", "Riley", "Joyce"]
        
        for char_name, char_data in arcs.items():
            if char_name not in main_chars:
                continue
            for ep_data in char_data:
                if ep_data.get("presence_score", 0) > 5:  # Only significant presence
                    ep_id = ep_data["episode_id"]
                    # Parse season from episode_id (e.g., "s02e14" -> 2)
                    season = int(ep_id[1:3])
                    character_seasons[char_name][season] += 1
        
        # Build nodes (seasons + characters)
        nodes = []
        node_map = {}
        idx = 0
        
        # Season nodes
        for s in range(1, 8):
            node_id = f"season_{s}"
            nodes.append({"id": node_id, "name": f"Season {s}", "type": "season"})
            node_map[node_id] = idx
            idx += 1
        
        # Character nodes
        main_chars = ["Buffy", "Willow", "Xander", "Giles", "Angel", "Spike", "Cordelia", "Oz", "Tara", "Anya", "Dawn", "Faith"]
        for char in main_chars:
            if char in character_seasons:
                node_id = f"char_{char}"
                total_episodes = sum(character_seasons[char].values())
                nodes.append({
                    "id": node_id,
                    "name": char,
                    "type": "character",
                    "total_episodes": total_episodes
                })
                node_map[node_id] = idx
                idx += 1
        
        # Build links (character -> season flows)
        links = []
        for char in main_chars:
            if char not in character_seasons:
                continue
            char_node = f"char_{char}"
            if char_node not in node_map:
                continue
            
            for season, count in character_seasons[char].items():
                season_node = f"season_{season}"
                if season_node in node_map and count > 0:
                    links.append({
                        "source": node_map[char_node],
                        "target": node_map[season_node],
                        "value": count
                    })
        
        return {"nodes": nodes, "links": links}
    except Exception as e:
        logger.error(f"Failed to compute character journey: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments/temporal-arcs")
async def get_temporal_arcs():
    """Get temporal arc data (characters, themes, sentiment over time)."""
    try:
        # Load episodes and character arcs
        episodes_path = DATA_DIR / "episodes.json"
        arcs_path = DATA_DIR / "character_arcs.json"
        
        if not episodes_path.exists() or not arcs_path.exists():
            raise HTTPException(status_code=404, detail="Data files not found")
        
        with open(episodes_path, 'r') as f:
            episodes = json.load(f)
        with open(arcs_path, 'r') as f:
            arcs = json.load(f)
        
        # Build timeline data
        timeline = []
        for ep in episodes:
            timeline.append({
                "id": ep["id"],
                "season": ep["season"],
                "episode": ep["episode"],
                "title": ep["title"],
                "themes": ep.get("themes", []),
                "characters": {}
            })
            
            # Add character presence
            for char, char_data in arcs.items():
                ep_data = next((d for d in char_data if d["episode_id"] == ep["id"]), None)
                if ep_data:
                    timeline[-1]["characters"][char] = ep_data["presence_score"]
        
        return {"timeline": timeline}
    except Exception as e:
        logger.error(f"Failed to get temporal arcs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

