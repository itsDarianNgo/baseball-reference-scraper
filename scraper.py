import argparse
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import os
import random


# Function to handle command line arguments
def handle_arguments():
    parser = argparse.ArgumentParser(description="Baseball Data Scraper")
    parser.add_argument("-p", "--proxies", type=str, help="Path to the text file with proxies", default=None)
    parser.add_argument("-s", "--start-year", type=int, help="The start year for data scraping", default=2021)
    parser.add_argument("-e", "--end-year", type=int, help="The end year for data scraping", default=2022)
    args = parser.parse_args()

    return args.proxies, args.start_year, args.end_year


# Function to load proxies from a text file
def load_proxies(proxy_file):
    if proxy_file is None:
        return None
    with open(proxy_file, "r") as f:
        proxies = f.read().splitlines()
    return proxies


# Function to make a request with error handling and optional proxy support
def make_request(url, proxies=None, retries=3):
    for _ in range(retries):
        if proxies:
            proxy = random.choice(proxies)
            try:
                response = requests.get(url, proxies={"http": proxy, "https": proxy})
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException:
                print(f"Error accessing {url} with proxy {proxy}. Retrying...")
                time.sleep(1)
        else:
            try:
                response = requests.get(url)
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException:
                print(f"Error accessing {url}. Retrying...")
                time.sleep(1)
    return None


def scrape_boxscore(url, proxies):
    retry_attempts = 3
    for attempt in range(retry_attempts):
        try:
            response = requests.get(url, proxies=proxies)
            response.raise_for_status()
        except (requests.RequestException, requests.HTTPError) as err:
            if attempt == retry_attempts - 1:
                raise SystemExit(err)
            else:
                time.sleep(3)
                continue

        soup = BeautifulSoup(response.content, "html.parser")
        try:
            teams = [team.text for team in soup.find_all("h2")]
            date = soup.find("div", {"itemtype": "https://schema.org/SportsEvent"}).find("strong").text
            venue = soup.find("div", {"itemprop": "location"}).find("a").text
            scores = [score.text for score in soup.find("div", {"class": "line_score_table"}).find_all("td")]
            batting_data = [data.text for data in soup.find("table", {"id": "div_" + teams[0] + "batting"}).find_all("td")]
            pitching_data = [data.text for data in soup.find("table", {"id": "div_" + teams[0] + "pitching"}).find_all("td")]
        except AttributeError:
            return {"status": "Missing data", "url": url}

        return {
            "teams": teams,
            "date": date,
            "venue": venue,
            "scores": scores,
            "batting_data": batting_data,
            "pitching_data": pitching_data,
        }


def scrape_year(year, proxies=None):
    base_url = f"https://www.baseball-reference.com/leagues/majors/{year}-schedule.shtml"
    response = make_request(base_url, proxies)
    if response is None:
        print(f"Failed to retrieve {base_url}")
        return None

    soup = BeautifulSoup(response.content, "html.parser")
    boxscore_links = [link.get("href") for link in soup.find_all("a", text="Boxscore")]
    boxscore_base_url = "https://www.baseball-reference.com"

    year_data = []
    for link in boxscore_links:
        boxscore_url = boxscore_base_url + link
        game_data = scrape_boxscore(boxscore_url, proxies)
        if game_data is not None:
            year_data.append(game_data)

        time.sleep(1)  # Pause for 1 second

    return year_data


def main():
    proxy_file, start_year, end_year = handle_arguments()
    proxies = load_proxies(proxy_file)

    # Main loop to iterate through years
    for year in range(start_year, end_year + 1):
        print(f"Scraping data for year: {year}")
        year_data = scrape_year(year, proxies)

        if year_data is not None:
            df = pd.DataFrame(year_data)
            df.to_csv(f"baseball_data_{year}.csv", index=False)
            print(f"Finished scraping data for year: {year}")


if __name__ == "__main__":
    main()
