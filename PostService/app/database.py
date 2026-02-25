# app/database.py
import sqlite3

DB_FILE = "posts.db"

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        username TEXT,
        content TEXT,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def create_post(user_id, username, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (user_id, username, content) VALUES (?, ?, ?)",
        (user_id, username, content)
    )
    conn.commit()
    conn.close()

def get_posts(limit=10, offset=0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM posts ORDER BY created_at DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    posts = cursor.fetchall()
    conn.close()
    return posts

def get_post(post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM posts WHERE id=?", (post_id,))
    post = cursor.fetchone()
    conn.close()
    return post

def update_post(post_id, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET content=? WHERE id=?", (content, post_id))
    conn.commit()
    conn.close()

def delete_post(post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id=?", (post_id,))
    conn.commit()
    conn.close()