import requests
import pandas as pd
from bs4 import BeautifulSoup
import time

# Initialize an empty list to store all match data
all_matches = []

# URL for Premier League standings
standings_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
data = requests.get(standings_url)

# Parse the HTML content using BeautifulSoup
soup = BeautifulSoup(data.text)

# Extract the standings table
standings_table = soup.select('table.stats_table')[0]

# Find all the links in the standings table
links = standings_table.find_all('a')

# Filter links to get only the team squad links
links = [l.get("href") for l in links]
links = [l for l in links if '/squads/' in l]
team_urls = [f"https://fbref.com{l}" for l in links]

# Get the URL for the first team
team_url = team_urls[0]
data = requests.get(team_url)

# Extract match data from the team's page
matches = pd.read_html(data.text, match="Scores & Fixtures")

# Parse the page to find shooting stats link
soup = BeautifulSoup(data.text)
links = soup.find_all('a')
links = [l.get("href") for l in links]
links = [l for l in links if l and 'all_comps/shooting/' in l]

# Fetch and parse shooting stats
data = requests.get(f"https://fbref.com{links[0]}")
shooting = pd.read_html(data.text, match="Shooting")[0]

# Clean up the shooting stats DataFrame
shooting.columns = shooting.columns.droplevel()

# Merge match data with shooting stats on the 'Date' column
team_data = matches[0].merge(
    shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]],
    on="Date"
)

# Define the years to loop through
years = list(range(2024, 2022, -1))

# Loop through the years and extract data for each team
for year in years:
    data = requests.get(standings_url)
    soup = BeautifulSoup(data.text)

    # Extract team URLs from the standings table
    standings_table = soup.select('table.stats_table')[0]
    links = [l.get("href") for l in standings_table.find_all('a')]
    links = [l for l in links if 'squads/' in l]
    team_urls = [f"https://fbref.com{l}" for l in links]

    # Get the previous season's URL for the next iteration
    previous_season = soup.select("a.prev")[0].get("href")
    standings_url = f"https://fbref.com/{previous_season}"

    # Loop through each team URL
    for team_url in team_urls:
        # Extract the team name from the URL
        team_name = team_url.split("/")[-1].replace("-Stats", "").replace("-", " ")

        # Get match data for the team
        data = requests.get(team_url)
        matches = pd.read_html(data.text, match="Scores & Fixtures")[0]

        # Get shooting stats for the team
        soup = BeautifulSoup(data.text)
        links = [l.get("href") for l in soup.find_all('a')]
        links = [l for l in links if l and 'all_comps/shooting/' in l]
        data = requests.get(f"https://fbref.com{links[0]}")
        shooting = pd.read_html(data.text, match="Shooting")[0]
        shooting.columns = shooting.columns.droplevel()

        try:
            # Merge match data with shooting stats
            team_data = matches.merge(
                shooting[["Date", "Sh", "SoT", "Dist", "FK", "PK", "PKatt"]],
                on="Date"
            )
        except ValueError:
            continue

        # Filter for Premier League competition
        team_data = team_data[team_data["Comp"] == "Premier League"]

        # Add season and team name columns
        team_data["Season"] = year
        team_data["Team"] = team_name

        # Append the team data to the all_matches list
        all_matches.append(team_data)

        # Sleep to avoid overloading the server
        time.sleep(1)
      