from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import pandas as pd
import csv
import time

# Setup Chrome options to run the browser headless
chrome_options = webdriver.ChromeOptions()
chrome_options.add_argument("--headless")

# Initialize the Chrome driver
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import csv
import time

# Setup
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
url = "https://www.baseball-reference.com/boxes/ANA/ANA202204070.shtml"
driver.get(url)
time.sleep(2)

# Extract the date
full_date = driver.find_element(By.XPATH, '//*[@id="content"]/div[2]/div[3]/div[1]').text.split("\n")[0]
date = full_date.split(",")[1].strip()  # Removes the day of the week

# Extract table
table = driver.find_element(By.XPATH, '//*[@id="HoustonAstrospitching"]')

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

    # GameID
    game_id = url.split("/")[-1].split(".")[0]

    # Extract rows
    for row in table.find_elements(By.TAG_NAME, "tr")[1:-1]:  # Excluding header and total row
        player_name = row.find_element(By.TAG_NAME, "th").text
        columns = row.find_elements(By.TAG_NAME, "td")
        row_data = [game_id, date, player_name] + [col.text for col in columns]
        writer.writerow(row_data)

driver.quit()
