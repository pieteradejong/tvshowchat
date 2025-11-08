#!/usr/bin/env python3.12
"""Utility for scraping Buffy episode data and inspecting pipeline status."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("scrape_episodes")
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))


CONTENT_DIR = ROOT_DIR / "app/content"
CONTENT_FILE = CONTENT_DIR / "btvs_all_seasons.json"
EPISODES_DIR = ROOT_DIR / "app/data/episodes"
EMBEDDINGS_DIR = ROOT_DIR / "app/data/embeddings"
CHROMA_DIR = ROOT_DIR / "app/data/chroma"


SEASON_RANGE = range(1, 8)


def load_latest_content() -> Dict[str, Any]:
    if not CONTENT_FILE.exists():
        return {}
    with CONTENT_FILE.open("r", encoding="utf-8") as f:
        return json.load(f)


def _season_counts_from_content(data: Dict) -> Dict[int, int]:
    counts: Dict[int, int] = {}
    for key, episodes in data.items():
        try:
            season_num = int(key.split('_')[1])
        except (IndexError, ValueError):
            continue
        counts[season_num] = len(episodes)
    return counts


def latest_content_path() -> Optional[Path]:
    return CONTENT_FILE if CONTENT_FILE.exists() else None


def import_latest_content() -> int:
    try:
        from app.services.storage.document_store import get_store
    except ImportError as exc:
        logger.error("Could not import document store: %s", exc)
        return 1

    latest = latest_content_path()
    if not latest:
        logger.error("No content files available. Run the crawler first.")
        return 1

    logger.info("Importing data from %s", latest)
    try:
        store = get_store()
        store.import_from_json(str(latest))
        print(f"Imported data from {latest.name}")
        return 0
    except Exception as exc:
        logger.error("Import failed: %s", exc)
        return 1


def reindex_chromadb() -> int:
    try:
        from app.services.vector_store import get_vector_store
    except ImportError as exc:
        logger.error("Could not import vector store: %s", exc)
        return 1

    try:
        vector_store = get_vector_store()
        summary = vector_store.rebuild_from_document_store()
        print("Reindexed ChromaDB. Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        return 0
    except Exception as exc:
        logger.error("Reindex failed: %s", exc)
        return 1


def status() -> int:
    print("=== Scraper Status ===")

    # Content file
    if CONTENT_FILE.exists():
        relative_path = CONTENT_FILE.relative_to(ROOT_DIR)
        print(f"Content JSON file: {relative_path}")
        data = load_latest_content()
        season_counts = _season_counts_from_content(data)
        if season_counts:
            total = sum(season_counts.values())
            for season in sorted(season_counts):
                print(f"Season {season}: {season_counts[season]} episodes")
            print(f"Total episodes (content): {total}")
        else:
            print("No season data found in latest content file.")
    else:
        print("Content JSON file: missing")

    # Document store
    print("\nDocument store:")
    if EPISODES_DIR.exists():
        season_files = sorted(EPISODES_DIR.glob("season_*.json"))
        print(f"Season files: {len(season_files)}")
        for season_file in season_files:
            try:
                season_num = int(season_file.stem.split('_')[1])
            except (IndexError, ValueError):
                season_num = season_file.stem
            with season_file.open("r", encoding="utf-8") as f:
                season_data = json.load(f)
            print(f"Season {season_num}: {len(season_data)} episodes")
    else:
        print("Document store directory missing.")

    # ChromaDB
    print("\nChromaDB:")
    sqlite_file = CHROMA_DIR / "chroma.sqlite3"
    if sqlite_file.exists():
        size_kb = sqlite_file.stat().st_size / 1024
        print(f"chroma.sqlite3 size: {size_kb:.1f} KB")
        try:
            import chromadb

            client = chromadb.PersistentClient(path=str(CHROMA_DIR.absolute()))
            collection = client.get_collection("buffy_episodes")
            count = collection.count()
            print(f"Collection count: {count}")
        except Exception as exc:  # pragma: no cover - informational only
            print(f"Failed to inspect ChromaDB collection: {exc}")
    else:
        print("ChromaDB file not found.")

    print("\nStatus check complete.")
    return 0



def latest_season_coverage() -> Dict[int, int]:
    data = load_latest_content()
    return _season_counts_from_content(data)


def crawl(target_seasons: Optional[Iterable[int]], force: bool) -> int:
    try:
        from app.services.scraping.crawl import fetch_parse_save_episodes
    except ImportError as exc:
        logger.error("Could not import crawler: %s", exc)
        return 1

    seasons = sorted(set(target_seasons)) if target_seasons else None
    existing_data = load_latest_content()
    coverage = _season_counts_from_content(existing_data)

    if seasons:
        season_labels = ", ".join(f"S{season}" for season in seasons)
        logger.info("Requested crawl for seasons: %s", season_labels)
        if not force and set(seasons).issubset(coverage.keys()):
            logger.warning("All requested seasons already present. Use --force to re-crawl.")
            return 0
    else:
        logger.info("Starting full crawl of all seasons")
        if not force and set(SEASON_RANGE).issubset(coverage.keys()):
            logger.warning("Content file already contains all seasons. Use --force to re-crawl.")
            return 0
        seasons = list(SEASON_RANGE)

    try:
        metadata = fetch_parse_save_episodes(seasons, existing_data)
    except Exception as exc:
        logger.error("Crawl failed: %s", exc)
        return 1

    if not metadata.get("saved"):
        logger.error("Crawl did not complete successfully; see logs above")
        return 1

    logger.info("Crawl completed successfully (%s episodes)", metadata.get("total_episodes", "unknown"))
    print("=== Crawl Summary ===")
    for season, count in sorted(metadata.get("season_counts", {}).items()):
        print(f"Season {season}: {count} episodes")
    combined_counts = metadata.get("combined_counts")
    if combined_counts:
        print("--- Combined Coverage ---")
        for season, count in sorted(combined_counts.items()):
            print(f"Season {season}: {count} episodes")
    print(f"Total episodes: {metadata.get('total_episodes', 'unknown')}")
    print(f"Saved to: {metadata.get('output_file')}")
    if metadata.get("validation_errors"):
        print("Validation warnings:")
        for message in metadata["validation_errors"]:
            print(f" - {message}")
    return 0



def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Buffy episode data.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Scrape all seasons (web request)")
    group.add_argument(
        "--season",
        type=int,
        nargs="+",
        metavar="N",
        help="Scrape specific season(s) (1-7)"
    )
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--import-latest", action="store_true", help="Import latest content JSON into the document store")
    parser.add_argument("--reindex-chroma", action="store_true", help="Rebuild ChromaDB collection from document store")
    parser.add_argument("--force", action="store_true", help="Force crawl even if data exists")
    return parser.parse_args()


def _validate_seasons(values: Iterable[int]) -> List[int]:
    seasons = sorted(set(int(v) for v in values))
    invalid = [s for s in seasons if s not in SEASON_RANGE]
    if invalid:
        raise ValueError(f"Invalid season numbers: {invalid}. Expected values between 1 and 7.")
    return seasons


def main() -> int:
    args = parse_args()

    exit_code = 0

    if args.status:
        status()

    if getattr(args, 'import_latest', False):
        exit_code |= import_latest_content()

    if getattr(args, 'reindex_chroma', False):
        exit_code |= reindex_chromadb()

    try:
        if args.season:
            target = _validate_seasons(args.season)
            exit_code |= crawl(target, args.force)
        elif args.all:
            exit_code |= crawl(list(SEASON_RANGE), args.force)
        elif not (args.status or getattr(args, 'import_latest', False) or getattr(args, 'reindex_chroma', False)):
            logger.info("No action requested. Use --status, --all, --season, --import-latest, or --reindex-chroma.")
    except ValueError as exc:
        logger.error(str(exc))
        return 1

    return 0 if exit_code == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
