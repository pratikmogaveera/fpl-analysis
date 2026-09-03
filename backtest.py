"""
backtest.py — Retroactive scoring model validation.

For each available GW pair (predict_sheet → actual_sheet), re-runs the full
scoring pipeline on the prediction sheet and compares the resulting rankings
against actual event_points from the next sheet.

Metrics per position:
  - Spearman rank correlation between next_gw_score rank and event_points rank
  - Top-N precision: % of top-N predicted players that appeared in top-N actual scorers

Usage:
    python backtest.py            # runs all available GW pairs
    python backtest.py --top 10   # change top-N (default: 15)
"""

import argparse

import pandas as pd
from scipy.stats import spearmanr
from tabulate import tabulate

# ── Constants (mirrors fpl_analysis.ipynb) ────────────────────────────────────

POSITION_MASTER = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}

PLAYERS_NUMERIC_COLUMNS = [
    "form", "points_per_game", "ep_next", "influence", "creativity",
    "threat", "ict_index", "value_form", "value_season", "selected_by_percent",
    "expected_goals", "expected_assists", "expected_goal_involvements",
    "expected_goals_conceded", "clean_sheets_per_90", "saves_per_90",
    "ppg_last", "defensive_contribution",
]

PLAYERS_NORMALIZATION_COLUMNS = [
    "form", "points_per_game", "ep_next", "fdr", "ict_index",
    "influence", "expected_goal_involvements", "expected_goals",
    "chance_of_playing_next_round", "clean_sheets_per_90", "saves_per_90",
    "threat", "ppg_last", "defensive_contribution",
]

GKP_WEIGHTS = {
    "ep_next": 0.25,
    "fdr": 0.05,
    "chance_of_playing_next_round": 0.025,
    "clean_sheets_per_90": 0.35,
    "saves_per_90": 0.125,
}
DEF_WEIGHTS = {
    "ep_next": 0.30,
    "fdr": 0.05,
    "chance_of_playing_next_round": 0.025,
    "ict_index": 0.075,
    "influence": 0.075,
    "defensive_contribution": 0.10,
    "clean_sheets_per_90": 0.125,
}
MID_WEIGHTS = {
    "ep_next": 0.20,
    "fdr": 0.05,
    "chance_of_playing_next_round": 0.025,
    "ict_index": 0.11,
    "influence": 0.11,
    "defensive_contribution": 0.10,
    "expected_goal_involvements": 0.13,
}
FWD_WEIGHTS = {
    "ep_next": 0.25,
    "fdr": 0.05,
    "chance_of_playing_next_round": 0.025,
    "threat": 0.15,
    "ict_index": 0.25,
    "expected_goals": 0.075,
}

POSITION_WEIGHTS = {"GKP": GKP_WEIGHTS, "DEF": DEF_WEIGHTS, "MID": MID_WEIGHTS, "FWD": FWD_WEIGHTS}
PRESEASON_DATA_SHEET = "GW0"


# ── Season blend ──────────────────────────────────────────────────────────────

def get_season_weights(gws_played: int) -> tuple[float, float, float]:
    """Returns (ppg_last_w, ppg_curr_w, form_curr_w) based on GWs played."""
    if gws_played < 1:
        return 1, 0, 0
    elif gws_played < 4:
        return 0.7, 0.2, 0.1
    elif gws_played < 7:
        return 0.4, 0.3, 0.3
    elif gws_played < 11:
        return 0.1, 0.4, 0.5
    else:
        return 0, 0.45, 0.55


# ── Scoring pipeline ──────────────────────────────────────────────────────────

