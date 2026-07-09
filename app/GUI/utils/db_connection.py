import sqlite3

_DEFAULT_DB_PATH = "data/argus_intelligence.db"


def get_gui_db_connection():
    conn = sqlite3.connect(_DEFAULT_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
