# import pymysql

# try:
#     connection = pymysql.connect(
#         host='localhost',
#         user='root',
#         password='test01!',
#         database='august_23rd',
#         cursorclass=pymysql.cursors.DictCursor # Optional: for dictionary results
#     )
#     print("Successfully connected to the database.")

#     # You can now create a cursor and execute queries
#     with connection.cursor() as cursor:
#         cursor.execute("SELECT * FROM players")
#         results = cursor.fetchall()
#         print(results)

# except pymysql.Error as e:
#     print(f"Error connecting to MySQL: {e}")

# finally:
#     if 'connection' in locals() and connection.open:
#         connection.close()
#         print("Database connection closed.")

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