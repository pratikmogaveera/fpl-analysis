import pandas as pd

PLAYERS_NUMERIC_COLUMNS = ['form', 'points_per_game', 'ep_next', 'influence', 'creativity', 'threat', 'ict_index', 'value_form', 'value_season',
                           'selected_by_percent', 'expected_goals', 'expected_assists', 'expected_goal_involvements', 'expected_goals_conceded']
POSITION_MASTER = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}
GAMEWEEK = 'GW1'

if __name__ == '__main__':
  players_df = pd.read_excel('./data/players_master.xlsx', sheet_name=GAMEWEEK)
  teams_df = pd.read_excel('./data/teams_master.xlsx', sheet_name=GAMEWEEK)
  fixtures_df = pd.read_excel('./data/fixtures_master.xlsx', sheet_name=GAMEWEEK)

  players_df['full_name'] = players_df['first_name'] + ' ' + players_df['second_name']
  players_df['position'] = players_df['element_type'].map(POSITION_MASTER)
  players_df['team_name'] = players_df['team'].map(dict(zip(teams_df['id'], teams_df['name'])))

  # Using `errors='coerce'` to enter NaN for invalid values without raising exceptions.
  for col in PLAYERS_NUMERIC_COLUMNS:
    players_df[col] = pd.to_numeric(players_df[col], errors='coerce')

  # FPL passes values into 'chance_of_playing_next_round' only during issues example 50, 75.
  # So missing value means player is fit to play. So replacing NA with 100 for calculations.
  players_df['chance_of_playing_next_round'] = players_df['chance_of_playing_next_round'].fillna(100)
  players_df['ep_next'] = players_df['ep_next'].fillna(0)
  players_df = players_df[players_df['status'].isin(['a', 'i', 'd'])]

  # FPL sends cost (euro) multiplied for 10 by default.
  players_df['cost'] = players_df['now_cost'] / 10

  print("\n\nTop Players: Total Points:")
  for id, pos in POSITION_MASTER.items():
    temp_df = players_df[players_df['position'] == pos].sort_values(by='total_points', ascending=False)
    print(f'\n{pos} ----------------------------------------')
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

  home = fixtures_df[['team_h', 'team_h_difficulty']].rename(columns={'team_h': 'team_id', 'team_h_difficulty': 'fdr'})
  away = fixtures_df[['team_a', 'team_a_difficulty']].rename(columns={'team_a': 'team_id', 'team_a_difficulty': 'fdr'})
  fdr_df = pd.concat([home, away])

  players_df['fdr'] = players_df['team'].map(dict(zip(fdr_df['team_id'], fdr_df['fdr'])))

  print("\n\nTop Players: Diffculty Rating:")
  players_df = players_df.sort_values(by='fdr')
  print(players_df[['full_name', 'team_name', 'fdr']].head(10))
