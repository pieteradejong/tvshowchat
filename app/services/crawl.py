import json
import requests
from bs4 import BeautifulSoup
from typing import Dict

"""
Script tailored for crawling specific content from specific URLs, for
Buffy the Vampire Slayer. Sole purpose is to generate initial content to 
seed vector database. Creating quality content for such purposes is likely
to remain closer to one-off tasks than automatable.
"""

def fetch_and_parse(url: str) -> Dict[str, str]:
    response = requests.get(url)
    if response.status_code != 200:
        return {}
    
    soup = BeautifulSoup(response.content, 'lxml')
    result = {}

    for header in ["Synopsis", "Summary"]:
        target_span = soup.find('span', {'id': 'Summary'})

        if target_span:
            parent_h2 = target_span.find_parent('h2')
            if parent_h2:
                paragraphs = []
                for sibling in parent_h2.find_next_siblings():
                    if sibling.name == 'p':
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
    main()
