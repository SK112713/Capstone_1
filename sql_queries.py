import streamlit as st
import pandas as pd
import pymysql
from db_connection import get_db_connection  # your existing connector

st.set_page_config(page_title="SQL Practice Explorer", layout="wide")
st.title("🧮 SQL Practice Explorer – 25 Queries")

# --------- DB helpers ----------
def run_query(query: str):
    conn = get_db_connection()
    if conn is None:
        st.error("Could not connect to the database.")
        return pd.DataFrame()
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description] if cur.description else []
            return pd.DataFrame(rows, columns=cols)
    except pymysql.MySQLError as e:
        st.error(f"Database error: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def table_exists(table_name: str) -> bool:
    conn = get_db_connection()
    if conn is None:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("SHOW TABLES LIKE %s;", (table_name,))
            return cur.fetchone() is not None
    except:
        return False
    finally:
        conn.close()

# --------- Query catalog ----------
# Each entry: { "sql": <template>, "requires": [<tables>] }
Q = {}

Q["Q1 • Players representing India"] = {
"sql": """-- Players who represent India
SELECT full_name, playing_role, batting_style, bowling_style
FROM players
WHERE country = 'India'
ORDER BY full_name;""",
"requires": ["players"]
}

Q["Q2 • Matches in last 30 days (desc)"] = {
"sql": """-- If you have 'matches' with a DATE/DATETIME column:
SELECT m.match_desc AS match_description,
       t1.team_name AS team1,
       t2.team_name AS team2,
       CONCAT(v.venue_name, ' (', v.city, ')') AS venue,
       m.match_date
FROM matches m
JOIN teams_dim t1 ON t1.team_id = m.team1_id
JOIN teams_dim t2 ON t2.team_id = m.team2_id
JOIN venues v ON v.venue_id = m.venue_id
WHERE m.match_date >= (CURRENT_DATE - INTERVAL 30 DAY)
ORDER BY m.match_date DESC;

/* If you only have 'live_matches' (match_date as VARCHAR):
SELECT series_name AS match_description, NULL AS team1, NULL AS team2,
       NULL AS venue, match_date
FROM live_matches
-- Convert or filter dates as needed
ORDER BY match_date DESC;
*/""",
"requires": ["matches","teams_dim","venues"]
}

Q["Q3 • Top 10 ODI run scorers"] = {
"sql": """SELECT p.full_name AS player,
       s.runs AS total_runs,
       s.batting_average,
       s.hundreds AS centuries
FROM player_stats_format s
JOIN players p ON p.player_id = s.player_id
WHERE s.format = 'ODI'
ORDER BY s.runs DESC
LIMIT 10;""",
"requires": ["player_stats_format","players"]
}

Q["Q4 • Venues capacity > 50,000"] = {
"sql": """SELECT venue_name, city, country, capacity
FROM venues
WHERE capacity > 50000
ORDER BY capacity DESC;""",
"requires": ["venues"]
}

Q["Q5 • Matches won by each team"] = {
"sql": """SELECT t.team_name,
       COUNT(*) AS total_wins
FROM matches m
JOIN teams_dim t ON t.team_id = m.winner_team_id
WHERE m.status = 'Completed'
GROUP BY t.team_name
ORDER BY total_wins DESC;""",
"requires": ["matches","teams_dim"]
}

Q["Q6 • Players per playing role"] = {
"sql": """SELECT playing_role, COUNT(*) AS player_count
FROM players
GROUP BY playing_role
ORDER BY player_count DESC;""",
"requires": ["players"]
}

Q["Q7 • Highest individual score per format"] = {
"sql": """-- Assuming innings_batting has per-innings player scores
SELECT ib.format, MAX(ib.runs) AS highest_score
FROM innings_batting ib
GROUP BY ib.format
ORDER BY FIELD(ib.format,'Test','ODI','T20I'), ib.format;""",
"requires": ["innings_batting"]
}

Q["Q8 • Series started in 2024"] = {
"sql": """SELECT series_name, host_country, match_type, start_date, total_matches
FROM series
WHERE YEAR(start_date) = 2024
ORDER BY start_date;""",
"requires": ["series"]
}

Q["Q9 • All-rounders >1000 runs & >50 wickets"] = {
"sql": """SELECT p.full_name, f.format, f.runs AS total_runs, b.wickets AS total_wickets
FROM players p
JOIN player_stats_format f ON f.player_id = p.player_id
JOIN bowling_stats_format b ON b.player_id = p.player_id AND b.format = f.format
WHERE f.runs > 1000 AND b.wickets > 50
  AND p.playing_role = 'All-rounder'
ORDER BY f.runs DESC, b.wickets DESC;""",
"requires": ["players","player_stats_format","bowling_stats_format"]
}

Q["Q10 • Last 20 completed matches (details)"] = {
"sql": """SELECT m.match_desc,
       t1.team_name AS team1, t2.team_name AS team2,
       tw.team_name AS winner,
       m.victory_margin, m.victory_type,
       v.venue_name
FROM matches m
JOIN teams_dim t1 ON t1.team_id = m.team1_id
JOIN teams_dim t2 ON t2.team_id = m.team2_id
LEFT JOIN teams_dim tw ON tw.team_id = m.winner_team_id
JOIN venues v ON v.venue_id = m.venue_id
WHERE m.status = 'Completed'
ORDER BY m.match_date DESC
LIMIT 20;""",
"requires": ["matches","teams_dim","venues"]
}

Q["Q11 • Player performance across formats"] = {
"sql": """SELECT p.full_name,
       SUM(CASE WHEN f.format='Test' THEN f.runs ELSE 0 END) AS test_runs,
       SUM(CASE WHEN f.format='ODI'  THEN f.runs ELSE 0 END) AS odi_runs,
       SUM(CASE WHEN f.format='T20I' THEN f.runs ELSE 0 END) AS t20i_runs,
       ROUND(AVG(f.batting_average),2) AS overall_batting_avg
FROM players p
JOIN player_stats_format f ON f.player_id = p.player_id
GROUP BY p.full_name
HAVING (SUM(CASE WHEN f.format='Test' THEN 1 ELSE 0 END)
      + SUM(CASE WHEN f.format='ODI'  THEN 1 ELSE 0 END)
      + SUM(CASE WHEN f.format='T20I' THEN 1 ELSE 0 END)) >= 2
ORDER BY p.full_name;""",
"requires": ["players","player_stats_format"]
}

Q["Q12 • Home vs away team wins"] = {
"sql": """-- Home if venue country == team country
SELECT t.team_name,
       SUM(CASE WHEN v.country = t.country AND m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS home_wins,
       SUM(CASE WHEN v.country <> t.country AND m.winner_team_id = t.team_id THEN 1 ELSE 0 END) AS away_wins
FROM matches m
JOIN venues v ON v.venue_id = m.venue_id
JOIN teams_dim t ON t.team_id IN (m.team1_id, m.team2_id)
WHERE m.status = 'Completed'
GROUP BY t.team_name
ORDER BY (home_wins + away_wins) DESC;""",
"requires": ["matches","venues","teams_dim"]
}

Q["Q13 • Partnerships ≥ 100 (consecutive batters)"] = {
"sql": """-- partnerships table holds combined runs for striker/non_striker
SELECT CONCAT(p1.full_name,' & ',p2.full_name) AS partnership,
       pr.runs AS partnership_runs,
       pr.innings_number
FROM partnerships pr
JOIN players p1 ON p1.player_id = pr.striker_id
JOIN players p2 ON p2.player_id = pr.non_striker_id
WHERE ABS(p1.batting_position - p2.batting_position) = 1
  AND pr.runs >= 100
ORDER BY pr.runs DESC;""",
"requires": ["partnerships","players"]
}

Q["Q14 • Bowling at venues (≥3 matches, ≥4 overs)"] = {
"sql": """SELECT p.full_name, v.venue_name,
       ROUND(SUM(b.runs_conceded)/SUM(b.overs),2) AS avg_economy,
       SUM(b.wickets) AS total_wickets,
       COUNT(DISTINCT b.match_id) AS matches_played
FROM innings_bowling b
JOIN players p ON p.player_id = b.player_id
JOIN matches m ON m.match_id = b.match_id
JOIN venues v ON v.venue_id = m.venue_id
WHERE b.overs >= 4
GROUP BY p.full_name, v.venue_name
HAVING COUNT(DISTINCT b.match_id) >= 3
ORDER BY avg_economy ASC, total_wickets DESC;""",
"requires": ["innings_bowling","players","matches","venues"]
}

Q["Q15 • Performers in close matches"] = {
"sql": """-- Close: decided by <50 runs OR <5 wickets
WITH close_matches AS (
  SELECT m.*
  FROM matches m
  WHERE (m.victory_type='runs' AND m.victory_margin < 50)
     OR (m.victory_type='wickets' AND m.victory_margin < 5)
     AND m.status='Completed'
),
batting_in_close AS (
  SELECT ib.match_id, ib.player_id, ib.runs
  FROM innings_batting ib
  JOIN close_matches cm ON cm.match_id = ib.match_id
)
SELECT p.full_name,
       ROUND(AVG(bc.runs),2) AS avg_runs_close,
       COUNT(*) AS close_matches_played,
       SUM(CASE WHEN m.winner_team_id = it.team_id THEN 1 ELSE 0 END) AS team_wins_when_batted
FROM batting_in_close bc
JOIN players p ON p.player_id = bc.player_id
JOIN innings_teams it ON it.match_id = bc.match_id AND it.player_id = bc.player_id
JOIN matches m ON m.match_id = bc.match_id
GROUP BY p.full_name
ORDER BY avg_runs_close DESC, team_wins_when_batted DESC;""",
"requires": ["matches","innings_batting","innings_teams","players"]
}

Q["Q16 • Yearly batting since 2020 (≥5 matches/yr)"] = {
"sql": """SELECT p.full_name,
       YEAR(m.match_date) AS year,
       ROUND(AVG(ib.runs),2) AS avg_runs_per_match,
       ROUND(AVG(ib.strike_rate),2) AS avg_sr
FROM innings_batting ib
JOIN players p ON p.player_id = ib.player_id
JOIN matches m ON m.match_id = ib.match_id
WHERE m.match_date >= '2020-01-01'
GROUP BY p.full_name, YEAR(m.match_date)
HAVING COUNT(DISTINCT m.match_id) >= 5
ORDER BY p.full_name, year;""",
"requires": ["innings_batting","players","matches"]
}

Q["Q17 • Toss win → match win % by decision"] = {
"sql": """SELECT toss_decision,
       ROUND(100 * SUM(CASE WHEN winner_team_id = toss_winner_team_id THEN 1 ELSE 0 END) / COUNT(*), 2)
         AS pct_won_after_winning_toss
FROM matches
WHERE status='Completed'
GROUP BY toss_decision
ORDER BY pct_won_after_winning_toss DESC;""",
"requires": ["matches"]
}

Q["Q18 • Most economical bowlers (ODI/T20, min 10 matches, ≥2 overs/mt avg)"] = {
"sql": """WITH bowl_counts AS (
  SELECT b.player_id, b.format,
         COUNT(DISTINCT b.match_id) AS matches_bowled,
         SUM(b.overs) AS overs_total,
         SUM(b.runs_conceded) AS runs_total,
         SUM(b.wickets) AS wickets_total
  FROM innings_bowling b
  WHERE b.format IN ('ODI','T20I')
  GROUP BY b.player_id, b.format
)
SELECT p.full_name, bc.format,
       ROUND(bc.runs_total / bc.overs_total, 2) AS economy_rate,
       bc.wickets_total AS total_wickets,
       bc.matches_bowled
FROM bowl_counts bc
JOIN players p ON p.player_id = bc.player_id
WHERE bc.matches_bowled >= 10
  AND (bc.overs_total / bc.matches_bowled) >= 2
ORDER BY economy_rate ASC, total_wickets DESC;""",
"requires": ["innings_bowling","players"]
}

Q["Q19 • Consistency: mean & stddev of runs (since 2022)"] = {
"sql": """SELECT p.full_name,
       ROUND(AVG(ib.runs),2) AS avg_runs,
       ROUND(STDDEV_SAMP(ib.runs),2) AS stddev_runs,
       COUNT(*) AS inns_count
FROM innings_batting ib
JOIN players p ON p.player_id = ib.player_id
JOIN matches m ON m.match_id = ib.match_id
WHERE m.match_date >= '2022-01-01'
  AND ib.balls_faced >= 10
GROUP BY p.full_name
HAVING inns_count >= 1
ORDER BY stddev_runs ASC, avg_runs DESC;""",
"requires": ["innings_batting","players","matches"]
}

Q["Q20 • Matches per format & batting avg (players with ≥20 total)"] = {
"sql": """SELECT p.full_name,
       SUM(CASE WHEN f.format='Test' THEN f.matches ELSE 0 END) AS test_matches,
       SUM(CASE WHEN f.format='ODI'  THEN f.matches ELSE 0 END) AS odi_matches,
       SUM(CASE WHEN f.format='T20I' THEN f.matches ELSE 0 END) AS t20i_matches,
       ROUND(AVG(CASE WHEN f.matches>0 THEN f.batting_average END),2) AS avg_bat_avg
FROM players p
JOIN player_stats_format f ON f.player_id = p.player_id
GROUP BY p.full_name
HAVING (test_matches + odi_matches + t20i_matches) >= 20
ORDER BY (test_matches + odi_matches + t20i_matches) DESC;""",
"requires": ["players","player_stats_format"]
}

Q["Q21 • Composite player ranking (per format)"] = {
"sql": """-- Uses player_stats_format (batting) + bowling_stats_format + fielding_stats_format
WITH points AS (
  SELECT p.player_id, p.full_name, f.format,
         -- Batting points
         ((f.runs * 0.01) + (f.batting_average * 0.5) + (f.strike_rate * 0.3)) AS batting_pts,
         -- Bowling points
         ((b.wickets * 2)
          + (50 - b.bowling_average) * 0.5
          + ((6 - b.economy_rate) * 2)) AS bowling_pts,
         -- Fielding points
         (fd.catches + (fd.stumpings * 2)) AS fielding_pts
  FROM players p
  LEFT JOIN player_stats_format f ON f.player_id = p.player_id
  LEFT JOIN bowling_stats_format b ON b.player_id = p.player_id AND b.format = f.format
  LEFT JOIN fielding_stats_format fd ON fd.player_id = p.player_id AND fd.format = f.format
)
SELECT full_name, format,
       ROUND(batting_pts + bowling_pts + fielding_pts, 2) AS total_points,
       ROUND(batting_pts,2) AS batting_pts,
       ROUND(bowling_pts,2) AS bowling_pts,
       ROUND(fielding_pts,2) AS fielding_pts
FROM points
ORDER BY format, total_points DESC
LIMIT 100;""",
"requires": ["players","player_stats_format","bowling_stats_format","fielding_stats_format"]
}

Q["Q22 • Head-to-head analysis (last 3 years, ≥5 matches)"] = {
"sql": """WITH recent AS (
  SELECT *
  FROM matches
  WHERE match_date >= (CURRENT_DATE - INTERVAL 3 YEAR)
),
pairs AS (
  SELECT LEAST(team1_id, team2_id) AS team_a,
         GREATEST(team1_id, team2_id) AS team_b,
         COUNT(*) AS games
  FROM recent
  GROUP BY LEAST(team1_id, team2_id), GREATEST(team1_id, team2_id)
  HAVING COUNT(*) >= 5
),
agg AS (
  SELECT p.team_a, p.team_b,
         SUM(CASE WHEN m.winner_team_id = p.team_a THEN 1 ELSE 0 END) AS wins_a,
         SUM(CASE WHEN m.winner_team_id = p.team_b THEN 1 ELSE 0 END) AS wins_b,
         AVG(CASE WHEN m.winner_team_id = p.team_a AND m.victory_type='runs' THEN m.victory_margin END) AS avg_margin_a_runs,
         AVG(CASE WHEN m.winner_team_id = p.team_b AND m.victory_type='runs' THEN m.victory_margin END) AS avg_margin_b_runs
  FROM pairs p
  JOIN recent m ON (LEAST(m.team1_id,m.team2_id)=p.team_a AND GREATEST(m.team1_id,m.team2_id)=p.team_b)
  GROUP BY p.team_a, p.team_b
)
SELECT ta.team_name AS team_a, tb.team_name AS team_b,
       games, wins_a, wins_b,
       ROUND(100 * wins_a/games,2) AS win_pct_a,
       ROUND(100 * wins_b/games,2) AS win_pct_b,
       avg_margin_a_runs, avg_margin_b_runs
FROM agg
JOIN pairs USING (team_a, team_b)
JOIN teams_dim ta ON ta.team_id = team_a
JOIN teams_dim tb ON tb.team_id = team_b
ORDER BY games DESC, win_pct_a DESC;""",
"requires": ["matches","teams_dim"]
}

Q["Q23 • Recent form (last 10 inns)"] = {
"sql": """WITH last10 AS (
  SELECT ib.player_id, ib.runs, ib.strike_rate,
         ROW_NUMBER() OVER (PARTITION BY ib.player_id ORDER BY m.match_date DESC) AS rn
  FROM innings_batting ib
  JOIN matches m ON m.match_id = ib.match_id
)
SELECT p.full_name,
       ROUND(AVG(CASE WHEN rn <= 5  THEN runs END),2) AS avg_last5,
       ROUND(AVG(CASE WHEN rn <= 10 THEN runs END),2) AS avg_last10,
       ROUND(AVG(CASE WHEN rn <= 10 THEN strike_rate END),2) AS sr_trend,
       SUM(CASE WHEN rn <= 10 AND runs >= 50 THEN 1 ELSE 0 END) AS fifties_last10,
       ROUND(STDDEV_SAMP(CASE WHEN rn <= 10 THEN runs END),2) AS consistency_stddev
FROM last10 l
JOIN players p ON p.player_id = l.player_id
GROUP BY p.full_name
ORDER BY avg_last10 DESC, consistency_stddev ASC;""",
"requires": ["innings_batting","matches","players"]
}

Q["Q24 • Best batting partnerships (≥5)"] = {
"sql": """WITH qualified AS (
  SELECT pr.striker_id, pr.non_striker_id,
         COUNT(*) AS partnerships,
         AVG(pr.runs) AS avg_runs,
         SUM(CASE WHEN pr.runs >= 50 THEN 1 ELSE 0 END) AS over_50_count,
         MAX(pr.runs) AS highest
  FROM partnerships pr
  WHERE ABS(pr.striker_pos - pr.non_striker_pos) = 1
  GROUP BY pr.striker_id, pr.non_striker_id
  HAVING partnerships >= 5
)
SELECT CONCAT(p1.full_name, ' & ', p2.full_name) AS pair,
       partnerships, ROUND(avg_runs,2) AS avg_runs,
       over_50_count, highest,
       ROUND(100.0 * over_50_count/partnerships,2) AS success_rate_pct
FROM qualified q
JOIN players p1 ON p1.player_id = q.striker_id
JOIN players p2 ON p2.player_id = q.non_striker_id
ORDER BY success_rate_pct DESC, avg_runs DESC, partnerships DESC
LIMIT 50;""",
"requires": ["partnerships","players"]
}

Q["Q25 • Quarterly performance & trajectory (≥6 quarters)"] = {
"sql": """WITH qb AS (
  SELECT ib.player_id,
         CONCAT(YEAR(m.match_date), '-Q', QUARTER(m.match_date)) AS yr_qtr,
         AVG(ib.runs) AS avg_runs_qtr,
         AVG(ib.strike_rate) AS avg_sr_qtr,
         COUNT(DISTINCT m.match_id) AS matches_qtr
  FROM innings_batting ib
  JOIN matches m ON m.match_id = ib.match_id
  GROUP BY ib.player_id, YEAR(m.match_date), QUARTER(m.match_date)
  HAVING matches_qtr >= 3
),
changes AS (
  SELECT qb.*, 
         LAG(avg_runs_qtr) OVER (PARTITION BY player_id ORDER BY yr_qtr) AS prev_runs,
         LAG(avg_sr_qtr)   OVER (PARTITION BY player_id ORDER BY yr_qtr) AS prev_sr
  FROM qb
),
qualified AS (
  SELECT player_id
  FROM qb
  GROUP BY player_id
  HAVING COUNT(*) >= 6
)
SELECT p.full_name, c.yr_qtr, 
       ROUND(c.avg_runs_qtr,2) AS avg_runs_qtr,
       ROUND(c.avg_sr_qtr,2)   AS avg_sr_qtr,
       CASE 
         WHEN c.prev_runs IS NULL THEN 'N/A'
         WHEN c.avg_runs_qtr > c.prev_runs AND c.avg_sr_qtr > c.prev_sr THEN 'Improving'
         WHEN c.avg_runs_qtr < c.prev_runs AND c.avg_sr_qtr < c.prev_sr THEN 'Declining'
         ELSE 'Stable'
       END AS trajectory
FROM changes c
JOIN qualified q USING (player_id)
JOIN players p ON p.player_id = c.player_id
ORDER BY p.full_name, c.yr_qtr;""",
"requires": ["innings_batting","matches","players"]
}

# Optional: add quick “simple” queries for your existing minimal tables
Q["(Simple) All match_details"] = {
"sql": "SELECT * FROM match_details ORDER BY match_id DESC LIMIT 100;",
"requires": ["match_details"]
}
Q["(Simple) Teams by match"] = {
"sql": "SELECT * FROM teams ORDER BY match_id DESC LIMIT 100;",
"requires": ["teams"]
}
Q["(Simple) Innings scores"] = {
"sql": "SELECT * FROM innings_scores ORDER BY match_id DESC, team_id, innings_number;",
"requires": ["innings_scores"]
}
Q["(Simple) Live matches (if any)"] = {
"sql": "SELECT * FROM live_matches ORDER BY match_date DESC LIMIT 100;",
"requires": ["live_matches"]
}

# --------- UI ----------
col1, col2 = st.columns([2,1])
with col1:
    selected = st.selectbox("📋 Select a question", list(Q.keys()), index=0)
with col2:
    st.write("")
    st.write("")
    st.caption("Edit SQL before running if your schema differs.")

requires = Q[selected]["requires"]
missing = [t for t in requires if not table_exists(t)]
if missing:
    st.warning(f"Heads up: your DB seems to be missing table(s): {', '.join(missing)}. "
               "You can still edit the SQL below to fit your schema.")

sql_text = st.text_area("🧾 SQL", Q[selected]["sql"], height=260, key="sqlbox")

row1, row2, row3 = st.columns([1,1,3])
with row1:
    run = st.button("▶ Run")
with row2:
    show_only_sql = st.checkbox("Show only SQL (don’t run)", value=False)

st.divider()

if show_only_sql:
    st.info("Showing SQL only. Uncheck to execute.")
elif run:
    df = run_query(sql_text)
    if df.empty:
        st.info("No rows returned.")
    else:
        st.success(f"Returned {len(df)} row(s).")
        st.dataframe(df, use_container_width=True)
