import logging

from app.core.agent.contracts import record_state_event, utc_now_iso
from app.core.agent.state import AgentState
from app.core.config import ArgusConfig
from app.core.llm_factory import build_llm
from app.tools.tool_registry import WSLBridgeTools
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


def reflective_node(state: AgentState) -> AgentState:
    logger.info("[Reflective Node] Analyzing failed attempt and selecting the next probe...")
    record_state_event(state, "reflective", "running", "Analyzing failure context and selecting next payload")
    state["current_node"] = "reflective"
    state["status"] = "running"
    state["updated_at"] = utc_now_iso()
    state["retry_count"] += 1

    failed_payload = state["failed_payloads"][-1] if state["failed_payloads"] else state.get("current_payload") or "unknown"
    analysis_input = state.get("last_probe_output") or "\n".join(state.get("error_log", []))

    analysis_result = "No verification performed."
    try:
        tools = WSLBridgeTools()
        analysis_result = tools.verify_output(state["target_ip"], f"controlled_probe:{failed_payload}", analysis_input)
        logger.info("[Reflective Node] Reflector analysis: %s", analysis_result)
    except Exception as e:
        logger.warning("[Reflective Node] Reflector service execution failed: %s", e)
        analysis_result = f"Reflector failed: {e}"

    next_payload = None
    try:
        llm = build_llm(ArgusConfig.load().model_name)
        system_instruction = (
            "You are an expert penetration tester. A probe did not confirm success. "
            "Suggest the next probe category only: sqli, path_traversal, or generic_probe. "
            "Output exactly one token."
        )
        user_prompt = (
            f"Last payload: {failed_payload}\n"
            f"Verification analysis: {analysis_result}\n"
            f"Error log: {' | '.join(state.get('error_log', []))}\n"
            "Next payload category:"
        )
        response = llm.invoke([SystemMessage(content=system_instruction), HumanMessage(content=user_prompt)])
        candidate = response.strip().strip('`').strip('"').strip("'").lower()
        if candidate in {"sqli", "path_traversal", "generic_probe"}:
            next_payload = candidate
    except Exception as e:
        logger.warning("[Reflective Node] LLM call failed (Ollama may be offline): %s", e)

    if not next_payload:
        if failed_payload == "sqli":
            next_payload = "path_traversal"
        elif failed_payload == "path_traversal":
            next_payload = "generic_probe"
        else:
            next_payload = "sqli"

    state["current_payload"] = next_payload
    state["last_error"] = analysis_result
    state["extracted_data"]["reflective"] = {"analysis": analysis_result, "next_payload": next_payload}

    if state["retry_count"] >= ArgusConfig.load().max_retries:
        state["current_payload"] = None
        state["status"] = "failed"
        record_state_event(state, "reflective", "failed", "Retry budget exhausted")
        return state

    state["progress_pct"] = max(state.get("progress_pct", 70), 75)
    record_state_event(state, "reflective", "completed", f"Selected next payload category: {next_payload}")
    return state
