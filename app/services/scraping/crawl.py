import json
import requests
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer
from typing import Dict
import time
from numpy import float32

BASE_URL = "https://buffy.fandom.com/"

"""
Script tailored for crawling specific content from specific URLs:
specifically, synopses and summaries for all available episode per season 
of Buffy the Vampire Slayer.
Sole purpose is to seed a vector database to enable similarity searches. 
"""


def fetch_parse_save_episodes():
    url = "https://buffy.fandom.com/wiki/List_of_Buffy_the_Vampire_Slayer_episodes"
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: url GET request failed: {response.status_code}")
        return

    soup = BeautifulSoup(response.content, "lxml")
    embedder = SentenceTransformer("all-MiniLM-L6-v2")
    result = {}

    # Tracking season number separately assumes non-changing DOM,
    # but this entire crawler does so, so we'll just do what is expedient.
    # Optimize for expedience, data completeness, and acquintance with bs4.
    tables = soup.find_all("table", class_="wikitable")
    season_number = 1
    print(
        f"Expect to find 7 tables, consistent with number of seasons. \
            Found: [{len(tables)}]"
    )
    for t in tables:
        curr_season = {}

        t_body = t.find("tbody")
        relevant_trs = [
            child
            for child in t_body.find_all("tr")
            if child.name == "tr" and len(child.find_all("td", recursive=False)) == 4
        ]

        # Each tr contains data for one episode
        for tr in relevant_trs:
            curr_episode = {}

            tds = tr.find_all("td")
            episode_number_text = tds[0].text.strip()
            if episode_number_text != '01': break

            curr_episode["episode_number"] = episode_number_text
            episode_airdate_text = tds[3].text.strip()
            curr_episode["episode_airdate"] = episode_airdate_text

            episode_title = tds[2].find("a")["title"].strip()
            curr_episode["episode_title"] = episode_title

            # Crawl episode page for synopsis and summary
            episode_link_relative = tds[2].find("a")["href"]
            full_episode_url = BASE_URL + episode_link_relative
            print(f"Crawling season {season_number} - episode {episode_number_text}")
            episode_page_data = extract_episode(full_episode_url)

            # synopsis not needed for now
            # curr_episode["episode_synopsis"] = episode_page_data["synopsis"]
            curr_episode["episode_summary"] = episode_page_data["summary"]

            # create and save embedding for summary
            episode_summary_as_str = "".join(episode_page_data["summary"])
            episode_summary_as_embedding = embedder.encode(episode_summary_as_str).astype(float32).tolist()
            print(f'summary embedding is of type: {type(episode_summary_as_embedding)}')
            # print(f'summary embedding sample: {episode_summary_as_embedding[:100]}')
            # print('any newslines in vector:')
            # print(any("\n" in element for element in episode_summary_as_embedding))
            for el in episode_summary_as_embedding:
                print(type(el))
            
                
            curr_episode["summary_embedding"] = episode_summary_as_embedding

            curr_season[episode_number_text] = curr_episode
            # end of row = episode

        result[f"season_{season_number}"] = curr_season
        season_number += 1
        # end of table = season
    # end of all tables / seasons

    # Save result dict to buffy_all_seasons_<timestamp>.json
    timestamp = str(int(time.time()))
    save_to_filename = f"app/content/buffy_all_seasons_{timestamp}.json"

    with open(save_to_filename, "w") as f:
        json.dump(result, f, indent=4)

    print(f"Saved crawl results to {save_to_filename}")

    """
    Crawl goal:
    [
        "season 1" : [
            "episode 19": {
                "season": 1,
                "number": 19,
                "title": "Empty Places",
                "air_date": "April 29, 2003",
                "writer": "Drew Z. Greenberg",
                "director": "James A. Contner",
                "synopsis": "",
                "summary": "",
            },
            "episode 20": {},
            ...
        ]
    ]
    """


def extract_episode(url: str) -> dict:
    response = requests.get(url)
    if response.status_code != 200:
        print(f"Error: episode page GET request failed: {response.status_code}")
        return {}

    soup = BeautifulSoup(response.content, "lxml")
    result = {}

    for header in ["Synopsis", "Summary"]:
        target_span = soup.find("span", {"id": "Summary"})

        if target_span:
            parent_h2 = target_span.find_parent("h2")
            if parent_h2:
                paragraphs = []
                for sibling in parent_h2.find_next_siblings():
                    if sibling.name == "p":
                        paragraphs.append(sibling.text.strip())
                    else:
                        break

                result[header.lower()] = paragraphs

    return result


"""
Script tailored for crawling specific content from specific URLs, for
Buffy the Vampire Slayer season summaries and synopses. Sole purpose is 
to generate initial content to 
seed vector database. Creating quality content for such purposes is likely
to remain closer to one-off tasks than automatable.
"""


def fetch_and_parse(url: str) -> Dict[str, str]:
    response = requests.get(url)
    if response.status_code != 200:
        return {}

    soup = BeautifulSoup(response.content, "lxml")
    result = {}

    for header in ["Synopsis", "Summary"]:
        target_span = soup.find("span", {"id": "Summary"})

        if target_span:
            parent_h2 = target_span.find_parent("h2")
            if parent_h2:
                paragraphs = []
                for sibling in parent_h2.find_next_siblings():
                    if sibling.name == "p":
                        paragraphs.append(sibling.text)
                    else:
                        break

                result[header] = paragraphs

    print(f"result: {result}")
    return result


def main():
    base_url = "https://buffy.fandom.com/wiki/Buffy_the_Vampire_Slayer_season_"
    seasons = range(1, 8)

    all_data = {}

    for season in seasons:
        url = f"{base_url}{season}"
        print(f"Fetching data from {url}")
        parsed_data = fetch_and_parse(url)
        print(f"parsed data: {parsed_data}")
        if parsed_data:
            all_data[f"Season {season}"] = parsed_data

    with open("buffy_data.json", "w") as f:
        json.dump(all_data, f, indent=4)


if __name__ == "__main__":
    # main()
    fetch_parse_save_episodes()
