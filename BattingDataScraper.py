import os
import csv
import time
import traceback
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
from selenium.webdriver.common.proxy import Proxy, ProxyType


# BrightData's Proxy
def get_proxy():
    proxy_url = "zproxy.lum-superproxy.io"
    proxy_username = "brd-customer-hl_6516ea8a-zone-data_center"
    proxy_password = "2xtk1vu7chok"
    proxy_port = 22225

    proxy_connection_string = f"http://{proxy_username}:{proxy_password}@{proxy_url}:{proxy_port}"

    return proxy_connection_string


# Initialize the UserAgent object
ua = UserAgent()
# Get a random user-agent
user_agent = ua.random

# Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument(f"user-agent={user_agent}")

# Disable images for faster loading
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)


def scrape_year(year):
    try:
        # Initialize the Proxy object
        proxy = Proxy()
        proxy.proxy_type = ProxyType.MANUAL
        proxy.http_proxy = get_proxy()
        proxy.ssl_proxy = get_proxy()

        capabilities = webdriver.DesiredCapabilities.CHROME
        proxy.add_to_capabilities(capabilities)

        # Setup the driver with the specified options and capabilities
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options, desired_capabilities=capabilities)

        # Set a delay for Selenium to wait up to 10 seconds for the elements to appear
        wait = WebDriverWait(driver, 10)

        url = f"https://www.baseball-reference.com/leagues/majors/{year}-schedule.shtml"
        driver.get(url)
        time.sleep(3)

        # Prepare CSV file for this year
        with open(f"data/BattingData/{year}-Batting-Data.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(
                [
                    "GameID",
                    "Date",
                    "Team",
                    "Player",
                    "IP",
                    "H",
                    "R",
                    "ER",
                    "BB",
                    "SO",
                    "HR",
                    "ERA",
                    "BF",
                    "Pit",
                    "Str",
                    "Ctct",
                    "StS",
                    "StL",
                    "GB",
                    "FB",
                    "LD",
                    "Unk",
                    "GSc",
                    "IR",
                    "IS",
                    "WPA",
                    "aLI",
                    "cWPA",
                    "acLI",
                    "RE24",
                ]
            )
            # Wait until boxscore links are present on the page
            boxscore_links = wait.until(EC.presence_of_all_elements_located((By.XPATH, '//p/em/a[contains(text(), "Boxscore")]')))
            links = [link.get_attribute("href") for link in boxscore_links]

            # Iterate through the links and scrape data
            for link in links:
                try:
                    driver.get(link)
                    time.sleep(3)
                except Exception as e:
                    print(f"Error accessing boxscore link {link}: {e}")
                    continue

                # Extract GameID from URL
                game_id = link.split("/")[-1].split(".")[0]

                # Find date of the match
                date = driver.find_element(By.XPATH, '//div[@class="scorebox_meta"]/div[1]').text
                date = " ".join(date.split(" ")[1:])  # Remove the day of the week

                # Find the team names and keep the spaces
                teams = driver.find_elements(By.XPATH, '//div[@class="scorebox"]//a[contains(@href, "/teams/")]')
                team_ids = [team.get_attribute("textContent") for team in teams]

                # Construct the IDs for the batting tables and remove the spaces and dots
                batting_table_ids = [team_id.replace(" ", "").replace(".", "") + "batting" for team_id in team_ids]

                # Iterate through the tables
                for team_id, batting_table_id in zip(team_ids, batting_table_ids):
                    table = driver.find_element(By.ID, batting_table_id)

                    for row in table.find_elements(By.TAG_NAME, "tr"):
                        # Check if the row is a player row
                        if len(row.find_elements(By.TAG_NAME, "th")) > 0:
                            player = row.find_element(By.TAG_NAME, "th").text
                            # Remove the comma and anything after
                            player = player.split(",")[0]

                            # Skip the row if it's the "Team Totals" row
                            if player == "Team Totals":
                                continue

                            data = [td.text for td in row.find_elements(By.TAG_NAME, "td")]

                            if data:
                                # Include the team name when writing to the CSV file
                                writer.writerow([game_id, date, team_id, player] + data)

            driver.quit()
    except Exception as e:
        print(f"Error scraping data for year {year}: {e}")
        traceback.print_exc()


# Make sure the directory exists
os.makedirs("data/BattingData", exist_ok=True)

# Specify the range of years
start_year = 2015
end_year = 2023

# Create a ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=3) as executor:
    # Submit tasks to the executor for each year
    futures = {executor.submit(scrape_year, year) for year in range(start_year, end_year + 1)}

    # Wait for all tasks to complete
    for future in as_completed(futures):
        print(f"Completed scraping for a year")
