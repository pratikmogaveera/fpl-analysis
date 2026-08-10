import json
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from models import BootstrapResponse

bootstrap_url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
fixtures_url = 'https://fantasy.premierleague.com/api/fixtures/'

players_master_xlsx_path = "./data/players_master.xlsx"
teams_master_xlsx_path = "./data/teams_master.xlsx"
fixture_master_xlsx_path = "./data/fixtures_master.xlsx"


def fetch_bootstrap_data() -> tuple[int, BootstrapResponse] | None:
  try:
    print("Fetching bootstrap data...")
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
      print("⚠ No upcoming gameweek found — season may be over.")
      return

    file_name = f"./data/raw/gw_{curr_gw_id}_{date.today()}.json"

    if Path(file_name).is_file():
      print(f"⚠ Raw JSON already exists: {file_name}")
    else:
      with open(file_name, "w") as file:
        json.dump(bootstrap_data, file, indent=2)
      print(f"✓ Raw JSON saved: {file_name}")

    return curr_gw_id, bootstrap_data

  except Exception as e:
    print(f"✗ Bootstrap fetch failed: {e}")


def write_xlsx(data: list[Any], path: str, gw_id: int, label: str) -> None:
  try:
    df = pd.DataFrame(data)

    if Path(path).is_file():
      writer_kwargs = {"engine": "openpyxl", "mode": "a", "if_sheet_exists": "replace"}
    else:
      writer_kwargs = {"engine": "openpyxl", "mode": "w"}

    with pd.ExcelWriter(path, **writer_kwargs) as writer:  # type: ignore
      df.to_excel(writer, sheet_name=f"GW{gw_id}", index=False)

    print(f"✓ {label}: GW{gw_id} sheet written ({len(df)} rows)")
  except Exception as e:
    print(f"✗ {label} write failed: {e}")


def generate_fixtures_master():
  try:
    print("Fetching all fixtures...")
    fixture_response = requests.get(fixtures_url)
    fixture_response.raise_for_status()
    fixture_data = fixture_response.json()

    df = pd.DataFrame(fixture_data).sort_values(by='id')

    with pd.ExcelWriter(fixture_master_xlsx_path, engine="openpyxl", mode="w") as writer:
      df.to_excel(writer, sheet_name="Fixtures", index=False)

    print(f"✓ Fixtures master written ({len(df)} fixtures)")

  except Exception as e:
    print(f"✗ Fixtures fetch failed: {e}")


if __name__ == "__main__":
  result = fetch_bootstrap_data()
  if result:
    gw_id, bootstrap_data = result
    print(f"\nWriting GW{gw_id} data...")
    write_xlsx(bootstrap_data["elements"], players_master_xlsx_path, gw_id, "Players")
    write_xlsx(bootstrap_data["teams"], teams_master_xlsx_path, gw_id, "Teams")
    print()
    generate_fixtures_master()
    print("\n✓ Done.")
