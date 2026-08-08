# FPL Analysis — Learning Notes

## 0. Data Pipeline — Fetch & Store

### Key Concepts

- **`requests.get(url)`** — makes an HTTP GET call; `.raise_for_status()` throws on 4xx/5xx so errors don't silently pass
- **`response.json()`** — parses the JSON response body into a Python dict/list directly; no need to call `json.loads` separately
- **`json.dump(data, file, indent=2)`** — writes a Python object to a file as pretty-printed JSON; `indent=2` makes it human-readable
- **`Path(file_name).is_file()`** — checks if a file already exists; used to prevent overwriting existing snapshots on re-runs
- **`pd.DataFrame(list_of_dicts)`** — converts a list of dicts into a DataFrame; each dict key becomes a column
- **`pd.ExcelWriter`** with `mode="a"` and `if_sheet_exists="replace"` — appends a new sheet to an existing xlsx without touching other sheets
- **`TypedDict`** — used to type-hint the FPL API response shape; helps editors catch key typos and makes the code self-documenting

### APIs / Tools Learned

| Tool | Usage |
|------|-------|
| `requests` | HTTP GET, `.raise_for_status()`, `.json()` |
| `json` module | `json.dump()` for writing, `json.load()` for reading |
| `pathlib.Path` | `.is_file()` for existence check |
| `pd.DataFrame` | construct from list of dicts |
| `pd.ExcelWriter` | write/append sheets to xlsx |
| `TypedDict` | type-hint dict shapes |

### Key Data Facts

- FPL bootstrap API: `https://fantasy.premierleague.com/api/bootstrap-static/`
- Top-level keys: `chips`, `events`, `game_settings`, `game_config`, `phases`, `teams`, `total_players`, `element_stats`, `element_types`, `elements`
- Upcoming GW detected via `event["is_next"] == True` in the `events` list
- Snapshots saved as `data/raw/gw_{n}_{date}.json`
- `elements` → players (563 rows, 105 columns); `teams` → 20 rows

---

## 1. Setup & Data Exploration

### Key Concepts

- **`json.load(file)`** — reads a JSON file into a Python object; different from `json.loads()` which takes a string
- **`pd.DataFrame(data["elements"])`** — correct way to build a DataFrame from an already-parsed list; `pd.read_json()` is for strings or file paths, not Python objects
- **`df.columns`** — returns an Index of all column names; iterate over it to print each one
- **`df.iloc[0]`** — selects the first row as a Series; `.keys()` on it gives column names, `.values` gives the row's data — useful for inspecting a single record
- **`df.iloc[0]` vs `df.columns`** — use `df.columns` for just column names; use `df.iloc[0]` when you want names + a sample value side by side

### Notable columns in `elements`

| Group | Columns |
|-------|---------|
| Identity | `id`, `code`, `first_name`, `second_name`, `web_name`, `team`, `element_type` |
| Availability | `can_transact`, `can_select`, `status`, `removed`, `chance_of_playing_next_round`, `chance_of_playing_this_round` |
| Cost | `now_cost`, `cost_change_event`, `cost_change_start`, `price_change_percent` |
| Performance | `total_points`, `form`, `points_per_game`, `ep_next`, `minutes`, `starts` |
| Attack stats | `goals_scored`, `assists`, `expected_goals`, `expected_assists`, `expected_goal_involvements` |
| Defence stats | `clean_sheets`, `goals_conceded`, `expected_goals_conceded`, `saves`, `penalties_saved` |
| ICT index | `influence`, `creativity`, `threat`, `ict_index` |
| Per-90 stats | `expected_goals_per_90`, `saves_per_90`, `clean_sheets_per_90`, `starts_per_90` |
| Ranks | `form_rank`, `form_rank_type`, `now_cost_rank`, `selected_rank`, etc. (`_type` = rank within position) |
| Set pieces | `corners_and_indirect_freekicks_order`, `direct_freekicks_order`, `penalties_order` |

### Columns needing type casting (string-encoded numbers)

These come back as strings from the API and must be cast before any numeric operation:
`form`, `points_per_game`, `ep_next`, `ep_this`, `influence`, `creativity`, `threat`, `ict_index`, `value_form`, `value_season`, `selected_by_percent`, `expected_goals`, `expected_assists`, `expected_goal_involvements`, `expected_goals_conceded`

Use `pd.to_numeric(df[col], errors='coerce')` for safe casting.

### Null patterns observed

- `chance_of_playing_next_round` / `chance_of_playing_this_round` — `None`/`nan` when no injury concern (treat as 100%)
- `ep_this` — `None` pre-season (no GW played yet)
- `news_added`, `corners_and_indirect_freekicks_order` etc. — `nan` when not applicable

### Top-level bootstrap JSON keys

| Key | Type | Size / Details |
|-----|------|----------------|
| `elements` | list | 563 — players, the main dataset |
| `teams` | list | 20 — Premier League teams |
| `events` | list | 38 — one per gameweek |
| `element_types` | list | 4 — position definitions (GK/DEF/MID/FWD) |
| `element_stats` | list | 26 — stat metadata (names, labels) |
| `chips` | list | 8 — chip types (wildcard, free hit, etc.) |
| `phases` | list | 11 — season month phases |
| `game_settings` | dict | flat config (squad size, transfer rules, etc.) |
| `game_config` | dict | nested: `settings`, `rules`, `scoring` |
| `total_players` | int | 1,936,724 — total FPL managers this season |

