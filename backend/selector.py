from pathlib import Path
import pandas as pd

# ---------------- PATH ----------------
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "odi_wc2023_players_stats_2019_2023.csv"

# ---------------- CAPTAIN POOL ----------------
CAPTAIN_POOL = {
    "virat kohli",
    "rohit sharma",
    "kane williamson",
    "babar azam",
    "jos buttler",
    "pat cummins",
    "temba bavuma",
    "dasun shanaka"
}

# ---------------- LOAD DATA ----------------
def load_data():
    df = pd.read_csv(DATA_PATH, sep="\t")

    df.columns = df.columns.str.strip()

    df["player_clean"] = df["player_clean"].str.lower().str.strip()
    df["player"] = df["player_clean"].str.title()

    df["final_role"] = (
        df["role"].str.lower()
        .replace({
            "batter": "batsman",
            "all-rounder": "allrounder",
            "all rounder": "allrounder",
            "utility": "allrounder",
            "wk": "wicketkeeper",
        })
    )

    numeric_cols = [
        "runs", "wickets", "bat_avg",
        "strike_rate", "economy",
        "matches_batted"
    ]

    for col in numeric_cols:
        if col not in df.columns:
            df[col] = 0
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


# ---------------- FORM SCORE ----------------
def form_score(r, pitch):
    score = (
        r["runs"] * 0.02 +
        r["bat_avg"] * 1.2 +
        r["strike_rate"] * 0.4 +
        r["wickets"] * 25 +
        max(0, 6 - r["economy"]) * 8
    )

    if pitch == "spin":
        score += r["wickets"] * 10
    elif pitch == "pace":
        score += r["strike_rate"] * 2

    return round(score, 2)


# ---------------- CAPTAIN SELECTION ----------------
def choose_captain(xi):
    eligible = xi[
        (xi["final_role"].isin(["batsman", "wicketkeeper", "allrounder"])) &
        (xi["player_clean"].isin(CAPTAIN_POOL))
    ].copy()

    eligible["cap_score"] = (
        eligible["matches_batted"] * 1.5 +
        eligible["bat_avg"] * 2 +
        eligible["runs"] * 0.01
    )

    eligible = eligible.sort_values("cap_score", ascending=False)

    captain = eligible.iloc[0]["player"]
    vice = eligible.iloc[1]["player"] if len(eligible) > 1 else None

    return captain, vice


# ---------------- AUTO BEST XI ----------------
def auto_best_xi(pitch_type="neutral", opponent=None, venue=None):
    df = load_data()

    if df.empty:
        raise ValueError("Dataset is empty")

    # Opponent filter
    if opponent:
        df = df[df["country"].str.lower() != opponent.lower()]

    if df.empty:
        raise ValueError("No players left after opponent filtering")

    # Elite bowler bias (Bumrah fix)
    elite_bowlers = {"jasprit bumrah", "trent boult", "mitchell starc"}
    df.loc[df["player_clean"].isin(elite_bowlers), "wickets"] *= 1.1

    # Score
    df["score"] = df.apply(lambda r: form_score(r, pitch_type), axis=1)

    # Role balance (FIXED)
    batsmen = df[df["final_role"] == "batsman"].nlargest(5, "score")
    wicketkeeper = df[df["final_role"] == "wicketkeeper"].nlargest(1, "score")
    allrounders = df[df["final_role"] == "allrounder"].nlargest(2, "score")
    bowlers = df[df["final_role"] == "bowler"].nlargest(3, "score")

    # Ensure WK exists
    if wicketkeeper.empty:
        wk_fallback = batsmen.head(1).copy()
        wk_fallback["final_role"] = "wicketkeeper"
        wicketkeeper = wk_fallback

    xi = pd.concat([batsmen, wicketkeeper, allrounders, bowlers])
    xi = xi.drop_duplicates("player_clean").head(11)

    # Safety fill
    if len(xi) < 11:
        remaining = df[~df["player_clean"].isin(xi["player_clean"])]
        xi = pd.concat([xi, remaining.nlargest(11 - len(xi), "score")])

    captain, vice = choose_captain(xi)

    role_order = {
        "batsman": 1,
        "wicketkeeper": 1,
        "allrounder": 2,
        "bowler": 3
    }

    xi["order"] = xi["final_role"].map(role_order)
    xi = xi.sort_values(["order", "score"], ascending=[True, False])

    return [
        {
            "player": r["player"],
            "role": r["final_role"],
            "country": r["country"],
            "runs": int(r["runs"]),
            "sr": round(r["strike_rate"], 2),
            "wickets": int(r["wickets"]),
            "economy": round(r["economy"], 2),
            "selection_score": r["score"],
            "captain": r["player"] == captain,
            "vice_captain": r["player"] == vice
        }
        for _, r in xi.iterrows()
    ]
