import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "odi_wc2023_players_stats_2019_2023.csv"

def auto_best_xi(pitch_type="neutral", opponent=None, venue=None):
    try:
        df = pd.read_csv(DATA_PATH)

        # Normalize column names
        df.columns = df.columns.str.lower().str.strip()

        REQUIRED_COLS = {"player", "role", "runs", "wickets", "country"}
        if not REQUIRED_COLS.issubset(df.columns):
            return {
                "error": "CSV missing required columns",
                "found": list(df.columns)
            }

        # Clean text fields
        df["player"] = df["player"].astype(str).str.strip()
        df["role"] = df["role"].str.lower().str.strip()
        df["country"] = df["country"].astype(str).str.strip()

        # Optional opponent filter
        if opponent:
            df = df[df["country"].str.lower() != opponent.lower()]

        if df.empty:
            return {"error": "No players found after filtering"}

        # Simple role-based selection
        batsmen = df[df["role"] == "batsman"].nlargest(5, "runs")
        allrounders = df[df["role"] == "allrounder"].nlargest(2, "runs")
        bowlers = df[df["role"] == "bowler"].nlargest(4, "wickets")

        final_xi = pd.concat([batsmen, allrounders, bowlers]).head(11)

        return {
            "count": len(final_xi),
            "players": final_xi[[
                "player", "role", "country", "runs", "wickets"
            ]].to_dict(orient="records")
        }

    except Exception as e:
        return {
            "error": "Internal selector error",
            "details": str(e)
        }
