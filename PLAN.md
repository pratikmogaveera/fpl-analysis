# FPL Analysis — Plan

Learn data analysis through FPL data while building a tool that recommends the best players for the next gameweek.

---

## 0. Data Pipeline — Fetch & Store

**Goal:** Build a weekly script that fetches the bootstrap API and stores snapshots for historical analysis.

**Tasks:**
- Write `fetch.py` to call `https://fantasy.premierleague.com/api/bootstrap-static/`
- Detect current GW number from `events` (find `is_next: true`)
- Save raw response as `data/raw/gw{n}_{date}.json`
- Extract `elements` and write as a new sheet `GW{n}` in `data/players.xlsx`
- Extract `teams` and write as a new sheet `GW{n}` in `data/teams.xlsx`
- Handle re-runs gracefully (don't duplicate a sheet if already exists)

**Key Concepts:**
- `requests` library for HTTP calls
- File I/O with `json` module
- Writing xlsx with `openpyxl` via `pd.ExcelWriter`
- Appending sheets to an existing workbook

**Done when:** Running `python fetch.py` saves the JSON and updates both xlsx files with a new GW sheet.

---

## 1. Setup & Data Exploration

**Goal:** Understand the dataset and get comfortable with the project structure.

**Tasks:**
- Set up `ml-env` and verify packages (pandas, matplotlib, seaborn)
- Explore the bootstrap JSON structure (`explore.py`)
- Understand what each top-level key contains

**Key Concepts:**
- JSON structure navigation
- Python dicts vs lists
- Reading API responses

**Done when:** You can describe what data is available and where each piece lives.

---

## 2. Pandas Basics — Loading & Inspecting

**Goal:** Load `elements` (players) into a DataFrame and do first explorations.

**Tasks:**
- Load `elements` into a DataFrame
- Inspect shape, dtypes, nulls
- Understand FPL's cost encoding (50 = £5.0m)
- Add a `name` column (first + second name)
- Map `team` ID to team name using `teams`
- Map `element_type` ID to position (GK/DEF/MID/FWD)

**Key Concepts:**
- `pd.DataFrame`, `.head()`, `.info()`, `.describe()`
- Column creation and transformation
- Merging DataFrames

**Done when:** You have a clean DataFrame with readable names, team names, and positions.

---

## 3. Data Cleaning & Normalization

**Goal:** Make the data analysis-ready.

**Tasks:**
- Normalize numeric columns stored as strings (`form`, `points_per_game`, `ep_next`, etc.)
- Handle nulls (`chance_of_playing_*`, `ep_next`)
- Filter out unavailable/removed players
- Derive `cost` column in £ from `now_cost`

**Key Concepts:**
- `pd.to_numeric`, `fillna`, `dropna`
- Boolean filtering
- Data types

**Done when:** No string-encoded numbers remain; dataset contains only active, selectable players.

---

## 4. Exploratory Analysis

**Goal:** Understand the shape and distribution of the data.

**Tasks:**
- Top 10 players by total points, by position
- Points per £ (value metric)
- Form vs season consistency (form vs points_per_game)
- Ownership distribution (`selected_by_percent`)
- Correlation between ICT index and total points

**Key Concepts:**
- Sorting, groupby, aggregation
- Correlation (`df.corr()`)
- Distributions and outliers

**Done when:** You can answer "who are the best value players right now?" with data.

---

## 5. Fixture Difficulty

**Goal:** Add fixture context to player scores.

**Tasks:**
- Understand `teams` strength ratings (attack/defence, home/away)
- Build a fixture difficulty rating (FDR) per team for next GW
- Join FDR back to the players DataFrame

**Key Concepts:**
- Multi-table joins
- Derived scoring from raw ratings
- Home vs away adjustments

**Done when:** Each player has an FDR score for the next gameweek attached to their row.

---

## 6. Next GW Scoring Model

**Goal:** Score every player for the next gameweek using a weighted formula.

**Tasks:**
- Define scoring factors: form, points_per_game, ep_next, FDR, chance_of_playing
- Assign weights to each factor
- Compute a composite `next_gw_score` per player
- Rank players by position

**Key Concepts:**
- Weighted scoring
- Normalization (min-max scaling)
- Decision logic

**Done when:** You can output a ranked list of recommended players per position for the next GW.

---

## 7. Visualization

**Goal:** Make the analysis readable with charts.

**Tasks:**
- Bar chart: top players by value (points per £)
- Scatter plot: form vs points_per_game
- Heatmap: correlation matrix of key stats
- Final GW recommendation table (styled DataFrame or chart)

**Key Concepts:**
- matplotlib basics (figure, axes, labels)
- seaborn (barplot, scatterplot, heatmap)
- Pandas styling

**Done when:** Analysis has clear, labeled charts that tell the story.

---

## 8. Notebook Consolidation

**Goal:** Bring everything into a clean Jupyter notebook.

**Tasks:**
- Move analysis from scripts into a structured notebook
- Add markdown cells explaining each step
- Final output: GW recommendation section at the end

**Key Concepts:**
- Jupyter notebook structure
- Reproducible analysis

**Done when:** Notebook runs top-to-bottom and produces the full analysis cleanly.

---

## 9. Enhancements (Post Phase 8)

### 9a. Dynamic GW detection ✅
**Goal:** Remove hardcoded `GAMEWEEK = 'GW1'` — detect the latest available GW from xlsx sheets automatically.

**Tasks:**
- Read sheet names from `players_master.xlsx`
- Pick the latest one (e.g. `GW10`)
- Pass as parameter to `build_players_df(gameweek)`

**Done when:** Script works without changing `GAMEWEEK` constant each week.

---

### 9b. Season-aware weight blending
**Goal:** Blend last season's stats with current season stats as the season progresses.

**Background:** Pre-season and early GWs (1–5), last season's `points_per_game` and `ict_index` are the most reliable signals. As the current season progresses, `form` (rolling recent GW average) becomes more meaningful. With only 1–2 GWs of data, a single 15-point haul skews form unfairly.

**Blended approach:**
```
score = (last_season_weight * last_season_stats) + (current_season_weight * current_season_stats)
```

| Season progress | Last season weight | Current season weight |
|----------------|-------------------|-----------------------|
| GW 1–5 | 80% | 20% |
| GW 6–15 | 50% | 50% |
| GW 16–25 | 30% | 70% |
| GW 26+ | 10% | 90% |

**Tasks:**
- Add `form` to normalization columns
- Introduce a `season_progress` factor based on current GW
- Shift `form` weight up and `points_per_game` weight down as GWs progress

**Done when:** Model automatically adjusts weights based on how many GWs have been played.

---

### 9c. Position-specific scoring models ✅
**Goal:** Different positions score differently — apply position-aware weights.

**Background:** A GK's score should weight `clean_sheets_per_90` and `saves_per_90` heavily. A FWD should weight `expected_goals` and `threat`. Currently all positions use the same formula.

**Tasks:**
- Define separate `WEIGHTS` dicts per position
- Apply the correct weights dict based on `position` when computing `next_gw_score`

**Done when:** GKP score uses GK-relevant stats, FWD score uses attacking stats.

---

### 9d. fetch.py robustness
**Goal:** Make the data pipeline production-ready.

**Tasks:**
- Add retry logic with exponential backoff for API calls
- Split `dump_raw_data()` into smaller focused functions
- Move file paths to a single config block at top of file

**Done when:** `fetch.py` handles transient API failures gracefully without crashing.
