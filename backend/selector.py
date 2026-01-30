from pathlib import Path
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "odi_wc2023_players_stats_2019_2023.csv"

PITCH_WEIGHTS = {
    "neutral": {"bat": 1.0, "bowl": 1.0},
    "pace": {"bat": 0.9, "bowl": 1.3},
    "spin": {"bat": 0.9, "bowl": 1.3},
}

CAPTAIN_POOL = {
    "Virat Kohli", "Babar Azam", "Kane Williamson",
    "Rohit Sharma", "Jos Buttler", "Pat Cummins"
}


def load_data():
    df = pd.read_csv(DATA_PATH, sep="\t")

    df.columns = df.columns.str.strip()

    required = {"player_clean", "country", "role", "runs", "strike_rate",
                "wickets", "economy"}

    if not required.issubset(df.columns):
        raise ValueError(
            f"CSV missing required columns, found: {list(df.columns)}"
        )

    df["player"] = df["player_clean"].str.title()
    df["role"] = df["role"].str.lower()

    df.fillna(0, inplace=True)
    return df


def auto_best_xi(
    pitch_type: str = "neutral",
    opponent: str | None = None,
    venue: str | None = None
):
    df = load_data()

    pitch = PITCH_WEIGHTS.get(pitch_type, PITCH_WEIGHTS["neutral"])

    df["bat_score"] = (
        df["runs"] * 0.6 + df["strike_rate"] * 0.4
    ) * pitch["bat"]

    df["bowl_score"] = (
        df["wickets"] * 30 - df["economy"] * 10
    ) * pitch["bowl"]

    df["selection_score"] = df["bat_score"] + df["bowl_score"]

    # Role balance
    batsmen = df[df["role"] == "batsman"].nlargest(4, "selection_score")
    allrounders = df[df["role"] == "allrounder"].nlargest(3, "selection_score")
    bowlers = df[df["role"] == "bowler"].nlargest(4, "selection_score")

    final_xi = pd.concat([batsmen, allrounders, bowlers])
    final_xi = final_xi.sort_values("selection_score", ascending=False)
    final_xi = final_xi.reset_index(drop=True)

    final_xi["rank"] = final_xi.index
    final_xi["captain"] = final_xi["player"].isin(CAPTAIN_POOL)
    final_xi["reason"] = final_xi.apply(
        lambda r: (
            f"Strong bowling impact ({int(r.wickets)} wkts)"
            if r.role == "bowler"
            else f"Consistent batting form ({int(r.runs)} runs)"
        ),
        axis=1
    )

    return final_xi[
        ["rank", "player", "role", "country",
         "runs", "strike_rate", "wickets",
         "economy", "selection_score",
         "captain", "reason"]
    ].to_dict(orient="records")
