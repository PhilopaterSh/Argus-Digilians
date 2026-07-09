import json
import uuid
from datetime import datetime, timezone

from app.GUI.utils.db_connection import get_gui_db_connection as _get_conn


def save_session(name, targets, settings, agent_state=None):
    conn = _get_conn()
    try:
        session_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        conn.execute(
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
        conn.commit()
        return session_id
    finally:
        conn.close()


def load_session(session_id):
    conn = _get_conn()
    try:
        cursor = conn.execute(
            "SELECT * FROM gui_sessions WHERE session_id = ?", (session_id,)
        )
        row = cursor.fetchone()
        if not row:
            return None
        session = dict(row)
        session["targets"] = json.loads(session.get("targets", "[]"))
        session["settings"] = json.loads(session.get("settings", "{}"))
        session["agent_state"] = json.loads(session.get("agent_state", "{}"))
        return session
    finally:
        conn.close()


def list_sessions():
    conn = _get_conn()
    try:
        cursor = conn.execute(
            "SELECT session_id, name, created_at, updated_at, status FROM gui_sessions ORDER BY updated_at DESC"
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


def delete_session(session_id):
    conn = _get_conn()
    try:
        conn.execute("DELETE FROM gui_sessions WHERE session_id = ?", (session_id,))
        conn.commit()
    finally:
        conn.close()


def update_session(session_id, targets=None, settings=None, agent_state=None):
    conn = _get_conn()
    try:
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
        conn.execute(
            f"UPDATE gui_sessions SET {', '.join(updates)} WHERE session_id = ?",
            params,
        )
        conn.commit()
    finally:
        conn.close()
