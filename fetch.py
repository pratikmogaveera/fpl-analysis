import json
from datetime import date
from pathlib import Path

import pandas as pd
import requests

url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
players_master_xlsx_path = "./data/players_master.xlsx"
teams_master_xlsx_path = "./data/teams_master.xlsx"


def dump_raw_data():
  try:
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()

    events = data["events"]
    upcoming_gameweek_title = None
    upcoming_gameweek_id = None
    for event in events:
      if event["is_next"]:
        upcoming_gameweek_id = event["id"]
        upcoming_gameweek_title = event["name"]
        break

    if not upcoming_gameweek_id:
      print("⚠ No upcoming gameweek is present.")
      return

    file_name = f"./data/raw/gw_{upcoming_gameweek_id}_{date.today()}.json"

    file_path = Path(file_name)
    if file_path.is_file():
      print(f"⚠ {upcoming_gameweek_title}'s data dump already exists.")
    else:
      with open(file_name, "w") as file:
        json.dump(data, file, indent=2)
      print(f"✓ {upcoming_gameweek_title}'s data successfully dumped.")

    return data, upcoming_gameweek_id

  except Exception as e:
    print(f"✗ Error: {e}")


def dump_data(data, path, gw_id):
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
    data, gw_id = result
    print('Dumping players master...')
    dump_data(data["elements"], players_master_xlsx_path, gw_id)
    print('Dumping teams master...')
    dump_data(data["teams"], teams_master_xlsx_path, gw_id)
