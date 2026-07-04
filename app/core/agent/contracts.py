"""Canonical runtime contracts for the tactical agent.

Production mode is the default runtime:
- execute the real LangGraph workflow
- write truthful state snapshots
- fail clearly on timeout or dependency errors

Demo/Test modes are explicit opt-in paths:
- they may simulate progress for UI or smoke testing
- they must never be the default production behavior
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, NotRequired, Optional, TypedDict

from langchain_core.messages import HumanMessage

AGENT_RUNNER_ENTRYPOINT = "scripts/run_agent.py"
STREAMLIT_DASHBOARD_ENTRYPOINT = "app/GUI/argus_studio.py"

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
    return datetime.now(timezone.utc).isoformat()


def normalize_run_mode(value: Optional[str]) -> str:
    if not value:
        return DEFAULT_AGENT_RUN_MODE
    normalized = value.strip().lower()
    if normalized in {AGENT_RUN_MODE_PRODUCTION, AGENT_RUN_MODE_DEMO, AGENT_RUN_MODE_TEST}:
        return normalized
    return DEFAULT_AGENT_RUN_MODE


def build_run_event(
    node: str,
    status: str,
    detail: str,
    *,
    run_id: Optional[str] = None,
    target: Optional[str] = None,
    mode: Optional[str] = None,
) -> AgentRunEvent:
    event: AgentRunEvent = {
        "node": node,
        "status": status,
        "detail": detail,
        "timestamp": utc_now_iso(),
    }
    if run_id:
        event["run_id"] = run_id
    if target:
        event["target"] = target
    if mode:
        event["mode"] = mode
    return event


def build_run_snapshot(
    run_id: str,
    target: str,
    mode: str,
    *,
    status: str = "starting",
    current_node: str = "init",
    progress_pct: int = 0,
    final_state: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None,
    started_at: Optional[str] = None,
    updated_at: Optional[str] = None,
    events: Optional[List[AgentRunEvent]] = None,
) -> AgentRunSnapshot:
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


def build_initial_agent_state(target: str, run_id: str, mode: str) -> Dict[str, Any]:
    now = utc_now_iso()
    return {
        "run_id": run_id,
        "target_ip": target,
        "mode": mode,
        "status": "starting",
        "current_node": "init",
        "started_at": now,
        "updated_at": now,
        "progress_pct": 0,
        "open_ports": [],
        "vulnerabilities": [],
        "current_payload": None,
        "failed_payloads": [],
        "exploit_success": False,
        "extracted_data": {},
        "error_log": [],
        "retry_count": 0,
        "last_error": None,
        "final_state": {},
        "messages": [HumanMessage(content=f"Execute pentest on {target}")],
    }