`element_types` and `teams` will be used in Phase 2 to map IDs to readable names.

### How `explore.py` prints the summary

Iterates over `data` (the top-level dict), checks the type of each value, and prints a meaningful detail — `len()` for lists/strings, `.keys()` for dicts, the value itself for ints.

---

## 2. Pandas Basics — Loading & Inspecting

### Key Concepts

**Three ways to add/join columns to a DataFrame:**

| Method | When to use | Example |
|--------|-------------|---------|
| Direct computation | Derive from existing columns of the same DataFrame | `df["full_name"] = df["first_name"] + " " + df["second_name"]` |
| `df.map(dict)` | Map one column's values to another using a lookup dict | `df["position"] = df["element_type"].map({1: "GKP", 2: "DEF", ...})` |
| `pd.merge(left, right, how, left_on, right_on)` | Join two DataFrames on a shared key — use when you need multiple columns from the other table | `pd.merge(players_df, teams_df, "left", left_on="team", right_on="id")` |

**Use `.map()` over `pd.merge()` when you only need one column** — merge adds all columns from the right DataFrame and bloats the result.

**Dict comprehension as the lookup for `.map()`:**
```python
players_df["team_name"] = players_df["team_code"].map(
    {team["code"]: team["name"] for team in data["teams"]}
)
```
The dict comprehension builds `{code: name, ...}` on the fly — no need to create a separate DataFrame.

### Inspection methods

| Method | What it tells you |
|--------|------------------|
| `df.shape` | `(rows, cols)` — quick size check |
| `df.info()` | Column names, non-null counts, dtypes, memory usage — most useful overview |
| `df.dtypes` | Per-column dtype — shows which columns are wrong type at a glance |
| `df.head(n)` | First n rows — default 5 |

### dtype observations on `elements`

- `str(33)` — 33 string columns, many are numbers stored as strings (`form`, `points_per_game`, `ep_next`, ICT fields, `expected_*`) — must cast in Phase 3
- `object(4)` — mixed/ambiguous types, including `chance_of_playing_this_round`
- `float64(14)`, `int64(51)` — already numeric, usable directly
- `chance_of_playing_this_round` is `object` while `chance_of_playing_next_round` is `float64` — caused by `None` values mixed with numbers in the pre-season state



### Why use `pd.DataFrame(list)` instead of `pd.read_json(list)`?
`pd.read_json` expects a JSON string or a file path — it will try to parse its argument as raw text. `data["elements"]` is already a Python list of dicts (parsed by `json.load`), so passing it to `pd.read_json` would fail or produce wrong results. `pd.DataFrame(list_of_dicts)` is the correct constructor for this case.

### What's the difference between `form_rank` and `form_rank_type`?
`form_rank` is a player's rank globally across all 563 players. `form_rank_type` is rank within their position (GK/DEF/MID/FWD). The `_type` suffix consistently means "within position" across all rank columns.

### Why is `now_cost` stored as an integer like 60 instead of 6.0?
FPL stores costs multiplied by 10 to avoid floating point in the database. Divide by 10 to get the £ value: `df["cost"] = df["now_cost"] / 10`.

---

## 3. Data Cleaning & Normalization

### Key Concepts

**`pd.to_numeric(series, errors='coerce')`** — converts a Series to numeric. `errors='coerce'` turns unconvertible values into `NaN` instead of raising — safe for messy data. Must assign back: `df[col] = pd.to_numeric(df[col], errors='coerce')`.

**`df[col].fillna(value)`** — replaces `NaN` with a default. Returns a new Series — must assign back. Common patterns:
- `fillna(100)` — treat missing availability as fully fit
- `fillna(0)` — treat missing expected points as zero

**Boolean indexing / filtering:**
```python
df = df[df['status'].isin(['a', 'i', 'd'])]
```
`.isin(list)` returns a boolean Series — `True` for rows to keep. Reassign to drop the excluded rows.

**`df.size` vs `len(df)` vs `df.shape[0]`**
- `df.size` — total cells (rows × columns) — rarely what you want
- `len(df)` or `df.shape[0]` — row count — use these to verify filter results

### Cleaning steps applied

| Step | Code pattern | Result |
|------|-------------|--------|
| Cast string numerics | `pd.to_numeric(df[col], errors='coerce')` | 14 columns: str → float64 |
| Fill availability nulls | `fillna(100)` | NaN → 100% available |
| Fill ep_next nulls | `fillna(0)` | NaN → 0 expected points |
| Filter inactive players | `.isin(['a', 'i', 'd'])` | 563 → 557 rows |
| Derive cost in £ | `df['cost'] = df['now_cost'] / 10` | New column, human-readable |

### Player status codes (undocumented by FPL, community-sourced)

| Code | Meaning | Keep for analysis? |
|------|---------|--------------------|
| `a` | Available | ✅ |
| `i` | Injured | ✅ (has chance_of_playing value) |
| `d` | Doubtful | ✅ (has chance_of_playing value) |
| `s` | Suspended | ❌ |
| `u` | Unavailable (loan/left club) | ❌ |

---

## 4. Exploratory Analysis

### Key Concepts

**Sorting a DataFrame:**
```python
df.sort_values(by='col', ascending=False)
```
Returns a new DataFrame — doesn't mutate the original unless you reassign. Use `temp_df` or inline `.head()` to avoid polluting `players_df`.

