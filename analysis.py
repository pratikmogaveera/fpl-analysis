import json
from typing import TypedDict

import pandas as pd


class FplResponse(TypedDict):
  chips: list[dict]
  events: list[dict]
  game_settings: dict
  game_config: dict
  phases: list[dict]
  teams: list[dict]
  total_players: int
  element_stats: list[dict]
  element_types: list[dict]
  elements: list[dict]


if __name__ == '__main__':
  data: FplResponse
  with open('./data/raw/fpl-bootstrap.json', 'r') as file:
    data: FplResponse = json.load(file)

  players_df = pd.DataFrame(data["elements"])

  players_df['full_name'] = players_df['first_name'] + \
      ' ' + players_df['second_name']

  players_df['position'] = players_df['element_type'].map(
    {pos['id']: pos['singular_name_short'] for pos in data["element_types"]})

  players_df['team_name'] = players_df['team_code'].map(
    {team['code']: team['name'] for team in data["teams"]})

  print(players_df[['full_name', 'team_name', 'position']].head(5))

  print(players_df.shape, players_df.dtypes, players_df.info())
