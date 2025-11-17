from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Tuple
import re
import logging

logger = logging.getLogger(__name__)


STOPWORDS = {
    "the","and","a","an","of","to","in","on","for","with","as","at","by","from","that","this","it","is",
    "are","was","were","be","been","or","but","not","into","their","his","her","they","them","he","she",
    "we","you","i","its","it's","about","over","after","before","when","where","who","whom","which",
    "while","then","than","so","because","just","also","more","most","very","can","could","should",
    "would","will","may","might","one","two","three","new","old","out","up","down","again","there","here",
}

# Seed list of prominent characters for v1 (can be refined later)
MAIN_CHARACTERS = [
    "Buffy", "Willow", "Xander", "Giles", "Angel", "Cordelia",
    "Spike", "Oz", "Anya", "Faith", "Dawn", "Tara", "Riley", "Joyce", "Wesley",
]


def _normalize_text(text: str) -> str:
    return re.sub(r"[^a-zA-Z0-9\s']", " ", text).lower()


def _sentence_split(paragraphs: List[str]) -> List[str]:
    text = " ".join(p.strip() for p in paragraphs if p and p.strip())
    # naive split on sentence terminators
    sentences = re.split(r"(?<=[.!?])\s+", text)
    return [s.strip() for s in sentences if s.strip()]


def _extract_keywords(sentences: List[str], top_k: int = 5) -> List[str]:
    freq: Dict[str, int] = {}
    for s in sentences:
        for tok in _normalize_text(s).split():
            if tok in STOPWORDS or len(tok) < 3:
                continue
            freq[tok] = freq.get(tok, 0) + 1
    # simple frequency top-k
    return [w for w, _ in sorted(freq.items(), key=lambda kv: (-kv[1], kv[0]))[:top_k]]


def _character_presence(sentences: List[str], characters: List[str]) -> Dict[str, int]:
    presence: Dict[str, int] = {c: 0 for c in characters}
    full_text = " ".join(sentences)
    for c in characters:
        # count case-insensitive mentions; handle simple possessives
        pattern = re.compile(rf"\b{re.escape(c)}('?s)?\b", re.IGNORECASE)
        presence[c] = len(pattern.findall(full_text))
    return presence


def _episode_id(season: int, episode_number: str) -> str:
    # Expect episode_number already zero-padded; be defensive
    try:
        ep = int(episode_number)
    except Exception:
        ep = int(re.sub(r"[^0-9]", "", episode_number) or "0")
    return f"s{season:02}e{ep:02}"


def build_v1_datasets(
    episodes_dir: Path = Path("app/data/episodes"),
    output_dir: Path = Path("app/data/episodes"),
) -> Tuple[Path, Path]:
    """
    Build:
      - episodes.json: flat list of episodes with basic metadata and lightweight features
      - character_arcs.json: character -> [{episode_id, presence_score}]
    """
    episodes: List[Dict] = []
    character_time_series: Dict[str, List[Tuple[str, int]]] = {c: [] for c in MAIN_CHARACTERS}

    # Iterate all seasons
    for season_file in sorted(episodes_dir.glob("season_*.json")):
        season_num = int(season_file.stem.split("_")[1])
        with season_file.open("r", encoding="utf-8") as f:
            season_data = json.load(f)

        # each key like "01": { ... }
        for ep_key in sorted(season_data.keys()):
            ep = season_data[ep_key]
            title = ep.get("title") or ep.get("episode_title") or ""
            airdate = ep.get("airdate") or ep.get("episode_airdate") or ""
            summary_list = ep.get("summary") or ep.get("episode_summary") or []
            sentences = _sentence_split(summary_list)
            logline = sentences[0] if sentences else title
            keywords = _extract_keywords(sentences, top_k=5)
            presence = _character_presence(sentences, MAIN_CHARACTERS)
            eid = _episode_id(season_num, ep.get("episode_number") or ep_key)

            episodes.append({
                "id": eid,
                "season": season_num,
                "episode": int(ep_key),
                "title": title,
                "airdate": airdate,
                "logline": logline,
                "themes": keywords[:5],
                # keep open fields for future (sentiment, quotes)
            })

            for character, count in presence.items():
                if count > 0:
                    character_time_series[character].append((eid, count))

    # Normalize character arcs: sort by episode_id
    character_arcs: Dict[str, List[Dict]] = {}
    for character, points in character_time_series.items():
        # Sort by season/episode derived from id
        points_sorted = sorted(
            points,
            key=lambda x: (int(x[0][1:3]), int(x[0][4:6]))  # sXXeYY
        )
        character_arcs[character] = [
            {"episode_id": eid, "presence_score": score} for eid, score in points_sorted
        ]

    output_dir.mkdir(parents=True, exist_ok=True)
    episodes_path = output_dir / "episodes.json"
    arcs_path = output_dir / "character_arcs.json"
    with episodes_path.open("w", encoding="utf-8") as f:
        json.dump(episodes, f, indent=2)
    with arcs_path.open("w", encoding="utf-8") as f:
        json.dump(character_arcs, f, indent=2)

    return episodes_path, arcs_path


