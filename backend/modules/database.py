import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "repurpose.db")

def init_db():
    """Initializes the SQLite database with required tables."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Users Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            mobile TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Research Sessions Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER,
            molecule TEXT,
            status TEXT,
            last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Analysis Reports Table (Caching)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analysis_cache (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            molecule TEXT NOT NULL,
            language TEXT NOT NULL,
            report_data TEXT NOT NULL, -- JSON formatted data
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(molecule, language)
        )
    ''')
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn
