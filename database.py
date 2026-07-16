import sqlite3
import os

DB_PATH = 'bot_database.db'

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            messages_count INTEGER DEFAULT 0,
            language TEXT DEFAULT 'uz',
            level TEXT DEFAULT 'B1'
        )
    ''')
    # Yangi ustunlarni qo'shish (eski bazani yangilash uchun)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN language TEXT DEFAULT "uz"')
    except:
        pass
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN level TEXT DEFAULT "B1"')
    except:
        pass
    conn.commit()
    conn.close()

def add_user(user_id: int, username: str, first_name: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO users (user_id, username, first_name)
        VALUES (?, ?, ?)
    ''', (user_id, username, first_name))
    conn.commit()
    conn.close()

def increment_message_count(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET messages_count = messages_count + 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def get_user_stats(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT messages_count FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

def set_user_pref(user_id: int, key: str, value: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    query = f'UPDATE users SET {key} = ? WHERE user_id = ?'
    cursor.execute(query, (value, user_id))
    conn.commit()
    conn.close()

def get_user_pref(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT language, level FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result if result else ("uz", "A2")
