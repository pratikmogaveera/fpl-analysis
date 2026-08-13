# FPL Analysis

A Python data analysis project that scores and ranks Fantasy Premier League players for the next gameweek using the official FPL bootstrap-static API.

## What It Does

`fetch.py` pulls live data from the FPL API and stores it locally as Excel snapshots. `fpl_analysis.ipynb` reads those snapshots and produces a ranked recommendation table per position (GKP, DEF, MID, FWD).

The scoring model combines:

- **Last-season PPG** (`ppg_last`) — stable baseline from the previous season, read from the pre-season snapshot
- **Current-season PPG** (`points_per_game`) — season-to-date running average
- **Form** — rolling recent GW points average
- **Expected points next GW** (`ep_next`) — FPL's own prediction
- **Fixture difficulty** (`fdr`) — inverted so easier fixtures score higher
- **Position-specific stats** — clean sheets, saves, ICT index, threat, depending on position
- **Availability** (`chance_of_playing_next_round`)

The blend between last-season and current-season signals shifts automatically as the season progresses — early GWs lean on last-season data, late GWs rely almost entirely on current form.

Per-90 stats are dampened by a `minutes_confidence` multiplier (`minutes_played / (gws_played × 90)`) so players with very few appearances don't inflate scores via tiny-sample statistics.

The notebook also surfaces **differential picks** — players with low ownership but strong scoring potential, ranked by a combined score that rewards both high `next_gw_score` and low `selected_by_percent`.

A **squad optimizer** uses linear programming (PuLP) to find the mathematically optimal 15-player squad under FPL constraints — 2 GKP, 5 DEF, 5 MID, 3 FWD, max 3 per team, total cost ≤ £100.0m.

## Tech Stack

- Python 3.12
- pandas — data manipulation
- matplotlib / seaborn — visualization
- openpyxl — xlsx read/write
- requests — HTTP calls to the FPL API
- PuLP — linear programming solver for squad optimization
- tabulate — markdown table export
- Jupyter — analysis notebook

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/pratikmogaveera/fpl-analysis.git
cd fpl-analysis
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Fetch FPL data

```bash
python fetch.py
```

Run this **once before GW1** to create the `GW0` pre-season snapshot (used as the last-season baseline), then **once after each gameweek** to add a new sheet with updated stats.

This writes three Excel files to `data/`:
- `players_master.xlsx` — player stats, one sheet per GW
- `teams_master.xlsx` — team data, one sheet per GW
- `fixtures_master.xlsx` — upcoming GW fixtures, one sheet per GW

### 4. Run the analysis notebook

```bash
jupyter notebook fpl_analysis.ipynb
```

Run all cells top to bottom. The notebook outputs five sections: ranked recommendations per position, differential picks, a personal watchlist lookup, the optimal squad, and optionally exports everything to a markdown report.

### 5. Tune weights (optional)

```bash
python explore.py           # display per-position correlation heatmaps interactively
python explore.py --save    # save heatmaps as PNG to data/
```

Use the heatmaps to understand which stats correlate most strongly with `total_points` per position, and adjust the `*_WEIGHTS` dicts in the notebook accordingly.

## File Structure

```
fpl-analysis/
├── fetch.py             — fetches bootstrap API, saves JSON + updates xlsx files
├── explore.py           — correlation analysis tool for weight tuning (per-position heatmaps)
├── models.py            — TypedDict definitions for FPL API responses
├── fpl_analysis.ipynb   — full analysis notebook (self-contained, runs top to bottom)
├── requirements.txt     — Python dependencies
├── data/
│   ├── raw/             — weekly JSON snapshots (gw{n}_{date}.json)
│   ├── reports/         — weekly markdown reports (gw{n}-dd-mm-yyyy.md)
│   ├── players_master.xlsx  — elements data, one sheet per GW (GW0 = pre-season / last season)
│   ├── teams_master.xlsx    — teams data, one sheet per GW
│   └── fixtures_master.xlsx — fixtures data, one sheet per GW (fixtures for upcoming GW)
├── DATA.md              — full FPL API field reference
├── PLAN.md              — project roadmap
├── NOTES.md             — learning notes and Q&A
└── README.md            — this file
```

## How the Scoring Model Works

### GW sheet naming

`fetch.py` saves data under `GW{n}` where `n` is the number of GWs already played (`event["id"] - 1`). Pre-season data is `GW0`. After GW1 is played, the next fetch creates `GW1`, and so on. All three xlsx files use the same sheet name so the notebook can read them consistently.

### Season-aware weight blending

The consistency signal (PPG + form) blends across three time horizons as the season progresses:

| GWs played | ppg_last | ppg_current | form |
|-----------|---------|------------|------|
| 0 (pre-season) | 100% | 0% | 0% |
| 1–3 | 70% | 20% | 10% |
| 4–6 | 40% | 30% | 30% |
| 7–10 | 10% | 40% | 50% |
| 11+ | 0% | 45% | 55% |

### minutes_confidence

Per-90 stats (`clean_sheets_per_90`, `saves_per_90`) are multiplied by `min(minutes_played / (gws_played × 90), 1.0)` before normalization. This prevents players with very few appearances (e.g. 1 game with a clean sheet) from appearing inflated.

Pre-season the denominator is `38 × 90` (a full season), so last-season per-90 stats are trusted proportionally to how many games the player actually played.

### Position-specific weights

Each position uses a different set of scoring factors backed by correlation analysis:

| Position | Key factors |
|----------|------------|
| GKP | `clean_sheets_per_90`, `saves_per_90` (inverted), `ep_next`, `fdr`, `chance_of_playing` |
| DEF | `ict_index`, `clean_sheets_per_90`, `ep_next`, `fdr`, `chance_of_playing` |
| MID | `ict_index`, `ep_next`, `fdr`, `chance_of_playing` |
| FWD | `threat`, `ep_next`, `fdr`, `chance_of_playing` |

Plus the blended consistency signal (`ppg_last` + `ppg_current` + `form`) shared across all positions with a combined weight of 0.20.

## Data Source

All data is pulled from the official FPL bootstrap-static API:

```
https://fantasy.premierleague.com/api/bootstrap-static/
```

No API key required. The API is public but undocumented — see `DATA.md` for a full field reference.
