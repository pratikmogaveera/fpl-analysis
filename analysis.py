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
  players_df = players_df[players_df['status'].isin(['a', 'i', 'd'])]

  players_df['cost'] = players_df['now_cost'] / 10

  print("\n\nTop Players: Total Points:")
  for pos in ['GKP', 'DEF', 'MID', 'FWD']:
    temp_df = players_df[players_df['position'] == pos].sort_values(by='total_points', ascending=False)
    print(f'{pos} ----------------------------------------')
    print(temp_df[['full_name', 'total_points']].head(10))

  players_df['points_per_euro'] = players_df['total_points'] / players_df['cost']
  temp_df = players_df.sort_values(by='points_per_euro', ascending=False)
  print("\n\nTop Players: Points per euro")
  print(temp_df[['full_name', 'total_points', 'cost', 'points_per_euro']].head(10))

  temp_df = players_df.sort_values(by='selected_by_percent', ascending=False)
  print("\n\nTop Players: By Ownership")
  print(temp_df[['full_name', 'total_points', 'cost', 'points_per_euro', 'selected_by_percent']].head(10))

  print("\n\nICT Index v/s Total Points Correlation:")
  temp = players_df[['ict_index', 'total_points']].corr()
  print(temp.iloc[0].iloc[1])
