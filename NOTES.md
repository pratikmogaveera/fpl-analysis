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
