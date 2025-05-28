from typing import Dict, List, Any
from datetime import datetime
import re
from pydantic import BaseModel, Field, validator

class EpisodeSummary(BaseModel):
    """Validates a single episode's summary data."""
    episode_number: str = Field(..., pattern=r'^\d{2}$')
    episode_airdate: str
    episode_title: str
    episode_summary: List[str]
    summary_embedding: List[float]

    @validator('episode_airdate')
    def validate_airdate(cls, v: str) -> str:
        """Validate air date format (e.g., 'March 10, 1997')."""
        try:
            datetime.strptime(v, '%B %d, %Y')
            return v
        except ValueError:
            raise ValueError('Invalid date format. Expected format: "Month DD, YYYY"')

    @validator('episode_summary')
    def validate_summary(cls, v: List[str]) -> List[str]:
        """Validate summary content."""
        if not v:
            raise ValueError('Summary cannot be empty')
        if any(len(p) < 10 for p in v):
            raise ValueError('Summary paragraphs too short')
        return v

    @validator('summary_embedding')
    def validate_embedding(cls, v: List[float]) -> List[float]:
        """Validate embedding vector."""
        if not v:
            raise ValueError('Embedding cannot be empty')
        if len(v) != 384:  # all-MiniLM-L6-v2 dimension
            raise ValueError(f'Invalid embedding dimension. Expected 384, got {len(v)}')
        return v

class SeasonData(BaseModel):
    """Validates a season's episode data."""
    __root__: Dict[str, EpisodeSummary]

    def __iter__(self):
        return iter(self.__root__.items())

    def __getitem__(self, key: str) -> EpisodeSummary:
        return self.__root__[key]

class BuffyData(BaseModel):
    """Validates the complete Buffy dataset."""
    __root__: Dict[str, SeasonData]

    def validate_season_numbers(self) -> bool:
        """Validate that season numbers are sequential."""
        season_numbers = [int(k.split('_')[1]) for k in self.__root__.keys()]
        return season_numbers == list(range(1, len(season_numbers) + 1))

    def validate_episode_numbers(self) -> bool:
        """Validate that episode numbers are sequential within each season."""
        for season_key, season in self.__root__.items():
            episode_numbers = [int(ep.episode_number) for ep in season.__root__.values()]
            if episode_numbers != list(range(1, len(episode_numbers) + 1)):
                return False
        return True

def validate_episode_data(data: Dict[str, Any]) -> BuffyData:
    """Validate the complete episode dataset."""
    try:
        buffy_data = BuffyData(__root__=data)
        
        # Additional validations
        if not buffy_data.validate_season_numbers():
            raise ValueError("Invalid season number sequence")
        if not buffy_data.validate_episode_numbers():
            raise ValueError("Invalid episode number sequence")
            
        return buffy_data
    except Exception as e:
        raise ValueError(f"Data validation failed: {str(e)}")

def validate_single_episode(data: Dict[str, Any]) -> EpisodeSummary:
    """Validate a single episode's data."""
    try:
        return EpisodeSummary(**data)
    except Exception as e:
        raise ValueError(f"Episode validation failed: {str(e)}") 