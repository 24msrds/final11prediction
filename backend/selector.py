# Render deploy fix
from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "odi_wc2023_players_stats_2019_2023.csv"

def auto_best_xi(pitch_type="neutral", opponent=None, venue=None):
    df = pd.read_csv(DATA_PATH, sep="\t")

    df.columns = df.columns.str.strip()
    df["player"] = df["player"].astype(str)
    df["country"] = df["country"].astype(str)
    df["role"] = df["role"].str.lower()

    if opponent:
        df = df[df["country"].str.lower() != opponent.lower()]

    # basic score
    df["score"] = (
        df.get("runs", 0) * 0.02 +
        df.get("wickets", 0) * 25
    )

    batsmen = df[df["role"].isin(["batsman", "batter"])].nlargest(5, "score")
    allrounders = df[df["role"].isin(["allrounder"])].nlargest(2, "score")
    bowlers = df[df["role"].isin(["bowler"])].nlargest(4, "score")

    xi = pd.concat([batsmen, allrounders, bowlers]).head(11)

    captain = xi.sort_values("score", ascending=False).iloc[0]["player"]

    result = []
    for _, r in xi.iterrows():
        result.append({
            "player": r["player"],
            "role": r["role"],
            "country": r["country"],
            "runs": int(r.get("runs", 0)),
            "sr": float(r.get("strike_rate", 0)),
            "wickets": int(r.get("wickets", 0)),
            "economy": float(r.get("economy", 0)),
            "captain": r["player"] == captain,
            "vice_captain": False
        })

    return result