**Filtering — `==` vs `.isin()`:**
- `df[df['col'] == value]` — single value, preferred
- `df[df['col'].isin([v1, v2])]` — multiple values
- Don't use `.isin([single_value])` — that's just `==` with extra steps

**Derived metric — points per £:**
```python
players_df['points_per_euro'] = players_df['total_points'] / players_df['cost']
```
Divides two numeric columns element-wise — no loop needed.

**Correlation:**
```python
df[['col1', 'col2']].corr()
```
Returns a 2×2 matrix. Diagonal is always 1.0 (self-correlation). Extract the scalar with `.iloc[0].iloc[1]`.

### Key findings (pre-season, GW1 2026/27)

| Analysis | Finding |
|----------|---------|
| Top GKP by points | Raya (162), Kelleher (143), Roefs (136) |
| Top DEF by points | Gabriel (209), Guéhi (179), Van Dijk (175) |
| Top MID by points | Bruno (235), Semenyo (202), Gibbs-White (188) |
| Top FWD by points | Haaland (239), Thiago (181), João Pedro (177) |
| ICT vs total_points correlation | **0.94** — very strong, ICT is a reliable scoring signal |
| Form | All 0.0 pre-season — not useful until GWs are played |

### Note on form
`form` is a rolling average of recent GW points — meaningless pre-season. Task 3 (form vs consistency) is deferred to mid-season when real GW data exists.

---

## 5. Fixture Difficulty

### Key Concepts

**`pd.read_excel(path, sheet_name='GW1')`** — reads a specific sheet from an xlsx file into a DataFrame. Omit `sheet_name` to read the first sheet.

**`df.rename(columns={old: new})`** — renames columns. Returns a new DataFrame — doesn't mutate. Useful when combining two DataFrames that have different column names but represent the same concept:
```python
home = fixtures_df[['team_h', 'team_h_difficulty']].rename(columns={'team_h': 'team_id', 'team_h_difficulty': 'fdr'})
away = fixtures_df[['team_a', 'team_a_difficulty']].rename(columns={'team_a': 'team_id', 'team_a_difficulty': 'fdr'})
```

**`pd.concat([df1, df2])`** — stacks two DataFrames vertically (appends rows). Requires matching column names. Use when two DataFrames represent the same type of data from different sources.

**`dict(zip(series1, series2))`** — creates a lookup dict by pairing two Series element-wise. Cleaner than a dict comprehension when both series are already in a DataFrame:
```python
dict(zip(fdr_df['team_id'], fdr_df['fdr']))  # → {team_id: fdr, ...}
```

**`iterrows()` vs vectorized operations** — avoid looping over DataFrame rows with `iterrows()` when possible. Use `.map()`, `.apply()`, or vectorized column operations instead — they're faster and more readable.

### FDR logic

FPL provides `team_h_difficulty` and `team_a_difficulty` per fixture — how hard the match is for the home/away team respectively (scale 1–5, lower = easier).

Steps:
1. Extract home and away sides as separate DataFrames with unified column names (`team_id`, `fdr`)
2. `pd.concat` them into one FDR table (20 rows, one per team)
3. `.map()` onto `players_df['team']` using the `{team_id: fdr}` dict

### Shared types via models.py

`TypedDict` definitions moved to `models.py` — imported wherever needed. Avoids duplication across files. Don't name the file `types.py` — shadows Python's built-in `types` module.

---

## 6. Next GW Scoring Model

### Key Concepts

**Why normalize before scoring?**
Each factor has a different scale — `chance_of_playing` is 0–100, `fdr` is 1–5, `ep_next` is 0–15. Without normalization, the column with the largest range dominates the score regardless of weight. Min-max scaling squashes all columns to 0–1 so weights are meaningful.

**Min-max normalization formula:**
```python
normalized = (value - min) / (max - min)
```
Result: 0.0 = worst in dataset, 1.0 = best in dataset.

**Inverting FDR:**
Lower FDR = easier fixture = better for the player. After normalizing, a low FDR would score 0 (worst). Invert with `1 - fdr_norm` so easy fixtures score high.

**Weighted sum:**
```python
players_df['next_gw_score'] = sum([
    players_df[f'{col}_norm'] * weight
    for col, weight in WEIGHTS.items()
])
```
Weights must sum to 1.0 — otherwise scores are scaled incorrectly.

**`df.copy()` to defragment:**
Adding many columns one at a time fragments DataFrame memory internally. `players_df = players_df.copy()` rebuilds it as a clean contiguous block — fixes the `PerformanceWarning`. Call it after all column additions are done.

### Scoring weights used

| Factor | Weight | Reasoning |
|--------|--------|-----------|
| `points_per_game` | 0.30 | Best measure of consistent scoring |
| `ep_next` | 0.25 | FPL's own GW prediction |
| `fdr` | 0.20 | Fixture difficulty (inverted) |
| `ict_index` | 0.15 | Influence/creativity/threat composite |
| `chance_of_playing` | 0.10 | Availability filter |

### GW1 top picks (pre-season)

| Position | Player | Score |
|----------|--------|-------|
| GKP | David Raya | 0.761 |
| DEF | Gabriel | 0.878 |
| MID | Bruno Fernandes | 0.987 |
| FWD | Erling Haaland | 0.894 |

---

## 7. Visualization

### Key Concepts

**matplotlib OO API vs stateful API:**
- `plt.bar(...)` — stateful, operates on "current figure" globally — fine for one chart
- `fig, ax = plt.subplots()` — OO, explicit figure/axes objects — use when making multiple charts
- Each `plt.show()` clears the current figure; next `plt.subplots()` starts fresh

