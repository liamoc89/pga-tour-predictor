"""
PGA Tour results scraper

Scrape historic PGA tour results from either ESPN / PGA Tour website

Covering 2002 - present
"""
import csv
import random
import time
from pathlib import Path

#### Need to figure out how to navigate to each individual page to retrieve the results.
# TODO : get the result for each of these events and con

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime


def parse_dates(date_str, year):
    date_parts = date_str.replace(" - ", " ").split(" ")
    start_month = date_parts[-1] if len(date_parts) < 4 else date_parts[1]
    end_month = start_month if len(date_parts) < 4 else date_parts[-1]
    start_day = date_parts[0]
    end_day = date_parts[-2] if len(date_parts) > 2 else start_day

    start_date_str = f"{start_day} {start_month} {year}"
    end_date_str = f"{end_day} {end_month} {year}"

    return (
        datetime.strptime(start_date_str, "%d %b %Y").date(),
        datetime.strptime(end_date_str, "%d %b %Y").date()
    )

def get_pga_tour_schedule_for_year(year: int) -> list[dict]:
    """
    Retrieves PGA Tour schedule for specified year.

    :param year: the year to retrieve schedule information for
    :return: a list of dictionaries containing information for each tournament in the given year
    """
    output_path = Path(f"data/pga_tour_results/")

    url = f"https://www.espn.co.uk/golf/schedule/_/season/{year}"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                             "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}

    res = requests.get(url, headers=headers)

    soup = BeautifulSoup(res.text, "html.parser")
    rows = soup.select("tbody.Table__TBODY tr.Table__TR")

    tournament_data = []

    for row in rows:
        # Tournament name + link
        link = row.select_one(".eventAndLocation__tournamentLink")
        if not link:
            continue

        tournament_name = link.getText(strip=True)
        href = link.find_parent("a")["href"]

        # Get tournament ID
        match = re.search(r"tournamentId=(\d+)", href)
        tournament_id = match.group(1) if match else None

        # Get tournament dates
        date_text = row.select_one(".dateRange__col").get_text(strip=True)
        start_date, end_date = parse_dates(date_text, year)

        # Course
        locations = row.select(".eventAndLocation__tournamentLocation")
        course = locations[0].get_text(strip=True) if locations else None

        tournament_data.append({
            "tournament_id": tournament_id,
            "tournament_name": tournament_name,
            "start_date": start_date,
            "end_date": end_date,
            "course": course,
        })

    save_to_csv(tournament_data, output_path, year)


def save_to_csv(tournaments: list[dict], output_path: Path, year: int) -> None:
    csv_fields = [
        "tournament_id",
        "tournament_name",
        "start_date",
        "end_date",
        "course",
    ]
    file_path = output_path / f"{year}_pga_tour_events.csv"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=csv_fields)
        writer.writeheader()
        writer.writerows(tournaments)
    print(f"\n💾 Saved {len(tournaments)} rows for season {year} → {file_path}")


for year in range(2002, 2026):
    get_pga_tour_schedule_for_year(year)
    time.sleep(random.randint(1, 5))
