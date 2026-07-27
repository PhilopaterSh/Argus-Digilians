import sqlite3

_DEFAULT_DB_PATH = "data/argus_intelligence.db"


def get_gui_db_connection():
    """Open a connection to the shared Argus SQLite database for GUI code.

    Returns:
        sqlite3.Connection: A connection with `row_factory` set to
        `sqlite3.Row` (so results are indexable by column name) and WAL
        journal mode enabled (safe for the GUI and the agent process to
        read/write the same file concurrently).
    """
    conn = sqlite3.connect(_DEFAULT_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn
