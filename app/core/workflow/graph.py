"""LangGraph workflow builder for Argus AI.

Supports two modes:
1. **Prebuilt mode**: Uses create_react_agent for models with tool_calls support.
2. **Custom mode**: Custom StateGraph with text-based ReAct for any model.
"""
import json
import re
import warnings
from typing import Any, Callable, Dict, Optional

from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from app.core.workflow.state import ArgusAgentState
from app.core.workflow.prompts import (
    build_react_system_prompt,
    build_prebuilt_system_prompt,
)
from app.core.memory.memory_service import ArgusMemory


warnings.filterwarnings("ignore", category=DeprecationWarning)


def _supports_tool_calls(llm: ChatOllama) -> bool:
    """Check if the LLM model supports native tool calling (bind_tools)."""
    try:
        llm.bind_tools([])
        return True
    except Exception:
        return False


def build_workflow(
    llm: ChatOllama,
    tools: list[BaseTool | Callable],
    memory: Optional[ArgusMemory] = None,
) -> Any:
    """Build and return a compiled LangGraph workflow.

    Auto-detects model capability:
    - Models with tool_calls support → prebuilt create_react_agent
    - Models without (e.g. WhiteRabbitNeo) → custom text-based ReAct graph

    Args:
        llm: LangChain Ollama chat model instance.
        tools: List of LangChain tools or callables.
        memory: Optional ArgusMemory for blackboard persistence.

    Returns:
        CompiledStateGraph ready for .invoke().
    """
    if _supports_tool_calls(llm):
        return _build_prebuilt_workflow(llm, tools, memory)
    return _build_custom_workflow(llm, tools, memory)


# ═══════════════════════════════════════════════════════
# Mode 1: Prebuilt (create_react_agent) for tool_calls
# ═══════════════════════════════════════════════════════
def _build_prebuilt_workflow(
    llm: ChatOllama, tools: list, memory: Optional[ArgusMemory] = None
) -> Any:
    """Build workflow using create_react_agent (requires tool_calls support)."""
    from langgraph.prebuilt import create_react_agent
    from app.core.workflow.state import ArgusPrebuiltState

    llm_with_tools = llm.bind_tools(tools)

    def prompt_fn(state: dict) -> list:
        """Dynamic prompt that injects blackboard context."""
        msg = build_prebuilt_system_prompt(state)
        return [SystemMessage(content=msg)] + state["messages"]

    def pre_hook(state: dict) -> dict:
        """Refresh blackboard before LLM call."""
        update = {"iteration_count": state.get("iteration_count", 0) + 1}
        if memory is not None:
            try:
                summary = memory.get_blackboard_summary()
                if summary and summary != "{}":
                    update["blackboard_summary"] = summary
            except Exception:
                pass
        return update

    def post_hook(state: dict) -> dict:
        """Save tool decisions after LLM response."""
        last = state["messages"][-1] if state["messages"] else None
        if last is None or memory is None:
            return {}
        target = state.get("target", "unknown")
        if hasattr(last, "tool_calls") and last.tool_calls:
            for tc in last.tool_calls:
                try:
                    memory.add_finding(
                        domain=target,
                        tool_name=tc.get("name", "unknown"),
                        data_type="llm_decision",
                        raw_data=str(tc.get("args", {})),
                        summary=f"LLM chose {tc['name']}",
                    )
                except Exception:
                    pass
        return {}

    return create_react_agent(
        llm_with_tools,
        tools,
        state_schema=ArgusPrebuiltState,
        prompt=prompt_fn,
        pre_model_hook=pre_hook,
        post_model_hook=post_hook,
        version="v2",
    )


