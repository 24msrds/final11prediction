from pathlib import Path
import pandas as pd

# -------------------------------------------------
# PATH CONFIG (RENDER + LOCAL SAFE)
# -------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "odi_wc2023_players_stats_2019_2023.csv"

# -------------------------------------------------
# CAPTAIN TRAINING POOL (EXPERIENCE-BASED ONLY)
# -------------------------------------------------
CAPTAIN_POOL = {
    "virat kohli",
    "rohit sharma",
    "kane williamson",
    "pat cummins",
    "babar azam",
    "jos buttler",
    "temba bavuma",
    "dasun shanaka",
}

# -------------------------------------------------
# LOAD & CLEAN DATA
# -------------------------------------------------
def load_data():
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found at {DATA_PATH}")

    df = pd.read_csv(DATA_PATH, sep="\t")

    # Clean columns
    df.columns = df.columns.str.strip()

    # Player names
    df["player_clean"] = df["player_clean"].astype(str).str.lower().str.strip()
    df["player"] = df["player_clean"].str.title()

    # Role normalization
    df["final_role"] = (
        df["role"]
        .astype(str)
        .str.lower()
        .replace({
            "batter": "batsman",
            "bat": "batsman",
            "all-rounder": "allrounder",
            "all rounder": "allrounder",
            "utility": "allrounder",
            "wk": "wicketkeeper",
            "wicket-keeper": "wicketkeeper",
        })
    )

    # Numeric safety
    numeric_cols = [
        "runs",
        "bat_avg",
        "strike_rate",
        "wickets",
        "economy",
        "matches_batted",
    ]

    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["country"] = df["country"].astype(str).str.strip()

    return df


# -------------------------------------------------
# FORM SCORE (SELECTION PURPOSE ONLY)
# -------------------------------------------------
def form_score(row, pitch_type):
    score = 0.0

    # Batting
    score += row["runs"] * 0.02
    score += row["bat_avg"] * 1.2
    score += row["strike_rate"] * 0.4

    # Bowling
    score += row["wickets"] * 25
    score += max(0, 6 - row["economy"]) * 8

    # Pitch bias
    if pitch_type == "spin":
        score += row["wickets"] * 10
    elif pitch_type == "pace":
        score += row["strike_rate"] * 2

    return round(score, 2)


# -------------------------------------------------
# CAPTAIN SELECTION (NO BOWLERS)
# -------------------------------------------------
def choose_captain(xi_df):
    eligible = xi_df[
        (xi_df["final_role"].isin(["batsman", "wicketkeeper", "allrounder"])) &
        (xi_df["player_clean"].isin(CAPTAIN_POOL))
    ].copy()

    if eligible.empty:
        return xi_df.iloc[0]["player"], None

    eligible["cap_score"] = (
        eligible["matches_batted"] * 1.5 +
        eligible["bat_avg"] * 2 +
        eligible["runs"] * 0.01
    )

    eligible = eligible.sort_values("cap_score", ascending=False)

    captain = eligible.iloc[0]["player"]
    vice = eligible.iloc[1]["player"] if len(eligible) > 1 else None

    return captain, vice


# -------------------------------------------------
# AUTO BEST XI (MAIN FUNCTION)
# -------------------------------------------------
def auto_best_xi(pitch_type="neutral", opponent=None, venue=None):
    df = load_data()

    # -------------------------------------------------
    # OPPONENT FILTER (NO ONE PLAYS AGAINST THEMSELVES)
    # -------------------------------------------------
    if opponent:
        df = df[df["country"].str.lower() != opponent.lower()]

    # -------------------------------------------------
    # ELITE BOWLER BIAS (BUMRAH FIX)
    # -------------------------------------------------
    elite_bowlers = {"jasprit bumrah", "trent boult", "mitchell starc"}
    df.loc[df["player_clean"].isin(elite_bowlers), "wickets"] *= 1.15

    # -------------------------------------------------
    # SCORE COMPUTATION
    # -------------------------------------------------
    df["score"] = df.apply(lambda r: form_score(r, pitch_type), axis=1)

    # -------------------------------------------------
    # ROLE-WISE SELECTION (11 PLAYERS)
    # -------------------------------------------------
    batsmen = df[df["final_role"] == "batsman"].nlargest(5, "score")
    wicketkeepers = df[df["final_role"] == "wicketkeeper"].nlargest(1, "score")
    allrounders = df[df["final_role"] == "allrounder"].nlargest(2, "score")
    bowlers = df[df["final_role"] == "bowler"].nlargest(3, "score")

    # Ensure at least 1 wicketkeeper
    if wicketkeepers.empty:
        fallback = batsmen.head(1).copy()
        fallback["final_role"] = "wicketkeeper"
        wicketkeepers = fallback

    xi = pd.concat([batsmen, wicketkeepers, allrounders, bowlers])
    xi = xi.drop_duplicates("player_clean").head(11)

    # Safety fill
    if len(xi) < 11:
        remaining = df[~df["player_clean"].isin(xi["player_clean"])]
        xi = pd.concat([xi, remaining.nlargest(11 - len(xi), "score")])

    # -------------------------------------------------
    # CAPTAIN & VICE
    # -------------------------------------------------
    captain, vice = choose_captain(xi)

    # -------------------------------------------------
    # SORT ORDER (BAT/WK → AR → BOWL)
    # -------------------------------------------------
    role_order = {
        "batsman": 1,
        "wicketkeeper": 1,
        "allrounder": 2,
        "bowler": 3,
    }

    xi["order"] = xi["final_role"].map(role_order)
    xi = xi.sort_values(["order", "score"], ascending=[True, False])

    # -------------------------------------------------
    # FINAL RESPONSE
    # -------------------------------------------------
    return [
        {
            "player": r["player"],
            "role": r["final_role"],
            "country": r["country"],
            "runs": int(r["runs"]),
            "sr": round(r["strike_rate"], 2),
            "wickets": int(r["wickets"]),
            "economy": round(r["economy"], 2),
            "selection_score": round(r["score"], 2),
            "captain": r["player"] == captain,
            "vice_captain": r["player"] == vice,
        }
        for _, r in xi.iterrows()
    ]
