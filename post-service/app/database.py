import os
import psycopg2
import psycopg2.extras

DATABASE_URL = os.environ["DATABASE_URL"]

def get_connection():
    return psycopg2.connect(DATABASE_URL)

def create_tables():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER,
        username TEXT,
        content TEXT,
        created_at TIMESTAMP DEFAULT NOW()
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def create_post(user_id, username, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO posts (user_id, username, content) VALUES (%s, %s, %s)",
        (user_id, username, content)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_posts(limit=10, offset=0):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute(
        "SELECT * FROM posts ORDER BY created_at DESC LIMIT %s OFFSET %s",
        (limit, offset)
    )
    posts = cursor.fetchall()
    cursor.close()
    conn.close()
    return posts

def get_post(post_id):
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM posts WHERE id=%s", (post_id,))
    post = cursor.fetchone()
    cursor.close()
    conn.close()
    return post

def update_post(post_id, content):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE posts SET content=%s WHERE id=%s", (content, post_id))
    conn.commit()
    cursor.close()
    conn.close()

def delete_post(post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE id=%s", (post_id,))
    conn.commit()
    cursor.close()
    conn.close()
