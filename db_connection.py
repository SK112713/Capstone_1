import pymysql
import streamlit as st

def get_db_connection():
    """Establishes and returns a PyMySQL connection."""
    try:
        conn = pymysql.connect(
            host="localhost",           # Replace with your MySQL host
            user="root",           # Replace with your MySQL username
            password="test01!",   # Replace with your MySQL password
            database="cricbuzz_database"
        )
        return conn
    except pymysql.MySQLError as e:
        st.error(f"Error connecting to MySQL: {e}")
        return None
