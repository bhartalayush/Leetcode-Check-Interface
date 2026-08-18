import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dsa_lock.db")

def get_connection():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)
    
    # 2. Daily Stats Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS daily_stats (
        date TEXT PRIMARY KEY, -- YYYY-MM-DD
        target_points REAL,
        completed_points REAL,
        debt REAL,
        streak INTEGER,
        longest_streak INTEGER
    )
    """)
    
    # 3. Solved Problems Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS problems (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        url TEXT,
        difficulty TEXT, -- Easy, Medium, Hard
        date_solved TEXT, -- YYYY-MM-DD
        points REAL,
        verified INTEGER DEFAULT 0 -- 0 = Manual, 1 = Verified
    )
    """)
    
    # 4. Planner Queue Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS planner (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        url TEXT,
        difficulty TEXT,
        added_date TEXT,
        status TEXT DEFAULT 'pending' -- pending, solved
    )
    """)
    
    # 5. Holidays Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS holidays (
        date TEXT PRIMARY KEY -- YYYY-MM-DD
    )
    """)
    
    # Insert default settings if not exists
    defaults = {
        "daily_target": "2.0",
        "easy_points": "1.0",
        "medium_points": "2.0",
        "hard_points": "4.0",
        "max_debt": "8.0",
        "blocklist_apps": "steam.exe,discord.exe,spotify.exe,EpicGamesLauncher.exe,riotclientservices.exe",
        "blocklist_domains": "youtube.com,instagram.com,netflix.com,twitch.tv",
        "emergency_pin": "1234",
        "start_with_windows": "False",
        "emergency_unlocked": "False",
        "emergency_unlock_time": "0", # Stores timestamp of unlock
        "trial_lock_active": "False",
        "leetcode_username": "ritTC1wAZ9",
        "app_suspended": "False",
        "app_suspension_time": "0"
    }
    
    for k, v in defaults.items():
        cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (k, v))
        
    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else default

def set_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized.")
