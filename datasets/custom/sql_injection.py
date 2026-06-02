# TEST FILE: SQL Injection (CWE-89)
import sqlite3

def get_user(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABLE: string concatenation in SQL
    query = "SELECT * FROM users WHERE id=" + user_id
    cursor.execute(query)
    return cursor.fetchone()

def search_users(name):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    # VULNERABLE: f-string in SQL
    cursor.execute(f"SELECT * FROM users WHERE name='{name}'")
    return cursor.fetchall()
