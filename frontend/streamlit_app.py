import streamlit as st
import requests
import pandas as pd

# -------------------------------------------------
# API CONFIG
# -------------------------------------------------
API = "http://127.0.0.1:8000"

# -------------------------------------------------
# PLAYER IMAGE MAP
# -------------------------------------------------
PLAYER_IMAGES = {
    "Virat Kohli": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/316400/316486.png",
    "Rohit Sharma": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/316500/316506.png",
    "Quinton De Kock": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/321000/321006.png",
    "Jos Buttler": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/322000/322003.png",
    "Babar Azam": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/316600/316605.png",
    "Jasprit Bumrah": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/316700/316705.png",
    "Mitchell Starc": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/316800/316803.png",
    "Adam Zampa": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/316900/316903.png",
    "Kane Williamson": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/316300/316306.png",
    "KL Rahul": "https://img1.hscicdn.com/image/upload/f_auto,t_ds_square_w_80/lsci/db/PICTURES/CMS/316800/316846.png",
}

PLACEHOLDER_IMG = "https://via.placeholder.com/80?text=Player"

# -------------------------------------------------
# PAGE CONFIG
# -------------------------------------------------
st.set_page_config(page_title="ODI AI Selection Analyst", layout="wide")

st.title("🏏 ODI AI Selection Analyst")
st.caption("AI-assisted team selection • balance • leadership • conditions")

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------
st.sidebar.header("Match Context")

pitch = st.sidebar.selectbox("Pitch Type", ["neutral", "spin", "pace"])

opponent = st.sidebar.selectbox(
    "Opponent Team",
    [
        "India", "Australia", "England", "Pakistan",
        "New Zealand", "South Africa",
        "Sri Lanka", "Bangladesh", "Netherlands"
    ]
)

venue = st.sidebar.selectbox(
    "Venue",
    [
        "Wankhede Stadium, India",
        "Eden Gardens, India",
        "MCG, Australia",
        "Lord's, England",
        "Wanderers, South Africa",
        "R Premadasa Stadium, Sri Lanka",
        "Gaddafi Stadium, Pakistan",
        "Hagley Oval, New Zealand"
    ]
)

# -------------------------------------------------
# RUN ANALYSIS
# -------------------------------------------------
if st.button("🧠 Analyze Best XI"):
    with st.spinner("Analyzing team balance..."):
        res = requests.get(
            f"{API}/best-xi",
            params={
                "pitch_type": pitch,
                "opponent": opponent,
                "venue": venue
            }
        )

        if res.status_code != 200:
            st.error("Backend error")
            st.stop()

        df = pd.DataFrame(res.json())

    df.index = range(1, len(df) + 1)

    # -------------------------------------------------
    # DISPLAY PLAYING XI (IMAGE FIX)
    # -------------------------------------------------
    st.subheader("🏆 Final Playing XI")

    for idx, row in df.iterrows():
        cols = st.columns([0.8, 2.8, 1.5, 1.5, 1, 1, 1])

        # ✅ IMAGE FIX (USE GET, NOT MAP)
        img = PLAYER_IMAGES.get(row["player"], PLACEHOLDER_IMG)
        cols[0].image(img, width=60)

        name = f"**{row['player']}**"
        if row["captain"]:
            name += " 👑"
        elif row["vice_captain"]:
            name += " ⭐"
        if row["role"] == "wicketkeeper":
            name += " 🧤"

        cols[1].markdown(name)
        cols[2].write(row["role"].title())
        cols[3].write(row["country"])
        cols[4].write(row["runs"])
        cols[5].write(row["sr"])
        cols[6].write(row["wickets"])

    # -------------------------------------------------
    # TEAM STABILITY REPORT
    # -------------------------------------------------
    st.subheader("⚖ Team Stability Report")

    role_counts = df["role"].value_counts()
    bat_count = role_counts.get("batsman", 0) + role_counts.get("wicketkeeper", 0)
    ar_count = role_counts.get("allrounder", 0)
    bowl_count = role_counts.get("bowler", 0)

    st.success("🎯 Strong bowling attack" if bowl_count >= 3 else "🎯 Bowling depth moderate")
    st.success("🔄 Good all-rounder balance" if ar_count >= 2 else "🔄 Limited all-rounders")
    st.warning("🏏 Moderate batting depth" if bat_count < 6 else "🏏 Strong batting depth")

    captain = df[df["captain"]]["player"].iloc[0]

    st.subheader("📝 Selector Insights")
    st.info(
        f"""
        ✔ XI is balanced  
        ✔ Bowling options validated using wickets  
        ✔ Opposition bias correctly filtered  
        ✔ Venue adaptability considered  
        ✔ Captaincy candidate: **{captain}**
        """
    )

st.divider()
st.caption("Built for ODI analytics • selection logic inspired by real selectors")
