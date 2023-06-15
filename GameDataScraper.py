import os
import csv
import time
import requests
import logging
from retrying import retry
from bs4 import BeautifulSoup

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Retry parameters
retry_params = {
    "stop_max_attempt_number": 3,
    "wait_exponential_multiplier": 1000,
    "wait_exponential_max": 10000,
}


@retry(**retry_params)
def get_page_content(url, proxies=None):
    response = requests.get(url, proxies=proxies)

    # Handle rate limiting
    if response.status_code == 429:
        logging.error("Rate limit reached. Sleeping for a minute...")
        time.sleep(60)
        return get_page_content(url, proxies=proxies)

    return BeautifulSoup(response.text, "html.parser")


def get_boxscore_links(year, proxies=None):
    url = f"https://www.baseball-reference.com/leagues/majors/{year}-schedule.shtml"
    soup = get_page_content(url, proxies=proxies)
    boxscore_links = [link["href"] for link in soup.find_all("a", string="Boxscore")]
    return boxscore_links


def parse_boxscore_page(url):
    response = requests.get(
        url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"}
    )
    if response.status_code != 200:
        raise Exception(f"Failed to load page {url}")

    soup = BeautifulSoup(response.content, "html.parser")

    # Extract home and away teams from the page title
    title = soup.find("title").text
    teams = title.split(" vs ")
    away_team = teams[0]
    home_team = teams[1].split(" Box Score: ")[0]

    # Extract scores from the team info section
    score_info = soup.find("div", {"class": "scorebox"}).find_all("div", {"class": "scores"})
    away_score = score_info[0].find("div", {"class": "score"}).text
    home_score = score_info[1].find("div", {"class": "score"}).text

    # Determine the winner
    winner = home_team if int(home_score) > int(away_score) else away_team

    # Extract additional game details
    game_details = soup.find("div", {"class": "scorebox_meta"}).find_all("div")
    venue = game_details[3].text.split(": ")[1]

    # Extract date from the title
    date = title.split(" Box Score: ")[1].split(" | ")[0]

    # Extract game ID from the URL
    game_id = url.split("/")[-1].split(".")[0]

    # Create a dictionary to store the extracted data
    game_data = {
        "GameID": game_id,
        "Date": date,
        "home_team": home_team,
        "away_team": away_team,
        "home_score": home_score,
        "away_score": away_score,
        "winner": winner,
        "venue": venue,
    }

    return game_data


def get_game_data(year, proxies=None):
    boxscore_links = get_boxscore_links(year, proxies=proxies)
    data_dir = "Data/GameData"
    os.makedirs(data_dir, exist_ok=True)

    # Check for existing data and load it if available
    try:
        with open(f"{data_dir}/{year}-GameData.csv", "r") as f:
            existing_data = [row for row in csv.DictReader(f)]
            existing_ids = {row["game_id"] for row in existing_data}
    except FileNotFoundError:
        existing_data = []
        existing_ids = set()

    all_game_data = existing_data

    for i, link in enumerate(boxscore_links, start=1):
        game_id = link.split("/")[-1].split(".")[0]
        if game_id in existing_ids:  # Skip this game if we've already scraped it
            continue

        boxscore_url = f"https://www.baseball-reference.com{link}"
        game_data = parse_boxscore_page(boxscore_url)
        all_game_data.append(game_data)

        # Save the data periodically
        with open(f"{data_dir}/{year}-GameData.csv", "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=all_game_data[0].keys())
            writer.writeheader()
            writer.writerows(all_game_data)

        logging.info(f"Scraped and saved data for game {i} of year {year}.")

        # Respect rate limiting
        time.sleep(3)

    logging.info(f"Saved data for all games of year {year}.")


# Load proxies from a text file
# with open('proxies.txt') as f:
#     proxies = [line.strip() for line in f]
# proxy_pool = cycle(proxies)

# Example usage:
get_game_data(2022)
