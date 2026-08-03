"""
explore.py — Correlation analysis tool for weight tuning.

Run this script to generate per-position correlation heatmaps showing how
each scoring factor correlates with total_points. Use the output to tune
the WEIGHTS dicts in the notebook.

Usage:
    python explore.py            # display charts interactively
    python explore.py --save     # save charts as PNG files in data/
"""

import sys
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import requests

POSITION_MASTER = {1: 'GKP', 2: 'DEF', 3: 'MID', 4: 'FWD'}

POSITION_CORR_COLUMNS = {
    'GKP': ['total_points', 'points_per_game', 'ep_next', 'fdr',
            'chance_of_playing_next_round', 'clean_sheets_per_90', 'saves_per_90'],
    'DEF': ['total_points', 'points_per_game', 'ep_next', 'fdr',
            'chance_of_playing_next_round', 'ict_index', 'clean_sheets_per_90'],
    'MID': ['total_points', 'points_per_game', 'ep_next', 'fdr',
            'chance_of_playing_next_round', 'ict_index', 'clean_sheets_per_90'],
    'FWD': ['total_points', 'points_per_game', 'ep_next', 'fdr',
            'chance_of_playing_next_round', 'threat', 'expected_goals'],
}

NUMERIC_COLUMNS = [
    'form', 'points_per_game', 'ep_next', 'influence', 'creativity', 'threat',
    'ict_index', 'value_form', 'value_season', 'selected_by_percent',
    'expected_goals', 'expected_assists', 'expected_goal_involvements',
    'expected_goals_conceded', 'clean_sheets_per_90', 'saves_per_90',
]


def get_gameweek() -> str:
    response = requests.get('https://fantasy.premierleague.com/api/bootstrap-static/')
    response.raise_for_status()
    data = response.json()
    for event in data['events']:
        if event['is_next']:
            return f"GW{event['id']}"
    raise RuntimeError('No upcoming gameweek found.')


def load_players(gameweek: str) -> pd.DataFrame:
    players_df = pd.read_excel('./data/players_master.xlsx', sheet_name=gameweek)
    teams_df = pd.read_excel('./data/teams_master.xlsx', sheet_name=gameweek)

    players_df['full_name'] = players_df['first_name'] + ' ' + players_df['second_name']
    players_df['position'] = players_df['element_type'].map(POSITION_MASTER)
    players_df['team_name'] = players_df['team'].map(dict(zip(teams_df['id'], teams_df['name'])))

    for col in NUMERIC_COLUMNS:
        players_df[col] = pd.to_numeric(players_df[col], errors='coerce')

    players_df['chance_of_playing_next_round'] = players_df['chance_of_playing_next_round'].fillna(100)
    players_df['ep_next'] = players_df['ep_next'].fillna(0)
    players_df = players_df[players_df['status'].isin(['a', 'i', 'd'])]
    players_df = players_df[players_df['minutes'] >= 900]
    players_df['cost'] = players_df['now_cost'] / 10

    return players_df


def plot_correlation(players_df: pd.DataFrame, save: bool = False) -> None:
    for pos, cols in POSITION_CORR_COLUMNS.items():
        temp_df = players_df[players_df['position'] == pos][cols].dropna()
        corr_matrix = temp_df.corr()

        fig, ax = plt.subplots(figsize=(8, 6))
        sns.heatmap(corr_matrix, annot=True, fmt='.2f', ax=ax, vmin=-1, vmax=1,
                    cmap='RdYlGn', linewidths=0.5)
        ax.set_title(f'Correlation Matrix: {pos} (n={len(temp_df)})')
        plt.tight_layout()

        if save:
            path = f'./data/corr_{pos.lower()}.png'
            plt.savefig(path, dpi=150)
            print(f'Saved: {path}')
        else:
            plt.show()

        plt.close()


if __name__ == '__main__':
    save_mode = '--save' in sys.argv

    print('Fetching current gameweek...')
    gameweek = get_gameweek()
    print(f'Using {gameweek}')

    print('Loading player data...')
    players_df = load_players(gameweek)
    print(f'Loaded {len(players_df)} players (>=900 min)')

    plot_correlation(players_df, save=save_mode)
