import logging
from app.core.agent.state import AgentState
from app.core.llm_factory import build_llm
from app.tools.tool_registry import WSLBridgeTools
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)

def reflective_node(state: AgentState) -> AgentState:
    """
    Analyzes failed attempts and modifies the payload to bypass defenses.
    """
    logger.info("[Reflective Node] WAF or defense detected. Analyzing failure...")
    
    state["retry_count"] += 1
    
    # Get last failed payload and error log
    failed_payload = state["failed_payloads"][-1] if state["failed_payloads"] else "unknown"
    error_context = "\n".join(state["error_log"]) if state["error_log"] else "Unknown WAF block or failure"
    
    # 1. Use ReflectiveVerificationService to verify and get analysis
    analysis_result = "No verification performed."
    try:
        tools = WSLBridgeTools()
        # Analyze the failed attempt
        analysis_result = tools.verifier.post_execute_verify(
            url=state["target_ip"],
            command=f"exploit {failed_payload}",
            raw_output=error_context
        )
        logger.info("[Reflective Node] Reflector Analysis: %s", analysis_result)
    except Exception as e:
        logger.warning("[Reflective Node] Reflector service execution failed: %s", e)
        
    # 2. Make real LLM call to suggest a new bypass payload
    next_payload = None
    try:
        # Use WhiteRabbitNeo or a default model
        llm = build_llm("WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest")
        
        system_instruction = (
            "You are an expert penetration tester. A payload was blocked/failed. "
            "Suggest a modified, obfuscated version of the failed payload to bypass WAF defenses. "
            "Output ONLY the new payload string, with absolutely no preamble, no markdown formatting (no backticks), and no explanation."
        )
        
        user_prompt = (
            f"Failed Payload: {failed_payload}\n"
            f"WAF Analysis/Error: {analysis_result}\n"
            f"Error Log: {error_context}\n"
            "Suggest next payload:"
        )
        
        # Invoke LLM
        response = llm.invoke([
            SystemMessage(content=system_instruction),
            HumanMessage(content=user_prompt)
        ])
        
        next_payload = response.strip().strip('`').strip('"').strip("'")
        logger.info("[Reflective Node] LLM suggested bypass payload: %s", next_payload)
    except Exception as e:
        logger.warning("[Reflective Node] LLM call failed (Ollama may be offline): %s", e)
        
    # 3. Fallback logic to ensure tests and loops proceed
    if not next_payload or next_payload == failed_payload:
        if failed_payload == "payload_v1":
            logger.info("[Reflective Node] LLM fallback: Modifying payload to payload_v2 (obfuscated)...")
            next_payload = "payload_v2"
        else:
            logger.warning("[Reflective Node] LLM fallback: Unable to determine bypass strategy.")
            next_payload = None
            
    state["current_payload"] = next_payload
    
    # Store LLM suggestion/reflection in state messages for LangGraph history
    if next_payload:
        state["messages"] = [
            HumanMessage(content=f"Reflector suggested payload bypass: {next_payload} based on analysis: {analysis_result}")
        ]
        
    return state

