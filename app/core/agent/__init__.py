"""Canonical tactical agent package exports."""

from app.core.agent.agent_factory import build_agent_executor
from app.core.agent.brain import ArgusBrain
from app.core.agent.react_workflow import build_workflow, extract_target
from app.core.agent.contracts import (
    AGENT_RUNNER_ENTRYPOINT,
    AGENT_RUN_MODE_DEMO,
    AGENT_RUN_MODE_PRODUCTION,
    AGENT_RUN_MODE_TEST,
    DEFAULT_AGENT_RUN_MODE,
    STREAMLIT_DASHBOARD_ENTRYPOINT,
    AgentRunEvent,
    AgentRunSnapshot,
    build_initial_agent_state,
    build_run_event,
    build_run_snapshot,
    normalize_run_mode,
)
from app.core.agent.state import AgentState

__all__ = [
    'ArgusBrain',
    'build_agent_executor',
    'build_workflow',
    'extract_target',
    'AGENT_RUNNER_ENTRYPOINT',
    'AGENT_RUN_MODE_DEMO',
    'AGENT_RUN_MODE_PRODUCTION',
    'AGENT_RUN_MODE_TEST',
    'DEFAULT_AGENT_RUN_MODE',
    'STREAMLIT_DASHBOARD_ENTRYPOINT',
    'AgentRunEvent',
    'AgentRunSnapshot',
    'AgentState',
    'build_initial_agent_state',
    'build_run_event',
    'build_run_snapshot',
    'normalize_run_mode',
]
