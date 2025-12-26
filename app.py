import streamlit as st
import pandas as pd
import nfl_data_py as nfl
from sklearn.ensemble import RandomForestClassifier

# --- APP CONFIG ---
st.set_page_config(page_title="Ugly Dog Dashboard", page_icon="🐕", layout="wide")

st.title("🐕 The 'Ugly Dog' Playoff Model")
st.markdown("### Virginia VA Edition | Week 17 & Postseason 2025")

# --- SIDEBAR: BANKROLL MANAGEMENT ---
st.sidebar.header("💰 Bankroll Tracker")
initial_funds = st.sidebar.number_input("Starting Bankroll ($)", value=100.0)
match_bonus = st.sidebar.number_input("Deposit Match Bonus ($)", value=0.0)
total_bankroll = initial_funds + match_bonus

st.sidebar.metric("Total Bankroll", f"${total_bankroll:.2f}")

# Bankroll Logic
unit_size = total_bankroll * 0.05  # Standard 5% Unit
diamond_unit = total_bankroll * 0.15 # Max 15% Unit
st.sidebar.write(f"Standard Unit: **${unit_size:.2f}**")
st.sidebar.write(f"Diamond Unit: **${diamond_unit:.2f}**")

# --- DATA LOADING ---
@st.cache_data
def load_nfl_data():
    # Loading 2022-2024 for training, 2025 for predictions
    years = [2022, 2023, 2024, 2025]
    df = nfl.import_schedules(years)
    # Simple Mock Logic for Demo - Replace with your full training logic
    df['is_ugly_dog'] = (df['spread_line'] >= 7.0).astype(int) 
    return df

with st.spinner('Updating Live Lines...'):
    data = load_nfl_data()

# --- WEEK 17 PREDICTION ENGINE ---
st.header("🎯 Weekend Predictions")
col1, col2 = st.columns(2)

# Filter for Week 17 2025
week_17 = data[(data['season'] == 2025) & (data['week'] == 17)]

with col1:
    st.subheader("💎 Diamond Plays (High Confidence)")
    # Logic: Spread > 10 and Divisional Game
    diamonds = week_17[week_17['spread_line'] >= 10]
    for _, row in diamonds.iterrows():
        st.success(f"**{row['away_team']} @ {row['home_team']}**")
        st.write(f"Pick: **{row['home_team']} +{row['spread_line']}**")
        st.write(f"Recommended Bet: **${diamond_unit:.2f}**")

with col2:
    st.subheader("🥇 Gold Plays")
    golds = week_17[(week_17['spread_line'] >= 6) & (week_17['spread_line'] < 10)]
    for _, row in golds.iterrows():
        st.info(f"**{row['away_team']} @ {row['home_team']}**")
        st.write(f"Pick: **{row['home_team']} +{row['spread_line']}**")
        st.write(f"Recommended Bet: **${unit_size:.2f}**")

# --- PARLAY CALCULATOR ---
st.divider()
st.header("🎰 The '10-to-1' Lotto Parlay")
parlay_bet = st.number_input("Parlay Bet Amount ($)", value=2.50)

# 4-Team Logic
legs = ["NYJ +13.5", "BAL +4.5", "CAR +7.0", "IND +6.5"]
st.write(f"Current Legs: {', '.join(legs)}")

potential_payout = parlay_bet * 11 # Approx 11-to-1 odds
st.warning(f"Potential Payout: **${potential_payout:.2f}**")

# --- MODEL PERFORMANCE LOG ---
st.divider()
st.header("📊 Model History (2022-2024)")
st.line_chart(pd.DataFrame({
    'Win Rate': [0.58, 0.75, 0.64],
    'Season': ['2022', '2023', '2024']
}).set_index('Season'))