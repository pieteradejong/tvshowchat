from typing import Dict, List, Optional
import json
import logging
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import torch
from tqdm import tqdm

logger = logging.getLogger(__name__)

class EmbeddingService:
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        base_dir: Path = Path("app/data"),
        device: str = "cuda" if torch.cuda.is_available() else "cpu"
    ):
        self.base_dir = base_dir
        self.episodes_dir = base_dir / "episodes"
        self.embeddings_dir = base_dir / "embeddings"
        self.model = SentenceTransformer(model_name, device=device)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        
    def _prepare_text(self, episode_data: Dict) -> List[str]:
        """Prepare text for embedding by combining relevant fields."""
        texts = []
        
        # Add title with context
        texts.append(f"Title: {episode_data['title']}")
        
        # Add each summary paragraph
        for i, summary in enumerate(episode_data['summary'], 1):
            texts.append(f"Summary Part {i}: {summary}")
        
        return texts
    
    def generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        return self.model.encode(texts, show_progress_bar=False)
    
    def save_embeddings(self, season: int, episode_num: str, texts: List[str], embeddings: np.ndarray) -> bool:
        """Save embeddings and their corresponding texts."""
        try:
            output_file = self.embeddings_dir / f"season_{season}_embeddings.json"
            
            # Load existing data if file exists
            if output_file.exists():
                with open(output_file, 'r') as f:
                    data = json.load(f)
            else:
                data = {}
            
            # Update with new episode embeddings
            episode_key = f"episode_{episode_num}"
            data[episode_key] = {
                "texts": texts,
                "embeddings": embeddings.tolist()
            }
            
            # Save with pretty printing
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving embeddings: {str(e)}")
            return False
    
    def process_episode(self, season: int, episode_num: str, episode_data: Dict) -> bool:
        """Process a single episode and generate embeddings."""
        try:
            # Prepare text for embedding
            texts = self._prepare_text(episode_data)
            
            # Generate embeddings
            embeddings = self.generate_embeddings(texts)
            
            # Save embeddings
            return self.save_embeddings(season, episode_num, texts, embeddings)
        except Exception as e:
            logger.error(f"Error processing episode {season}.{episode_num}: {str(e)}")
            return False
    
    def process_season(self, season: int) -> bool:
        """Process all episodes in a season."""
        try:
            season_file = self.episodes_dir / f"season_{season}.json"
            if not season_file.exists():
                logger.error(f"Season {season} data not found")
                return False
            
            with open(season_file, 'r') as f:
                season_data = json.load(f)
            
            success = True
            for episode_num, episode_data in tqdm(
                season_data.items(),
                desc=f"Processing Season {season}",
                unit="episode"
            ):
                if not self.process_episode(season, episode_num, episode_data):
                    success = False
            
            return success
        except Exception as e:
            logger.error(f"Error processing season {season}: {str(e)}")
            return False
    
    def process_all_seasons(self, seasons: Optional[List[int]] = None) -> bool:
        """Process all seasons or specified seasons."""
        if seasons is None:
            seasons = list(range(1, 8))  # All 7 seasons
        
        success = True
        for season in seasons:
            logger.info(f"Processing embeddings for season {season}")
            if not self.process_season(season):
                success = False
                logger.error(f"Failed to process season {season}")
        
        return success
    
    def load_embeddings(self, season: int, episode_num: str) -> Optional[Dict]:
        """Load embeddings for a specific episode."""
        try:
            embedding_file = self.embeddings_dir / f"season_{season}_embeddings.json"
            if not embedding_file.exists():
                return None
            
            with open(embedding_file, 'r') as f:
                data = json.load(f)
            
            episode_key = f"episode_{episode_num}"
            if episode_key not in data:
                return None
            
            return {
                "texts": data[episode_key]["texts"],
                "embeddings": np.array(data[episode_key]["embeddings"])
            }
        except Exception as e:
            logger.error(f"Error loading embeddings: {str(e)}")
            return None
    
    def get_episode_embedding(self, season: int, episode_num: str) -> Optional[np.ndarray]:
        """Get the average embedding for an episode."""
        data = self.load_embeddings(season, episode_num)
        if data is None:
            return None
        
        # Return the average of all embeddings for the episode
        return np.mean(data["embeddings"], axis=0)
    
    def find_similar_episodes(
        self,
        query: str,
        top_k: int = 5,
        seasons: Optional[List[int]] = None
    ) -> List[Dict]:
        """Find episodes similar to the query text."""
        # Generate query embedding
        query_embedding = self.model.encode([query])[0]
        
        results = []
        
        # Process all seasons or specified seasons
        if seasons is None:
            seasons = list(range(1, 8))
        
        for season in seasons:
            embedding_file = self.embeddings_dir / f"season_{season}_embeddings.json"
            if not embedding_file.exists():
                continue
            
            with open(embedding_file, 'r') as f:
                season_data = json.load(f)
            
            # Calculate similarity for each episode
            for episode_key, episode_data in season_data.items():
                episode_num = episode_key.split('_')[1]
                episode_embedding = np.mean(episode_data["embeddings"], axis=0)
                
                # Calculate cosine similarity
                similarity = np.dot(query_embedding, episode_embedding) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(episode_embedding)
                )
                
                results.append({
                    "season": season,
                    "episode": episode_num,
                    "similarity": float(similarity),
                    "texts": episode_data["texts"]
                })
        
        # Sort by similarity and return top_k results
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k] 