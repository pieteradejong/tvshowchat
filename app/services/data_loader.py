from typing import Dict, List, Optional
import json
import logging
from pathlib import Path
import asyncio
from datetime import datetime
from .data_pipeline import DataPipeline
from .embedding_service import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)

class DataLoader:
    def __init__(
        self,
        base_dir: Path = Path("app/data")
    ):
        self.base_dir = base_dir
        self.pipeline = DataPipeline(base_dir)
        self.embedding_service = EmbeddingService(base_dir)
        self.vector_store = VectorStore()
        
    async def load_episode(self, season: int, episode: str) -> Optional[Dict]:
        """Load a single episode from the vector store."""
        return self.vector_store.get_episode(season, episode)
    
    async def load_season(self, season: int) -> Optional[Dict]:
        """Load all episodes for a season from the vector store."""
        try:
            # Get all episodes for the season
            results = self.vector_store.collection.get(
                where={"season": season},
                include=["metadatas", "documents"]
            )
            
            if not results["ids"]:
                return None
            
            # Format into season data
            season_data = {}
            for i in range(len(results["ids"])):
                metadata = results["metadatas"][i]
                season_data[metadata["episode"]] = {
                    "season": metadata["season"],
                    "episode": metadata["episode"],
                    "title": metadata["title"],
                    "text": results["documents"][i]
                }
            
            return season_data
        except Exception as e:
            logger.error(f"Error loading season {season}: {str(e)}")
            return None
    
    async def initialize_data(self, force_refresh: bool = False) -> bool:
        """Initialize or refresh all data."""
        try:
            # Check if we need to refresh data
            if force_refresh or not self._check_data_completeness():
                logger.info("Refreshing episode data...")
                if not await self.pipeline.run_pipeline():
                    return False
                
                logger.info("Generating embeddings and updating vector store...")
                if not await self._update_vector_store():
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Error initializing data: {str(e)}")
            return False
    
    async def _update_vector_store(self) -> bool:
        """Update the vector store with all episodes."""
        try:
            # Reset vector store
            self.vector_store.reset()
            
            # Process all seasons
            for season in range(1, 8):
                season_file = self.base_dir / "episodes" / f"season_{season}.json"
                if not season_file.exists():
                    continue
                
                with open(season_file, 'r') as f:
                    season_data = json.load(f)
                
                # Add each episode to vector store
                for episode_num, episode_data in season_data.items():
                    if not self.vector_store.add_episode(
                        season=season,
                        episode=episode_num,
                        title=episode_data["title"],
                        summary=episode_data["summary"],
                        metadata={
                            "airdate": episode_data.get("airdate"),
                            "processed_at": episode_data.get("processed_at")
                        }
                    ):
                        logger.error(f"Failed to add episode {season}.{episode_num}")
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Error updating vector store: {str(e)}")
            return False
    
    def _check_data_completeness(self) -> bool:
        """Check if we have complete data for all seasons."""
        try:
            stats = self.vector_store.get_stats()
            expected_episodes = 144  # 7 seasons * ~22 episodes
            
            return (
                stats["total_episodes"] == expected_episodes and
                len(stats["seasons"]) == 7
            )
        except Exception as e:
            logger.error(f"Error checking data completeness: {str(e)}")
            return False
    
    def get_data_stats(self) -> Dict:
        """Get statistics about the loaded data."""
        try:
            stats = self.vector_store.get_stats()
            stats["last_updated"] = datetime.fromtimestamp(
                self.base_dir.stat().st_mtime
            ).isoformat()
            return stats
        except Exception as e:
            logger.error(f"Error getting data stats: {str(e)}")
            return {
                "total_episodes": 0,
                "seasons": [],
                "collection_name": "buffy_episodes",
                "embedding_model": "all-MiniLM-L6-v2",
                "last_updated": None
            } 