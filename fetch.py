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
    curr_gw_id: int | None = None
    for event in events:
      if event["is_next"]:
        # curr_gw_id = last played GW (0 during pre-season)
        # event["id"] is the upcoming GW, so subtract 1
        curr_gw_id = event["id"] - 1
        break

    if curr_gw_id is None:
      print("⚠ No upcoming gameweek is present.")
      return

    file_name = f"./data/raw/gw_{curr_gw_id}_{date.today()}.json"

    if Path(file_name).is_file():
      print(f"⚠ GW{curr_gw_id} data dump already exists.")
    else:
      with open(file_name, "w") as file:
        json.dump(bootstrap_data, file, indent=2)
      print(f"✓ GW{curr_gw_id} data successfully dumped.")

    # Fixtures are fetched for the upcoming GW (curr_gw_id + 1) since that's
    # what we're predicting for. The sheet is named GW{curr_gw_id} to match
    # the players/teams sheets — all three form a consistent snapshot.
    fixture_response = requests.get(fixture_url(curr_gw_id + 1))
    fixture_response.raise_for_status()
    fixture_data = fixture_response.json()

    return curr_gw_id, bootstrap_data, fixture_data

  except Exception as e:
    print(f"✗ Error: {e}")


def dump_data(data: list[Any], path: str, gw_id: int) -> None:
  try:
    df = pd.DataFrame(data)

    if Path(path).is_file():
      writer_kwargs = {"engine": "openpyxl", "mode": "a", "if_sheet_exists": "replace"}
    else:
      writer_kwargs = {"engine": "openpyxl", "mode": "w"}

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
