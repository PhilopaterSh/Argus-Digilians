import json
import uuid
from datetime import datetime, timezone
from app.GUI.utils.blackboard import _get_memory


def save_session(name, targets, settings, agent_state=None):
    memory = _get_memory()
    session_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    memory.execute(
        """INSERT OR REPLACE INTO gui_sessions
           (session_id, name, created_at, updated_at, targets, settings, agent_state, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            session_id,
            name,
            now,
            now,
            json.dumps(targets, default=str),
            json.dumps(settings, default=str),
            json.dumps(agent_state, default=str) if agent_state else "{}",
            "active",
        ),
    )
    memory.conn.commit()
    return session_id


def load_session(session_id):
    memory = _get_memory()
    cursor = memory.execute(
        "SELECT * FROM gui_sessions WHERE session_id = ?", (session_id,)
    )
    row = cursor.fetchone()
    if not row:
        return None
    columns = [desc[0] for desc in cursor.description]
    session = dict(zip(columns, row))
    session["targets"] = json.loads(session.get("targets", "[]"))
    session["settings"] = json.loads(session.get("settings", "{}"))
    session["agent_state"] = json.loads(session.get("agent_state", "{}"))
    return session


def list_sessions():
    memory = _get_memory()
    cursor = memory.execute(
        "SELECT session_id, name, created_at, updated_at, status FROM gui_sessions ORDER BY updated_at DESC"
    )
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in rows]


def delete_session(session_id):
    memory = _get_memory()
    memory.execute("DELETE FROM gui_sessions WHERE session_id = ?", (session_id,))
    memory.conn.commit()


def update_session(session_id, targets=None, settings=None, agent_state=None):
    memory = _get_memory()
    now = datetime.now(timezone.utc).isoformat()
    updates = ["updated_at = ?"]
    params = [now]
    if targets is not None:
        updates.append("targets = ?")
        params.append(json.dumps(targets, default=str))
    if settings is not None:
        updates.append("settings = ?")
        params.append(json.dumps(settings, default=str))
    if agent_state is not None:
        updates.append("agent_state = ?")
        params.append(json.dumps(agent_state, default=str))
    params.append(session_id)
    memory.execute(
        f"UPDATE gui_sessions SET {', '.join(updates)} WHERE session_id = ?",
        params,
    )
    memory.conn.commit()
