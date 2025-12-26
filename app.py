import streamlit as st
import pandas as pd
import nfl_data_py as nfl
import os

# --- APP CONFIG ---
st.set_page_config(page_title="Ugly Dog Elite", page_icon="🐕", layout="wide")

# --- DATA ENGINE WITH OFFLINE FALLBACK ---
@st.cache_data(ttl=3600)
def load_all_data(year, week):
    file_path = f"backup_data_{year}.csv"
    stats_path = f"backup_stats_{year}.csv"
    
    try:
        # 1. ATTEMPT LIVE FETCH: Schedule & Odds
        sched = nfl.import_schedules([year])
        
        # 2. ATTEMPT LIVE FETCH: EPA Stats (Play-by-Play)
        pbp = nfl.import_pbp_data([year])
        off_epa = pbp.groupby('posteam')['epa'].mean().reset_index().rename(columns={'posteam': 'team', 'epa': 'off_epa'})
        def_epa = pbp.groupby('defteam')['epa'].mean().reset_index().rename(columns={'defteam': 'team', 'epa': 'def_epa'})
        stats = pd.merge(off_epa, def_epa, on='team')

        if not sched.empty:
            sched.to_csv(file_path, index=False)
            stats.to_csv(stats_path, index=False)
            return sched[sched['week'] == week].copy(), stats, "Live"
            
    except Exception as e:
        # FALLBACK TO LOCAL CSV
        if os.path.exists(file_path) and os.path.exists(stats_path):
            offline_df = pd.read_csv(file_path)
            offline_stats = pd.read_csv(stats_path)
            return offline_df[offline_df['week'] == week].copy(), offline_stats, "Offline"
        else:
            return None, None, "Error"

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

# --- SCORE PROJECTION FUNCTION ---
def get_ai_score(h_team, a_team, stats):
    avg_score = 22.0
    try:
        h_s = stats[stats['team'] == h_team].iloc[0]
        a_s = stats[stats['team'] == a_team].iloc[0]
        # Formula: Base + (Offense EPA - Defense EPA) * Scaling Factor
        h_p = avg_score + (h_s['off_epa'] * 12) - (a_s['def_epa'] * 12) + 1.5
        a_p = avg_score + (a_s['off_epa'] * 12) - (h_s['def_epa'] * 12)
        return h_p, a_p
    except:
        return 0, 0

# --- MAIN DISPLAY ---
if games is not None and not games.empty:
    st.title(f"🐕 Ugly Dog Elite ({mode})")
    
    # Live Scores Table (Brief)
    with st.expander("📊 Live Scoreboard / Recent Results"):
        st.dataframe(games[['away_team', 'away_score', 'home_team', 'home_score', 'result']])

    st.header(f"🎯 Week {current_week} AI Predictions")
    t1, t2, t3 = st.columns(3)
    
    parlay_legs = []

    for _, row in games.iterrows():
        # Identify the Dog & Points
        if row['spread_line'] > 0:
            underdog, points = row['home_team'], row['spread_line']
            matchup = f"{row['away_team']} @ **{row['home_team']}**"
        else:
            underdog, points = row['away_team'], abs(row['spread_line'])
            matchup = f"**{row['away_team']}** @ {row['home_team']}"
        
        # AI Score Calculation
        hp, ap = get_ai_score(row['home_team'], row['away_team'], stats_df)

        # Categorize into Columns
        if points >= 10:
            with t1:
                st.success(f"💎 **DIAMOND: {underdog} +{points}**")
                st.write(matchup)
                if hp > 0: st.caption(f"AI Projected: {row['away_team']} {ap:.1f} - {row['home_team']} {hp:.1f}")
                st.write(f"Bet: **${diamond_unit:.2f}**")
                parlay_legs.append(f"{underdog} +{points}")
                st.divider()
        elif points >= 7:
            with t2:
                st.info(f"🥇 **GOLD: {underdog} +{points}**")
                st.write(matchup)
                if hp > 0: st.caption(f"AI Projected: {row['away_team']} {ap:.1f} - {row['home_team']} {hp:.1f}")
                st.write(f"Bet: **${unit:.2f}**")
                parlay_legs.append(f"{underdog} +{points}")
                st.divider()
        elif points >= 4:
            with t3:
                st.warning(f"🥈 **SILVER: {underdog} +{points}**")
                st.write(matchup)
                if hp > 0: st.caption(f"AI Projected: {row['away_team']} {ap:.1f} - {row['home_team']} {hp:.1f}")
                st.write(f"Bet: **${unit/2:.2f}**")
                parlay_legs.append(f"{underdog} +{points}")
                st.divider()

    # --- PARLAY SECTION ---
    st.header("🎰 Automated Lotto Parlay")
    if len(parlay_legs) >= 2:
        st.write("Suggested Legs:", " | ".join(parlay_legs[:4]))
        amt = st.number_input("Parlay Risk", value=2.50)
        st.write(f"Est. Payout: **${amt * 11:.2f}**")

else:
    st.error("No games found. Try adjusting the Week slider or clearing cache.")

if st.sidebar.button("🔄 Clear Cache & Sync Live"):
    st.cache_data.clear()
    st.rerun()
