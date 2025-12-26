import streamlit as st
import pandas as pd
import nfl_data_py as nfl
import os

# --- APP CONFIG ---
st.set_page_config(page_title="Ugly Dog Elite", page_icon="🐕", layout="wide")

# --- DATA ENGINE WITH OFFLINE FALLBACK ---
@st.cache_data(ttl=3600)
def load_data_with_backup(year, week):
    file_path = f"backup_data_{year}.csv"
    
    try:
        # 1. ATTEMPT LIVE FETCH
        sched = nfl.import_schedules([year])
        if not sched.empty:
            # Success! Save a local backup for next time
            sched.to_csv(file_path, index=False)
            st.sidebar.success("✅ Connected to Live Feed")
            return sched[sched['week'] == week].copy(), "Live"
            
    except Exception as e:
        # 2. LIVE FETCH FAILED -> ATTEMPT OFFLINE LOAD
        if os.path.exists(file_path):
            st.sidebar.warning("⚠️ Using Offline Backup Data")
            offline_df = pd.read_csv(file_path)
            return offline_df[offline_df['week'] == week].copy(), "Offline"
        else:
            st.sidebar.error("🚨 No Live Feed and No Backup Found.")
            return None, "Error"

# --- BANKROLL & UI ---
st.sidebar.title("💰 VA Bankroll Tracker")
cash = st.sidebar.number_input("Cash Deposits ($)", value=50.0)
bonus = st.sidebar.number_input("VA Match Bonus ($)", value=50.0)
total_bankroll = cash + bonus
st.sidebar.metric("Total Bankroll", f"${total_bankroll:.2f}")

current_week = st.sidebar.slider("NFL Week", 1, 18, 17)

# --- EXECUTE LOAD ---
games, data_mode = load_data_with_backup(2025, current_week)

# --- APP CONTENT ---
if games is not None and not games.empty:
    st.title(f"🐕 Ugly Dog Elite ({data_mode} Mode)")
    
    # [Insert your Tier Logic & Parlay Calculator here from previous steps]
    
    # --- DISPLAY TABLE ---
    st.header(f"📅 Week {current_week} Odds")
    st.dataframe(games[['away_team', 'home_team', 'spread_line', 'gametime', 'result']])
    
else:
    st.error("Wait for the NFL servers to wake up or check your connection.")
    if st.button("🔄 Force Retry"):
        st.cache_data.clear()
        st.rerun()

# --- FOOTER ---
if data_mode == "Offline":
    st.info("Note: Odds and scores are from the last successful sync. They may be a few hours old.")