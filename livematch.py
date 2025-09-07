import streamlit as st
import requests
import pandas as pd
import pymysql
from db_connection import get_db_connection

# -------------------------
# Streamlit Page Config
# -------------------------
st.set_page_config(page_title="Live Matches", layout="wide")
st.title("🏏 Live Matches Dashboard (API + DB Powered)")

# -------------------------
# API Config
# -------------------------
API_URL = "https://cricbuzz-cricket.p.rapidapi.com/matches/v1/live"
HEADERS = {
    "x-rapidapi-key": "05be0855e7msh0088c5d61d942a7p11ae06jsn2eac138a9d2c",
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}

# -------------------------
# Fetch Live Matches from API
# -------------------------
@st.cache_data(ttl=60)
def fetch_live_matches():
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=10)
        if resp.status_code == 200:
            return resp.json()
        else:
            st.error(f"API Error {resp.status_code}: {resp.text}")
    except Exception as e:
        st.error(f"Error fetching API data: {e}")
    return {}

# -------------------------
# Save Data to MySQL
# -------------------------
def save_to_db(data):
    conn = get_db_connection()
    if not conn:
        st.error("❌ DB Connection failed")
        return

    try:
        with conn.cursor() as cursor:
            for match_type in data.get("typeMatches", []):
                for series in match_type.get("seriesMatches", []):
                    series_data = series.get("seriesAdWrapper", {})
                    series_id = series_data.get("seriesId")
                    series_name = series_data.get("seriesName", "")
                    for match in series_data.get("matches", []):
                        match_info = match.get("matchInfo", {})
                        match_score = match.get("matchScore", {})

                        match_id = match_info.get("matchId")
                        if not match_id:
                            continue

                        # Upsert match_details
                        cursor.execute("""
                            INSERT INTO match_details 
                            (match_id, series_id, series_name, match_descr, match_format, venue, city, status) 
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                            ON DUPLICATE KEY UPDATE
                                series_id=VALUES(series_id),
                                series_name=VALUES(series_name),
                                match_descr=VALUES(match_descr),
                                match_format=VALUES(match_format),
                                venue=VALUES(venue),
                                city=VALUES(city),
                                status=VALUES(status)
                        """, (
                            match_id,
                            series_id,
                            series_name,
                            match_info.get("matchDesc"),
                            match_info.get("matchFormat"),
                            match_info.get("venueInfo", {}).get("ground"),
                            match_info.get("venueInfo", {}).get("city"),
                            match_info.get("status")
                        ))

                        # Upsert teams
                        for team_key in ["team1", "team2"]:
                            team = match_info.get(team_key, {})
                            if team:
                                cursor.execute("""
                                    INSERT INTO teams (team_id, match_id, team_name) 
                                    VALUES (%s,%s,%s)
                                    ON DUPLICATE KEY UPDATE
                                        team_name=VALUES(team_name)
                                """, (
                                    team.get("teamId"),
                                    match_id,
                                    team.get("teamName")
                                ))

                        # Upsert innings_scores
                        for team_key in ["team1Score", "team2Score"]:
                            team_score = match_score.get(team_key, {})
                            if team_score:
                                team_info = match_info.get(team_key.replace("Score", ""), {})
                                team_id = team_info.get("teamId")
                                for innings_key, inng in team_score.items():
                                    innings_number = int(innings_key[-1]) if innings_key[-1].isdigit() else 1
                                    cursor.execute("""
                                        INSERT INTO innings_scores 
                                        (match_id, team_id, innings_number, runs, wickets, overs)
                                        VALUES (%s,%s,%s,%s,%s,%s)
                                        ON DUPLICATE KEY UPDATE
                                            runs=VALUES(runs),
                                            wickets=VALUES(wickets),
                                            overs=VALUES(overs)
                                    """, (
                                        match_id,
                                        team_id,
                                        innings_number,
                                        inng.get("runs"),
                                        inng.get("wickets"),
                                        inng.get("overs")
                                    ))
        conn.commit()
    except Exception as e:
        st.error(f"❌ Error saving to DB: {e}")
    finally:
        conn.close()

# -------------------------
# Utility: Get Data as DataFrame
# -------------------------
def get_data_as_dataframe(query, params=None):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                results = cursor.fetchall()
                columns = [desc[0] for desc in cursor.description]
                return pd.DataFrame(results, columns=columns)
        except pymysql.MySQLError as e:
            st.error(f"Database error: {e}")
            return pd.DataFrame()
        finally:
            conn.close()
    return pd.DataFrame()

# -------------------------
# Step 1: Fetch from API & Save
# -------------------------
data = fetch_live_matches()
if data:
    save_to_db(data)

# -------------------------
# Step 2: Show Matches from DB with Filters
# -------------------------
matches_df = get_data_as_dataframe(
    "SELECT match_id, series_id, series_name, match_descr, status, match_format, venue, city "
    "FROM match_details ORDER BY match_id DESC;"
)

if matches_df.empty:
    st.info("⚠️ No matches available in the database.")
else:
    # -------------------
    # Filter by Match Format
    # -------------------
    format_options = ["All"] + matches_df["match_format"].dropna().unique().tolist()
    selected_format = st.selectbox("Filter by Format", format_options)

    # Apply filter
    if selected_format != "All":
        filtered_df = matches_df[matches_df["match_format"] == selected_format]
    else:
        filtered_df = matches_df.copy()

    # Display matches
    for _, match in filtered_df.iterrows():
        expander_title = f"Match {match.match_id} - {match.match_descr} ({match.match_format})"
        with st.expander(expander_title + f" ({match.status})"):
            st.write(f"**Series:** {match.series_name} (ID: {match.series_id})")
            st.write(f"**Venue:** {match.venue}, {match.city}")

            # Teams
            teams_df = get_data_as_dataframe(
                "SELECT team_id, team_name FROM teams WHERE match_id = %s;", 
                (match.match_id,)
            )

            # Innings
            innings_df = get_data_as_dataframe(
                "SELECT team_id, innings_number, runs, wickets, overs "
                "FROM innings_scores WHERE match_id = %s;", 
                (match.match_id,)
            )

            for _, team in teams_df.iterrows():
                st.subheader(f"🏏 {team.team_name}")

                team_innings = innings_df[innings_df["team_id"] == team.team_id].copy()
                team_innings = team_innings.drop_duplicates(subset=["team_id", "innings_number"])

                if team_innings.empty:
                    st.write("_No innings data available yet._")
                else:
                    display_df = team_innings[["innings_number", "runs", "wickets", "overs"]].reset_index(drop=True)
                    st.table(display_df)
