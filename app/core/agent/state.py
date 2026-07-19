"""State type for app/core/agent/graph.py's superseded LangGraph node graph.

Superseded by `ArgusAgentState`/`ArgusPrebuiltState` in
`app/core/agent/react_state.py`, which is what `react_workflow.py` (the live
ReAct loop `ArgusBrain` actually drives, per specs 017/018/019) uses.
Retained per Constitution Principle VII (superseded artifacts carry a
resolving header rather than being silently deleted) - `graph.py` itself is
kept, not removed, per that same principle; see
`scripts/diagnose_legacy_tactical_graph.py`'s docstring for the full history.
"""
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Canonical runtime state passed between LangGraph nodes.

    "Canonical" for `graph.py`'s superseded node graph specifically - not the
    live agent path. See this module's docstring above.
    """

    run_id: str
    state_file: str
    target_ip: str
    mode: str
    status: str
    current_node: str
    started_at: str
    updated_at: str
    progress_pct: int
    events: List[Dict[str, Any]]
    open_ports: List[int]
    vulnerabilities: List[Dict[str, Any]]
    current_payload: Optional[str]
    failed_payloads: List[str]
    exploit_success: bool
    extracted_data: Dict[str, Any]
    error_log: List[str]
    retry_count: int
    last_error: Optional[str]
    last_probe_output: Optional[str]
    final_state: Dict[str, Any]
    messages: Annotated[List[BaseMessage], add_messages]
