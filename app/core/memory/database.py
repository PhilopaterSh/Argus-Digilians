import os
import sqlite3
from contextlib import contextmanager
from sqlite3 import Connection
from typing import Generator


class SQLiteDatabase:
    """
    SQLite database manager for Argus intelligence storage.

    This class is responsible only for:
        - Managing SQLite connections.
        - Providing a safe database session context manager.
        - Initializing the required database schema.
        - Clearing and rebuilding the database.

    It does not contain business logic for targets, findings, entities,
    relations, or summaries. Those responsibilities should remain in their
    dedicated store/service classes.
    """

    def __init__(self, db_path: str = "argus_intelligence.db"):
        """
        Initialize the SQLite database manager.

        Args:
            db_path:
                Path to the SQLite database file. If the file does not exist,
                it will be created automatically during schema initialization.
        """

        self.db_path = db_path

        # Ensure all required tables exist when the database manager is created.
        self.init_db()

    def connect(self) -> Connection:
        """
        Create a new SQLite database connection.

        A new connection is created each time this method is called. This keeps
        connection usage simple and avoids sharing the same connection across
        unrelated operations.

        Returns:
            Connection:
                Active SQLite connection object.
        """

        return sqlite3.connect(self.db_path)

    @contextmanager
    def session(self) -> Generator[Connection, None, None]:
        """
        Provide a managed SQLite database session.

        This context manager automatically:
            - Opens a database connection.
            - Yields the connection to the caller.
            - Commits changes if no exception occurs.
            - Closes the connection after use.

        Returns:
            Generator[Connection, None, None]:
                Managed SQLite connection.

        Note:
            In the current implementation, exceptions are not explicitly rolled
            back before closing the connection. For stronger transaction safety,
            consider adding conn.rollback() inside an except block.
        """

        conn = self.connect()

        try:
            yield conn

            # Commit all changes made during the session.
            conn.commit()

        finally:
            # Always close the connection to avoid resource leaks.
            conn.close()

    def init_db(self) -> None:
        """
        Initialize the database schema.

        Creates all required tables if they do not already exist.

        Tables:
            targets:
                Stores discovered domains, subdomains, and target metadata.

            findings:
                Stores technical findings collected from tools such as nmap,
                whatweb, Nikto, FFUF, fuzzing, and secret analysis.

            entities:
                Stores knowledge graph nodes such as domains, IPs, technologies,
                files, secrets, and vulnerabilities.

            relations:
                Stores knowledge graph edges between entities.

            global_state:
                Stores global AI-ready state, summaries, or cached metadata.
        """

        with self.session() as conn:
            cursor = conn.cursor()

            # Stores discovered targets and their discovery metadata.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS targets (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT UNIQUE,
                    parent_domain TEXT,
                    status TEXT DEFAULT 'discovered',
                    priority INTEGER DEFAULT 0,
                    last_seen DATETIME
                )
            """)

            # Stores raw and summarized findings collected from different tools.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_id INTEGER,
                    tool_name TEXT,
                    data_type TEXT,
                    raw_data TEXT,
                    summary TEXT,
                    timestamp DATETIME,
                    FOREIGN KEY (target_id) REFERENCES targets(id)
                )
            """)

            # Stores knowledge graph nodes/entities.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT,
                    value TEXT UNIQUE,
                    metadata TEXT,
                    first_seen DATETIME
                )
            """)

            # Stores knowledge graph relationships between entities.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    source_id INTEGER,
                    target_id INTEGER,
                    type TEXT,
                    strength FLOAT DEFAULT 1.0,
                    timestamp DATETIME,
                    FOREIGN KEY (source_id) REFERENCES entities(id),
                    FOREIGN KEY (target_id) REFERENCES entities(id),
                    UNIQUE(source_id, target_id, type)
                )
            """)

            # Stores global summaries or application-level state.
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS global_state (
                    key TEXT PRIMARY KEY,
                    value TEXT,
                    updated_at DATETIME
                )
            """)

    def clear(self) -> None:
        """
        Delete the existing database file and recreate the schema.

        This method is useful when resetting Argus memory during development,
        testing, or when starting a fresh intelligence collection session.
        """

        # Remove the existing SQLite database file if it exists.
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        # Recreate all required tables after deleting the database.
        self.init_db()