def build_quotes_dataset(
    content_file: Path = Path("app/content/btvs_all_seasons.json"),
    output_dir: Path = Path("app/data/episodes"),
) -> Path:
    """
    Extract quotes from content file and build quotes.json.
    Quotes are organized by character (if extractable), season, and episode.
    """
    quotes_list: List[Dict] = []
    by_character: Dict[str, List[str]] = {}  # character -> list of quote IDs
    by_season: Dict[int, List[str]] = {}  # season -> list of quote IDs
    
    if not content_file.exists():
        logger.warning(f"Content file not found: {content_file}")
        return output_dir / "quotes.json"
    
    with content_file.open("r", encoding="utf-8") as f:
        content_data = json.load(f)
    
    quote_counter = 0
    
    for season_key, season_data in sorted(content_data.items()):
        if not season_key.startswith("season_"):
            continue
        season_num = int(season_key.split("_")[1])
        by_season[season_num] = []
        
        for ep_key in sorted(season_data.keys()):
            ep = season_data[ep_key]
            episode_quotes = ep.get("episode_quotes") or ep.get("quotes") or []
            if not episode_quotes:
                continue
            
            title = ep.get("episode_title") or ep.get("title") or ""
            episode_num = int(ep_key) if ep_key.isdigit() else int(re.sub(r"[^0-9]", "", ep_key) or "0")
            eid = _episode_id(season_num, str(episode_num))
            
            for quote_text in episode_quotes:
                if not quote_text or not quote_text.strip():
                    continue
                
                quote_counter += 1
                quote_id = f"{eid}-quote-{quote_counter}"
                
                # Try to extract character name from quote (simple heuristic)
                character = None
                quote_lower = quote_text.lower()
                for char in MAIN_CHARACTERS:
                    # Check if character name appears near quote markers or at start
                    if f"{char.lower()}:" in quote_lower or quote_lower.startswith(char.lower()):
                        character = char
                        break
                
                quote_obj = {
                    "id": quote_id,
                    "episode_id": eid,
                    "text": quote_text.strip(),
                    "character": character,
                    "season": season_num,
                    "episode": episode_num,
                    "title": title,
                }
                quotes_list.append(quote_obj)
                by_season[season_num].append(quote_id)
                
                if character:
                    if character not in by_character:
                        by_character[character] = []
                    by_character[character].append(quote_id)
    
    output = {
        "quotes": quotes_list,
        "by_character": by_character,
        "by_season": {str(k): v for k, v in by_season.items()},
    }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    quotes_path = output_dir / "quotes.json"
    with quotes_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    return quotes_path