**`ax.barh(y, x)`** — horizontal bar chart. Better than `ax.bar` for long labels. Sorts bottom-to-top, so sort ascending before plotting if you want best at top.

**seaborn with matplotlib axes:**
Pass `ax=ax` to any seaborn function to draw on a specific axes:
```python
sns.scatterplot(data=df, x='col1', y='col2', ax=ax)
sns.heatmap(corr_matrix, annot=True, fmt='.2f', ax=ax)
sns.kdeplot(data=df, x='col1', y='col2', fill=True, ax=ax)
```

**`sns.heatmap`** — visualizes a correlation matrix. Key params:
- `annot=True` — show values inside cells
- `fmt='.2f'` — format to 2 decimal places
- `vmin=0, vmax=1` — fix color scale to 0–1 range for absolute comparison

**`sns.kdeplot`** — 2D density plot. Shows where data is concentrated — better than scatter for large datasets with overlapping points. Use `fill=True` for filled contours.

**`df.groupby('col').head(n)`** — returns top n rows per group. Use after sorting to get top n per category:
```python
df.sort_values('score', ascending=False).groupby('position').head(5)
```

**`df.to_string(index=False)`** — prints DataFrame without row index. Cleaner for terminal output.

**Pandas `.style`** — styling API for DataFrames (background gradients, formatting). Only renders visually in Jupyter — use in Phase 8 notebook, not plain scripts.

### Charts built

| Chart | Type | Key insight |
|-------|------|-------------|
| Top players by points/£ | `barh` | Best value players are cheap defenders/GKs from last season |
| ICT vs total points | `scatterplot` | 0.94 correlation, two clear outliers (Bruno, Haaland) |
| ICT vs total points density | `kdeplot` | Most players cluster at low ICT/low points |
| Correlation matrix | `heatmap` | ICT (0.94) and PPG (0.90) are strongest total_points predictors |
| GW recommendation table | `to_string` | Top 5 per position ranked by next_gw_score |

### Module pattern

`viz.py` imports `build_players_df` from `analysis.py` — avoids copy-pasting the pipeline. Functions in `analysis.py` outside `if __name__ == '__main__'` are importable as a module.

---

## Weight Decision Methodology

### How to decide weights in a scoring model

**1. Start with the correlation matrix**
Correlation with the target variable (`total_points`) gives a ranked signal strength. Higher correlation → more predictive → higher weight candidate.

| Feature | Correlation with total_points |
|---------|-------------------------------|
| `ict_index` | 0.94 |
| `points_per_game` | 0.90 |
| `cost` | 0.60 |
| `ep_next` | 0.54 |
| `selected_by_percent` | 0.54 |

**2. Apply domain knowledge**
Raw correlation isn't everything. `points_per_game` measures season-long consistency — a more stable signal than `ict_index` which can spike for one big game. For FPL, consistent scorers are more reliable picks than one-week performers. So PPG got a higher weight (0.30) than ICT (0.15) despite slightly lower correlation.

**3. Check for collinearity (avoid double-counting)**
ICT and PPG correlate with each other at **0.83** — they measure similar things. Giving both high weights double-counts the same signal. In a formal model, handle this with PCA or regularization. In a simple weighted model, just cap combined weight of highly correlated pairs.

**4. Handle special features differently**
- `chance_of_playing` — acts as a penalty, not a reward. Low historical correlation but critical for availability. Keep weight low (0.10) but ensure 0% availability kills the score.
- `fdr` — forward-looking, not historical. Correlation with past points is meaningless. Weight based on FPL community consensus on how much fixtures matter (~0.20).

**5. Validate with intuition**
Run the model and check if top picks make sense. Bruno, Haaland, Gabriel, Raya at the top — that's correct. If the output looks wrong, revisit weights.

### When to retune weights

- **Pre-season** — `form` is 0, `ep_next` is less accurate. Lean on PPG and ICT.
- **Mid-season** — `form` becomes meaningful (rolling recent GW points). `ep_next` improves as FPL has current season data. Increase their weights.
- **End of season** — fixture difficulty matters more for rotation-heavy squads.

---

## 9c. Position-Specific Scoring Models

### Key Concepts

**Why position-specific weights?**
A generic scoring model treats all positions the same. But a GK scores from clean sheets and saves — not goals. A FWD scores from goals and threat — not clean sheets. Applying position-relevant stats improves ranking quality within each position group.

### Scoring factors per position

| Position | Key factors | Dropped/irrelevant |
|----------|-------------|-------------------|
| GKP | `clean_sheets_per_90`, `saves_per_90`, `points_per_game`, `ep_next`, `fdr` | `ict_index` (attacker-biased) |
| DEF | `clean_sheets_per_90`, `points_per_game`, `ep_next`, `ict_index`, `fdr` | `saves_per_90` |
| MID | `ict_index`, `points_per_game`, `ep_next`, `clean_sheets_per_90`, `fdr` | `saves_per_90` |
| FWD | `threat`, `points_per_game`, `ep_next`, `fdr` | `clean_sheets_per_90`, `saves_per_90` |

**`threat` vs `expected_goals` for FWD:**
Both correlate at 0.97 with each other — using both would double-count the same signal. `threat` is chosen as it's forward-looking (measures attacking intent) vs `expected_goals` which is historical.

