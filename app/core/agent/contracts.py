"""Canonical runtime contracts for the tactical agent."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, NotRequired, Optional, TypedDict

from langchain_core.messages import HumanMessage

from app.core.agent.state import AgentState

AGENT_RUNNER_ENTRYPOINT = "scripts/run_agent.py"
STREAMLIT_DASHBOARD_ENTRYPOINT = "app/GUI/dashboard.py"
AGENT_RUN_MODE_PRODUCTION = "production"
AGENT_RUN_MODE_DEMO = "demo"
AGENT_RUN_MODE_TEST = "test"
DEFAULT_AGENT_RUN_MODE = AGENT_RUN_MODE_PRODUCTION


class AgentRunEvent(TypedDict):
    node: str
    status: str
    detail: str
    timestamp: str
    run_id: NotRequired[str]
    target: NotRequired[str]
    mode: NotRequired[str]


class AgentRunSnapshot(TypedDict):
    run_id: str
    target: str
    mode: str
    status: str
    current_node: str
    started_at: str
    updated_at: str
    progress_pct: int
    events: List[AgentRunEvent]
    final_state: Dict[str, Any]
    error: Optional[str]


def utc_now_iso() -> str:
    """Utc now iso."""
    return datetime.now(timezone.utc).isoformat()


def normalize_run_mode(value: Optional[str]) -> str:
    """Normalize a run-mode string to one of the recognized constants.

    Args:
        value (str | None): Raw mode string (case/whitespace-insensitive).

    Returns:
        str: `value` lowercased/stripped if it matches production/demo/
        test, else `DEFAULT_AGENT_RUN_MODE`.
    """
    if not value:
        return DEFAULT_AGENT_RUN_MODE
    normalized = value.strip().lower()
    if normalized in {AGENT_RUN_MODE_PRODUCTION, AGENT_RUN_MODE_DEMO, AGENT_RUN_MODE_TEST}:
        return normalized
    return DEFAULT_AGENT_RUN_MODE


def build_run_event(node: str, status: str, detail: str, *, run_id: Optional[str] = None, target: Optional[str] = None, mode: Optional[str] = None) -> AgentRunEvent:
    """Build one AgentRunEvent dict, timestamped now.

    Args:
        node (str): The graph node/agent step this event is from.
        status (str): "running"/"completed"/"failed".
        detail (str): Human-readable event text.
        run_id (str | None): Included only if truthy.
        target (str | None): Included only if truthy.
        mode (str | None): Included only if truthy.

    Returns:
        AgentRunEvent: The event dict.
    """
    event: AgentRunEvent = {"node": node, "status": status, "detail": detail, "timestamp": utc_now_iso()}
    if run_id:
        event["run_id"] = run_id
    if target:
        event["target"] = target
    if mode:
        event["mode"] = mode
    return event


def build_run_snapshot(run_id: str, target: str, mode: str, *, status: str = "starting", current_node: str = "init", progress_pct: int = 0, final_state: Optional[Dict[str, Any]] = None, error: Optional[str] = None, started_at: Optional[str] = None, updated_at: Optional[str] = None, events: Optional[List[AgentRunEvent]] = None) -> AgentRunSnapshot:
    """Build a full AgentRunSnapshot dict, filling timestamps if omitted.

    Args:
        run_id (str): This run's id.
        target (str): The target being analyzed.
        mode (str): The run mode.
        status (str): Run status.
        current_node (str): Current graph node name.
        progress_pct (int): Progress percentage (0-100).
        final_state (dict | None): Final report data; `{}` if omitted.
        error (str | None): Error message, if any.
        started_at (str | None): Defaults to now if omitted.
        updated_at (str | None): Defaults to now if omitted.
        events (list[AgentRunEvent] | None): Defaults to `[]` if omitted.

    Returns:
        AgentRunSnapshot: The snapshot dict.
    """
    now = utc_now_iso()
    return {
        "run_id": run_id,
        "target": target,
        "mode": mode,
        "status": status,
        "current_node": current_node,
        "started_at": started_at or now,
        "updated_at": updated_at or now,
        "progress_pct": progress_pct,
        "events": list(events or []),
        "final_state": dict(final_state or {}),
        "error": error,
    }


def build_initial_agent_state(target: str, run_id: str, mode: str, state_file: str) -> Dict[str, Any]:
    """Build the fresh AgentState dict a new tactical-graph run starts from.

    Args:
        target (str): The target to analyze.
        run_id (str): This run's id.
        mode (str): The run mode.
        state_file (str): Path the state file will be written to (stored
            in the state itself for downstream reference).

    Returns:
        Dict[str, Any]: The initial state, with all counters/lists at
        their zero values and a single seed `HumanMessage` in `messages`.
    """
    now = utc_now_iso()
    return {
        "run_id": run_id,
        "state_file": state_file,
        "target_ip": target,
        "mode": mode,
        "status": "starting",
        "current_node": "init",
        "started_at": now,
        "updated_at": now,
        "progress_pct": 0,
        "events": [],
        "open_ports": [],
        "vulnerabilities": [],
        "current_payload": None,
        "failed_payloads": [],
        "exploit_success": False,
        "extracted_data": {},
        "error_log": [],
        "retry_count": 0,
        "last_error": None,
        "last_probe_output": None,
        "final_state": {},
        "messages": [HumanMessage(content=f"Execute pentest on {target}")],
    }


def load_json_file(path: str) -> Dict[str, Any]:
    """Read and parse a JSON file, tolerating a missing or invalid file.

    Args:
        path (str): Path to the JSON file.

    Returns:
        Dict[str, Any]: The parsed content, or `{}` if the file doesn't
        exist or fails to parse.
    """
    file_path = Path(path)
    if not file_path.exists():
        return {}
    try:
        return json.loads(file_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def write_json_file(path: str, payload: Dict[str, Any]) -> None:
    """Write a dict to a JSON file, creating parent directories if needed.

    Args:
        path (str): Path to write to.
        payload (Dict[str, Any]): Data to serialize (non-JSON-serializable
            values are stringified via `default=str`).

    Returns:
        None
    """
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")


def append_run_event(state_file: str, event: AgentRunEvent) -> None:
    """Append one event to a state file's event list and refresh its top-level fields.

    Args:
        state_file (str): Path to the state JSON file (loaded, updated,
            and rewritten in place).
        event (AgentRunEvent): The event to append; its `node`/`status`/
            `timestamp` (and `run_id`/`target`/`mode` if present) also
            overwrite the state's own top-level fields.

    Returns:
        None
    """
    state = load_json_file(state_file)
    events = list(state.get("events", []))
    events.append(event)
    state["events"] = events
    state["current_node"] = event.get("node", state.get("current_node", "unknown"))
    state["status"] = event.get("status", state.get("status", "unknown"))
    state["updated_at"] = event.get("timestamp", utc_now_iso())
    if event.get("run_id"):
        state["run_id"] = event["run_id"]
    if event.get("target"):
        state["target"] = event["target"]
    if event.get("mode"):
        state["mode"] = event["mode"]
    write_json_file(state_file, state)


def record_state_event(state: AgentState, node: str, status: str, detail: str) -> AgentState:
    """Append an event to an in-memory state dict and, if it names a
    state_file, persist it there too via `append_run_event`.

    Args:
        state (AgentState): The in-memory agent state to update.
        node (str): The graph node/agent step this event is from.
        status (str): "running"/"completed"/"failed".
        detail (str): Human-readable event text.

    Returns:
        AgentState: `state`, mutated in place (`events`,
        `current_node`, `status`, `updated_at` updated) and returned for
        convenience.
    """
    event = build_run_event(node, status, detail, run_id=state.get("run_id"), target=state.get("target_ip"), mode=state.get("mode"))
    events = list(state.get("events", []))
    events.append(dict(event))
    state["events"] = events
    state["current_node"] = node
    state["status"] = status
    state["updated_at"] = event["timestamp"]
    state_file = state.get("state_file")
    if state_file:
        append_run_event(state_file, event)
    return state


def persist_run_snapshot(state_file: str, snapshot: AgentRunSnapshot) -> None:
    """Persist run snapshot."""
    write_json_file(state_file, snapshot)
