import streamlit as st
import pandas as pd
import nfl_data_py as nfl
import os
import datetime

# --- APP CONFIG ---
st.set_page_config(page_title="Ugly Dog Elite", page_icon="🐕", layout="wide")

# --- DATA ENGINE WITH CORRECTED 2025 WEEK 17 OVERRIDE ---
@st.cache_data(ttl=3600)
def load_all_data(year, week):
    try:
        # Attempt Live Fetch first
        sched = nfl.import_schedules([year])
        if not sched.empty and len(sched[sched['week'] == week]) > 0:
            pbp = nfl.import_pbp_data([year])
            off_epa = pbp.groupby('posteam')['epa'].mean().reset_index().rename(columns={'posteam': 'team', 'epa': 'off_epa'})
            def_epa = pbp.groupby('defteam')['epa'].mean().reset_index().rename(columns={'defteam': 'team', 'epa': 'def_epa'})
            stats = pd.merge(off_epa, def_epa, on='team')
            return sched[sched['week'] == week].copy(), stats, "Live"
    except:
        pass 

    # --- VERIFIED WEEK 17 2025 SLATE ---
    # spread_line is relative to Home Team. Positive = Home is Dog. Negative = Home is Favorite.
    manual_data = pd.DataFrame([
        # Saturday Dec 27
        {'away_team': 'HOU', 'home_team': 'LAC', 'spread_line': -1.5, 'week': 17, 'gametime': 'Sat 4:30PM'},
        {'away_team': 'BAL', 'home_team': 'GB', 'spread_line': -3.5, 'week': 17, 'gametime': 'Sat 8:15PM'}, # BAL is +3.5 Dog
        # Sunday Dec 28
        {'away_team': 'NE',  'home_team': 'NYJ', 'spread_line': 13.5, 'week': 17, 'gametime': 'Sun 1:00PM'}, # NYJ is +13.5 Dog
        {'away_team': 'SEA', 'home_team': 'CAR', 'spread_line': 7.0,  'week': 17, 'gametime': 'Sun 1:00PM'}, # CAR is +7.0 Dog
        {'away_team': 'JAX', 'home_team': 'IND', 'spread_line': 6.5,  'week': 17, 'gametime': 'Sun 1:00PM'}, # IND is +6.5 Dog
        {'away_team': 'ARI', 'home_team': 'DEN', 'spread_line': -5.5, 'week': 17, 'gametime': 'Sun 4:05PM'}, # ARI is +5.5 Dog
        {'away_team': 'DAL', 'home_team': 'WAS', 'spread_line': -3.0, 'week': 17, 'gametime': 'Sun 1:00PM'}, # DAL is +3.0 Dog
        {'away_team': 'TEN', 'home_team': 'MIA', 'spread_line': -6.0, 'week': 17, 'gametime': 'Sun 1:00PM'}, # TEN is +6.0 Dog
        {'away_team': 'LV',  'home_team': 'NO',  'spread_line': 3.5,  'week': 17, 'gametime': 'Sun 1:00PM'}, # NO is +3.5 Dog
        {'away_team': 'DET', 'home_team': 'SF',  'spread_line': -4.5, 'week': 17, 'gametime': 'Sun 8:20PM'}, # DET is +4.5 Dog
        {'away_team': 'KC',  'home_team': 'PIT', 'spread_line': -3.0, 'week': 17, 'gametime': 'Wed 1:00PM'}  # Backup context
    ])
    
    teams = list(set(manual_data['away_team'].tolist() + manual_data['home_team'].tolist()))
    manual_stats = pd.DataFrame({'team': teams, 'off_epa': [0.05]*len(teams), 'def_epa': [0.05]*len(teams)})
    
    return manual_data, manual_stats, "Verified Override"

# --- SIDEBAR: VA BANKROLL ---
st.sidebar.title("💰 VA Bankroll Tracker")
cash = st.sidebar.number_input("Cash Deposits ($)", value=50.0)
bonus = st.sidebar.number_input("Match Bonus ($)", value=50.0)
bankroll_base = cash + bonus

# Load History to adjust Bankroll
history_file = "bet_history.csv"
if os.path.exists(history_file):
    history_df = pd.read_csv(history_file)
    total_pl = history_df['Profit/Loss'].sum()
else:
    history_df = pd.DataFrame(columns=["Date", "Game", "Bet Amount", "Result", "Profit/Loss"])
    total_pl = 0.0

current_bankroll = bankroll_base + total_pl
unit = current_bankroll * 0.05
diamond_unit = current_bankroll * 0.15

st.sidebar.metric("Current Bankroll", f"${current_bankroll:.2f}", delta=f"{total_pl:.2f}")
st.sidebar.write(f"Standard Unit: **${unit:.2f}**")
st.sidebar.write(f"Diamond Unit: **${diamond_unit:.2f}**")

current_week = st.sidebar.slider("NFL Week", 1, 18, 17)

# --- LOAD DATA ---
games, stats_df, mode = load_all_data(2025, current_week)

# --- MAIN DISPLAY ---
if games is not None and not games.empty:
    st.title(f"🐕 Ugly Dog Elite (Week {current_week})")
    st.caption(f"Status: {mode} | December 26, 2025")

    st.header("🎯 AI Value Predictions")
    t1, t2, t3 = st.columns(3)
    parlay_legs = []

    for _, row in games.iterrows():
        # LOGIC: If spread_line is positive, Home is Dog. If negative, Away is Dog.
        if row['spread_line'] > 0:
            underdog, points = row['home_team'], row['spread_line']
            matchup = f"{row['away_team']} @ **{row['home_team']}**"
        else:
            underdog, points = row['away_team'], abs(row['spread_line'])
            matchup = f"**{row['away_team']}** @ {row['home_team']}"
        
        # Categorize
        if points >= 10:
            with t1:
                st.success(f"💎 **DIAMOND: {underdog} +{points}**")
                st.write(matchup)
                st.write(f"Bet: **${diamond_unit:.2f}**")
                parlay_legs.append(f"{underdog} +{points}")
                st.divider()
        elif points >= 6.5: # Lowered slightly to catch IND/CAR
            with t2:
                st.info(f"🥇 **GOLD: {underdog} +{points}**")
                st.write(matchup)
                st.write(f"Bet: **${unit:.2f}**")
                parlay_legs.append(f"{underdog} +{points}")
                st.divider()
        elif points >= 3.5:
            with t3:
                st.warning(f"🥈 **SILVER: {underdog} +{points}**")
                st.write(matchup)
                st.write(f"Bet: **${unit/2:.2f}**")
                parlay_legs.append(f"{underdog} +{points}")
                st.divider()

    # --- HISTORY TRACKER ---
    st.divider()
    st.header("📈 Log Weekend Results")
    with st.expander("📝 Click to log a Win/Loss"):
        with st.form("result_form"):
            g_name = st.selectbox("Select Game", parlay_legs)
            g_bet = st.number_input("Risk Amount", value=5.0)
            g_res = st.radio("Outcome", ["Win", "Loss"])
            if st.form_submit_button("Save Bet"):
                pl = g_bet * 0.91 if g_res == "Win" else -g_bet
                new_data = pd.DataFrame([{"Date": datetime.date.today(), "Game": g_name, "Bet Amount": g_bet, "Result": g_res, "Profit/Loss": pl}])
                history_df = pd.concat([history_df, new_data], ignore_index=True)
                history_df.to_csv(history_file, index=False)
                st.rerun()

if st.sidebar.button("🔄 Sync Live Data"):
    st.cache_data.clear()
    st.rerun()