**`saves_per_90` for GKP — known limitation:**
A GK behind a weak defence faces more shots and accumulates higher `saves_per_90`. This inflates scores for GKs on poor defensive teams. Raya (Arsenal, strong defence) scores lower on saves than a GK on a leaky team despite being a better pick. No easy fix without opponent-adjusted stats.

### Minutes filter

Players with fewer than 900 minutes of last-season PL data are excluded:
```python
players_df = players_df[players_df['minutes'] >= 900]
```

**Why 900 minutes (~10 full games)?**
Per-90 stats on small samples are unreliable. A GK who played 1 game might have 3 saves from that one match, giving a `saves_per_90` that vastly overstates their typical output.

### Known limitation: new signings

Players new to the PL (transferred from abroad) have 0 PL minutes and are excluded by the minutes filter. This is an accepted tradeoff — no reliable data means no reliable score. 

Workarounds (not yet implemented):
- Use only `ep_next` and `fdr` for new signings (no per-90 stats)
- This is partially addressed by Phase 9b (season-aware blending) — once new signings play a few GWs, current-season stats start accumulating and can be blended in

### Correlation findings per position (GW1 2026/27)

| Position | Strongest signal | Notes |
|----------|-----------------|-------|
| GKP | `clean_sheets_per_90` (0.91), `saves_per_90` (0.90) | Both proxy the same thing: GK involved in clean sheets |
| DEF | `clean_sheets_per_90` (0.91) | Defenders score heavily from clean sheets |
| MID | `ict_index` (0.83), `clean_sheets_per_90` (0.83) | ICT captures midfield involvement; clean sheets bonus also significant |
| FWD | `threat` (0.92), `expected_goals` (0.90) | Near-identical signal — use one only |


---

## 9b. Season-Aware Weight Blending

> **Note:** This section documents the original two-way blend between `ppg_last` and `form`. It was later enhanced in **9f** to a three-way blend that also includes current-season `points_per_game`. The weight thresholds and `get_season_weights` signature were updated in 9f — refer to the 9f section for the current implementation.

### Key Concepts

**Why blend last-season vs current-season stats?**
Pre-season and early GWs, the live `form` column is noisy — one 15-point haul from a single game skews a rolling average based on 1–2 games. Last season's `points_per_game` is a stable baseline. As the season progresses and more GW data accumulates, `form` becomes reliable and `points_per_game` becomes stale. The model needs to shift trust accordingly.

**The blending approach:**
```python
consistency_score = (last_w * ppg_last_norm) + (curr_w * form_norm)
```

| GWs played | last_w | curr_w |
|-----------|--------|--------|
| 0 (pre-season) | 1.0 | 0.0 |
| 1–5 | 0.8 | 0.2 |
| 6–15 | 0.5 | 0.5 |
| 16–25 | 0.3 | 0.7 |
| 26+ | 0.1 | 0.9 |

**`get_season_weights(gws_played) -> tuple[float, float]`:**
Returns `(last_w, curr_w)`. Pre-season is treated as 0 GWs played → full weight on last-season data. The `curr_gw_id` variable (derived from `event["id"] - 1`) doubles as the GWs-played count.

**Weights must still sum to 1.0:**
`ppg_last` and `form` share the same 0.20 budget:
```python
FORM_AND_PPG_WEIGHTS = {
    'ppg_last': 0.20 * last_w,
    'form':     0.20 * curr_w
}
```
This replaces the old static `'points_per_game': 0.20` entry. Everything else in the position weights dicts stays unchanged.

**Don't mutate constants:**
Build fresh merged dicts using dict unpacking instead of `.update()`:
```python
gkp_weights = {**GKP_WEIGHTS, **FORM_AND_PPG_WEIGHTS}
```
This avoids the problem where re-running the scoring cell would double-insert keys into the same dict.

---

## 9e. True Last-Season PPG Blend

### Key Concepts

**The flaw in 9b's original implementation:**
Both `points_per_game` and `form` were read from the same weekly snapshot. Mid-season, `points_per_game` is already updated with this season's data — so the "last season" side of the blend was not actually last season. The fix: read `points_per_game` from the `GW0` sheet specifically.

**Why GW0?**
`GW0` is the pre-season bootstrap snapshot — fetched before GW1 is played. At that point, all player stats still reflect the previous season. It's the only sheet guaranteed to hold true last-season data, regardless of when the notebook runs.

**`code` as the stable join key:**
FPL player `id` can change between seasons. `code` is a permanent player identifier that persists across seasons. Always join historical data on `code`, not `id`.

**Left join — not right join:**
```python
players_df_last_season = players_df_last_season[['points_per_game', 'code']].rename(
    columns={'points_per_game': 'ppg_last'}
)
players_df = players_df.merge(players_df_last_season, on='code', how='left')
players_df['ppg_last'] = players_df['ppg_last'].fillna(0)
```
- **Left join** — keeps all current players, looks up their GW0 PPG
- **Right join would be wrong** — it would keep all GW0 players and drop current players with no GW0 match
- **`fillna(0)` for new players** — players promoted from abroad or new to PL have no GW0 entry; `0` is a conservative default (no last-season data = no last-season signal). Will be addressed more gracefully in 9f when current-season PPG is added as a third signal.

