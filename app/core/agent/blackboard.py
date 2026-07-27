import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, Any

DB_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/argus_intelligence.db"))

_schema_ready = False

def get_connection():
    """Open a connection to the tactical-graph blackboard DB, initializing
    its schema on first use.

    Returns:
        sqlite3.Connection: A new connection to `DB_PATH`.
    """
    global _schema_ready
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if not _schema_ready:
        # Set before calling init_schema() (which itself calls get_connection())
        # to avoid infinite recursion on the first call.
        _schema_ready = True
        init_schema()
    return sqlite3.connect(DB_PATH)

def init_schema():
    """Create schema_info/blackboard_entries if missing, recording schema version 1."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create schema_info table for version tracking
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_info (
            version INTEGER PRIMARY KEY,
            applied_at DATETIME NOT NULL
        )
    """)
    
    cursor.execute("SELECT version FROM schema_info ORDER BY version DESC LIMIT 1")
    row = cursor.fetchone()
    current_version = row[0] if row else 0
    
    if current_version < 1:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS blackboard_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                target TEXT NOT NULL,
                state_snapshot TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)
        cursor.execute(
            "INSERT INTO schema_info (version, applied_at) VALUES (?, ?)",
            (1, datetime.utcnow().isoformat())
        )
        conn.commit()
        
    conn.close()

def save_entry(target: str, state_snapshot: Dict[str, Any], status: str):
    """Insert one row recording a completed/failed tactical-graph run.

    Args:
        target (str): The target that was analyzed.
        state_snapshot (Dict[str, Any]): The final agent state, JSON-
            serialized with `default=str` so non-serializable values
            (e.g. LangChain message objects) don't crash the insert.
        status (str): e.g. "SUCCESS"/"FAILED".
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Safely serialize state_snapshot using default=str to prevent crashes on non-serializable objects (e.g. messages)
    serialized_state = json.dumps(state_snapshot, default=str)
    
    cursor.execute(
        "INSERT INTO blackboard_entries (timestamp, target, state_snapshot, status) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), target, serialized_state, status)
    )
    conn.commit()
    conn.close()
