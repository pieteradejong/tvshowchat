import json
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from typing import Dict, Optional, Any
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

def extract_episode(url: str) -> Dict[str, Any]:
    """Extract episode data with improved error handling."""
    try:
        response = make_request(url)
        if not response:
            return {}

        soup = BeautifulSoup(response.content, "lxml")
        result = {}

        # Extract basic content sections
        for section in [
            "Synopsis", "Summary", "Quotes", "Trivia", "Continuity", 
            "Cultural References", "Music", "Production", "Reception",
            "Appearances", "Death Count", "Body Count"
        ]:
            section_id = section.lower().replace(" ", "_")
            target_span = soup.find("span", {"id": section})
            if not target_span:
                continue

            parent_h2 = target_span.find_parent("h2")
            if not parent_h2:
                continue

            paragraphs = []
            for sibling in parent_h2.find_next_siblings():
                if sibling.name == "p":
                    cleaned_text = clean_text(sibling.text)
                    if cleaned_text:
                        paragraphs.append(cleaned_text)
                elif sibling.name == "h2":  # Stop at next section
                    break

            if paragraphs:
                result[section_id] = paragraphs

        # Extract production info from infobox
        infobox = soup.find("table", {"class": "infobox"})
        if infobox:
            production_info = {
                "director": None,
                "writer": None,
                "production_code": None,
                "us_viewers_millions": None,
                "original_air_date": None,
                "filming_location": None,
                "network": None,
                "running_time": None,
                "budget": None
            }
            
            for row in infobox.find_all("tr"):
                header = row.find("th")
                value = row.find("td")
                if header and value:
                    key = clean_text(header.text).lower().replace(" ", "_")
                    val = clean_text(value.text)
                    
                    if key in production_info:
                        if key == "us_viewers":
                            match = re.search(r'(\d+\.?\d*)\s*million', val)
                            if match:
                                production_info[key] = float(match.group(1))
                        elif key == "budget":
                            match = re.search(r'\$(\d+(?:,\d+)*)', val)
                            if match:
                                production_info[key] = int(match.group(1).replace(',', ''))
                        else:
                            production_info[key] = val
            
            result.update({k: v for k, v in production_info.items() if v is not None})

        # Extract character information
        character_sections = {
            "cast": {"id": "Cast", "categories": ["main_cast", "guest_stars", "recurring_characters", "first_appearances", "last_appearances"]},
            "characters": {"id": "Characters", "categories": ["characters_introduced", "characters_mentioned", "characters_died"]},
            "mythology": {"id": "Mythology", "categories": ["mythology_references", "prophecies", "arc_connections"]}
        }

        for section_name, section_info in character_sections.items():
            section = soup.find("span", {"id": section_info["id"]})
            if section:
                parent_h2 = section.find_parent("h2")
                if parent_h2:
                    section_data = {cat: [] for cat in section_info["categories"]}
                    current_category = None
                    
                    for sibling in parent_h2.find_next_siblings():
                        if sibling.name == "h3":
                            header = clean_text(sibling.text).lower()
                            # Map header to category
                            if "main" in header or "regular" in header:
                                current_category = "main_cast"
                            elif "guest" in header:
                                current_category = "guest_stars"
                            elif "recurring" in header:
                                current_category = "recurring_characters"
                            elif "first" in header:
                                current_category = "first_appearances"
                            elif "last" in header:
                                current_category = "last_appearances"
                            elif "introduced" in header:
                                current_category = "characters_introduced"
                            elif "mentioned" in header:
                                current_category = "characters_mentioned"
                            elif "died" in header or "death" in header:
                                current_category = "characters_died"
                            elif "mythology" in header:
                                current_category = "mythology_references"
                            elif "prophecy" in header:
                                current_category = "prophecies"
                            elif "arc" in header or "connection" in header:
                                current_category = "arc_connections"
                        elif sibling.name == "ul" and current_category:
                            for li in sibling.find_all("li"):
                                name = clean_text(li.text)
                                if name:
                                    section_data[current_category].append(name)
                        elif sibling.name == "h2":
                            break
                    
                    # Add non-empty categories to result
                    result.update({f"{section_name}_{k}": v for k, v in section_data.items() if v})

        # Extract awards and reception
        awards_section = soup.find("span", {"id": "Awards"})
        if awards_section:
            parent_h2 = awards_section.find_parent("h2")
            if parent_h2:
                awards = []
                for sibling in parent_h2.find_next_siblings():
                    if sibling.name == "ul":
                        for li in sibling.find_all("li"):
                            award = clean_text(li.text)
                            if award:
                                awards.append(award)
                    elif sibling.name == "h2":
                        break
                if awards:
                    result["awards"] = awards

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

        # Process all seasons
        for season_idx, table in enumerate(tables, 1):
            season_num = season_idx
            curr_season = {}
            logger.info(f"Processing season {season_num}")

            t_body = table.find("tbody")
            if not t_body:
                logger.warning(f"No tbody found for season {season_num}")
                continue

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
                        "season_number": season_num
                    }

                    # Get episode details
                    episode_link = tds[2].find("a")["href"]
                    full_url = BASE_URL + episode_link
                    logger.info(f"Crawling season {season_num} - episode {episode_number}")
                    
                    episode_page_data = extract_episode(full_url)
                    if not episode_page_data.get("summary"):
                        logger.warning(f"No summary found for episode {episode_number}")
                        continue

                    # Map scraped data to our model
                    episode_data.update({
                        "episode_summary": episode_page_data.get("summary", []),
                        "episode_synopsis": episode_page_data.get("synopsis"),
                        "episode_quotes": episode_page_data.get("quotes"),
                        "episode_trivia": episode_page_data.get("trivia"),
                        "director": episode_page_data.get("director"),
                        "writer": episode_page_data.get("writer"),
                        "production_code": episode_page_data.get("production_code"),
                        "us_viewers_millions": episode_page_data.get("us_viewers_millions"),
                        "guest_stars": episode_page_data.get("guest_stars"),
                        "recurring_characters": episode_page_data.get("recurring_characters"),
                        "first_appearances": episode_page_data.get("first_appearances"),
                        "continuity_notes": episode_page_data.get("continuity"),
                        "cultural_references": episode_page_data.get("cultural_references"),
                        "music": episode_page_data.get("music")
                    })
                    
                    # Generate embeddings
                    summary_text = " ".join(episode_page_data.get("summary", []))
                    episode_data["summary_embedding"] = embedder.encode(summary_text).astype(float32).tolist()
                    
                    if episode_page_data.get("synopsis"):
                        synopsis_text = " ".join(episode_page_data["synopsis"])
                        episode_data["synopsis_embedding"] = embedder.encode(synopsis_text).astype(float32).tolist()
                    
                    if episode_page_data.get("quotes"):
                        quotes_text = " ".join(episode_page_data["quotes"])
                        episode_data["quotes_embedding"] = embedder.encode(quotes_text).astype(float32).tolist()

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

        # Validate and save complete dataset
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