**Zero-denominator guard in normalization:**
Pre-season, `form` is `0.0` for every player. Min-max normalization: `(0 - 0) / (0 - 0) = 0/0 = NaN`. Same risk for any column where all values are identical. Fix:
```python
col_min = players_df[col].min()
col_max = players_df[col].max()
denominator = col_max - col_min if col_max != col_min else 1
players_df[f'{col}_norm'] = (players_df[col] - col_min) / denominator
```
When all values are equal, `denominator = 1` and `col - col_min = 0`, giving `0.0` for everyone — correct, since no player has an advantage on that factor.

---

## Weight Rebalancing (From Correlation Data)

### Key Concepts

**Using `explore.py` to tune weights:**
`explore.py` generates per-position correlation heatmaps showing each scoring factor's correlation with `total_points`. The heatmap is the evidence base for weight decisions — higher correlation → more predictive → candidate for higher weight.

**`saves_per_90` inversion:**
`saves_per_90` negatively correlates with `total_points` (−0.18 to −0.72 across positions). A GK making lots of saves plays for a weak team, concedes more, and earns fewer points. It must be inverted like `fdr`:
```python
if col in ['fdr', 'saves_per_90']:
    players_df[f'{col}_norm'] = 1 - ((players_df[col] - col_min) / denominator)
```

**FDR correlation insight:**
FDR shows weak correlation with last-season `total_points` (−0.01 to −0.16) across positions. This is expected — season-long stats aggregate many fixtures, so no single fixture difficulty dominates. FDR's value is as a per-GW signal, not across a full season. Keep it in the model but don't over-weight it.

### Weight changes made (backed by correlation data)

| Position | Change | Reason |
|----------|--------|--------|
| GKP | `clean_sheets_per_90`: 0.25→0.275 | Strong signal (0.63) |
| GKP | `saves_per_90`: 0.15→0.125 | Negative correlation — now inverted |
| DEF | `ict_index`: 0.10→0.25 | Strongest DEF signal (0.88) |
| DEF | `chance_of_playing`: 0.10→0.05 | Weak signal (0.11) |
| DEF | `clean_sheets_per_90`: 0.25→0.15 | Moderate signal (0.36), reduced |
| MID | `ict_index`: 0.25→0.32 | Dominant MID signal (0.92) |
| MID | `clean_sheets_per_90` | Dropped — near-zero correlation (0.12) |
| MID | `fdr`: 0.15→0.18 | Small bump to keep weights summing to 1.0 |
| FWD | `threat`: 0.35→0.375 | Strongest FWD signal (0.95) |
| FWD | `fdr`: 0.15→0.10 | Near-zero correlation (−0.04) |

All position weight sets still sum to 1.0 after rebalancing.

---

## Q&A

### Why does `ppg_last` use `fillna(0)` rather than the median?
`0` is a conservative default — a player with no last-season data gets no contribution from the last-season side of the blend. This is intentional: we don't want to artificially inflate a new signing's score with an assumed average. Once they play a few GWs, their current-season `ppg` (9f) and `form` will carry the scoring.

### Why is `GW0` a special sheet?
`GW0` is the sheet written when `fetch.py` runs before GW1 starts (`event["id"] - 1 = 0`). It contains the bootstrap snapshot from the pre-season window, which is the only time all player stats reflect the completed previous season.

### Why `code` and not `id` as the join key?
FPL reassigns `id` values between seasons — a player who was `id=123` in 2024/25 might be `id=456` in 2025/26. `code` is a permanent club-assigned identifier that never changes across seasons. Always use `code` for cross-season joins.

### Why is the minutes filter at 900?
900 minutes ≈ 10 full games. Per-90 stats on fewer appearances are unreliable (one exceptional game dominates the average). This threshold filters out players whose per-90 stats are statistically misleading. Planned replacement in 9g: a `minutes_confidence` multiplier that scales scores down gradually rather than cutting off hard.

---

## 9f. Three-Way Blend: ppg_last + ppg_current + form

### Key Concepts

**Why three signals instead of two?**
After 9e, the blend was `ppg_last` vs `form`. But this ignores current-season `points_per_game` — a season-to-date average that's more stable than form but more current than last season. Three time horizons give a fuller picture:

| Signal | Memory | Reliability |
|--------|--------|-------------|
| `ppg_last` | Full previous season | Stable but stale as season progresses |
| `points_per_game` (current) | All GWs this season | Medium stability, improves over time |
| `form` | Last few GWs | Noisy early, reactive and accurate late |

**Updated `get_season_weights` signature:**
```python
def get_season_weights(gws_played: int) -> tuple[float, float, float]:
    # returns (ppg_last_w, ppg_current_w, form_w)
```

**Weight progression:**

| GWs played | ppg_last | ppg_current | form |
|-----------|---------|------------|------|
| 0 (pre-season) | 1.0 | 0 | 0 |
| 1–3 | 0.7 | 0.2 | 0.1 |
| 4–6 | 0.4 | 0.3 | 0.3 |
| 7–10 | 0.1 | 0.4 | 0.5 |
| 11+ | 0 | 0.45 | 0.55 |

**Why form gets slightly more than ppg_current at GW11+:**
By mid-to-late season, `points_per_game` accumulates results from the whole season — a player who started well but faded still carries a high season average. `form` captures the current trajectory more accurately, so it gets the edge (0.55 vs 0.45).

**`ppg_last` drops to zero after GW10:**
After 10 GWs, there's enough current-season data to be self-sufficient. Last season is ancient history at this point — different tactics, different manager, possibly different squad role. Hard cutoff at GW11+ is intentional.

