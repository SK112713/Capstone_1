# import streamlit as st
# import pandas as pd
# import pymysql
# from db_connection import get_db_connection  # Your separate DB connection

# st.title("⚡ Cricbuzz Players - CRUD Operations")

# # -------------------------
# # Helper: Get DataFrame from query
# # -------------------------
# def get_data_as_dataframe(query):
#     conn = get_db_connection()
#     if conn:
#         try:
#             with conn.cursor() as cursor:
#                 cursor.execute(query)
#                 results = cursor.fetchall()
#                 columns = [desc[0] for desc in cursor.description]
#                 return pd.DataFrame(results, columns=columns)
#         except pymysql.MySQLError as e:
#             st.error(f"Database error: {e}")
#             return pd.DataFrame()
#         finally:
#             conn.close()
#     return pd.DataFrame()

# # -------------------------
# # CREATE: Insert Player
# # -------------------------
# def insert_player(player_id, name, team, batting, bowling, country):
#     conn = get_db_connection()
#     try:
#         with conn.cursor() as cursor:
#             sql = """
#                 INSERT INTO players (player_id, full_name, team_name, batting_style, bowling_style, country)
#                 VALUES (%s, %s, %s, %s, %s, %s)
#             """
#             cursor.execute(sql, (player_id, name, team, batting, bowling, country))
#             conn.commit()
#             st.success(f"✅ Player {name} inserted successfully!")
#     except pymysql.MySQLError as e:
#         st.error(f"❌ Error inserting player: {e}")
#     finally:
#         conn.close()

# # -------------------------
# # UPDATE: Update Player
# # -------------------------
# def update_player(player_id, name, team, batting, bowling, country):
#     conn = get_db_connection()
#     try:
#         with conn.cursor() as cursor:
#             sql = """
#                 UPDATE players
#                 SET full_name=%s, team_name=%s, batting_style=%s, bowling_style=%s, country=%s
#                 WHERE player_id=%s
#             """
#             cursor.execute(sql, (name, team, batting, bowling, country, player_id))
#             conn.commit()
#             st.success(f"✅ Player {name} updated successfully!")
#     except pymysql.MySQLError as e:
#         st.error(f"❌ Error updating player: {e}")
#     finally:
#         conn.close()

# # -------------------------
# # DELETE: Delete Player
# # -------------------------
# def delete_player(player_id):
#     conn = get_db_connection()
#     try:
#         with conn.cursor() as cursor:
#             sql = "DELETE FROM players WHERE player_id=%s"
#             cursor.execute(sql, (player_id,))
#             conn.commit()
#             st.success(f"🗑️ Player {player_id} deleted successfully!")
#     except pymysql.MySQLError as e:
#         st.error(f"❌ Error deleting player: {e}")
#     finally:
#         conn.close()

# # -------------------------
# # Streamlit UI
# # -------------------------
# operation = st.sidebar.selectbox("Select Operation", ["Create", "Read", "Update", "Delete"])

# if operation == "Create":
#     st.subheader("➕ Add New Player")
#     player_id = st.number_input("Player ID", min_value=1, step=1)
#     name = st.text_input("Full Name")
#     team = st.text_input("Team Name")
#     batting = st.text_input("Batting Style")
#     bowling = st.text_input("Bowling Style")
#     country = st.text_input("Country")

#     if st.button("Insert Player"):
#         insert_player(player_id, name, team, batting, bowling, country)

# elif operation == "Read":
#     st.subheader("📖 Players List")
#     df = get_data_as_dataframe("SELECT * FROM players;")
#     if not df.empty:
#         st.dataframe(df, use_container_width=True)
#     else:
#         st.info("No players found.")

# elif operation == "Update":
#     st.subheader("✏️ Update Player")
#     df = get_data_as_dataframe("SELECT * FROM players;")
#     if not df.empty:
#         selected_id = st.selectbox("Select Player ID", df["player_id"].tolist())
#         player_row = df[df["player_id"] == selected_id].iloc[0]

#         name = st.text_input("Full Name", value=player_row["full_name"])
#         team = st.text_input("Team Name", value=player_row["team_name"])
#         batting = st.text_input("Batting Style", value=player_row["batting_style"])
#         bowling = st.text_input("Bowling Style", value=player_row["bowling_style"])
#         country = st.text_input("Country", value=player_row["country"])

#         if st.button("Update Player"):
#             update_player(selected_id, name, team, batting, bowling, country)
#     else:
#         st.info("No players available to update.")

# elif operation == "Delete":
#     st.subheader("🗑️ Delete Player")
#     df = get_data_as_dataframe("SELECT * FROM players;")
#     if not df.empty:
#         selected_id = st.selectbox("Select Player ID to Delete", df["player_id"].tolist())
#         if st.button("Delete Player"):
#             delete_player(selected_id)
#     else:
#         st.info("No players available to delete.")


import streamlit as st
import pandas as pd
import pymysql
from db_connection import get_db_connection

st.set_page_config(page_title="Players CRUD App", layout="wide")
st.title("🏏 Players Table CRUD Operations")

# --- Utility function ---
def run_query(query, params=None, fetch=False):
    conn = get_db_connection()
    result = None
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute(query, params or ())
                if fetch:
                    result = cursor.fetchall()
                    cols = [desc[0] for desc in cursor.description]
                    result = pd.DataFrame(result, columns=cols)
                conn.commit()
        except pymysql.MySQLError as e:
            st.error(f"Database error: {e}")
        finally:
            conn.close()
    return result

# We are restricting to only players table
selected_table = "players"

# --- Step 1: Select CRUD operation ---
operation = st.radio("⚙️ Select operation:", ["Read", "Create", "Update", "Delete"])

# --- Step 2: Perform operation ---
if operation == "Read":
    st.subheader("📖 Read from players")
    df = run_query("SELECT * FROM players LIMIT 50;", fetch=True)
    if df is not None and not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No records found in `players`.")

elif operation == "Create":
    st.subheader("➕ Insert into players")
    player_id = st.text_input("Player ID")
    player_name = st.text_input("Player Name")
    batting_style = st.text_input("Batting Style")
    bowling_style = st.text_input("Bowling Style")

    if st.button("Insert Record"):
        run_query(
            """INSERT INTO players (player_id, player_name, batting_style, bowling_style) 
               VALUES (%s, %s, %s, %s);""",
            (player_id, player_name, batting_style, bowling_style)
        )
        st.success("✅ Player record inserted successfully!")

elif operation == "Update":
    st.subheader("✏️ Update players")
    record_id = st.text_input("Enter Player ID to update")
    new_name = st.text_input("New Player Name")

    if st.button("Update Record"):
        run_query(
            "UPDATE players SET player_name=%s WHERE player_id=%s;",
            (new_name, record_id)
        )
        st.success("✅ Player record updated successfully!")

elif operation == "Delete":
    st.subheader("🗑️ Delete from players")
    record_id = st.text_input("Enter Player ID to delete")

    if st.button("Delete Record"):
        run_query(
            "DELETE FROM players WHERE player_id=%s;",
            (record_id,)
        )
        st.success("✅ Player record deleted successfully!")
