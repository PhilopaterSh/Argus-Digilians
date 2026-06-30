import sys
import os
import sqlite3

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from app.core.memory.memory_service import ArgusMemory

_DEFAULT_DB_PATH = os.path.join("data", "argus_intelligence.db")


def _get_gui_conn():
    conn = sqlite3.connect(_DEFAULT_DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


_memory = None


def _get_memory():
    global _memory
    if _memory is None:
        _memory = ArgusMemory()
    return _memory


def load_targets():
    memory = _get_memory()
    return memory.get_blackboard_summary()


def save_target(url, target_type="url", status="pending", tags=None):
    memory = _get_memory()
    return memory.upsert_target(url)


def load_findings(target_id=None):
    return _get_memory().get_blackboard_summary()


def load_entities():
    return []


def load_relations():
    return []


def get_blackboard_summary():
    return _get_memory().get_blackboard_summary()


def build_graph_data():
    try:
        import networkx as nx
        G = nx.DiGraph()
        return G
    except ImportError:
        return None


def init_gui_tables():
    conn = _get_gui_conn()
    try:
        conn.execute(
            """CREATE TABLE IF NOT EXISTS gui_sessions (
                session_id TEXT PRIMARY KEY,
                name TEXT,
                created_at TEXT,
                updated_at TEXT,
                targets TEXT,
                settings TEXT,
                agent_state TEXT,
                status TEXT DEFAULT 'active'
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS gui_jobs (
                job_id TEXT PRIMARY KEY,
                session_id TEXT,
                target_id TEXT,
                type TEXT,
                status TEXT DEFAULT 'queued',
                agent_state TEXT,
                current_node TEXT,
                progress_pct INTEGER DEFAULT 0,
                started_at TEXT,
                completed_at TEXT,
                error TEXT
            )"""
        )
        conn.commit()
    finally:
        conn.close()
