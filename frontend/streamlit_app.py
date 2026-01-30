import streamlit as st
import pandas as pd
import requests

API = "https://final11prediction.onrender.com"

st.set_page_config(page_title="ODI AI Final XI", layout="wide")

st.title("🏏 ODI AI Final XI Selector")
st.caption("AI-powered Best XI selection using ODI player statistics")

with st.expander("🔍 Backend Status"):
    try:
        res = requests.get(API)
        st.success(res.json()["status"])
    except:
        st.error("Backend not reachable")

pitch = st.selectbox("Pitch Type", ["neutral", "pace", "spin"])
opponent = st.selectbox(
    "Opponent",
    ["Pakistan", "India", "Australia", "England", "South Africa"]
)
venue = st.selectbox(
    "Venue",
    ["Lahore", "Wankhede", "MCG", "Lords", "Centurion"]
)

if st.button("⚡ Generate Best XI"):
    with st.spinner("Analyzing players..."):
        res = requests.get(
            f"{API}/best-xi",
            params={
                "pitch_type": pitch,
                "opponent": opponent,
                "venue": venue
            }
        )

    if res.status_code != 200:
        st.error("Backend returned an error")
        st.code(res.text)
    else:
        df = pd.DataFrame(res.json())

        df = df.sort_values("selection_score", ascending=False)
        df.index = range(1, len(df) + 1)

        st.subheader("🏆 Final Playing XI")
        st.dataframe(df, use_container_width=True)

        st.subheader("📊 Selection Score Comparison")
        st.bar_chart(
            df.set_index("player")["selection_score"]
        )
