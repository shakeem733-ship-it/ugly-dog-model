import streamlit as st
import pandas as pd
import nfl_data_py as nfl
import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="Ugly Dog Elite", page_icon="🐕", layout="wide")

# Custom CSS for a clean look
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR: BANKROLL & VA SETTINGS ---
st.sidebar.title("💰 VA Bankroll Tracker")
st.sidebar.markdown("---")
cash = st.sidebar.number_input("Cash Deposits ($)", value=50.0)
bonus = st.sidebar.number_input("VA Match Bonus ($)", value=50.0)
bankroll = cash + bonus

unit = bankroll * 0.05
diamond_unit = bankroll * 0.15

st.sidebar.metric("Total Bankroll", f"${bankroll:.2f}")
st.sidebar.write(f"Standard Unit: **${unit:.2f}**")
st.sidebar.write(f"Diamond Unit: **${diamond_unit:.2f}**")

current_week = st.sidebar.slider("NFL Week", 1, 18, 17)

# --- DATA ENGINE (Cached) ---
@st.cache_data(ttl=3600) # Refresh every hour
def load_all_data(year, week):
    # 1. Load Schedule/Odds
    sched = nfl.import_schedules([year])
    weekly = sched[sched['week'] == week].copy()
    
    # 2. Load EPA Stats (Using 2025 season data)
    pbp = nfl.import_pbp_data([year])
    off_epa = pbp.groupby('posteam')['epa'].mean().reset_index().rename(columns={'posteam': 'team', 'epa': 'off_epa'})
    def_epa = pbp.groupby('defteam')['epa'].mean().reset_index().rename(columns={'defteam': 'team', 'epa': 'def_epa'})
    stats = pd.merge(off_epa, def_epa, on='team')
    
    return weekly, stats

try:
    with st.spinner('Fetching Live NFL Data...'):
        games, stats_df = load_all_data(2025, current_week)
except:
    st.error("Live Data Feed Offline. Please refresh.")
    st.stop()

# --- MAIN DASHBOARD ---
st.title("🐕 Ugly Dog Elite: AI Betting & Live Scores")
st.write(f"**Current Status:** Week {current_week} | 2025 Season")

# --- LIVE SCOREBOARD SECTION ---
st.header("🏁 Live Scoreboard")
score_cols = st.columns(4)
for i, (_, row) in enumerate(games.iterrows()):
    with score_cols[i % 4]:
        # Using nfl_data_py result column to show live progress
        home_score = row['home_score'] if not pd.isna(row['home_score']) else 0
        away_score = row['away_score'] if not pd.isna(row['away_score']) else 0
        status = "FINAL" if row['game_type'] != 'REG' or not pd.isna(row['result']) else "UPCOMING"
        
        st.markdown(f"""
        **{row['away_team']}** {int(away_score)}  
        **{row['home_team']}** {int(home_score)}  
        *{status}*
        """)
st.divider()

# --- AI PREDICTION TIERS ---
st.header("🎯 AI Value Predictions")
t1, t2, t3 = st.columns(3)

def get_ai_projection(h_team, a_team, stats_df):
    avg_score = 22.0
    try:
        h_s = stats_df[stats_df['team'] == h_team].iloc[0]
        a_s = stats_df[stats_df['team'] == a_team].iloc[0]
        
        h_proj = avg_score + (h_s['off_epa'] * 12) - (a_s['def_epa'] * 12) + 1.5
        a_proj = avg_score + (a_s['off_epa'] * 12) - (h_s['def_epa'] * 12)
        return h_proj, a_proj
    except:
        return 0, 0

parlay_legs = []

# Logic to sort games into columns
for _, row in games.iterrows():
    h_proj, a_proj = get_ai_projection(row['home_team'], row['away_team'], stats_df)
    spread = row['spread_line']
    abs_spread = abs(spread)
    
    # Identify the Dog
    dog = row['home_team'] if spread > 0 else row['away_team']
    
    # Tier Logic
    target_col = None
    if abs_spread >= 10: target_col = t1; color = "green"; label = "DIAMOND"
    elif abs_spread >= 7: target_col = t2; color = "blue"; label = "GOLD"
    elif abs_spread >= 4: target_col = t3; color = "orange"; label = "SILVER"
    
    if target_col:
        with target_col:
            st.markdown(f"### :{color}[{label}]")
            st.write(f"**{row['away_team']} @ {row['home_team']}**")
            st.write(f"Vegas Line: **{dog} +{abs_spread}**")
            st.write(f"AI Score: {a_team} {a_proj:.1f} - {h_team} {h_proj:.1f}")
            
            # Highlight value
            ai_diff = abs(a_proj - h_proj)
            if abs(ai_diff - abs_spread) > 3:
                st.write("🔥 **High Value detected vs Spread**")
            
            parlay_legs.append(f"{dog} +{abs_spread}")
            st.divider()

# --- THE AUTO-PARLAY ---
st.header("🎰 Automated Lotto Parlay")
if len(parlay_legs) >= 2:
    st.write("Suggested Ticket:", " ➔ ".join(parlay_legs[:4]))
    amt = st.number_input("Parlay Risk", value=2.50)
    st.write(f"Est. Return: **${amt * 11:.2f}**")
else:
    st.write("Not enough qualifying dogs for a parlay today.")

if st.button("🔄 Force Update All Data"):
    st.cache_data.clear()
    st.rerun()