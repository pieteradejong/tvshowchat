import json
import requests
from bs4 import BeautifulSoup
from typing import Dict

def fetch_and_parse(url: str) -> Dict[str, str]:
    response = requests.get(url)
    if response.status_code != 200:
        return {}
    
    soup = BeautifulSoup(response.content, 'html.parser')
    result = {}

    for key in ["Synopsis", "Summary"]:
        # TODO: find span with id "Synopsis" and then all <p>s innerHTML
        section = soup.find('span', {'id': key})
        if section:
            content = []
            for elem in section.find_next_siblings():
                if elem.name and elem.name.startswith('h'):
                    break  # Stop when reaching the next header
                if elem.name:
                    content.append(str(elem))
            result[key] = ' '.join(content)

    return result

def main():
    base_url = "https://buffy.fandom.com/wiki/Buffy_the_Vampire_Slayer_season_"
    seasons = range(1, 8)

    all_data = {}

    for season in seasons:
        url = f"{base_url}{season}"
        print(f"Fetching data from {url}")
        parsed_data = fetch_and_parse(url)
        if parsed_data:
            all_data[f"Season {season}"] = parsed_data

    with open("buffy_data.json", "w") as f:
        json.dump(all_data, f, indent=4)

if __name__ == "__main__":
    main()

