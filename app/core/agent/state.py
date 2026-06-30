from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    The state dictionary that is passed around the LangGraph nodes.
    Maintains the cyclical context of the tactical pentest.
    """
    target_ip: str
    open_ports: List[int]
    vulnerabilities: List[Dict[str, Any]]
    
    # Execution Tracking
    current_payload: Optional[str]
    failed_payloads: List[str]
    exploit_success: bool
    
    # Results
    extracted_data: Dict[str, Any]
    error_log: List[str]
    retry_count: int
