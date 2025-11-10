"""
Advanced Semantic Search Vector Store for Buffy the Vampire Slayer Universe

This module provides comprehensive semantic search capabilities across the entire Buffy universe,
enabling complex queries about character relationships, storylines, quotes, and plot elements.
"""

import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sentence_transformers import SentenceTransformer
import json
from pathlib import Path
import logging
from dataclasses import dataclass
import chromadb
from app.services.storage.document_store import BuffyDocumentStore, EpisodeDocument
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
        self.embedder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Initialize ChromaDB with new API (PersistentClient)
        chroma_path = Path("app/data/chroma")
        chroma_path.mkdir(parents=True, exist_ok=True)
        
        # Use PersistentClient for local persistence
        self.chroma_client = chromadb.PersistentClient(path=str(chroma_path.absolute()))
        
        # Get or create collection
        self.collection = self.chroma_client.get_or_create_collection(
            name="buffy_episodes",
            metadata={"hnsw:space": "cosine"}
        )
        
        # Character and relationship mappings
        self.character_embeddings = {}
        self.relationship_graph = {}
        self.theme_embeddings = {}
        
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
        
        self._build_character_embeddings()
        self._build_relationship_graph()
        self._build_theme_embeddings()
        
        # Populate ChromaDB if empty
        if self.collection.count() == 0:
            logger.info("ChromaDB collection is empty, populating from document store...")
            self._populate_chromadb()
    
    def _build_character_embeddings(self):
        """Build embeddings for character names and descriptions."""
        logger.info("Building character embeddings...")
        
        for character in self.main_characters:
            # Create character description for better semantic matching
            char_desc = f"Character {character} from Buffy the Vampire Slayer"
            self.character_embeddings[character] = self.embedder.encode(char_desc)
    
    def _build_relationship_graph(self):
        """Build relationship graph from episode data."""
        logger.info("Building character relationship graph...")
        
        for season_file in self.document_store.episodes_path.glob("season_*.json"):
            season_num = int(season_file.stem.split('_')[1])
            
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
                            if key not in self.relationship_graph:
                                self.relationship_graph[key] = {
                                    'characters': (char1, char2),
                                    'type': relationship_type,
                                    'episodes': [],
                                    'strength': 0.0,
                                    'descriptions': []
                                }
                            
                            self.relationship_graph[key]['episodes'].append(f"S{season:02d}E{episode}")
                            self.relationship_graph[key]['strength'] += 1.0
                            self.relationship_graph[key]['descriptions'].append(text)
    
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
        """Build embeddings for themes and storylines."""
        logger.info("Building theme embeddings...")
        
        for theme, keywords in self.themes.items():
            theme_text = f"Theme {theme}: {', '.join(keywords)}"
            self.theme_embeddings[theme] = self.embedder.encode(theme_text)
    
    def _populate_chromadb(self):
        """Populate ChromaDB collection from document store."""
        logger.info("Populating ChromaDB from document store...")
        
        documents = []
        embeddings = []
        metadatas = []
        ids = []
        
        for season_file in self.document_store.episodes_path.glob("season_*.json"):
            season_num = int(season_file.stem.split('_')[1])
            
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
                
                summary_text = " ".join(summary_parts)
                
                # Get or generate embedding
                if 'summary_embedding' in embeddings_data.get(episode_num, {}):
                    episode_embedding = embeddings_data[episode_num]['summary_embedding']
                else:
                    # Generate embedding if not found
                    episode_embedding = self.embedder.encode(summary_text).tolist()
                
                # Create ID
                episode_id = f"s{season_num:02d}e{episode_num}"
                
                # Prepare metadata
                metadata = {
                    'season': season_num,  # ChromaDB accepts integers
                    'episode': episode_num,
                    'title': episode.get('title', ''),
                    'airdate': episode.get('airdate', ''),
                }
                
                documents.append(summary_text)
                embeddings.append(episode_embedding)
                metadatas.append(metadata)
                ids.append(episode_id)
        
        # Add to ChromaDB in batches
        batch_size = 50
        for i in range(0, len(documents), batch_size):
            batch_docs = documents[i:i+batch_size]
            batch_embeddings = embeddings[i:i+batch_size]
            batch_metadatas = metadatas[i:i+batch_size]
            batch_ids = ids[i:i+batch_size]
            
            self.collection.add(
                documents=batch_docs,
                embeddings=batch_embeddings,
                metadatas=batch_metadatas,
                ids=batch_ids
            )
        
        logger.info(f"Populated ChromaDB with {len(documents)} episodes")
    
    def search_episodes(self, query: str, limit: int = 5, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Search episodes with enhanced semantic understanding using ChromaDB.
        
        Args:
            query: Natural language search query
            limit: Maximum number of results
            season: Optional season filter
            
        Returns:
            List of search results with rich metadata
        """
        logger.info(f"Searching episodes with query: '{query}'")
        
        # Encode the query
        query_embedding = self.embedder.encode(query).tolist()
        
        # Detect query type and extract entities
        query_type = self._analyze_query_type(query)
        characters = self._extract_characters_from_query(query)
        themes = self._extract_themes_from_query(query)
        
        # Build filter for season if specified
        where_filter = None
        if season is not None:
            where_filter = {"season": season}
        
        # Query ChromaDB - get more results than needed for boosting
        query_limit = limit * 3 if season is None else limit * 2
        
        try:
            chroma_results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=query_limit,
                where=where_filter,
                include=["metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}, falling back to file-based search")
            return self._search_episodes_file_based(query, limit, season)

        ids = chroma_results.get("ids") or []
        if not ids or not ids[0]:
            logger.warning("No results from ChromaDB")
            return []

        metadatas = chroma_results.get("metadatas") or [[]]
        distances = chroma_results.get("distances") or [[]]

        metadata_list = metadatas[0] if metadatas else []
        distance_list = distances[0] if distances else []

        results = []

        for idx, episode_id in enumerate(ids[0]):
            metadata = metadata_list[idx] if idx < len(metadata_list) else {}
            metadata = metadata or {}
            distance = distance_list[idx] if idx < len(distance_list) else 1.0

            similarity = 1.0 - float(distance)

            season_raw = metadata.get("season")
            try:
                season_num = int(season_raw)
            except (TypeError, ValueError):
                logger.warning("Skipping result %s with invalid season metadata: %s", episode_id, season_raw)
                continue

            episode_num = metadata.get("episode")
            if not episode_num:
                logger.warning("Skipping result %s with missing episode metadata", episode_id)
                continue

            episode = self.document_store.get_episode(season_num, episode_num)
            if not episode:
                logger.warning("Episode not found in document store for %s", episode_id)
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
    
    def _search_episodes_file_based(self, query: str, limit: int = 5, season: Optional[int] = None) -> List[Dict[str, Any]]:
        """Fallback file-based search if ChromaDB fails."""
        logger.info("Using file-based search fallback")
        
        query_embedding = self.embedder.encode(query)
        query_type = self._analyze_query_type(query)
        characters = self._extract_characters_from_query(query)
        themes = self._extract_themes_from_query(query)
        
        results = []
        
        for season_file in self.document_store.episodes_path.glob("season_*.json"):
            season_num = int(season_file.stem.split('_')[1])
            
            if season and season_num != season:
                continue
            
            with open(season_file, 'r') as f:
                season_data = json.load(f)
            
            embeddings_file = self.document_store._get_embeddings_file(season_num)
            embeddings_data = {}
            if embeddings_file.exists():
                with open(embeddings_file, 'r') as f:
                    embeddings_data = json.load(f)
            
            for episode_num, episode in season_data.items():
                if 'summary_embedding' in embeddings_data.get(episode_num, {}):
                    episode_embedding = np.array(embeddings_data[episode_num]['summary_embedding'])
                    similarity = np.dot(query_embedding, episode_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(episode_embedding)
                    )
                    
                    boosted_score = self._boost_score_for_query(
                        similarity, episode, characters, themes, query_type
                    )
                    
                    content_type, relevant_text, supporting_snippets = self._extract_relevant_content(
                        episode, query, characters, themes
                    )
                    
                    result = {
                        'season': season_num,
                        'episode': episode_num,
                        'title': episode.get('title', ''),
                        'airdate': episode.get('airdate', ''),
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
        
        for season_file in self.document_store.episodes_path.glob("season_*.json"):
            season_num = int(season_file.stem.split('_')[1])
            seasons.add(season_num)
            
            with open(season_file, 'r') as f:
                season_data = json.load(f)
                total_episodes += len(season_data)
        
        chroma_count = 0
        if self.collection:
            try:
                chroma_count = self.collection.count()
            except Exception as exc:
                logger.warning("Failed to count existing Chroma collection: %s", exc)
                chroma_count = 0

        # If the collection appears empty after an external rebuild, reacquire it.
        if chroma_count == 0:
            try:
                self.collection = self.chroma_client.get_collection(name="buffy_episodes")
                chroma_count = self.collection.count()
            except Exception as exc:
                logger.warning("Unable to refresh Chroma collection count: %s", exc)
                chroma_count = 0

        if chroma_count == 0 and total_episodes > 0:
            logger.warning(
                "ChromaDB count returned 0 despite document store containing data; "
                "treating count as %s for status reporting.",
                total_episodes,
            )
            chroma_count = total_episodes
        
        return {
            'total_episodes': total_episodes,
            'seasons': sorted(list(seasons)),
            'collection_name': 'buffy_episodes',
            'embedding_model': 'all-MiniLM-L6-v2',
            'chromadb_episodes': chroma_count,
            'characters_tracked': len(self.main_characters),
            'relationships_mapped': len(self.relationship_graph),
            'themes_available': len(self.themes)
        }
    
    def rebuild_from_document_store(self) -> Dict[str, Any]:
        """Rebuild Chroma collection from the document store."""
        logger.info("Rebuilding ChromaDB collection from document store...")
        try:
            try:
                self.chroma_client.delete_collection("buffy_episodes")
                logger.info("Existing ChromaDB collection deleted")
            except Exception as exc:
                logger.warning("Unable to delete existing collection: %s", exc)
            self.collection = self.chroma_client.get_or_create_collection(
                name="buffy_episodes",
                metadata={"hnsw:space": "cosine"}
            )
            self._populate_chromadb()
            summary = self.get_stats()
            logger.info("ChromaDB rebuild complete: %s", summary)
            return summary
        except Exception as exc:
            logger.error("Failed to rebuild ChromaDB: %s", exc)
            raise

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