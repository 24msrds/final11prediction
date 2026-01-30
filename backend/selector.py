from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "odi_wc2023_players_stats_2019_2023.csv"

REQUIRED_COLS = {
    "player_clean", "country", "role",
    "matches_batted", "runs", "bat_avg", "strike_rate",
    "matches_bowled", "overs", "wickets", "economy", "bowling_sr"
}

def load_data():
    # ✅ IMPORTANT FIX: sep="\t"
    df = pd.read_csv(DATA_PATH, sep="\t")

    df.columns = df.columns.str.strip()

    missing = REQUIRED_COLS - set(df.columns)
    if missing:
        raise ValueError({
            "error": "CSV missing required columns",
            "missing": list(missing),
            "found": list(df.columns)
        })

    df["player_clean"] = df["player_clean"].astype(str).str.strip().str.lower()
    df["player"] = df["player_clean"].str.title()

    df["role"] = (
        df["role"].astype(str).str.lower()
        .replace({
            "batter": "batsman",
            "all-rounder": "allrounder",
            "all rounder": "allrounder",
            "wk": "wicketkeeper",
            "wicket-keeper": "wicketkeeper"
        })
    )

    for col in [
        "runs", "bat_avg", "strike_rate",
        "wickets", "economy",
        "matches_batted", "matches_bowled"
    ]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    return df


def compute_score(row, pitch):
    score = (
        row["runs"] * 0.02 +
        row["bat_avg"] * 1.2 +
        row["strike_rate"] * 0.4 +
        row["wickets"] * 25 +
        max(0, 6 - row["economy"]) * 8
    )

    if pitch == "spin":
        score += row["wickets"] * 10
    elif pitch == "pace":
        score += row["strike_rate"] * 2

    return round(score, 2)


def auto_best_xi(pitch_type="neutral", opponent=None):
    df = load_data()

    if opponent:
        df = df[df["country"].str.lower() != opponent.lower()]

    df["score"] = df.apply(lambda r: compute_score(r, pitch_type), axis=1)

    batsmen = df[df["role"] == "batsman"].nlargest(5, "score")
    wicketkeeper = df[df["role"] == "wicketkeeper"].nlargest(1, "score")
    allrounders = df[df["role"] == "allrounder"].nlargest(2, "score")
    bowlers = df[df["role"] == "bowler"].nlargest(3, "score")

    xi = pd.concat([batsmen, wicketkeeper, allrounders, bowlers])
    xi = xi.drop_duplicates("player_clean").head(11)

    xi = xi.sort_values("score", ascending=False)

    captain = xi.iloc[0]["player"]
    vice = xi.iloc[1]["player"]

    return [
        {
            "player": r["player"],
            "role": r["role"],
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
