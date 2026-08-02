# FPL Bootstrap API — Data Reference

Source: `fpl-boostrap.json` (FPL official bootstrap-static endpoint)  
Total FPL managers this season: **1,936,724**

---

## Top-Level Keys

| Key | Type | Size | Description |
|-----|------|------|-------------|
| `elements` | list | 563 | Every player — the main table |
| `teams` | list | 20 | All 20 Premier League clubs |
| `events` | list | 38 | One entry per gameweek |
| `element_types` | list | 4 | Position definitions (GK/DEF/MID/FWD) |
| `element_stats` | list | 26 | Metadata: stat names and labels |
| `chips` | list | 8 | Chip definitions and valid GW windows |
| `phases` | list | 11 | Season phases by month |
| `game_settings` | dict | — | League sizes, H2H config |
| `game_config` | dict | — | Scoring rules, squad rules |
| `total_players` | int | — | Total registered FPL managers |

---

## elements — Players (563 rows)

The richest table. One row per player.

### Identity

| Field | Type | Notes |
|-------|------|-------|
| `id` | int | FPL internal player ID |
| `first_name` | str | |
| `second_name` | str | |
| `web_name` | str | Display name used in FPL UI |
| `known_name` | str | Common name (often empty) |
| `code` | int | Opta player code |
| `photo` | str | `{code}.jpg` |
| `team` | int | Team ID (maps to `teams.id`) — use this to join players to teams |
| `team_code` | int | Opta external team code (maps to `teams.code`) — same value, different field name |
| `element_type` | int | Position ID (1=GK, 2=DEF, 3=MID, 4=FWD) |
| `status` | str | `a`=available, `d`=doubtful, `i`=injured, `s`=suspended, `u`=unavailable |
| `birth_date` | str | ISO date |
| `region` | int | Nationality region code |

### Availability

| Field | Type | Notes |
|-------|------|-------|
| `can_select` | bool | Can be picked in squad |
| `can_transact` | bool | Can be transferred in/out |
| `removed` | bool | Permanently removed from game |
| `chance_of_playing_next_round` | int\|null | 0–100, null = no info |
| `chance_of_playing_this_round` | int\|null | 0–100, null = no info |
| `news` | str | Injury/suspension news text |
| `news_added` | str\|null | Datetime news was added |

### Cost & Ownership

| Field | Type | Notes |
|-------|------|-------|
| `now_cost` | int | Current price × 10 (e.g. 60 = £6.0m) |
| `cost_change_start` | int | Price change since season start |
| `cost_change_event` | int | Price change this GW |
| `selected_by_percent` | str | % of managers who own this player |
| `transfers_in` | int | Total transfers in (season) |
| `transfers_out` | int | Total transfers out (season) |
| `transfers_in_event` | int | Transfers in this GW |
| `transfers_out_event` | int | Transfers out this GW |

### Season Stats

| Field | Type | Notes |
|-------|------|-------|
| `total_points` | int | Total FPL points this season |
| `event_points` | int | Points scored in latest GW |
| `points_per_game` | str | Average points per game played |
| `form` | str | Average points over last 30 days |
| `minutes` | int | Total minutes played |
| `starts` | int | Number of starts |
| `goals_scored` | int | |
| `assists` | int | |
| `clean_sheets` | int | |
| `goals_conceded` | int | |
| `own_goals` | int | |
| `yellow_cards` | int | |
| `red_cards` | int | |
| `saves` | int | GK only |
| `penalties_saved` | int | |
| `penalties_missed` | int | |
| `bonus` | int | Total bonus points |
| `bps` | int | Raw Bonus Points System score |
| `dreamteam_count` | int | Times in FPL dream team |
| `in_dreamteam` | bool | In dream team this GW |

### Expected Stats (xStats)

| Field | Type | Notes |
|-------|------|-------|
| `expected_goals` | str | xG season total |
| `expected_assists` | str | xA season total |
| `expected_goal_involvements` | str | xG + xA |
| `expected_goals_conceded` | str | xGC season total |
| `expected_goals_per_90` | float | |
| `expected_assists_per_90` | float | |
| `expected_goal_involvements_per_90` | float | |
| `expected_goals_conceded_per_90` | float | |

