from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import csv
import time

# Setup
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
# Set a delay for Selenium to wait up to 10 seconds for the elements to appear
wait = WebDriverWait(driver, 10)
url = "https://www.baseball-reference.com/leagues/majors/2020-schedule.shtml"
driver.get(url)
time.sleep(3)

# Prepare CSV file
with open("pitchers_data.csv", "w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(
        [
            "GameID",
            "Date",
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

        # Find the team names
        teams = driver.find_elements(By.XPATH, '//div[@class="scorebox"]//a[contains(@href, "/teams/")]')
        team_ids = [team.get_attribute("textContent").replace(" ", "").replace(".", "") for team in teams]
        print(team_ids)

        # Construct the IDs for the pitching tables
        pitching_table_ids = [f"{team_id}pitching" for team_id in team_ids]
        print(pitching_table_ids)

        for pitching_table_id in pitching_table_ids:
            table = driver.find_element(By.ID, pitching_table_id)

            for row in table.find_elements(By.TAG_NAME, "tr"):
                # Check if the row is a player row
                if len(row.find_elements(By.TAG_NAME, "th")) > 0:
                    player = row.find_element(By.TAG_NAME, "th").text.split(",")[0]

                    # Skip the row if the player's name is "Team Totals"
                    if player == "Team Totals":
                        continue

                    data = [td.text for td in row.find_elements(By.TAG_NAME, "td")]

                    if data:
                        writer.writerow([game_id, date, player] + data)

    driver.quit()
