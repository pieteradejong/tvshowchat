#!/usr/bin/env python3.12
"""Utility for scraping Buffy episode data and inspecting pipeline status."""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("scrape_episodes")

CONTENT_DIR = Path("app/content")
EPISODES_DIR = Path("app/data/episodes")
EMBEDDINGS_DIR = Path("app/data/embeddings")
CHROMA_DIR = Path("app/data/chroma")


def list_content_files() -> List[Path]:
    return sorted(CONTENT_DIR.glob("buffy_all_seasons_*.json"))


def load_latest_content() -> Dict:
    files = list_content_files()
    if not files:
        return {}
    latest = max(files, key=lambda p: p.stat().st_mtime)
    with latest.open("r", encoding="utf-8") as f:
        return json.load(f)


def status() -> int:
    print("=== Scraper Status ===")

    # Content files
    content_files = list_content_files()
    print(f"Content JSON files: {len(content_files)}")
    if content_files:
        latest = max(content_files, key=lambda p: p.stat().st_mtime)
        print(f"Latest content file: {latest.name}")
        data = load_latest_content()
        seasons = list(data.keys())
        print(f"Seasons available: {seasons if seasons else 'None'}")
        if "season_1" in data:
            print(f"Season 1 episodes: {len(data['season_1'])}")
    else:
        print("No content files found.")

    # Document store
    print("\nDocument store:")
    if EPISODES_DIR.exists():
        season_files = list(EPISODES_DIR.glob("season_*.json"))
        print(f"Season files: {len(season_files)}")
        if season_files:
            with season_files[0].open("r", encoding="utf-8") as f:
                season_data = json.load(f)
                print(f"Sample season ({season_files[0].name}) episodes: {len(season_data)}")
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
            print(f"Collection count: {collection.count()}")
        except Exception as exc:  # pragma: no cover - informational only
            print(f"Failed to inspect ChromaDB collection: {exc}")
    else:
        print("ChromaDB file not found.")

    print("\nStatus check complete.")
    return 0


def crawl_all() -> int:
    try:
        from app.services.scraping.crawl import fetch_parse_save_episodes
    except ImportError as exc:
        logger.error("Could not import crawler: %s", exc)
        return 1

    logger.info("Starting full crawl of all seasons...")
    try:
        fetch_parse_save_episodes()
    except Exception as exc:
        logger.error("Crawl failed: %s", exc)
        return 1

    logger.info("Crawl completed successfully.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape Buffy episode data.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--all", action="store_true", help="Scrape all seasons (web request)")
    group.add_argument("--season", type=int, help="Scrape a single season (1-7)")
    parser.add_argument("--status", action="store_true", help="Show pipeline status")
    parser.add_argument("--force", action="store_true", help="Force crawl even if data exists")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.status:
        return status()

    if args.season and args.season != 1:
        logger.error("Season-specific crawl not yet implemented. Use --all or season 1.")
        return 1

    if args.season == 1 or args.all:
        if not args.force and list_content_files():
            logger.warning("Content files already exist. Use --force to re-crawl.")
            return 0
        return crawl_all()

    logger.info("No action requested. Use --status, --all, or --season.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