### ICT Index (FPL's own metric)

| Field | Type | Notes |
|-------|------|-------|
| `influence` | str | Impact on match result |
| `creativity` | str | Chance creation |
| `threat` | str | Goal threat |
| `ict_index` | str | Combined I + C + T score |
| `influence_rank` | int | Overall rank |
| `influence_rank_type` | int | Rank within position |
| `creativity_rank` | int | |
| `creativity_rank_type` | int | |
| `threat_rank` | int | |
| `threat_rank_type` | int | |
| `ict_index_rank` | int | |
| `ict_index_rank_type` | int | |

### Defensive Stats

| Field | Type | Notes |
|-------|------|-------|
| `clearances_blocks_interceptions` | int | |
| `recoveries` | int | |
| `tackles` | int | |
| `defensive_contribution` | int | Combined defensive metric |
| `defensive_contribution_per_90` | float | |

### Per-90 Stats

| Field | Notes |
|-------|-------|
| `saves_per_90` | |
| `goals_conceded_per_90` | |
| `clean_sheets_per_90` | |
| `starts_per_90` | Useful to check rotation risk |

### Value Metrics

| Field | Notes |
|-------|-------|
| `value_form` | Form / cost |
| `value_season` | Total points / cost |
| `ep_next` | Expected points next GW (FPL model) |
| `ep_this` | Expected points this GW |

### Rankings

| Field | Notes |
|-------|-------|
| `now_cost_rank` | Price rank overall |
| `now_cost_rank_type` | Price rank within position |
| `form_rank` | |
| `form_rank_type` | |
| `points_per_game_rank` | |
| `points_per_game_rank_type` | |
| `selected_rank` | Ownership rank |
| `selected_rank_type` | |

### Set Pieces

| Field | Notes |
|-------|-------|
| `corners_and_indirect_freekicks_order` | null = not a taker |
| `corners_and_indirect_freekicks_text` | Description |
| `direct_freekicks_order` | |
| `direct_freekicks_text` | |
| `penalties_order` | |
| `penalties_text` | |

---

## teams — Clubs (20 rows)

| Field | Notes |
|-------|-------|
| `id` | Maps to `elements.team` — **use this as the join key** |
| `name` | Full name (e.g. "Arsenal") |
| `short_name` | 3-letter code (e.g. "ARS") |
| `code` | Opta external code — maps to `elements.team_code` (different field, same value) |
| `played` | Matches played |
| `win` / `draw` / `loss` | Season record |
| `points` | League points |
| `position` | League table position |
| `strength_overall_home` | 1–5 rating |
| `strength_overall_away` | 1–5 rating |
| `strength_attack_home` | Granular attack strength |
| `strength_attack_away` | |
| `strength_defence_home` | |
| `strength_defence_away` | |

> **Note:** Strength ratings are on a 1–5 scale. Used to compute Fixture Difficulty Rating (FDR).  
> At season start `attack/defence` sub-ratings may be 0 — only `overall` is reliable early on.

---

## events — Gameweeks (38 rows)

| Field | Notes |
|-------|-------|
| `id` | GW number (1–38) |
| `name` | "Gameweek 1" etc. |
| `deadline_time` | ISO datetime (UTC) |
| `finished` | Whether GW is complete |
| `is_previous` / `is_current` / `is_next` | Flags for current state |
| `average_entry_score` | Average score across all managers |
| `highest_score` | Top score that GW |
| `most_selected` | Player ID most selected |
| `most_transferred_in` | Player ID most transferred in |
| `most_captained` | Player ID most captained |
| `most_vice_captained` | |
| `top_element` | Player ID with most points |
| `top_element_info` | `{id, points}` |
| `transfers_made` | Total transfers that GW |
| `chip_plays` | List of `{chip_name, num_played}` |

> Season hasn't started yet — `finished: false` and most fields are null/0 for all GWs.

---

## element_types — Positions (4 rows)

