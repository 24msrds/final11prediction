from pathlib import Path
import pandas as pd

# =========================================================
# PATH
# =========================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "odi_wc2023_players_stats_2019_2023.csv"

# =========================================================
# VENUE → PITCH AUTO MAP
# =========================================================
VENUE_PITCH_MAP = {
    "Wankhede Stadium, India": "pace",
    "Eden Gardens, India": "spin",
    "MA Chidambaram Stadium, India": "spin",

    "MCG, Australia": "pace",
    "SCG, Australia": "spin",
    "Optus Stadium, Australia": "pace",

    "Lord's, England": "pace",
    "The Oval, England": "pace",

    "Wanderers, South Africa": "pace",

    "R Premadasa Stadium, Sri Lanka": "spin",

    "Gaddafi Stadium, Pakistan": "neutral",

    "Hagley Oval, New Zealand": "pace"
}

def infer_pitch_type(venue: str) -> str:
    return VENUE_PITCH_MAP.get(venue, "neutral")

# =========================================================
# CAPTAIN POOL (EXPERIENCE ONLY)
# =========================================================
CAPTAIN_POOL = {
    "virat kohli",
    "rohit sharma",
    "kane williamson",
    "babar azam",
    "pat cummins",
    "jos buttler",
    "temba bavuma",
    "dasun shanaka"
}

# =========================================================
# LOAD DATA (TSV SAFE)
# =========================================================
def load_data():
    df = pd.read_csv(DATA_PATH, sep="\t")

    # Fix broken single-column TSV
    if len(df.columns) == 1:
        df = df[df.columns[0]].str.split("\t", expand=True)
        df.columns = [
            "player_clean","country","role","matches_batted","runs",
            "bat_avg","strike_rate","x4s","x6s",
            "matches_bowled","overs","wickets","economy","bowling_sr"
        ]

    df.columns = df.columns.str.strip()

    df["player_clean"] = df["player_clean"].str.lower().str.strip()
    df["player"] = df["player_clean"].str.title()
    df["country"] = df["country"].str.strip()

    df["final_role"] = (
        df["role"].str.lower()
        .replace({
            "batter": "batsman",
            "bat": "batsman",
            "wk": "wicketkeeper",
            "all rounder": "allrounder",
            "all-rounder": "allrounder"
        })
    )

    numeric_cols = [
        "runs","bat_avg","strike_rate",
        "wickets","economy","matches_batted"
    ]

    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df

# =========================================================
# SELECTION SCORE (BALANCED)
# =========================================================
def compute_selection_score(row, pitch):
    bat_score = (
        row["runs"] * 0.03 +
        row["bat_avg"] * 1.2 +
        row["strike_rate"] * 0.6
    )

    bowl_score = (
        row["wickets"] * 22 +
        max(0, 6 - row["economy"]) * 10
    )

    score = bat_score + bowl_score

    if pitch == "spin":
        score += row["wickets"] * 6
    elif pitch == "pace":
        score += row["strike_rate"] * 1.5

    return round(score, 2)

# =========================================================
# PLAYER EXPLANATION
# =========================================================
def explain_player(row, pitch, opponent):
    reasons = []

    if row["final_role"] in ["batsman", "wicketkeeper"]:
        reasons.append("Strong ODI batting record")
        if row["strike_rate"] >= 90:
            reasons.append("High strike rate suits modern ODIs")

    if row["final_role"] == "bowler":
        reasons.append("Reliable wicket-taking bowler")
        if row["economy"] <= 5.5:
            reasons.append("Maintains good economy rate")

    if pitch == "spin" and row["final_role"] in ["bowler", "allrounder"]:
        reasons.append("Pitch expected to assist spin")

    if pitch == "pace" and row["final_role"] == "bowler":
        reasons.append("Conditions favor pace bowling")

    reasons.append(f"Past performance considered vs {opponent}")

    return "; ".join(reasons)

# =========================================================
# CAPTAIN SELECTION (NO BOWLING BIAS)
# =========================================================
def choose_captain(xi):
    eligible = xi[
        (xi["player_clean"].isin(CAPTAIN_POOL)) &
        (xi["final_role"] != "bowler")
    ].copy()

    if eligible.empty:
        return xi.sort_values("selection_score", ascending=False).iloc[0]["player"]

    eligible["cap_score"] = (
        eligible["matches_batted"] * 2 +
        eligible["bat_avg"] * 3 +
        eligible["runs"] * 0.02
    )

    return eligible.sort_values("cap_score", ascending=False).iloc[0]["player"]

# =========================================================
# AUTO BEST XI (MAIN FUNCTION)
# =========================================================
def auto_best_xi(opponent: str, venue: str):
    df = load_data()

    # Remove opponent players
    df = df[df["country"].str.lower() != opponent.lower()]

    pitch = infer_pitch_type(venue)

    # Compute score
    df["selection_score"] = df.apply(
        lambda r: compute_selection_score(r, pitch), axis=1
    )

    # Role-based selection
    batsmen = df[df["final_role"] == "batsman"].nlargest(5, "selection_score")
    wicketkeeper = df[df["final_role"] == "wicketkeeper"].nlargest(1, "selection_score")
    allrounders = df[df["final_role"] == "allrounder"].nlargest(2, "selection_score")
    bowlers = df[df["final_role"] == "bowler"].nlargest(3, "selection_score")

    # Fallback WK
    if wicketkeeper.empty:
        wk = batsmen.head(1).copy()
        wk["final_role"] = "wicketkeeper"
        wicketkeeper = wk

    xi = pd.concat([batsmen, wicketkeeper, allrounders, bowlers])
    xi = xi.drop_duplicates("player_clean").head(11)

    captain = choose_captain(xi)

    xi["explanation"] = xi.apply(
        lambda r: explain_player(r, pitch, opponent), axis=1
    )

    role_order = {
        "batsman": 1,
        "wicketkeeper": 1,
        "allrounder": 2,
        "bowler": 3
    }

    xi["order"] = xi["final_role"].map(role_order)
    xi = xi.sort_values(["order", "selection_score"], ascending=[True, False])

    return [
        {
            "player": r["player"],
            "role": r["final_role"],
            "country": r["country"],
            "runs": int(r["runs"]),
            "sr": round(r["strike_rate"], 2),
            "wickets": int(r["wickets"]),
            "economy": round(r["economy"], 2),
            "selection_score": round(r["selection_score"], 2),
            "captain": r["player"] == captain,
            "explanation": r["explanation"]
        }
        for _, r in xi.iterrows()
    ]
