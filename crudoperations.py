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
