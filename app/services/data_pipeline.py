from typing import Dict, List, Optional
import json
import logging
import asyncio
from pathlib import Path
from datetime import datetime
import aiohttp
from bs4 import BeautifulSoup
import time
from ratelimit import limits, sleep_and_retry

logger = logging.getLogger(__name__)

class DataPipeline:
    def __init__(self, base_dir: Path = Path("app/data")):
        self.base_dir = base_dir
        self.episodes_dir = base_dir / "episodes"
        self.embeddings_dir = base_dir / "embeddings"
        self.backup_dir = base_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create directories if they don't exist
        self.episodes_dir.mkdir(parents=True, exist_ok=True)
        self.embeddings_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Rate limiting settings
        self.ONE_MINUTE = 60
        self.MAX_REQUESTS_PER_MINUTE = 30
        
    @sleep_and_retry
    @limits(calls=30, period=60)
    async def fetch_episode_data(self, season: int, episode: int) -> Optional[Dict]:
        """Fetch episode data with rate limiting."""
        url = f"https://api.example.com/buffy/season/{season}/episode/{episode}"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to fetch episode {season}.{episode}: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching episode {season}.{episode}: {str(e)}")
            return None

    async def process_episode(self, data: Dict) -> Dict:
        """Process and clean episode data."""
        # Clean and validate episode data
        processed = {
            "season_number": data["season_number"],
            "episode_number": data["episode_number"].zfill(2),
            "title": data["title"],
            "airdate": data["airdate"],
            "summary": [s.strip() for s in data["summary"] if s.strip()],
            "processed_at": datetime.now().isoformat()
        }
        return processed

    def save_episode(self, season: int, episode_data: Dict) -> bool:
        """Save episode data to JSON file."""
        try:
            season_file = self.episodes_dir / f"season_{season}.json"
            
            # Load existing data if file exists
            if season_file.exists():
                with open(season_file, 'r') as f:
                    season_data = json.load(f)
            else:
                season_data = {}
            
            # Update with new episode data
            episode_num = episode_data["episode_number"]
            season_data[episode_num] = episode_data
            
            # Save with backup
            self._backup_file(season_file)
            with open(season_file, 'w') as f:
                json.dump(season_data, f, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"Error saving episode data: {str(e)}")
            return False

    def _backup_file(self, file_path: Path) -> None:
        """Create backup of file before modification."""
        if file_path.exists():
            backup_path = self.backup_dir / file_path.name
            with open(file_path, 'r') as src, open(backup_path, 'w') as dst:
                dst.write(src.read())

    async def collect_season_data(self, season: int, start_episode: int = 1, end_episode: int = 22) -> bool:
        """Collect all episodes for a season."""
        success = True
        for episode in range(start_episode, end_episode + 1):
            data = await self.fetch_episode_data(season, episode)
            if data:
                processed = await self.process_episode(data)
                if not self.save_episode(season, processed):
                    success = False
            else:
                success = False
            # Rate limiting is handled by the decorator
            await asyncio.sleep(0.1)  # Small delay between requests
        return success

    def validate_data(self) -> Dict[str, List[str]]:
        """Validate all collected data."""
        issues = {
            "missing_episodes": [],
            "invalid_data": [],
            "incomplete_data": []
        }
        
        for season_file in self.episodes_dir.glob("season_*.json"):
            if season_file.name == "season_stats.json":
                continue
            try:
                season_num = int(season_file.stem.split('_')[1])
            except (ValueError, IndexError):
                continue
            
            with open(season_file, 'r') as f:
                season_data = json.load(f)
            expected_episodes = 22 if season_num != 7 else 22  # Adjust for season 7
            
            # Check for missing episodes
            for ep in range(1, expected_episodes + 1):
                ep_key = str(ep).zfill(2)
                if ep_key not in season_data:
                    issues["missing_episodes"].append(f"Season {season_num} Episode {ep}")
                    continue
                
                # Validate episode data
                ep_data = season_data[ep_key]
                required_fields = ["title", "airdate", "summary"]
                if not all(field in ep_data for field in required_fields):
                    issues["invalid_data"].append(f"Season {season_num} Episode {ep}")
                elif not ep_data["summary"]:
                    issues["incomplete_data"].append(f"Season {season_num} Episode {ep}")
        
        return issues

    async def run_pipeline(self, seasons: List[int] = None) -> bool:
        """Run the complete data pipeline for specified seasons."""
        if seasons is None:
            seasons = list(range(1, 8))  # All 7 seasons
        
        success = True
        for season in seasons:
            logger.info(f"Processing season {season}")
            if not await self.collect_season_data(season):
                success = False
                logger.error(f"Failed to process season {season}")
        
        # Validate collected data
        issues = self.validate_data()
        if any(issues.values()):
            logger.warning("Data validation issues found:")
            for category, problems in issues.items():
                if problems:
                    logger.warning(f"{category}: {len(problems)} issues")
                    for problem in problems[:5]:  # Show first 5 issues
                        logger.warning(f"  - {problem}")
        
        return success and not any(issues.values()) 