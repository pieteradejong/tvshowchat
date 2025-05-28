import json
from pathlib import Path
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime
import shutil
from dataclasses import dataclass, asdict
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

@dataclass
class EpisodeDocument:
    """Represents a single episode's data."""
    # Basic metadata
    season_number: int
    episode_number: str
    title: str
    airdate: str
    
    # Content
    summary: List[str]
    synopsis: Optional[List[str]] = None
    quotes: Optional[List[str]] = None
    trivia: Optional[List[str]] = None
    
    # Production info
    director: Optional[str] = None
    writer: Optional[str] = None
    production_code: Optional[str] = None
    us_viewers_millions: Optional[float] = None
    original_air_date: Optional[str] = None
    filming_location: Optional[str] = None
    network: Optional[str] = None
    running_time: Optional[str] = None
    budget: Optional[int] = None
    
    # Cast & Characters
    main_cast: Optional[List[str]] = None
    guest_stars: Optional[List[str]] = None
    recurring_characters: Optional[List[str]] = None
    first_appearances: Optional[List[str]] = None
    last_appearances: Optional[List[str]] = None
    characters_introduced: Optional[List[str]] = None
    characters_mentioned: Optional[List[str]] = None
    characters_died: Optional[List[str]] = None
    
    # Story elements
    continuity_notes: Optional[List[str]] = None
    cultural_references: Optional[List[str]] = None
    music: Optional[List[str]] = None
    mythology_references: Optional[List[str]] = None
    prophecies: Optional[List[str]] = None
    arc_connections: Optional[List[str]] = None
    
    # Awards and reception
    awards: Optional[List[str]] = None
    death_count: Optional[int] = None
    body_count: Optional[int] = None
    
    # Technical
    summary_embedding: Optional[List[float]] = None
    synopsis_embedding: Optional[List[float]] = None
    quotes_embedding: Optional[List[float]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary, excluding None values."""
        return {k: v for k, v in asdict(self).items() if v is not None}

class BuffyDocumentStore:
    def __init__(self, base_path: str = "app/data"):
        self.base_path = Path(base_path)
        self.episodes_path = self.base_path / "episodes"
        self.embeddings_path = self.base_path / "embeddings"
        self._ensure_dirs()
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")

    def _ensure_dirs(self):
        """Ensure storage directories exist."""
        self.episodes_path.mkdir(parents=True, exist_ok=True)
        self.embeddings_path.mkdir(parents=True, exist_ok=True)

    def _get_season_file(self, season: int) -> Path:
        """Get path for season file."""
        return self.episodes_path / f"season_{season}.json"

    def _get_embeddings_file(self, season: int) -> Path:
        """Get path for season embeddings file."""
        return self.embeddings_path / f"season_{season}_embeddings.json"

    def backup(self):
        """Create a backup of all data."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.base_path / f"backup_{timestamp}"
        backup_path.mkdir(parents=True)
        
        # Copy all files
        for file in self.episodes_path.glob("*.json"):
            shutil.copy2(file, backup_path / file.name)
        for file in self.embeddings_path.glob("*.json"):
            shutil.copy2(file, backup_path / file.name)
            
        logger.info(f"Created backup at {backup_path}")

    def save_episode(self, episode: EpisodeDocument):
        """Save a single episode."""
        season_file = self._get_season_file(episode.season_number)
        embeddings_file = self._get_embeddings_file(episode.season_number)
        
        # Load existing data
        season_data = {}
        if season_file.exists():
            with open(season_file, 'r') as f:
                season_data = json.load(f)
        
        embeddings_data = {}
        if embeddings_file.exists():
            with open(embeddings_file, 'r') as f:
                embeddings_data = json.load(f)
        
        # Update episode data
        episode_dict = episode.to_dict()
        
        # Separate embeddings
        episode_embeddings = {}
        for key in ['summary_embedding', 'synopsis_embedding', 'quotes_embedding']:
            if key in episode_dict:
                episode_embeddings[key] = episode_dict.pop(key)
        
        # Save episode data
        season_data[episode.episode_number] = episode_dict
        with open(season_file, 'w') as f:
            json.dump(season_data, f, indent=2)
        
        # Save embeddings
        if episode_embeddings:
            embeddings_data[episode.episode_number] = episode_embeddings
            with open(embeddings_file, 'w') as f:
                json.dump(embeddings_data, f, indent=2)

    def get_episode(self, season: int, episode: str) -> Optional[Dict[str, Any]]:
        """Get episode data by season and episode number."""
        try:
            season_file = self._get_season_file(season)
            embeddings_file = self._get_embeddings_file(season)
            
            if not season_file.exists():
                return None
            
            # Load episode data
            with open(season_file, 'r') as f:
                season_data = json.load(f)
            
            if episode not in season_data:
                return None
            
            episode_data = season_data[episode]
            
            # Load embeddings if they exist
            if embeddings_file.exists():
                with open(embeddings_file, 'r') as f:
                    embeddings_data = json.load(f)
                if episode in embeddings_data:
                    episode_data.update(embeddings_data[episode])
            
            return episode_data
            
        except Exception as e:
            logger.error(f"Error retrieving episode data: {str(e)}")
            return None

    def get_season(self, season: int) -> Dict[str, Dict[str, Any]]:
        """Get all episodes for a season."""
        try:
            season_file = self._get_season_file(season)
            if not season_file.exists():
                return {}
            
            with open(season_file, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            logger.error(f"Error retrieving season data: {str(e)}")
            return {}

    def search_episodes(self, query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Search episodes using semantic search."""
        try:
            # Encode query
            query_embedding = self.embedder.encode(query)
            
            # Search through all seasons
            results = []
            for season_file in self.episodes_path.glob("season_*.json"):
                with open(season_file, 'r') as f:
                    season_data = json.load(f)
                
                # Get embeddings for this season
                season_num = int(season_file.stem.split('_')[1])
                embeddings_file = self._get_embeddings_file(season_num)
                embeddings_data = {}
                if embeddings_file.exists():
                    with open(embeddings_file, 'r') as f:
                        embeddings_data = json.load(f)
                
                # Calculate similarity for each episode
                for episode_num, episode in season_data.items():
                    if 'summary_embedding' in embeddings_data.get(episode_num, {}):
                        episode_embedding = np.array(embeddings_data[episode_num]['summary_embedding'])
                        similarity = np.dot(query_embedding, episode_embedding) / (
                            np.linalg.norm(query_embedding) * np.linalg.norm(episode_embedding)
                        )
                        results.append({
                            'season': season_num,
                            'episode': episode_num,
                            'data': episode,
                            'score': float(similarity)
                        })
            
            # Sort by similarity and return top results
            results.sort(key=lambda x: x['score'], reverse=True)
            return results[:limit]
            
        except Exception as e:
            logger.error(f"Error searching episodes: {str(e)}")
            return []

    def import_from_json(self, json_path: str):
        """Import data from a JSON file."""
        try:
            with open(json_path, 'r') as f:
                data = json.load(f)
            
            for season_key, season_data in data.items():
                season_num = int(season_key.split('_')[1])
                for episode_num, episode in season_data.items():
                    # Convert to EpisodeDocument
                    doc = EpisodeDocument(
                        season_number=season_num,
                        episode_number=episode['episode_number'],
                        title=episode['episode_title'],
                        airdate=episode['episode_airdate'],
                        summary=episode.get('episode_summary', []),
                        synopsis=episode.get('episode_synopsis'),
                        quotes=episode.get('episode_quotes'),
                        trivia=episode.get('episode_trivia'),
                        director=episode.get('director'),
                        writer=episode.get('writer'),
                        production_code=episode.get('production_code'),
                        us_viewers_millions=episode.get('us_viewers_millions'),
                        original_air_date=episode.get('original_air_date'),
                        filming_location=episode.get('filming_location'),
                        network=episode.get('network'),
                        running_time=episode.get('running_time'),
                        budget=episode.get('budget'),
                        main_cast=episode.get('cast_main_cast'),
                        guest_stars=episode.get('cast_guest_stars'),
                        recurring_characters=episode.get('cast_recurring_characters'),
                        first_appearances=episode.get('cast_first_appearances'),
                        last_appearances=episode.get('cast_last_appearances'),
                        characters_introduced=episode.get('characters_introduced'),
                        characters_mentioned=episode.get('characters_mentioned'),
                        characters_died=episode.get('characters_died'),
                        continuity_notes=episode.get('continuity'),
                        cultural_references=episode.get('cultural_references'),
                        music=episode.get('music'),
                        mythology_references=episode.get('mythology_references'),
                        prophecies=episode.get('prophecies'),
                        arc_connections=episode.get('arc_connections'),
                        awards=episode.get('awards'),
                        death_count=episode.get('death_count'),
                        body_count=episode.get('body_count'),
                        summary_embedding=episode.get('summary_embedding'),
                        synopsis_embedding=episode.get('synopsis_embedding'),
                        quotes_embedding=episode.get('quotes_embedding')
                    )
                    self.save_episode(doc)
            
            logger.info(f"Successfully imported data from {json_path}")
            self.backup()
            
        except Exception as e:
            logger.error(f"Error importing data from {json_path}: {str(e)}")
            raise

# Singleton instance
store = BuffyDocumentStore()

def get_store() -> BuffyDocumentStore:
    """Get the document store instance."""
    return store 