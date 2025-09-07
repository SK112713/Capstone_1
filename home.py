import streamlit as st
import pymysql
from db_connection import get_db_connection

# --- Page Config ---
st.set_page_config(
    page_title="Cricket Live Stats DB",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Sidebar Navigation ---
st.sidebar.title("⚡ Navigation")
pages = ["🏠 Home", "📊 View Data", "🗄️ CRUD Operations", "📈 Analytics"]
choice = st.sidebar.radio("Go to:", pages)

# --- Helper: Get DB Summary ---
def get_db_summary():
    conn = get_db_connection()
    with conn.cursor() as cursor:
        cursor.execute("SELECT COUNT(*) FROM match_details")
        match_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(*) FROM players")
        player_count = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT series_id) FROM match_details")
        series_count = cursor.fetchone()[0]

    conn.close()
    return match_count, player_count, series_count

# --- Home Page ---
if choice == "🏠 Home":
    # Logo + Title
    st.image("https://cdn-icons-png.flaticon.com/512/3003/3003935.png", width=80)  # cricket icon
    st.title("🏏 Cricket Live Stats Database")

    st.markdown("""
    Welcome to the **Cricket Live Stats Management System** 🎉  

    This project helps you:  
    - Store and manage live match & player data from APIs  
    - Perform **CRUD operations** on MySQL tables  
    - Explore and visualize match details with interactive dashboards  

    ---
    """)

    # --- Database Summary Cards ---
    st.subheader("📌 Database Overview")

    match_count, player_count, series_count = get_db_summary()

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Matches", match_count)
    with col2:
        st.metric("Total Players", player_count)
    with col3:
        st.metric("Total Series", series_count)

    st.markdown("---")

    # --- Quick Navigation Buttons ---
    st.subheader("🚀 Quick Navigation")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📊 View Data"):
            st.session_state["page"] = "📊 View Data"

    with col2:
        if st.button("🗄️ CRUD Operations"):
            st.session_state["page"] = "🗄️ CRUD Operations"

    with col3:
        if st.button("📈 Analytics"):
            st.session_state["page"] = "📈 Analytics"

    # Handle button navigation
    if "page" in st.session_state:
        choice = st.session_state["page"]

# --- Placeholder Pages ---
elif choice == "📊 View Data":
    st.title("📊 View Data")
    st.info("This page will show database tables (link to your `Read` page).")

elif choice == "🗄️ CRUD Operations":
    st.title("🗄️ CRUD Operations")
    st.info("This page will let you Create, Read, Update, Delete records (link to CRUD app).")

elif choice == "📈 Analytics":
    st.title("📈 Analytics")
    st.info("This page will show charts and insights from your match data.")
