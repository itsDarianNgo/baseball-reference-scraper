from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time
import os

# Make sure the directory exists
os.makedirs("data/PitchingData", exist_ok=True)

# Setup Chrome options
chrome_options = Options()
chrome_options.add_argument("--headless")  # Ensure GUI is off
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")

# Disable images for faster loading
prefs = {"profile.managed_default_content_settings.images": 2}
chrome_options.add_experimental_option("prefs", prefs)
# Setup the driver with the specified options
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
# Set a delay for Selenium to wait up to 10 seconds for the elements to appear
wait = WebDriverWait(driver, 10)

# Specify the range of years
start_year = 2010
end_year = 2023

# Iterate through the years
for year in range(start_year, end_year + 1):
    url = f"https://www.baseball-reference.com/leagues/majors/{year}-schedule.shtml"
    driver.get(url)
    time.sleep(3)

    # Prepare CSV file for this year
    with open(f"data/PitchingData/{year}-Pitching-Data.csv", "w", newline="") as file:
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
            driver.get(link)
            time.sleep(3)

            # Extract GameID from URL
            game_id = link.split("/")[-1].split(".")[0]

            # Find date of the match
            date = driver.find_element(By.XPATH, '//div[@class="scorebox_meta"]/div[1]').text
            date = " ".join(date.split(" ")[1:])  # Remove the day of the week

            # Find the team names and keep the spaces
            teams = driver.find_elements(By.XPATH, '//div[@class="scorebox"]//a[contains(@href, "/teams/")]')
            team_ids = [team.get_attribute("textContent") for team in teams]

            # Construct the IDs for the pitching tables and remove the spaces and dots
            pitching_table_ids = [team_id.replace(" ", "").replace(".", "") + "pitching" for team_id in team_ids]

            # Iterate through the tables
            for team_id, pitching_table_id in zip(team_ids, pitching_table_ids):
                table = driver.find_element(By.ID, pitching_table_id)

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
