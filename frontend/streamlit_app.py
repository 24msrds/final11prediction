import streamlit as st
import requests
import pandas as pd

# ------------------------------
# PAGE CONFIG
# ------------------------------
st.set_page_config(
    page_title="ODI AI Final XI Selector",
    layout="centered"
)

st.title("🏏 ODI AI Final XI Selector")
st.caption("AI-powered Best XI selection using ODI player statistics")

# ------------------------------
# BACKEND CONFIG (RENDER)
# ------------------------------
API_BASE = "https://final11prediction.onrender.com"

# ------------------------------
# SIDEBAR INPUTS
# ------------------------------
st.sidebar.header("Match Conditions")

pitch_type = st.sidebar.selectbox(
    "Pitch Type",
    ["neutral", "batting", "bowling"]
)

opponent = st.sidebar.text_input(
    "Opponent Team",
    placeholder="e.g. Pakistan"
)

venue = st.sidebar.text_input(
    "Venue",
    placeholder="e.g. Lahore"
)

# ------------------------------
# HEALTH CHECK
# ------------------------------
with st.expander("🔍 Backend Status"):
    try:
        health = requests.get(f"{API_BASE}/", timeout=10)
        if health.status_code == 200:
            st.success("Backend is running ✅")
            st.json(health.json())
        else:
            st.warning("Backend reachable but returned unexpected response")
    except Exception as e:
        st.error("Backend not reachable ❌")
        st.code(str(e))

# ------------------------------
# FETCH BEST XI
# ------------------------------
st.markdown("---")

if st.button("⚡ Generate Best XI"):
    if opponent.strip() == "" or venue.strip() == "":
        st.warning("Please enter both opponent and venue.")
    else:
        with st.spinner("Selecting Best XI using AI logic..."):
            try:
                response = requests.get(
                    f"{API_BASE}/best-xi",
                    params={
                        "pitch_type": pitch_type,
                        "opponent": opponent,
                        "venue": venue
                    },
                    timeout=30
                )

                if response.status_code == 200:
                    data = response.json()

                    st.success("✅ Best XI Generated")

                    # ------------------------------
                    # DISPLAY RESULT
                    # ------------------------------
                    if isinstance(data, list):
                        df = pd.DataFrame(data)
                        st.subheader("🏏 Selected Playing XI")
                        st.dataframe(df, use_container_width=True)

                    elif isinstance(data, dict):
                        st.subheader("🏏 Selected Playing XI")
                        st.json(data)

                    else:
                        st.write(data)

                else:
                    st.error("❌ Backend returned an error")
                    st.code(f"Status Code: {response.status_code}")
                    st.text(response.text)

            except requests.exceptions.Timeout:
                st.error("⏳ Backend timeout. Please try again.")
            except requests.exceptions.ConnectionError:
                st.error("🔌 Unable to connect to backend.")
            except Exception as e:
                st.error("Unexpected error occurred")
                st.code(str(e))

# ------------------------------
# FOOTER
# ------------------------------
st.markdown("---")
st.caption(
    "Built with FastAPI + Streamlit | Deployed on Render & Streamlit Cloud"
)
