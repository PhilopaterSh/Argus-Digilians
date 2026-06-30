import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/argus_intelligence.db"))

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_schema():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS blackboard_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME NOT NULL,
            target TEXT NOT NULL,
            state_snapshot TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def save_entry(target: str, state_snapshot: Dict[str, Any], status: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO blackboard_entries (timestamp, target, state_snapshot, status) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), target, json.dumps(state_snapshot), status)
    )
    conn.commit()
    conn.close()

# Initialize schema when module is imported
init_schema()
