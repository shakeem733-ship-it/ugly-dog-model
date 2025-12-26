import streamlit as st
import pandas as pd
import nfl_data_py as nfl
import os

# --- APP CONFIG ---
st.set_page_config(page_title="Ugly Dog Elite", page_icon="🐕", layout="wide")

# --- DATA ENGINE WITH FULL WEEK 17 OVERRIDE ---
@st.cache_data(ttl=3600)
def load_all_data(year, week):
    try:
        # Attempt to pull live data
        sched = nfl.import_schedules([year])
        stats_pbp = nfl.import_pbp_data([year])
        
        # If live data is found, process it
        if not sched.empty and len(sched[sched['week'] == week]) > 0:
            off_epa = stats_pbp.groupby('posteam')['epa'].mean().reset_index().rename(columns={'posteam': 'team', 'epa': 'off_epa'})
            def_epa = stats_pbp.groupby('defteam')['epa'].mean().reset_index().rename(columns={'defteam': 'team', 'epa': 'def_epa'})
            stats = pd.merge(off_epa, def_epa, on='team')
            return sched[sched['week'] == week].copy(), stats, "Live"
    except:
        pass # If anything fails, move to Override below

    # --- FULL WEEK 17 OVERRIDE (DEC 27-28, 2025) ---
    st.sidebar.warning("⚠️ Using Manual Override: Week 17 Slate")
    
    manual_data = pd.DataFrame([
        # Saturday Games
        {'away_team': 'HOU', 'home_team': 'LAC', 'spread_line': -1.5, 'week': 17, 'gametime': 'Sat 4:30PM'},
        {'away_team': 'BAL', 'home_team': 'GB', 'spread_line': 4.5, 'week': 17, 'gametime': 'Sat 8:00PM'},
        # Sunday Games
        {'away_team': 'NE', 'home_team': 'NYJ', 'spread_line': 13.5, 'week': 17, 'gametime': 'Sun 1:00PM'},
        {'away_team': 'SEA', 'home_team': 'CAR', 'spread_line': 7.0, 'week': 17, 'gametime': 'Sun 1:00PM'},
        {'away_team': 'JAX', 'home_team': 'IND', 'spread_line': 6.5, 'week': 17, 'gametime': 'Sun 1:00PM'},
        {'away_team': 'TEN', 'home_team': 'MIA', 'spread_line': 6.0, 'week': 17, 'gametime': 'Sun 1:00PM'},
        {'away_team': 'ARI', 'home_team': 'LAR', 'spread_line': 7.5, 'week': 17, 'gametime': 'Sun 4:05PM'},
        {'away_team': 'ATL', 'home_team': 'WAS', 'spread_line': -3.0, 'week': 17, 'gametime': 'Sun 1:00PM'},
        {'away_team': 'LV', 'home_team': 'NO', 'spread_line': 3.5, 'week': 17, 'gametime': 'Sun 1:00PM'},
        {'away_team': 'DAL', 'home_team': 'PHI', 'spread_line': -9.0, 'week': 17, 'gametime': 'Sun 4:25PM'},
        {'away_team': 'DET', 'home_team': 'SF', 'spread_line': -2.5, 'week': 17, 'gametime': 'Sun 8:20PM'}
    ])
    
    # Placeholder stats so score logic doesn't crash
    teams = list(set(manual_data['away_team'].tolist() + manual_data['home_team'].tolist()))
    manual_stats = pd.DataFrame({'team': teams, 'off_epa': [0.05]*len(teams), 'def_epa': [0.05]*len(teams)})
    
    return manual_data, manual_stats, "Override"

# --- SIDEBAR: VA BANKROLL ---
st.sidebar.title("💰 VA Bankroll Tracker")
cash = st.sidebar.number_input("Cash Deposits ($)", value=50.0)
bonus = st.sidebar.number_input("Match Bonus ($)", value=50.0)
bankroll = cash + bonus
unit = bankroll * 0.05
diamond_unit = bankroll * 0.15

st.sidebar.metric("Total Bankroll", f"${bankroll:.2f}")
st.sidebar.write(f"Standard Unit: **${unit:.2f}**")
st.sidebar.write(f"Diamond Unit: **${diamond_unit:.2f}**")

current_week = st.sidebar.slider("NFL Week", 1, 18, 17)

# --- LOAD DATA ---
games, stats_df, mode = load_all_data(2025, current_week)

# --- SCORE PROJECTION ---
def get_ai_score(h_team, a_team, stats):
    avg_score = 22.0
    try:
        h_s = stats[stats['team'] == h_team].iloc[0]
        a_s = stats[stats['team'] == a_team].iloc[0]
        h_p = avg_score + (h_s['off_epa'] * 12) - (a_s['def_epa'] * 12) + 1.5
        a_p = avg_score + (a_s['off_epa'] * 12) - (h_s['def_epa'] * 12)
        return h_p, a_p
    except: return 21.0, 20.0 # Default fallback

# --- MAIN DISPLAY ---
if games is not None and not games.empty:
    st.title(f"🐕 Ugly Dog Elite (Week {current_week})")
    st.caption(f"Data Source: {mode}")

    st.header("🎯 AI Value Predictions")
    t1, t2, t3 = st.columns(3)
    parlay_legs = []

    for _, row in games.iterrows():
        # Identify Underdog: If spread > 0, home is dog. If spread < 0, away is dog.
        if row['spread_line'] > 0:
            underdog, points = row['home_team'], row['spread_line']
            matchup = f"{row['away_team']} @ **{row['home_team']}**"
        else:
            underdog, points = row['away_team'], abs(row['spread_line'])
            matchup = f"**{row['away_team']}** @ {row['home_team']}"
        
        hp, ap = get_ai_score(row['home_team'], row['away_team'], stats_df)

        # Categorize
        if points >= 10:
            with t1:
                st.success(f"💎 **DIAMOND: {underdog} +{points}**")
                st.write(matchup)
                st.write(f"Bet: **${diamond_unit:.2f}**")
                parlay_legs.append(f"{underdog} +{points}")
                st.divider()
        elif points >= 7:
            with t2:
                st.info(f"🥇 **GOLD: {underdog} +{points}**")
                st.write(matchup)
                st.write(f"Bet: **${unit:.2f}**")
                parlay_legs.append(f"{underdog} +{points}")
                st.divider()
        elif points >= 4:
            with t3:
                st.warning(f"🥈 **SILVER: {underdog} +{points}**")
                st.write(matchup)
                st.write(f"Bet: **${unit/2:.2f}**")
                parlay_legs.append(f"{underdog} +{points}")
                st.divider()

    # --- PARLAY SECTION ---
    st.header("🎰 Automated Lotto Parlay")
    if len(parlay_legs) >= 2:
        st.write("Suggested Legs:", " | ".join(parlay_legs[:4]))
        amt = st.number_input("Parlay Risk ($)", value=2.50)
        st.write(f"Est. Payout: **${amt * 11:.2f}**")
    
    # --- FULL SLATE ---
    with st.expander("📝 View Full Odds Board"):
        st.table(games[['away_team', 'home_team', 'spread_line', 'gametime']])

if st.sidebar.button("🔄 Clear Cache & Sync"):
    st.cache_data.clear()
    st.rerun()
