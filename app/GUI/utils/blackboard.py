import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from app.core.memory.memory_service import ArgusMemory
from app.GUI.utils.db_connection import get_gui_db_connection as _get_gui_conn


_memory = None


def _get_memory():
    """Return the process-wide ArgusMemory instance, creating it once.

    Returns:
        ArgusMemory: The shared instance.
    """
    global _memory
    if _memory is None:
        _memory = ArgusMemory()
    return _memory


def load_targets():
    """Return the Blackboard's current summary.

    Returns:
        str: `ArgusMemory.get_blackboard_summary()`'s JSON string.
    """
    memory = _get_memory()
    return memory.get_blackboard_summary()


def save_target(url, target_type="url", status="pending", tags=None):
    """Upsert a target into the Blackboard by URL/domain.

    Args:
        url (str): The target URL/domain to upsert.
        target_type (str): Currently unused - `ArgusMemory.upsert_target`
            has no such concept; accepted for call-site compatibility.
        status (str): Currently unused, same reason.
        tags: Currently unused, same reason.

    Returns:
        None: `ArgusMemory.upsert_target()` always returns `None`.
    """
    memory = _get_memory()
    return memory.upsert_target(url)


def load_findings(target_id=None):
    """Load findings."""
    return _get_memory().get_blackboard_summary()


def load_entities():
    """Load entities."""
    return []


def load_relations():
    """Load relations."""
    return []


def get_blackboard_summary():
    """Get blackboard summary."""
    return _get_memory().get_blackboard_summary()


def get_blackboard_counts():
    """Get blackboard counts."""
    return _get_memory().get_blackboard_counts()


def build_graph_data():
    """Builds a real networkx graph from the targets/findings the tactical
    agent actually writes (via ArgusMemory.upsert_target()/add_finding()).
    Previously this returned an always-empty DiGraph unconditionally, so the
    Knowledge Graph tab showed "No entities found" even with a fully
    populated Blackboard.

    Returns:
        networkx.DiGraph | None: A graph with one node per domain and per
        finding (edges from domain to finding, labeled by tool name), or
        `None` if `networkx` isn't installed.
    """
    try:
        import networkx as nx
    except ImportError:
        return None

    G = nx.DiGraph()
    for domain, tool_name, data_type, summary in _get_memory().get_findings_graph_rows():
        if domain not in G:
            G.add_node(domain, label=domain, type="domain", properties={})
        finding_id = f"{domain}::{tool_name}::{data_type}"
        if finding_id not in G:
            G.add_node(
                finding_id,
                label=f"{tool_name}/{data_type}",
                type="finding",
                properties={"summary": summary},
            )
        G.add_edge(domain, finding_id, label=tool_name)
    return G


def init_gui_tables():
    """Create the `gui_sessions`/`gui_jobs` tables if they don't already exist."""
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