**`FORM_AND_PPG_WEIGHTS` becomes three keys:**
```python
FORM_AND_PPG_WEIGHTS = {
    'ppg_last':        0.20 * ppg_last_w,
    'points_per_game': 0.20 * ppg_curr_w,
    'form':            0.20 * form_curr_w,
}
```
The combined budget is still 0.20 — the same as the old static `'points_per_game': 0.20`. All three signals share that budget, so total weights across each position dict still sum to 1.0.

**`points_per_game` was already normalized:**
No extra work needed — `points_per_game` has been in `PLAYERS_NORMALIZATION_COLUMNS` since earlier phases, so `points_per_game_norm` already exists in the DataFrame.

### Q&A

#### Why does ppg_last have non-zero weight until GW10 rather than GW5/6?
Early in the season, current-season `ppg_current` and `form` are based on the same 1–9 games. A player who had one great game has inflated stats in both. Last-season data provides a stable anchor to dampen that noise until there's enough current-season evidence to trust.

#### Why 0.45/0.55 at GW11+ rather than 0.5/0.5?
Pure symmetry has no particular advantage. The slight form bias reflects that `ppg_current` accumulates results across the whole season — early-season form still pulls the average up. Form captures the current trajectory better in the second half of the season.

---

## 9g. minutes_confidence Multiplier Replaces Hard 900-Min Filter

### Key Concepts

**The original problem:**
Walter Benítez (90 minutes, 1 game) was outranking David Raya (3330 minutes, 37 games) because per-90 stats on 1 game are extreme outliers. A single clean sheet gives `clean_sheets_per_90 = 1.0` and a single match with 3 saves gives `saves_per_90 = 3.0` — both near the top of the dataset. After normalization, Benítez dominated every GKP factor.

The 900-minute hard filter excluded him, but it's blunt — players just below the threshold are dropped entirely while those just above are included at full weight.

**The fix — `minutes_confidence`:**
Instead of filtering, compute a confidence multiplier and apply it to per-90 stats *before* normalization:

```python
conf_denominator = curr_gw_id * 90 if curr_gw_id > 0 else 38 * 90
players_df['minutes_confidence'] = (players_df['minutes'] / conf_denominator).clip(upper=1.0)

for col in ['clean_sheets_per_90', 'saves_per_90']:
    players_df[col] = players_df[col] * players_df['minutes_confidence']
```

**How the formula works:**
`minutes_confidence = minutes_played / (gws_played * 90)`

- A player who played every minute gets `1.0` — full confidence
- A player who played half the available minutes gets `0.5` — stats halved before normalization
- Pre-season (`curr_gw_id = 0`): denominator would be `0 * 90 = 0` — division by zero. Guard: use `38 * 90 = 3420` (a full season) as the baseline

**Pre-season example:**
- Raya: `3330 / 3420 = 0.974` — nearly full confidence
- Benítez: `90 / 3420 = 0.026` — near-zero confidence. His `clean_sheets_per_90 = 1.0` becomes `0.026`. After normalization he no longer dominates.

**Why apply before normalization (not after):**
The multiplier dampens the raw stat value. When normalization runs, Benítez's adjusted `clean_sheets_per_90 = 0.026` is near the bottom of the dataset — he gets a low normalized score. If we multiplied *after* normalization, we'd be changing the weighted sum and breaking the 0–1 score scale.

