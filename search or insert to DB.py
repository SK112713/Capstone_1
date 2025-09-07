# import streamlit as st
# import pandas as pd
# import requests
# import pymysql
# from db_connection import get_db_connection  # your DB connection function

# # RapidAPI Config
# API_URL = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/search"
# API_KEY = "05be0855e7msh0088c5d61d942a7p11ae06jsn2eac138a9d2c"  # replace with your key

# headers = {
#     "x-rapidapi-key": API_KEY,
#     "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
# }

# st.title("Cricbuzz Players - CRUD with API")

# # 🔍 Search Player Section
# player_name_input = st.text_input("Enter Player Name:")

# def fetch_player_details(player_name):
#     """Fetch player details from Cricbuzz API"""
#     try:
#         resp = requests.get(API_URL, headers=headers, params={"plrN": player_name})
#         if resp.status_code == 200:
#             data = resp.json()
#             if "player" in data and len(data["player"]) > 0:
#                 return data["player"][0]  # first matching player
#             else:
#                 st.warning("No player found with that name.")
#         else:
#             st.error(f"API Error {resp.status_code}: {resp.text}")
#     except Exception as e:
#         st.error(f"Error fetching player data: {e}")
#     return None

# def insert_player_into_db(player):
#     """Insert player details into DB"""
#     conn = get_db_connection()
#     try:
#         with conn.cursor() as cursor:
#             sql = """
#             INSERT INTO players (player_id, full_name, team_name)
#             VALUES (%s, %s, %s)
#             ON DUPLICATE KEY UPDATE 
#                 full_name=VALUES(full_name),
#                 team_name=VALUES(team_name);
#             """
#             cursor.execute(sql, (
#                 player.get("id"),
#                 player.get("name"),
#                 player.get("teamName")
#             ))
#             conn.commit()
#             st.success(f"✅ Player {player.get('name')} saved successfully!")
#     except Exception as e:
#         st.error(f"Error inserting player: {e}")
#     finally:
#         conn.close()

# # CRUD Options
# crud_action = st.selectbox("Choose Operation", ["Read All Players", "Search Player", "Insert Player", "Delete Player"])

# if crud_action == "Read All Players":
#     conn = get_db_connection()
#     try:
#         df = pd.read_sql("SELECT * FROM players;", conn)
#         st.dataframe(df, use_container_width=True)
#     except Exception as e:
#         st.error(f"Error: {e}")
#     finally:
#         conn.close()

# elif crud_action == "Search Player":
#     if st.button("Fetch Player"):
#         if player_name_input:
#             player = fetch_player_details(player_name_input)
#             if player:
#                 st.write("🔍 Player Found:")
#                 st.json(player)
#         else:
#             st.warning("Enter a Player Name first.")

# elif crud_action == "Insert Player":
#     if st.button("Fetch & Insert Player"):
#         if player_name_input:
#             player = fetch_player_details(player_name_input)
#             if player:
#                 st.write("📥 Player Details Ready to Insert:")
#                 st.json(player)
#                 insert_player_into_db(player)
#         else:
#             st.warning("Enter a Player Name first.")

# elif crud_action == "Delete Player":
#     del_id = st.text_input("Enter Player ID to Delete:")
#     if st.button("Delete Player"):
#         if del_id:
#             conn = get_db_connection()
#             try:
#                 with conn.cursor() as cursor:
#                     cursor.execute("DELETE FROM players WHERE player_id=%s", (del_id,))
#                     conn.commit()
#                     st.success(f"🗑️ Player {del_id} deleted successfully.")
#             except Exception as e:
#                 st.error(f"Error: {e}")
#             finally:
#                 conn.close()
#         else:
#             st.warning("Enter Player ID to delete.")

import streamlit as st
import pandas as pd
import requests
import pymysql
from db_connection import get_db_connection  # your DB connection function

# RapidAPI Config
API_URL = "https://cricbuzz-cricket.p.rapidapi.com/stats/v1/player/search"
API_KEY = "05be0855e7msh0088c5d61d942a7p11ae06jsn2eac138a9d2c"  # replace with your actual RapidAPI key

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "cricbuzz-cricket.p.rapidapi.com"
}

st.title("⚡ Cricbuzz Players - Search & Insert (API)")

# ------------------ FUNCTIONS ------------------
def fetch_players(player_name, limit=3):
    """Fetch limited players from Cricbuzz API"""
    try:
        resp = requests.get(API_URL, headers=headers, params={"plrN": player_name})
        if resp.status_code == 200:
            data = resp.json()
            if "player" in data and len(data["player"]) > 0:
                return data["player"][:limit]  # return top 'limit' players
            else:
                st.warning("No players found with that name.")
        else:
            st.error(f"API Error {resp.status_code}: {resp.text}")
    except Exception as e:
        st.error(f"Error fetching player data: {e}")
    return []

def insert_players_into_db(players):
    """Insert multiple players into DB"""
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
            INSERT INTO players (player_id, full_name, team_name)
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE 
                full_name=VALUES(full_name),
                team_name=VALUES(team_name);
            """
            for p in players:
                cursor.execute(sql, (
                    p.get("id"),
                    p.get("name"),
                    p.get("teamName", "N/A")
                ))
            conn.commit()
            st.success(f"✅ Inserted/Updated {len(players)} players successfully!")
    except Exception as e:
        st.error(f"Error inserting players: {e}")
    finally:
        conn.close()

# ------------------ UI ------------------
crud_action = st.selectbox("Choose Operation", ["Search Players (API)", "Insert Players (from API)"])

# 🔍 SEARCH PLAYERS (API)
if crud_action == "Search Players (API)":
    player_name_input = st.text_input("Enter Player Name:")
    if st.button("Fetch Players"):
        if player_name_input:
            players = fetch_players(player_name_input, limit=3)
            if players:
                df = pd.DataFrame(players)[["id", "name", "teamName"]]
                st.dataframe(df, use_container_width=True)
        else:
            st.warning("Enter a Player Name first.")

# ➕ INSERT PLAYERS (API → DB)
elif crud_action == "Insert Players (from API)":
    player_name_input = st.text_input("Enter Player Name to Insert:")
    if st.button("Fetch & Insert Players"):
        if player_name_input:
            players = fetch_players(player_name_input, limit=3)
            if players:
                df = pd.DataFrame(players)[["id", "name", "teamName"]]
                st.dataframe(df, use_container_width=True)
                insert_players_into_db(players)
        else:
            st.warning("Enter a Player Name first.")

