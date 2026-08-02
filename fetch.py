import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

from models import BootstrapResponse, Fixture
from typing import Any


def fixture_url(gameweek_id):
  return f'https://fantasy.premierleague.com/api/fixtures/?event={gameweek_id}'


bootstrap_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'

players_master_xlsx_path = "./data/players_master.xlsx"
teams_master_xlsx_path = "./data/teams_master.xlsx"
fixture_master_xlsx_path = "./data/fixtures_master.xlsx"


def dump_raw_data() -> tuple[int, BootstrapResponse, list[Fixture]] | None:
  try:
    bootstrap_response = requests.get(bootstrap_url)
    bootstrap_response.raise_for_status()
    bootstrap_data = bootstrap_response.json()

    events = bootstrap_data["events"]
    upcoming_gameweek_title: str | None = None
    upcoming_gameweek_id: int | None = None
    for event in events:
      if event["is_next"]:
        upcoming_gameweek_id = event["id"]
        upcoming_gameweek_title = event["name"]
        break

    if not upcoming_gameweek_id:
      print("⚠ No upcoming gameweek is present.")
      return

    file_name = f"./data/raw/gw_{upcoming_gameweek_id}_{date.today()}.json"

    if Path(file_name).is_file():
      print(f"⚠ {upcoming_gameweek_title}'s data dump already exists.")
    else:
      with open(file_name, "w") as file:
        json.dump(bootstrap_data, file, indent=2)
      print(f"✓ {upcoming_gameweek_title}'s data successfully dumped.")

    fixture_response = requests.get(fixture_url(upcoming_gameweek_id))
    fixture_response.raise_for_status()
    fixture_data = fixture_response.json()

    return upcoming_gameweek_id, bootstrap_data, fixture_data

  except Exception as e:
    print(f"✗ Error: {e}")


def dump_data(data: list[Any], path: str, gw_id: int) -> None:
  try:
    df = pd.DataFrame(data)

    if_xlsx_exists = Path(path).is_file()
    writer_kwargs = {"engine": "openpyxl", "mode": "a", "if_sheet_exists": "replace"} if if_xlsx_exists else {"engine":
                                                                                                              "openpyxl", "mode": "w"}
    with pd.ExcelWriter(path, **writer_kwargs) as writer:  # type: ignore
      df.to_excel(writer, sheet_name=f"GW{gw_id}", index=False)

    print("✓ Data dumped successfully.")
  except Exception as e:
    print(f"✗ Data Dump Error: {e}")


if __name__ == "__main__":
  result = dump_raw_data()
  if result:
    gw_id, bootstrap_data, fixture_data = result
    print('Dumping players master...')
    dump_data(bootstrap_data["elements"], players_master_xlsx_path, gw_id)
    print('Dumping teams master...')
    dump_data(bootstrap_data["teams"], teams_master_xlsx_path, gw_id)
    print('Dumping fixture master...')
    dump_data(fixture_data, fixture_master_xlsx_path, gw_id)
