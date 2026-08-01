import json
from typing import TypedDict

import pandas as pd

numeric_columns = ['form', 'points_per_game', 'ep_next', 'influence', 'creativity', 'threat', 'ict_index', 'value_form', 'value_season',
                   'selected_by_percent', 'expected_goals', 'expected_assists', 'expected_goal_involvements', 'expected_goals_conceded']


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

  players_df['full_name'] = players_df['first_name'] + ' ' + players_df['second_name']

  players_df['position'] = players_df['element_type'].map(
    {pos['id']: pos['singular_name_short'] for pos in data["element_types"]})

  players_df['team_name'] = players_df['team_code'].map({team['code']: team['name'] for team in data["teams"]})

  for col in numeric_columns:
    players_df[col] = pd.to_numeric(players_df[col], errors='coerce')

  players_df['chance_of_playing_next_round'] = players_df['chance_of_playing_next_round'].fillna(100)

  players_df['ep_next'] = players_df['ep_next'].fillna(0)

  # print(players_df['status'].unique())
  # print(players_df['removed'].unique())

  print(len(players_df))
  players_df = players_df[players_df['status'].isin(['a', 'i', 'd'])]
  print(len(players_df))

  players_df['cost'] = players_df['now_cost'] / 10
  print(players_df['cost'].head(5))
