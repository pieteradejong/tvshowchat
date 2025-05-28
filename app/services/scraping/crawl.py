import json
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from typing import Dict, Optional
import time
import re
from numpy import float32
import logging
from ratelimit import limits, sleep_and_retry
from tenacity import retry, stop_after_attempt, wait_exponential
from app.services.pipeline.validation import validate_single_episode, validate_episode_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app/logs/scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

BASE_URL = "https://buffy.fandom.com/"
ONE_MINUTE = 60
MAX_REQUESTS_PER_MINUTE = 30

@sleep_and_retry
@limits(calls=MAX_REQUESTS_PER_MINUTE, period=ONE_MINUTE)
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def make_request(url: str) -> Optional[requests.Response]:
    """Make a rate-limited and retried request to the URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed for {url}: {str(e)}")
        raise

def clean_text(text: str) -> str:
    """Clean and normalize text content."""
    # Remove extra whitespace
    text = ' '.join(text.split())
    # Remove special characters but keep basic punctuation
    text = re.sub(r'[^\w\s.,!?-]', '', text)
    return text.strip()

def extract_episode(url: str) -> Dict[str, list]:
    """Extract episode data with improved error handling."""
    try:
        response = make_request(url)
        if not response:
            return {}

        soup = BeautifulSoup(response.content, "lxml")
        result = {}

        for header in ["Synopsis", "Summary"]:
            target_span = soup.find("span", {"id": "Summary"})
            if not target_span:
                logger.warning(f"Summary section not found for {url}")
                continue

            parent_h2 = target_span.find_parent("h2")
            if not parent_h2:
                logger.warning(f"Summary header not found for {url}")
                continue

            paragraphs = []
            for sibling in parent_h2.find_next_siblings():
                if sibling.name == "p":
                    cleaned_text = clean_text(sibling.text)
                    if cleaned_text:  # Only add non-empty paragraphs
                        paragraphs.append(cleaned_text)
                elif sibling.name == "h2":  # Stop at next section
                    break

            if paragraphs:
                result[header.lower()] = paragraphs
            else:
                logger.warning(f"No paragraphs found for {header} in {url}")

        return result
    except Exception as e:
        logger.error(f"Error extracting episode data from {url}: {str(e)}")
        return {}

def fetch_parse_save_episodes():
    """Main function to fetch, parse, and save episode data with validation."""
    try:
        url = f"{BASE_URL}wiki/List_of_Buffy_the_Vampire_Slayer_episodes"
        response = make_request(url)
        if not response:
            return

        soup = BeautifulSoup(response.content, "lxml")
        embedder = SentenceTransformer("all-MiniLM-L6-v2")
        result = {}
        validation_errors = []

        tables = soup.find_all("table", class_="wikitable")
        logger.info(f"Found {len(tables)} season tables")

        # MVP: Only process season 1 (the first table)
        if tables:
            table = tables[0]
            season_num = 1
            curr_season = {}
            logger.info(f"Processing season {season_num}")

            t_body = table.find("tbody")
            if not t_body:
                logger.warning(f"No tbody found for season {season_num}")
            else:
                relevant_trs = [
                    child for child in t_body.find_all("tr")
                    if child.name == "tr" and len(child.find_all("td", recursive=False)) == 4
                ]

                for tr in relevant_trs:
                    try:
                        tds = tr.find_all("td")
                        if len(tds) < 4:
                            continue

                        episode_number = tds[0].text.strip()
                        if not episode_number.isdigit():
                            continue

                        episode_data = {
                            "episode_number": episode_number.zfill(2),
                            "episode_airdate": tds[3].text.strip(),
                            "episode_title": tds[2].find("a")["title"].strip(),
                        }

                        # Get episode details
                        episode_link = tds[2].find("a")["href"]
                        full_url = BASE_URL + episode_link
                        logger.info(f"Crawling season {season_num} - episode {episode_number}")
                        
                        episode_page_data = extract_episode(full_url)
                        if not episode_page_data.get("summary"):
                            logger.warning(f"No summary found for episode {episode_number}")
                            continue

                        episode_data["episode_summary"] = episode_page_data["summary"]
                        
                        # Generate embedding
                        summary_text = " ".join(episode_page_data["summary"])
                        episode_data["summary_embedding"] = embedder.encode(summary_text).astype(float32).tolist()

                        # Validate episode data
                        try:
                            validated_episode = validate_single_episode(episode_data)
                            curr_season[episode_number.zfill(2)] = validated_episode.dict()
                        except ValueError as e:
                            validation_errors.append(f"Season {season_num}, Episode {episode_number}: {str(e)}")
                            continue

                    except Exception as e:
                        logger.error(f"Error processing episode in season {season_num}: {str(e)}")
                        continue

                if curr_season:
                    result[f"season_{season_num}"] = curr_season
        else:
            logger.error("No season tables found!")

        # Validate complete dataset
        try:
            validated_data = validate_episode_data(result)
            timestamp = str(int(time.time()))
            save_to_filename = f"app/content/buffy_all_seasons_{timestamp}.json"

            with open(save_to_filename, "w") as f:
                json.dump(validated_data.dict()["__root__"], f, indent=4)

            logger.info(f"Saved validated crawl results to {save_to_filename}")
            
            if validation_errors:
                logger.warning("Validation errors occurred:")
                for error in validation_errors:
                    logger.warning(error)

        except ValueError as e:
            logger.error(f"Dataset validation failed: {str(e)}")

    except Exception as e:
        logger.error(f"Fatal error in fetch_parse_save_episodes: {str(e)}")
        raise

if __name__ == "__main__":
    fetch_parse_save_episodes()