| id | Position | Squad Select | Min Play | Max Play |
|----|----------|-------------|----------|----------|
| 1 | Goalkeeper (GKP) | 2 | 1 | 1 |
| 2 | Defender (DEF) | 5 | 3 | 5 |
| 3 | Midfielder (MID) | 5 | 2 | 5 |
| 4 | Forward (FWD) | 3 | 1 | 3 |

---

## element_stats — Stat Labels (26 rows)

Maps internal field names to display labels.

| label | name (field) |
|-------|-------------|
| Minutes played | `minutes` |
| Goals scored | `goals_scored` |
| Assists | `assists` |
| Clean sheets | `clean_sheets` |
| Goals conceded | `goals_conceded` |
| Own goals | `own_goals` |
| Penalties saved | `penalties_saved` |
| Penalties missed | `penalties_missed` |
| Yellow cards | `yellow_cards` |
| Red cards | `red_cards` |
| Saves | `saves` |
| Bonus | `bonus` |
| Bonus Points System | `bps` |
| Influence | `influence` |
| Creativity | `creativity` |
| Threat | `threat` |
| ICT Index | `ict_index` |
| Clearances, blocks and interceptions | `clearances_blocks_interceptions` |
| Recoveries | `recoveries` |
| Tackles | `tackles` |
| Defensive Contribution | `defensive_contribution` |
| Game(s) Started | `starts` |
| Expected Goals | `expected_goals` |
| Expected Assists | `expected_assists` |
| Expected Goal Involvements | `expected_goal_involvements` |
| Expected Goals Conceded | `expected_goals_conceded` |

---

## chips (8 rows)

| name | number | GWs | type |
|------|--------|-----|------|
| Wildcard | 1 | GW2–19 | transfer |
| Wildcard | 2 | GW20–38 | transfer |
| Free Hit | 1 | GW2–19 | transfer |
| Free Hit | 2 | GW20–38 | transfer |
| Bench Boost (`bboost`) | 1 | GW1–19 | team |
| Bench Boost | 2 | GW20–38 | team |
| Triple Captain (`3xc`) | 1 | GW1–19 | team |
| Triple Captain | 2 | GW20–38 | team |

---

## phases (11 rows)

Season split by month. Used for monthly mini-league scoring.

| Phase | GWs |
|-------|-----|
| Overall | 1–38 |
| August | 1–2 |
| September | 3–5 |
| October | 6–9 |
| November | 10–12 |
| December | 13–18 |
| January | 19–23 |
| February | 24–27 |
| March | 28–30 |
| April | 31–33 |
| May | 34–38 |

---

## game_config — Scoring Rules

### Points per action

| Action | GKP | DEF | MID | FWD |
|--------|-----|-----|-----|-----|
| Playing 45+ min | 1 | 1 | 1 | 1 |
| Playing 60+ min | 2 | 2 | 2 | 2 |
| Goal scored | 10 | 6 | 5 | 4 |
| Assist | 3 | 3 | 3 | 3 |
| Clean sheet | 4 | 4 | 1 | 0 |
| Defensive contribution | 0 | 2 | 2 | 2 |
| Save (per 3) | 1 | — | — | — |
| Penalty saved | 5 | — | — | — |
| Penalty missed | -2 | -2 | -2 | -2 |
| Yellow card | -1 | -1 | -1 | -1 |
| Red card | -3 | -3 | -3 | -3 |
| Own goal | -2 | -2 | -2 | -2 |
| Goals conceded (per 2) | -1 | -1 | 0 | 0 |
| Bonus points | 1–3 per game | | | |

---

## Key Things to Know

- **Cost encoding:** `now_cost` is stored as an integer × 10. A player at 60 costs £6.0m.
- **String numbers:** `form`, `points_per_game`, `ep_next`, `influence`, `creativity`, `threat`, `ict_index`, `expected_*` are all stored as strings — cast to float before using.
- **Null fields:** `chance_of_playing_*` is null (not 100) when no injury concern. Treat null as 100%.
- **Team strength:** `strength_attack/defence` sub-ratings are 0 at season start. Use `strength_overall_home/away` for fixture difficulty early in the season.
- **Season state:** This data is pre-season (GW1 deadline Aug 21, 2026). No GW has been played yet.
