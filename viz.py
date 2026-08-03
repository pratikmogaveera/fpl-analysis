import matplotlib.pyplot as plt
import seaborn as sns

import analysis

if __name__ == '__main__':
  players_df = analysis.build_players_df()

  fig, ax = plt.subplots()
  top_10_by_value = players_df.sort_values(by='points_per_euro', ascending=False).head(
    10).sort_values(by='points_per_euro', ascending=True)
  ax.barh(top_10_by_value['full_name'], top_10_by_value['points_per_euro'])
  ax.set_title('Top players: Points per Euro')
  plt.tight_layout()
  plt.show()

  active = players_df[players_df['total_points'] > 0]
  fig, ax = plt.subplots()
  sns.kdeplot(data=active, x='ict_index', y='total_points', fill=True, ax=ax)
  ax.set_title('ICT Index vs Total Points — Density')
  plt.tight_layout()
  plt.show()

  corr_cols = ['total_points', 'ict_index', 'points_per_game', 'ep_next', 'selected_by_percent', 'cost']
  corr_matrix = players_df[corr_cols].corr()

  fig, ax = plt.subplots()
  sns.heatmap(corr_matrix, annot=True, fmt='.2f', ax=ax, vmin=0, vmax=12)
  ax.set_title('Correlation Matrix')
  plt.tight_layout()
  plt.show()

  rec_cols = ['full_name', 'team_name', 'position', 'cost', 'fdr', 'next_gw_score']
  recommendations = players_df.sort_values(by=['position', 'next_gw_score'],
                                           ascending=False).groupby('position').head(5)[rec_cols]
  print(recommendations.to_string(index=False))
