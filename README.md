# FPL Analysis

Data analysis project using the official FPL API to understand player performance and recommend picks for the next gameweek.

## Purpose

Learn data analysis (pandas, matplotlib, seaborn) through a real-world dataset while building a tool that scores and ranks FPL players each gameweek.

## Tech Stack

- Python 3.12
- pandas — data manipulation
- matplotlib / seaborn — visualization
- openpyxl — xlsx read/write
- requests — API fetch
- Jupyter — notebook consolidation

## How to Run

```bash
# Activate environment
ml   # alias for: source ~/Desktop/Projects/ML/ml-env/bin/activate

# Fetch latest GW data
python fetch.py
```

## File Structure

```
fpl-analysis/
├── fetch.py            — fetches bootstrap API, saves JSON + updates xlsx files
├── explore.py          — Phase 1: inspect bootstrap JSON structure and player columns
├── models.py           — TypedDict definitions for FPL API responses
├── fpl_analysis.ipynb  — Phase 8: full analysis notebook (self-contained, runs top to bottom)
├── data/
│   ├── raw/            — weekly JSON snapshots (gw{n}_{date}.json)
│   ├── players.xlsx    — elements data, one sheet per GW
│   ├── teams.xlsx      — teams data, one sheet per GW
│   └── fixtures_master.xlsx — fixtures data, one sheet per GW
├── DATA.md             — full API field reference
├── PLAN.md             — project roadmap
├── NOTES.md            — concepts and Q&A per phase
└── README.md           — this file
```

## Progress

- [x] Phase 0 — Data pipeline (fetch + store)
- [x] Phase 1 — Setup & data exploration
- [x] Phase 2 — Pandas basics
- [x] Phase 3 — Data cleaning & normalization
- [x] Phase 4 — Exploratory analysis
- [x] Phase 5 — Fixture difficulty
- [x] Phase 6 — Next GW scoring model
- [x] Phase 7 — Visualization
- [x] Phase 8 — Notebook consolidation

## Resources

- [FPL API](https://fantasy.premierleague.com/api/bootstrap-static/)
- [pandas docs](https://pandas.pydata.org/docs/)
- [seaborn docs](https://seaborn.pydata.org/)