def score_gw(
    predict_sheet: str,
    next_gw_id: int,
    xl_players: pd.ExcelFile,
    xl_teams: pd.ExcelFile,
    fixtures_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Re-runs the full scoring pipeline for a given prediction sheet.

    predict_sheet: the GW sheet used as input (e.g. 'GW0' to predict GW1)
    next_gw_id:    the GW being predicted (e.g. 1)
    Returns a DataFrame with columns: code, web_name, position, next_gw_score
    """
    curr_gw_id = next_gw_id - 1

    players_df = pd.read_excel(xl_players, sheet_name=predict_sheet)
    players_df_last = pd.read_excel(xl_players, sheet_name=PRESEASON_DATA_SHEET)
    teams_df = pd.read_excel(xl_teams, sheet_name=predict_sheet)
    current_gw_fixtures = fixtures_df[fixtures_df["event"] == next_gw_id]

    # Join last-season ppg from GW0.
    players_df_last = players_df_last[["points_per_game", "minutes", "code"]].rename(
        columns={"points_per_game": "ppg_last", "minutes": "minutes_last"}
    )
    players_df = players_df.merge(players_df_last, on="code", how="left")
    players_df["ppg_last"] = players_df["ppg_last"].fillna(0)
    players_df["minutes_last"] = players_df["minutes_last"].fillna(0)

    players_df["position"] = players_df["element_type"].map(POSITION_MASTER)
    players_df["team_name"] = players_df["team"].map(dict(zip(teams_df["id"], teams_df["name"])))

    # Cast string-encoded numeric columns.
    for col in PLAYERS_NUMERIC_COLUMNS:
        players_df[col] = pd.to_numeric(players_df[col], errors="coerce")

    players_df["chance_of_playing_next_round"] = players_df["chance_of_playing_next_round"].fillna(100)
    players_df["ep_next"] = players_df["ep_next"].fillna(0)

    # Drop unavailable players.
    players_df = players_df[players_df["status"].isin(["a", "i", "d"])]

    # minutes_confidence dampening.
    conf_denominator = curr_gw_id * 90 if curr_gw_id > 0 else 38 * 90
    players_df["minutes_confidence"] = (players_df["minutes"] / conf_denominator).clip(upper=1.0)

    ppg_last_confidence = (players_df["minutes_last"] / (38 * 90)).clip(upper=1.0)
    players_df["ppg_last"] = players_df["ppg_last"] * ppg_last_confidence

    for col in ["clean_sheets_per_90", "saves_per_90", "defensive_contribution", "points_per_game", "form"]:
        players_df[col] = players_df[col] * players_df["minutes_confidence"]

    # FDR for the predicted GW.
    home = current_gw_fixtures[["team_h", "team_h_difficulty"]].rename(
        columns={"team_h": "team_id", "team_h_difficulty": "fdr"}
    )
    away = current_gw_fixtures[["team_a", "team_a_difficulty"]].rename(
        columns={"team_a": "team_id", "team_a_difficulty": "fdr"}
    )
    fdr_map = dict(zip(pd.concat([home, away])["team_id"], pd.concat([home, away])["fdr"]))
    players_df["fdr"] = players_df["team"].map(fdr_map)

    players_df = players_df.copy()

    # Normalize.
    for col in PLAYERS_NORMALIZATION_COLUMNS:
        col_min = players_df[col].min()
        col_max = players_df[col].max()
        denominator = col_max - col_min if col_max != col_min else 1
        if col in ["fdr", "saves_per_90"]:
            players_df[f"{col}_norm"] = 1 - ((players_df[col] - col_min) / denominator)
        else:
            players_df[f"{col}_norm"] = (players_df[col] - col_min) / denominator

    # Season-aware consistency blend.
    ppg_last_w, ppg_curr_w, form_curr_w = get_season_weights(curr_gw_id)
    form_ppg_weights = {
        "ppg_last": 0.20 * ppg_last_w,
        "points_per_game": 0.20 * ppg_curr_w,
        "form": 0.20 * form_curr_w,
    }

    # Score per position.
    for pos, pos_weights in POSITION_WEIGHTS.items():
        weights = {**pos_weights, **form_ppg_weights}
        mask = players_df["position"] == pos
        players_df.loc[mask, "next_gw_score"] = sum(
            [players_df.loc[mask, f"{col}_norm"] * w for col, w in weights.items()]
        )

    return players_df[["code", "web_name", "position", "next_gw_score"]].dropna(subset=["next_gw_score"])


# ── Metrics ───────────────────────────────────────────────────────────────────

def evaluate(predicted_df: pd.DataFrame, actual_df: pd.DataFrame, top_n: int) -> dict:
    """
    Joins predicted next_gw_score against actual event_points.
    Returns per-position metrics dict.
    """
    actual = actual_df[["code", "event_points"]].copy()
    merged = predicted_df.merge(actual, on="code", how="inner")

    results = []
    for pos in POSITION_MASTER.values():
        pos_df = merged[merged["position"] == pos].copy()
        if len(pos_df) < 2:
            continue

        # Rank both — higher score/points = rank 1.
        pos_df["pred_rank"] = pos_df["next_gw_score"].rank(ascending=False, method="min")
        pos_df["actual_rank"] = pos_df["event_points"].rank(ascending=False, method="min")

        # Spearman correlation between the two rank columns.
        corr, pvalue = spearmanr(pos_df["pred_rank"], pos_df["actual_rank"])

        # Top-N precision: overlap between top-N predicted and top-N actual.
        top_predicted = set(pos_df.nsmallest(top_n, "pred_rank")["code"])
        top_actual = set(pos_df.nsmallest(top_n, "actual_rank")["code"])
        precision = len(top_predicted & top_actual) / top_n * 100

        results.append({
            "position": pos,
            "n_players": len(pos_df),
            "spearman_r": round(corr, 3),
            "p_value": round(pvalue, 4),
            "top_n_precision": f"{precision:.0f}%  ({len(top_predicted & top_actual)}/{top_n})",
        })

    return results


# ── Main ──────────────────────────────────────────────────────────────────────

def main(top_n: int) -> None:
    xl_players = pd.ExcelFile("./data/players_master.xlsx")
    xl_teams = pd.ExcelFile("./data/teams_master.xlsx")
    fixtures_df = pd.read_excel("./data/fixtures_master.xlsx", sheet_name="Fixtures")

    # Discover available GW sheets (GW0, GW1, GW2, ...) sorted numerically.
    gw_sheets = sorted(
        [s for s in xl_players.sheet_names if s.startswith("GW")],
        key=lambda s: int(s[2:]),
    )
    print(f"Available sheets: {gw_sheets}\n")

    # Build pairs: (predict_sheet, actual_sheet, next_gw_id)
    # GW0 → predict GW1 using GW1 actual event_points
    # GW1 → predict GW2 using GW2 actual event_points
    pairs = []
    for i in range(len(gw_sheets) - 1):
        predict_sheet = gw_sheets[i]
        actual_sheet = gw_sheets[i + 1]
        next_gw_id = int(actual_sheet[2:])  # GW1 → 1, GW2 → 2
        pairs.append((predict_sheet, actual_sheet, next_gw_id))

    if not pairs:
        print("Not enough GW sheets to backtest. Need at least GW0 + GW1.")
        return

    all_results = []

    for predict_sheet, actual_sheet, next_gw_id in pairs:
        print(f"{'─' * 60}")
        print(f"Predicting GW{next_gw_id}  |  Input: {predict_sheet}  →  Actual: {actual_sheet}")
        print(f"{'─' * 60}")

        predicted_df = score_gw(predict_sheet, next_gw_id, xl_players, xl_teams, fixtures_df)
        actual_df = pd.read_excel(xl_players, sheet_name=actual_sheet)[["code", "event_points"]]

        results = evaluate(predicted_df, actual_df, top_n)

        for r in results:
            r["gw"] = f"GW{next_gw_id}"

        print(tabulate(results, headers="keys", tablefmt="rounded_outline", floatfmt=".3f"))
        print()
        all_results.extend(results)

    # Summary across all GWs.
    if len(pairs) > 1:
        print(f"{'═' * 60}")
        print("Summary — average Spearman r per position across all GWs")
        print(f"{'═' * 60}")
        summary_df = pd.DataFrame(all_results)
        summary = (
            summary_df.groupby("position")["spearman_r"]
            .agg(["mean", "min", "max"])
            .round(3)
            .reset_index()
        )
        summary.columns = ["position", "avg_r", "min_r", "max_r"]
        print(tabulate(summary.to_dict("records"), headers="keys", tablefmt="rounded_outline"))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backtest FPL scoring model.")
    parser.add_argument("--top", type=int, default=15, help="Top-N for precision metric (default: 15)")
    args = parser.parse_args()
    main(top_n=args.top)
