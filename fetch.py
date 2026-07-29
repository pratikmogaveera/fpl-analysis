from datetime import date
import json
from pathlib import Path
import requests

url = 'https://fantasy.premierleague.com/api/bootstrap-static/'


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

  except Exception as e:
    print(f"✗ Error: {e}")


if __name__ == "__main__":
  dump_raw_data()