# ═══════════════════════════════════════════════════════
# Mode 2: Custom text-based ReAct for any model
# ═══════════════════════════════════════════════════════
def _build_custom_workflow(
    llm: Any, tools: list, memory: Optional[ArgusMemory] = None
) -> Any:
    """Build a custom StateGraph with text-based ReAct parsing.

    Works with any LLM (no native tool_calls needed).
    The LLM outputs: Thought/Action/Action Input/Final Answer.
    """
    tool_map = _build_tool_map(tools)

    # ── Nodes ──────────────────────────────────────────
    def agent_node(state: ArgusAgentState) -> dict:
        """LLM generates ReAct-formatted output."""
        system_text = build_react_system_prompt({**state, "_tools": tool_map})
        response = llm.invoke([SystemMessage(content=system_text)] + state["messages"])
        return {
            "messages": [response],
            "iteration_count": state["iteration_count"] + 1,
        }

    def _parse_react_output(content: str, default_input: str) -> dict:
        """Parse LLM output: try JSON Action, then text format.

        Returns dict with optional keys: tool_name, tool_input, phase.
        """
        # 1. Detect Final Answer
        if re.search(r"Final Answer:", content):
            return {"phase": "done"}

        # 2. Try JSON Action format
        #    Action: {"name": "tool", "input": "value"}
        json_match = re.search(r"Action:\s*(\{.*?\})", content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(1))
                name = parsed.get("name") or parsed.get("action") or parsed.get("tool")
                inp = parsed.get("input") or parsed.get("arguments") or parsed.get("arg")
                if name:
                    return {
                        "tool_name": name,
                        "tool_input": str(inp or default_input),
                        "phase": "",
                    }
            except json.JSONDecodeError:
                pass

        # 3. Fallback: Text Action format
        #    Action: tool_name
        #    Action Input: value
        action_match = re.search(r"Action:\s*(\w[\w-]*)", content)
        input_match = re.search(r"Action Input:\s*(.+)", content)

        if action_match:
            return {
                "tool_name": action_match.group(1),
                "tool_input": input_match.group(1).strip() if input_match else default_input,
                "phase": "",
            }

        # 4. Nothing detected
        return {"tool_error": "Invalid format", "_raw": content}

    def parse_node(state: ArgusAgentState) -> dict:
        """Extract Action or detect Final Answer from LLM output.

        Returns tool_name/tool_input on success, format error on failure.
        """
        last = state["messages"][-1]
        content = last.content if hasattr(last, "content") else str(last)
        result = _parse_react_output(content, state["target"])

        # If format error, tell the model
        if "tool_error" in result:
            guidance = (
                f"Observation: Output format not recognised.\n"
                f"Expected: Action: {{\"name\": \"tool_name\", \"input\": \"value\"}}\n"
                f"Or: Action: tool_name / Action Input: value\n"
                f"Got: {content[:200]}"
            )
            return {
                "tool_error": guidance,
                "tool_name": None,
                "tool_input": None,
                "phase": "format_error",
                "messages": [HumanMessage(content=guidance)],
            }

        return result

    def execute_node(state: ArgusAgentState) -> dict:
        """Run the chosen tool and feed back the Observation."""
        name = state.get("tool_name")
        inp = state.get("tool_input", state["target"])

        if not name or name not in tool_map:
            obs = f"Observation: Unknown tool '{name}'. Available: {list(tool_map.keys())}"
            return {"tool_error": obs, "messages": [HumanMessage(content=obs)]}

        try:
            result = tool_map[name](inp)
            obs = f"Observation: {result}"
            bb = (
                f"{state['blackboard_summary']}\n"
                f"- [{name}] {str(inp)[:80]} -> {str(result)[:200]}"
            ).strip()
            update = {
                "tool_result": str(result)[:2000],
                "tool_error": None,
                "blackboard_summary": bb,
                "messages": [HumanMessage(content=obs)],
            }
            if memory is not None:
                try:
                    memory.add_finding(
                        domain=state["target"],
                        tool_name=name,
                        data_type="tool_output",
                        raw_data=str(result)[:5000],
                        summary=str(result)[:200],
                    )
                except Exception:
                    pass
            return update
        except Exception as e:
            obs = f"Observation: Error executing {name}: {e}"
            return {"tool_error": obs, "messages": [HumanMessage(content=obs)]}

    # ── Conditional routers ────────────────────────────
    def route_after_agent(state: ArgusAgentState) -> str:
        return "parse"

    def route_after_parse(state: ArgusAgentState) -> str:
        phase = state.get("phase", "")
        if phase == "done":
            return "end"
        if phase == "format_error":
            return "agent"  # loop back so model sees the format error
        if state.get("tool_name"):
            return "execute"
        return "end"

    def route_after_execute(state: ArgusAgentState) -> str:
        if state["iteration_count"] >= state["max_iterations"]:
            return "end"
        return "agent"

    # ── Assemble ───────────────────────────────────────
    builder = StateGraph(ArgusAgentState)
    builder.add_node("agent", agent_node)
    builder.add_node("parse", parse_node)
    builder.add_node("execute", execute_node)

    builder.add_edge(START, "agent")
    builder.add_conditional_edges("agent", route_after_agent)
    builder.add_conditional_edges(
        "parse", route_after_parse, {"execute": "execute", "agent": "agent", "end": END}
    )
    builder.add_conditional_edges(
        "execute", route_after_execute, {"agent": "agent", "end": END}
    )

    return builder.compile()


# ═══════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════
def _build_tool_map(tools: list) -> Dict[str, Callable]:
    """Convert a list of tools/callables to a name → func dict."""
    tool_map = {}
    for t in tools:
        if isinstance(t, BaseTool):
            tool_map[t.name] = t.func if hasattr(t, "func") else t.run
        elif callable(t):
            name = getattr(t, "name", t.__name__)
            tool_map[name] = t
        elif isinstance(t, dict) and "name" in t and "func" in t:
            tool_map[t["name"]] = t["func"]
    return tool_map


def extract_target(query: str) -> str:
    """Extract target URL/domain from a user query."""
    for part in query.split():
        part = part.strip(".,;!?\"'")
        if part.startswith(("http://", "https://")):
            return part
        if "." in part and " " not in part:
            return part
    return query
