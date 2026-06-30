import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from app.core.memory.memory_service import ArgusMemory


_memory = None


def _get_memory():
    global _memory
    if _memory is None:
        _memory = ArgusMemory()
    return _memory


def load_targets():
    memory = _get_memory()
    return memory.get_all_targets()


def save_target(url, target_type="url", status="pending", tags=None):
    memory = _get_memory()
    return memory.upsert_target(url, target_type, status, tags or [])


def delete_target(target_id):
    memory = _get_memory()
    return memory.delete_target(target_id)


def load_findings(target_id=None):
    memory = _get_memory()
    if target_id:
        return memory.get_findings_by_target(target_id)
    return memory.get_all_findings()


def load_entities():
    memory = _get_memory()
    return memory.get_all_entities()


def load_relations():
    memory = _get_memory()
    return memory.get_all_relations()


def get_blackboard_summary():
    memory = _get_memory()
    return memory.get_blackboard_summary()


def build_graph_data():
    entities = load_entities()
    relations = load_relations()
    try:
        import networkx as nx
        G = nx.DiGraph()
        for entity in entities:
            G.add_node(
                str(entity.get("id", entity.get("name", "unknown"))),
                label=entity.get("name", "unknown"),
                type=entity.get("type", "unknown"),
                properties=entity,
            )
        for rel in relations:
            G.add_edge(
                str(rel.get("source_id", "")),
                str(rel.get("target_id", "")),
                label=rel.get("relationship", "related_to"),
                properties=rel,
            )
        return G
    except ImportError:
        return None


def init_gui_tables():
    memory = _get_memory()
    memory.execute(
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
    memory.execute(
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
    memory.conn.commit()
