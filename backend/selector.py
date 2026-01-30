import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "odi_wc2023_players_stats_2019_2023.csv"

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
            "wk": "wicketkeeper"
        })
    )

    for col in ["runs", "bat_avg", "strike_rate", "wickets", "economy"]:
        df[col] = pd.to_numeric(df.get(col, 0), errors="coerce").fillna(0)

    return df


def score_player(r, pitch):
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


def auto_best_xi(pitch_type="neutral", opponent=None, venue=None):
    df = load_data()

    if opponent:
        df = df[df["country"].str.lower() != opponent.lower()]

    df["score"] = df.apply(lambda r: score_player(r, pitch_type), axis=1)

    batsmen = df[df["final_role"] == "batsman"].nlargest(5, "score")
    wicketkeeper = df[df["final_role"] == "wicketkeeper"].nlargest(1, "score")
    allrounders = df[df["final_role"] == "allrounder"].nlargest(2, "score")
    bowlers = df[df["final_role"] == "bowler"].nlargest(3, "score")

    if wicketkeeper.empty:
        wk = batsmen.head(1).copy()
        wk["final_role"] = "wicketkeeper"
        wicketkeeper = wk

    xi = pd.concat([batsmen, wicketkeeper, allrounders, bowlers])
    xi = xi.drop_duplicates("player_clean").head(11)
    xi = xi.sort_values("score", ascending=False)

    captain = xi.iloc[0]["player"]
    vice = xi.iloc[1]["player"]

    return [
        {
            "player": r["player"],
            "role": r["final_role"],
            "country": r["country"],
            "runs": int(r["runs"]),
            "sr": round(r["strike_rate"], 2),
            "wickets": int(r["wickets"]),
            "economy": round(r["economy"], 2),
            "captain": r["player"] == captain,
            "vice_captain": r["player"] == vice
        }
        for _, r in xi.iterrows()
    ]
