"""
Advanced Semantic Search Vector Store for Buffy the Vampire Slayer Universe

This module provides comprehensive semantic search capabilities across the entire Buffy universe,
enabling complex queries about character relationships, storylines, quotes, and plot elements.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import json
from dataclasses import dataclass
from app.services.embedder import EMBEDDING_MODEL, load_embedder
from app.services.storage.document_store import BuffyDocumentStore
from app.config.config import logger

@dataclass
class SearchResult:
    """Enhanced search result with rich metadata."""
    season: int
    episode: str
    title: str
    airdate: str
    content_type: str  # 'summary', 'synopsis', 'quote', 'character_interaction'
    text: str
    snippets: List[str]
    score: float
    characters: List[str]
    themes: List[str]
    context: str

class AdvancedVectorStore:
    """
    Advanced semantic search store for the Buffy universe.
    
    Features:
    - Character relationship mapping
    - Theme and storyline detection
    - Multi-modal search (episodes, quotes, scenes, relationships)
    - Context-aware results
    - Season and episode filtering
    """
    
    def __init__(self, document_store: BuffyDocumentStore):
        self.document_store = document_store
        self.embedder = load_embedder()
        
        # In-memory index: one unit-normalised vector per episode, searched by exact
        # brute-force cosine. Built from the document store on first search.
        self._index_matrix: Optional[np.ndarray] = None
        self._index_meta: List[Dict[str, Any]] = []
        
        # Character and relationship mappings - lazy loaded to save memory/CPU at startup
        self._character_embeddings = None
        self._relationship_graph = None
        self._theme_embeddings = None
        
        # Buffy universe knowledge base
        self.main_characters = {
            'Buffy', 'Willow', 'Xander', 'Giles', 'Angel', 'Spike', 'Cordelia',
            'Oz', 'Tara', 'Anya', 'Dawn', 'Faith', 'Riley', 'Jenny', 'Joyce',
            'The Master', 'Drusilla', 'Darla', 'Ethan Rayne', 'Mayor Wilkins',
            'Glory', 'Warren', 'Jonathan', 'Andrew', 'The First Evil'
        }
        
        self.relationship_types = {
            'romantic': ['love', 'relationship', 'dating', 'boyfriend', 'girlfriend', 'kiss', 'sleep together'],
            'friendship': ['friend', 'best friend', 'close', 'bond', 'support', 'help'],
            'enemy': ['enemy', 'foe', 'fight', 'battle', 'opponent', 'rival', 'hate'],
            'family': ['mother', 'father', 'sister', 'brother', 'family', 'parent'],
            'mentor': ['watcher', 'teacher', 'guide', 'mentor', 'train', 'teach']
        }
        
        self.themes = {
            'romance': ['love', 'romance', 'relationship', 'dating', 'kiss', 'heart'],
            'friendship': ['friend', 'friendship', 'bond', 'support', 'loyalty'],
            'family': ['family', 'mother', 'father', 'sister', 'brother', 'parent'],
            'magic': ['magic', 'spell', 'witch', 'sorcery', 'enchantment', 'curse'],
            'vampire': ['vampire', 'blood', 'bite', 'stake', 'undead', 'night'],
            'demon': ['demon', 'monster', 'creature', 'supernatural', 'evil'],
            'school': ['school', 'high school', 'college', 'student', 'teacher', 'class'],
            'death': ['death', 'die', 'kill', 'murder', 'sacrifice', 'grave'],
            'power': ['power', 'strength', 'ability', 'skill', 'force', 'might'],
            'sacrifice': ['sacrifice', 'give up', 'lose', 'abandon', 'forsake']
        }
        
        # Defer expensive operations:
        # - Character/theme embeddings: built on first use
        # - Relationship graph: built on first use (very expensive, reads all files)
        # - Vector index: built on first search
    
    @property
    def character_embeddings(self) -> Dict[str, np.ndarray]:
        """Lazy-load character embeddings."""
        if self._character_embeddings is None:
            self._build_character_embeddings()
        return self._character_embeddings
    
    @property
    def relationship_graph(self) -> Dict[str, Any]:
        """Lazy-load relationship graph (expensive - reads all episode files)."""
        if self._relationship_graph is None:
            self._build_relationship_graph()
        return self._relationship_graph
    
    @property
    def theme_embeddings(self) -> Dict[str, np.ndarray]:
        """Lazy-load theme embeddings."""
        if self._theme_embeddings is None:
            self._build_theme_embeddings()
        return self._theme_embeddings
    
    def _build_character_embeddings(self):
        """Build embeddings for character names and descriptions."""
        logger.info("Building character embeddings (lazy-loaded)...")
        self._character_embeddings = {}
        
        for character in self.main_characters:
            # Create character description for better semantic matching
            char_desc = f"Character {character} from Buffy the Vampire Slayer"
            self._character_embeddings[character] = self.embedder.encode(char_desc)
    
    def _build_relationship_graph(self):
        """Build relationship graph from episode data (expensive - lazy-loaded)."""
        logger.info("Building character relationship graph (lazy-loaded, may take a moment)...")
        self._relationship_graph = {}
        
        for season_file in self.document_store.episodes_path.glob("season_*.json"):
            if season_file.name == "season_stats.json":
                continue
            try:
                season_num = int(season_file.stem.split('_')[1])
            except (ValueError, IndexError):
                continue
            
            with open(season_file, 'r') as f:
                season_data = json.load(f)
            
            for episode_num, episode in season_data.items():
                # Extract character interactions from summary text
                summary_text = " ".join(episode.get('summary', []))
                self._extract_relationships_from_text(summary_text, season_num, episode_num)
    
    def _extract_relationships_from_text(self, text: str, season: int, episode: str):
        """Extract character relationships from episode text."""
        text_lower = text.lower()
        
        for char1 in self.main_characters:
            if char1.lower() in text_lower:
                for char2 in self.main_characters:
                    if char1 != char2 and char2.lower() in text_lower:
                        # Find relationship type based on context
                        relationship_type = self._detect_relationship_type(text_lower, char1, char2)
                        
                        if relationship_type:
                            key = f"{char1}-{char2}"
                            if key not in self._relationship_graph:
                                self._relationship_graph[key] = {
                                    'characters': (char1, char2),
                                    'type': relationship_type,
                                    'episodes': [],
                                    'strength': 0.0,
                                    'descriptions': []
                                }
                            
                            self._relationship_graph[key]['episodes'].append(f"S{season:02d}E{episode}")
                            self._relationship_graph[key]['strength'] += 1.0
                            self._relationship_graph[key]['descriptions'].append(text)
    
    def _detect_relationship_type(self, text: str, char1: str, char2: str) -> Optional[str]:
        """Detect relationship type between two characters based on context."""
        char1_lower = char1.lower()
        char2_lower = char2.lower()
        
        # Find text segments containing both characters
        segments = []
        words = text.split()
        for i, word in enumerate(words):
            if char1_lower in word:
                # Get context around this word
                start = max(0, i - 10)
                end = min(len(words), i + 10)
                segment = " ".join(words[start:end])
                if char2_lower in segment:
                    segments.append(segment)
        
        # Analyze segments for relationship indicators
        for segment in segments:
            segment_lower = segment.lower()
            
            for rel_type, indicators in self.relationship_types.items():
                for indicator in indicators:
                    if indicator in segment_lower:
                        return rel_type
        
        return None
    
    def _build_theme_embeddings(self):
        """Build embeddings for themes and storylines (lazy-loaded)."""
        logger.info("Building theme embeddings (lazy-loaded)...")
        self._theme_embeddings = {}
        
        for theme, keywords in self.themes.items():
            theme_text = f"Theme {theme}: {', '.join(keywords)}"
            self._theme_embeddings[theme] = self.embedder.encode(theme_text)
    
    def _build_index(self):
        """Build the in-memory vector index from the document store."""
        logger.info("Building vector index from document store...")
        
        vectors = []
        metadatas = []
        
        for season_file in sorted(self.document_store.episodes_path.glob("season_*.json")):
            if season_file.name == "season_stats.json":
                continue
            try:
                season_num = int(season_file.stem.split('_')[1])
            except (ValueError, IndexError):
                continue
            
            with open(season_file, 'r') as f:
                season_data = json.load(f)
            
            # Get embeddings for this season
            embeddings_file = self.document_store._get_embeddings_file(season_num)
            embeddings_data = {}
            if embeddings_file.exists():
                with open(embeddings_file, 'r') as f:
                    embeddings_data = json.load(f)
            
            for episode_num, episode in season_data.items():
                # Get summary text
                summary_parts = episode.get('summary', [])
                if not summary_parts:
                    continue
                
                # Get or generate embedding
                if 'summary_embedding' in embeddings_data.get(episode_num, {}):
                    episode_embedding = embeddings_data[episode_num]['summary_embedding']
                else:
                    # Generate embedding if not found
                    episode_embedding = self.embedder.encode(" ".join(summary_parts))
                
                vectors.append(np.asarray(episode_embedding, dtype=np.float64))
                metadatas.append({
                    'id': f"s{season_num:02d}e{episode_num}",
                    'season': season_num,
                    'episode': episode_num,
                    'title': episode.get('title', ''),
                    'airdate': episode.get('airdate', ''),
                })
        
        if vectors:
            matrix = np.vstack(vectors)
            norms = np.linalg.norm(matrix, axis=1, keepdims=True)
            norms[norms == 0] = 1.0
            self._index_matrix = matrix / norms
        else:
            self._index_matrix = np.zeros((0, 0))
        self._index_meta = metadatas
        
        logger.info(f"Indexed {len(metadatas)} episodes")
    
    def _ensure_index(self):
        if self._index_matrix is None:
            self._build_index()
    
    def _nearest(self, query_embedding: np.ndarray, n: int,
                 season: Optional[int]) -> List[Tuple[Dict[str, Any], float]]:
        """Exact top-n episodes by cosine similarity, optionally within one season.
        
        Deterministic: ties keep index order (season file, then episode order).
        """
        self._ensure_index()
        if not self._index_meta or n <= 0:
            return []
        
        query = np.asarray(query_embedding, dtype=np.float64)
        norm = np.linalg.norm(query)
        if norm == 0:
            return []
        similarities = self._index_matrix @ (query / norm)
        
        candidates = np.arange(len(self._index_meta))
        if season is not None:
            candidates = candidates[[m['season'] == season for m in self._index_meta]]
        order = candidates[np.argsort(-similarities[candidates], kind="stable")]
        return [(self._index_meta[i], float(similarities[i])) for i in order[:n]]
    
    def search_episodes(self, query: str, limit: int = 5, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search episodes with enhanced semantic understanding.
        
        Args:
            query: Natural language search query
            limit: Maximum number of results
            season: Optional season filter
            
        Returns:
            List of search results with rich metadata
        """
        logger.info(f"Searching episodes with query: '{query}'")
        
        # Encode the query
        query_embedding = self.embedder.encode(query)
        
        # Detect query type and extract entities
        query_type = self._analyze_query_type(query)
        characters = self._extract_characters_from_query(query)
        themes = self._extract_themes_from_query(query)
        
        # Get more candidates than needed, then re-rank them with the query boosts
        query_limit = limit * 3 if season is None else limit * 2
        
        results = []
        
        for metadata, similarity in self._nearest(query_embedding, query_limit, season):
            season_num = metadata['season']
            episode_num = metadata['episode']
            episode = self.document_store.get_episode(season_num, episode_num)
            if not episode:
                logger.warning("Episode not found in document store for %s", metadata['id'])
                continue

            boosted_score = self._boost_score_for_query(
                similarity, episode, characters, themes, query_type
            )

            content_type, relevant_text, supporting_snippets = self._extract_relevant_content(
                episode, query, characters, themes
            )

            result = {
                'season': season_num,
                'episode': episode_num,
                'title': metadata.get('title', episode.get('title', '')),
                'airdate': metadata.get('airdate', episode.get('airdate', '')),
                'content_type': content_type,
                'text': relevant_text,
                'snippets': supporting_snippets,
                'score': float(boosted_score),
                'characters': self._extract_characters_from_episode(episode),
                'themes': self._extract_themes_from_episode(episode),
                'context': self._generate_context(episode, query, characters)
            }

            results.append(result)

        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def _analyze_query_type(self, query: str) -> str:
        """Analyze the type of query (character relationship, theme, etc.)."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['relationship', 'together', 'between', 'and']):
            return 'relationship'
        elif any(word in query_lower for word in ['quote', 'say', 'said', 'dialogue']):
            return 'quote'
        elif any(word in query_lower for word in ['scene', 'moment', 'happens']):
            return 'scene'
        elif any(word in query_lower for word in ['episode', 'show', 'season']):
            return 'episode'
        else:
            return 'general'
    
    def _extract_characters_from_query(self, query: str) -> List[str]:
        """Extract character names from the query."""
        query_lower = query.lower()
        found_characters = []
        
        for character in self.main_characters:
            if character.lower() in query_lower:
                found_characters.append(character)
        
        return found_characters
    
    def _extract_themes_from_query(self, query: str) -> List[str]:
        """Extract themes from the query."""
        query_lower = query.lower()
        found_themes = []
        
        for theme, keywords in self.themes.items():
            for keyword in keywords:
                if keyword in query_lower:
                    found_themes.append(theme)
                    break
        
        return found_themes
    
    def _boost_score_for_query(self, base_score: float, episode: Dict, 
                              characters: List[str], themes: List[str], 
                              query_type: str) -> float:
        """Boost similarity score based on query-specific factors."""
        boosted_score = base_score
        
        # Character match boost
        episode_text = " ".join(episode.get('summary', [])).lower()
        for character in characters:
            if character.lower() in episode_text:
                boosted_score += 0.1
        
        # Theme match boost
        for theme in themes:
            theme_keywords = self.themes.get(theme, [])
            for keyword in theme_keywords:
                if keyword in episode_text:
                    boosted_score += 0.05
                    break
        
        # Query type specific boosts
        if query_type == 'relationship' and len(characters) >= 2:
            boosted_score += 0.15
        
        return boosted_score
    
    def _extract_relevant_content(
        self,
        episode: Dict,
        query: str,
        characters: List[str],
        themes: List[str]
    ) -> Tuple[str, str, List[str]]:
        """Extract the most relevant content from the episode."""
        summary_parts = episode.get('summary', [])

        if not summary_parts:
            synopsis_parts = episode.get('synopsis') or []
            combined = synopsis_parts if isinstance(synopsis_parts, list) else [synopsis_parts]
            combined_text = combined[0] if combined else ''
            return 'synopsis', combined_text, combined[1:3] if len(combined) > 1 else []

        query_lower = query.lower()
        query_words = [word for word in query_lower.split() if word]

        scored_segments: List[Tuple[float, str]] = []

        for part in summary_parts:
            part_lower = part.lower()
            score = 0.0

            # Character mentions
            for character in characters:
                if character.lower() in part_lower:
                    score += 1.0

            # Theme keywords
            for theme in themes:
                theme_keywords = self.themes.get(theme, [])
                for keyword in theme_keywords:
                    if keyword in part_lower:
                        score += 0.5
                        break

            # Query word matches
            for word in query_words:
                if len(word) < 3:
                    continue
                if word in part_lower:
                    score += 0.3

            # Fallback for general similarity
            if not characters and not themes and not query_words:
                score += 0.1

            scored_segments.append((score, part))

        scored_segments.sort(key=lambda item: item[0], reverse=True)

        # Ensure we have at least the first paragraph even if scores equal
        if not scored_segments or scored_segments[0][0] == 0:
            primary = summary_parts[0]
            supporting = summary_parts[1:3]
        else:
            primary = scored_segments[0][1]
            supporting = [segment for _, segment in scored_segments[1:4] if segment != primary]

        return 'summary', primary, supporting
    
    def _extract_characters_from_episode(self, episode: Dict) -> List[str]:
        """Extract character names mentioned in the episode."""
        episode_text = " ".join(episode.get('summary', [])).lower()
        found_characters = []
        
        for character in self.main_characters:
            if character.lower() in episode_text:
                found_characters.append(character)
        
        return found_characters
    
    def _extract_themes_from_episode(self, episode: Dict) -> List[str]:
        """Extract themes present in the episode."""
        episode_text = " ".join(episode.get('summary', [])).lower()
        found_themes = []
        
        for theme, keywords in self.themes.items():
            for keyword in keywords:
                if keyword in episode_text:
                    found_themes.append(theme)
                    break
        
        return found_themes
    
    def _generate_context(self, episode: Dict, query: str, characters: List[str]) -> str:
        """Generate contextual information about the search result."""
        context_parts = []
        
        if characters:
            context_parts.append(f"Features characters: {', '.join(characters)}")
        
        themes = self._extract_themes_from_episode(episode)
        if themes:
            context_parts.append(f"Themes: {', '.join(themes)}")
        
        return " | ".join(context_parts) if context_parts else ""
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store."""
        total_episodes = 0
        seasons = set()
        season_counts: Dict[int, int] = {}
        embedding_counts: Dict[int, int] = {}

        for season_file in self.document_store.episodes_path.glob("season_*.json"):
            if season_file.name == "season_stats.json":
                continue
            try:
                season_num = int(season_file.stem.split('_')[1])
            except (ValueError, IndexError):
                continue
            seasons.add(season_num)

            with open(season_file, 'r') as f:
                season_data = json.load(f)
                episode_count = len(season_data)
                total_episodes += episode_count
                season_counts[season_num] = episode_count

            embeddings_file = self.document_store._get_embeddings_file(season_num)
            embed_count = 0
            if embeddings_file.exists():
                with open(embeddings_file, 'r') as f:
                    embeddings_data = json.load(f)
                    embed_count = len(embeddings_data)
            embedding_counts[season_num] = embed_count

        # Ensure embedding counts account for all tracked seasons
        for season in seasons:
            embedding_counts.setdefault(season, 0)

        embeddings_total = sum(embedding_counts.values())

        self._ensure_index()
        
        return {
            'total_episodes': total_episodes,
            'seasons': sorted(list(seasons)),
            'season_counts': season_counts,
            'embedding_counts': embedding_counts,
            'embedding_total': embeddings_total,
            'collection_name': 'buffy_episodes',
            'embedding_model': EMBEDDING_MODEL,
            'indexed_episodes': len(self._index_meta),
            'characters_tracked': len(self.main_characters),
            'relationships_mapped': len(self.relationship_graph),
            'themes_available': len(self.themes)
        }
    
    def rebuild_from_document_store(self) -> Dict[str, Any]:
        """Rebuild the vector index from the document store."""
        logger.info("Rebuilding vector index from document store...")
        self._build_index()
        summary = self.get_stats()
        logger.info("Vector index rebuild complete: %s", summary)
        return summary

    def get_episode(self, season: int, episode: str) -> Optional[Dict[str, Any]]:
        """Get a specific episode by season and episode number."""
        return self.document_store.get_episode(season, episode)

# Global instance
_vector_store = None

def get_vector_store() -> AdvancedVectorStore:
    """Get the global vector store instance."""
    global _vector_store
    if _vector_store is None:
        from app.services.storage.document_store import get_store
        document_store = get_store()
        _vector_store = AdvancedVectorStore(document_store)
    return _vector_store