**`.clip(upper=1.0)`:**
Without clipping, a player could theoretically exceed `1.0` confidence (e.g. if FPL's minutes data has minor overcount errors). `.clip(upper=1.0)` caps it cleanly. Using `min()` on a pandas Series wouldn't work — `.clip()` is the correct vectorized approach.

**Why 90 and not 95 or 100:**
FPL records minutes in 90-minute blocks — it doesn't include stoppage time. Raya's 3330 minutes / 37 games = exactly 90 per game, confirming the data uses clean 90-minute units.

### Result

Benítez moved from rank 1 to rank 6 in GKP scores. Raya remains at rank 1 with score `0.87` vs Benítez's `0.61`. Low-minute players are still included in the dataset (they can be recommended if forward-looking signals like `ep_next` and `fdr` are strong) but their per-90 stats are appropriately discounted.

### Q&A

#### Why apply the multiplier only to `clean_sheets_per_90` and `saves_per_90` and not all per-90 stats?
Those are the only two per-90 stats currently in the scoring model for any position. Other per-90 stats (`expected_goals_per_90`, `starts_per_90`, etc.) are in the API data but not in `PLAYERS_NORMALIZATION_COLUMNS`. If more per-90 stats are added to scoring in future, extend the loop.

#### Why not apply the multiplier to `form` and `points_per_game`?
`form` is handled by the season-aware blending (9b/9f) — at GW0 it gets zero weight, so there's no risk of noise from small samples. `points_per_game` (current season) also gets zero weight at GW0 for the same reason.

#### What happens to genuinely new players with 0 minutes?
`0 / conf_denominator = 0.0` — their `clean_sheets_per_90` and `saves_per_90` become `0.0`. They still get scored via `ep_next` and `fdr` which don't depend on historical minutes. This is intentional — no per-90 signal, but still rankable via forward-looking data.

---

## Watchlist Player Lookup

### Key Concepts

**What it does:**
Adds a `position_rank` column to `players_df` showing each player's rank within their position by `next_gw_score`. Then filters the DataFrame by a hardcoded `watchlist` of player `code`s and displays a styled table per position — same format as the main recommendation table but only for the players you care about.

**`df.groupby('position')['col'].rank(ascending=False, method='min')`:**
Computes rank within each position group independently. `ascending=False` means rank 1 = highest score. `method='min'` handles ties by giving both players the lower rank (e.g. two players tied for 2nd both get rank 2, next is rank 4).

This is a vectorized operation — no loop needed. The result is a Series aligned to `players_df`'s index, so you can assign it directly as a new column.

**Why `code` and not `id` in the watchlist:**
`code` is the permanent player identifier — stable across seasons. `id` can change. Using `code` means the watchlist stays valid next season without updates.

**Pattern — filter then group:**
```python
watchlist = [204936, 210462, ...]
filtered_players = players_df[players_df['code'].isin(watchlist)]

for _, pos in POSITION_MASTER.items():
    temp_df = filtered_players[filtered_players['position'] == pos]
    if temp_df.empty:
        continue
    display(temp_df[watchlist_cols].sort_values('position_rank').style...)
```
The `if temp_df.empty: continue` guard skips positions with no watchlist players rather than printing an empty table.

---

## 9h. Differential Player Recommendations

### Key Concepts

**What is a differential?**
A player selected by a small percentage of managers. If they score big, you gain rank over the field. If they blank, you lose nothing relative to heavily-owned players who also blanked. The value is asymmetric — high upside, low downside versus the field.

**Why not just filter by ownership threshold?**
A hard threshold (e.g. ≤10%) misses context — 10% ownership pre-season is different from 10% mid-season when premiums dominate. The table shows all players ranked by differential score and lets the manager decide, rather than excluding players arbitrarily.

**The `differential_score` formula:**
```python
differential_score = next_gw_score * selected_by_percent_norm
```
Where `selected_by_percent_norm` is inverted min-max normalized *per position group* — so 0 = most owned, 1 = least owned within that position. Multiplying by `next_gw_score` rewards players with both strong scoring potential and low ownership.

**Why normalize per position, not globally?**
A GK at 8% ownership is normal. A MID at 8% ownership is a genuine differential. Global normalization would treat them the same. Per-position normalization makes the differential signal meaningful within each position's ownership distribution.

**Writing per-position values back with `.loc[mask]`:**
```python
mask = players_df['position'] == pos
players_df.loc[mask, 'selected_by_percent_norm'] = 1 - ((temp_df[col] - col_min) / denominator)
```
`temp_df` is a filtered view — computing min/max on it gives position-group stats. `.loc[mask, col]` writes the result back into the correct rows of `players_df` without touching other positions. No merge needed.

**Why not merge back?**
`merge` on a DataFrame that has a new column added in a loop creates duplicate column names (`_x`, `_y` suffixes) on subsequent iterations, breaking the DataFrame. `.loc` writes in-place to specific rows — the correct pattern for per-group assignments.

### Q&A

#### Why multiply rather than subtract or divide?
Multiplication penalizes either extreme hard — a player with a great score but high ownership gets dampened; a player with low ownership but a poor score also scores low. You need both signals to be high for a strong differential pick. Subtraction would allow a very low-ownership player with a bad score to rank high.

#### Why is `selected_by_percent_norm` not in `PLAYERS_NORMALIZATION_COLUMNS`?
Because global normalization would lose the per-position context. It's computed separately in the differential cell with position-aware min/max — adding it to the global normalization loop would overwrite it with an inferior global version.

---

## Weight Update: defensive_contribution Added to DEF and MID

### What changed

`defensive_contribution` (a native FPL API field — combined defensive metric) was added to the DEF and MID scoring models after correlation analysis showed strong signal:

| Position | `defensive_contribution` corr | Notes |
|----------|-------------------------------|-------|
| DEF | 0.79 | Stronger than `clean_sheets_per_90` (0.36), weaker than `ict_index` (0.88) |
| MID | 0.84 | Near-equal to `ict_index` (0.88), correlated with it at ~0.74 |

**Updated weights:**

DEF: `ep_next` 0.25→0.15, added `defensive_contribution: 0.10`
MID: `ep_next` 0.15→0.07, added `defensive_contribution: 0.13`

Both position dicts still sum to 0.80 (+ 0.20 FORM_AND_PPG = 1.0).

### Why weights sum to 0.80, not 1.0

Position-specific dicts intentionally leave 0.20 unallocated. That budget is filled at scoring time by `FORM_AND_PPG_WEIGHTS` — the season-aware blend of `ppg_last`, `ppg_current`, and `form`. This shared signal applies equally to all positions, so it's defined separately and merged in via dict unpacking:

```python
def_weights = {**DEF_WEIGHTS, **FORM_AND_PPG_WEIGHTS}  # sums to 1.0
```

### minutes_confidence extended to defensive_contribution

`defensive_contribution` is a per-game cumulative stat — small sample players produce inflated values just like `clean_sheets_per_90`. The multiplier was extended:

```python
for col in ['clean_sheets_per_90', 'saves_per_90', 'defensive_contribution']:
    players_df[col] = players_df[col] * players_df['minutes_confidence']
```

This runs before normalization, so outliers from 1–2 game samples are dampened before they can dominate the ranking.

### Double-counting consideration

`ict_index` and `defensive_contribution` correlate with each other (~0.74 for both DEF and MID). Using both adds some redundancy but they measure different things — ICT captures attacking/creative involvement while `defensive_contribution` measures defensive actions. Accepted tradeoff given the correlation with `total_points`.
