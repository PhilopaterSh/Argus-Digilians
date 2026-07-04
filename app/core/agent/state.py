from typing import Annotated, Any, Dict, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Canonical runtime state passed between LangGraph nodes."""

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