def build_character_moments_dataset(
    content_file: Path = Path("app/content/btvs_all_seasons.json"),
    output_dir: Path = Path("app/data/episodes"),
) -> Path:
    """
    Extract character moments (first appearances, last appearances, deaths).
    Build character_moments.json with timeline events.
    """
    moments_list: List[Dict] = []
    by_character: Dict[str, List[str]] = {}  # character -> list of moment IDs
    
    if not content_file.exists():
        logger.warning(f"Content file not found: {content_file}")
        return output_dir / "character_moments.json"
    
    with content_file.open("r", encoding="utf-8") as f:
        content_data = json.load(f)
    
    # Track first appearances
    first_seen: Dict[str, Tuple[int, int, str]] = {}  # character -> (season, episode, episode_id)
    
    for season_key, season_data in sorted(content_data.items()):
        if not season_key.startswith("season_"):
            continue
        season_num = int(season_key.split("_")[1])
        
        for ep_key in sorted(season_data.keys()):
            ep = season_data[ep_key]
            episode_num = int(ep_key) if ep_key.isdigit() else int(re.sub(r"[^0-9]", "", ep_key) or "0")
            eid = _episode_id(season_num, str(episode_num))
            title = ep.get("episode_title") or ep.get("title") or ""
            
            # First appearances
            first_appearances = ep.get("first_appearances") or []
            for char in first_appearances:
                if char and char not in first_seen:
                    first_seen[char] = (season_num, episode_num, eid)
                    moment_id = f"{eid}-first-{char}"
                    moment_obj = {
                        "id": moment_id,
                        "character": char,
                        "episode_id": eid,
                        "type": "first_appearance",
                        "season": season_num,
                        "episode": episode_num,
                        "title": title,
                    }
                    moments_list.append(moment_obj)
                    if char not in by_character:
                        by_character[char] = []
                    by_character[char].append(moment_id)
            
            # Character deaths (check summary for death mentions)
            summary_list = ep.get("episode_summary") or ep.get("summary") or []
            summary_text = " ".join(summary_list).lower()
            # Simple heuristic: look for "dies", "killed", "death" near character names
            for char in MAIN_CHARACTERS:
                char_lower = char.lower()
                if char_lower in summary_text:
                    # Check for death indicators near character name
                    death_patterns = [
                        f"{char_lower} dies",
                        f"{char_lower} is killed",
                        f"{char_lower} death",
                        f"kills {char_lower}",
                    ]
                    if any(pattern in summary_text for pattern in death_patterns):
                        moment_id = f"{eid}-death-{char}"
                        # Check if we already have a death moment for this character
                        if not any(m.get("character") == char and m.get("type") == "death" for m in moments_list):
                            moment_obj = {
                                "id": moment_id,
                                "character": char,
                                "episode_id": eid,
                                "type": "death",
                                "season": season_num,
                                "episode": episode_num,
                                "title": title,
                            }
                            moments_list.append(moment_obj)
                            if char not in by_character:
                                by_character[char] = []
                            by_character[char].append(moment_id)
    
    # Calculate last appearances from character arcs
    arcs_path = output_dir / "character_arcs.json"
    if arcs_path.exists():
        with arcs_path.open("r", encoding="utf-8") as f:
            arcs = json.load(f)
        
        for char, arc_points in arcs.items():
            if not arc_points:
                continue
            # Last point in arc is last appearance
            last_point = arc_points[-1]
            last_eid = last_point["episode_id"]
            # Parse season/episode from ID
            season_num = int(last_eid[1:3])
            episode_num = int(last_eid[4:6])
            
            # Get episode title
            title = ""
            for season_key, season_data in content_data.items():
                if season_key == f"season_{season_num}":
                    ep_key = f"{episode_num:02d}"
                    if ep_key in season_data:
                        title = season_data[ep_key].get("episode_title") or season_data[ep_key].get("title") or ""
                    break
            
            moment_id = f"{last_eid}-last-{char}"
            moment_obj = {
                "id": moment_id,
                "character": char,
                "episode_id": last_eid,
                "type": "last_appearance",
                "season": season_num,
                "episode": episode_num,
                "title": title,
            }
            moments_list.append(moment_obj)
            if char not in by_character:
                by_character[char] = []
            by_character[char].append(moment_id)
    
    output = {
        "moments": moments_list,
        "by_character": by_character,
    }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    moments_path = output_dir / "character_moments.json"
    with moments_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    return moments_path


def build_season_stats(
    episodes_path: Path = Path("app/data/episodes/episodes.json"),
    arcs_path: Path = Path("app/data/episodes/character_arcs.json"),
    output_dir: Path = Path("app/data/episodes"),
) -> Path:
    """
    Build season comparison statistics from existing episodes.json and character_arcs.json.
    """
    if not episodes_path.exists():
        logger.warning(f"Episodes file not found: {episodes_path}")
        return output_dir / "season_stats.json"
    
    with episodes_path.open("r", encoding="utf-8") as f:
        episodes = json.load(f)
    
    arcs = {}
    if arcs_path.exists():
        with arcs_path.open("r", encoding="utf-8") as f:
            arcs = json.load(f)
    
    # Group episodes by season
    seasons_data: Dict[int, Dict] = {}
    
    for ep in episodes:
        season = ep["season"]
        if season not in seasons_data:
            seasons_data[season] = {
                "episode_count": 0,
                "characters": {},
                "themes": [],
                "theme_counts": {},
            }
        
        seasons_data[season]["episode_count"] += 1
        
        # Aggregate themes
        for theme in ep.get("themes", []):
            if theme:
                seasons_data[season]["theme_counts"][theme] = seasons_data[season]["theme_counts"].get(theme, 0) + 1
                if theme not in seasons_data[season]["themes"]:
                    seasons_data[season]["themes"].append(theme)
    
    # Aggregate character presence from arcs
    for char, arc_points in arcs.items():
        for point in arc_points:
            eid = point["episode_id"]
            season = int(eid[1:3])
            if season in seasons_data:
                if char not in seasons_data[season]["characters"]:
                    seasons_data[season]["characters"][char] = 0
                seasons_data[season]["characters"][char] += 1
    
    # Sort themes by frequency
    for season in seasons_data.values():
        season["themes"] = sorted(
            season["themes"],
            key=lambda t: season["theme_counts"].get(t, 0),
            reverse=True
        )[:10]  # Top 10 themes
    
    output = {
        "seasons": {str(k): v for k, v in sorted(seasons_data.items())},
    }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    stats_path = output_dir / "season_stats.json"
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, indent=2)
    
    return stats_path


if __name__ == "__main__":
    build_v1_datasets()

