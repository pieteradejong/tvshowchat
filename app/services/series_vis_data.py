from __future__ import annotations
import json
from pathlib import Path
from typing import Dict, List, Tuple
import re


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


if __name__ == "__main__":
    build_v1_datasets()

