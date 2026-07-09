"""LangGraph workflow builder for Argus AI.

Supports two modes:
1. **Prebuilt mode**: Uses create_react_agent for models with tool_calls support.
2. **Custom mode**: Custom StateGraph with text-based ReAct for any model.
"""
import json
import re
import warnings
from typing import Any, Callable, Dict, Optional

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from pydantic import BaseModel, Field

from app.core.agent.react_state import ArgusAgentState
from app.core.agent.react_prompts import (
    build_react_system_prompt,
    build_prebuilt_system_prompt,
)
from app.core.memory.memory_service import ArgusMemory
from app.core.schemas import SecurityReport


warnings.filterwarnings("ignore", category=DeprecationWarning)


class _ArgusAction(BaseModel):
    """Structured Action decision (012 FR-C9 / ADR-13): Ollama format=json primary path."""
    thought: str = Field(description="Brief reasoning for this step")
    tool: Optional[str] = Field(default=None, description="Tool name to call next; omit when giving the final answer")
    input: Optional[str] = Field(default=None, description="Input value to pass to the tool")
    final_answer: Optional[str] = Field(default=None, description="The complete final report; set only when done")


def _try_structured_action(llm: Any, system_text: str, messages: list) -> Optional[str]:
    """Attempt Ollama format=json structured decoding of the next Action (012 FR-C9).

    Returns a synthesized ReAct-format content string on success, so the existing
    regex parser in parse_node can consume it unchanged. Returns None if structured
    decoding is unavailable or the model does not honor it, so callers fall back to
    plain llm.invoke() + regex parsing (012 FR-C10).
    """
    if not hasattr(llm, "with_structured_output"):
        return None
    try:
        structured_llm = llm.with_structured_output(_ArgusAction)
        result = structured_llm.invoke([SystemMessage(content=system_text)] + messages)
        action = result if isinstance(result, _ArgusAction) else _ArgusAction(**result)
    except Exception:
        return None

    if action.final_answer:
        return f"Thought: {action.thought}\nFinal Answer: {action.final_answer}"
    if action.tool:
        return (
            f"Thought: {action.thought}\n"
            f"Action: {json.dumps({'name': action.tool, 'input': action.input or ''})}"
        )
    return None


def _try_structured_final_answer(llm: Any, raw_answer: str) -> Optional[dict]:
    """Coerce a free-text final answer into the SecurityReport schema (specs/018).

    Applies the same schema-constrained-decoding reliability fix as
    `_try_structured_action` to the final report shape, not just tool
    selection - a free-text "Final Answer:" is just as prone to the format
    drift that motivated this module's structured-first approach.

    Args:
        llm (Any): The LLM in use; only attempted if it exposes
            `with_structured_output` (Ollama 0.3.0+ / LangChain's wrapper
            around it).
        raw_answer (str): The text following "Final Answer:" in the
            agent's last message.

    Returns:
        Optional[dict]: A `SecurityReport.model_dump()` dict on success, or
        None if structured decoding is unavailable or fails - callers must
        fall back to the raw text rather than fabricate a report
        (Constitution VIII - Truthful Runtime).
    """
    if not hasattr(llm, "with_structured_output"):
        return None
    try:
        structured_llm = llm.with_structured_output(SecurityReport)
        result = structured_llm.invoke([
            SystemMessage(content=(
                "Extract a SecurityReport from the following penetration test "
                "final answer. Preserve all real findings verbatim; do not "
                "invent findings, scores, or steps that aren't supported by "
                "the text."
            )),
            HumanMessage(content=raw_answer),
        ])
        report = result if isinstance(result, SecurityReport) else SecurityReport(**result)
        return report.model_dump()
    except Exception:
        return None


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
    - Models with tool_calls support -> prebuilt create_react_agent
    - Models without (e.g. WhiteRabbitNeo) -> custom text-based ReAct graph

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


# =======================================================
# Mode 1: Prebuilt (create_react_agent) for tool_calls
# =======================================================
def _build_prebuilt_workflow(
    llm: ChatOllama, tools: list, memory: Optional[ArgusMemory] = None
) -> Any:
    """Build workflow using create_react_agent (requires tool_calls support)."""
    from langgraph.prebuilt import create_react_agent
    from app.core.agent.react_state import ArgusPrebuiltState

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


# =======================================================
# Mode 2: Custom text-based ReAct for any model
# =======================================================
def _build_custom_workflow(
    llm: Any, tools: list, memory: Optional[ArgusMemory] = None
) -> Any:
    """Build a custom StateGraph with text-based ReAct parsing.

    Works with any LLM (no native tool_calls needed).
    The LLM outputs: Thought/Action/Action Input/Final Answer.
    """
    tool_map = _build_tool_map(tools)

    # -- Nodes ------------------------------------------
    def agent_node(state: ArgusAgentState) -> dict:
        """LLM generates the next Action: format=json structured decoding first
        (012 FR-C9), falling back to free-text ReAct output for parse_node's
        regex parser when structured decoding is unavailable/fails (FR-C10)."""
        system_text = build_react_system_prompt({**state, "_tools": tool_map})
        structured_content = _try_structured_action(llm, system_text, state["messages"])
        if structured_content is not None:
            response = AIMessage(content=structured_content)
        else:
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

        Also blocks a call whose (tool, input) pair exactly matches one
        already in `state["tool_call_history"]` - see the inline comment
        below for why.

        Args:
            state (ArgusAgentState): Current graph state; reads the latest
                message (the agent's raw output) and `tool_call_history`.

        Returns:
            dict: A partial state update. On success: `tool_name`/`tool_input`/
            `phase`. On a format error or blocked duplicate call: `tool_error`,
            `tool_name`/`tool_input` cleared to `None`, `phase` set to
            `"format_error"`/`"duplicate_call"`, and a guidance `HumanMessage`
            appended to `messages`.
        """
        last = state["messages"][-1]
        content = str(last.content) if hasattr(last, "content") else str(last)
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

        # A live run against scanme.nmap.org repeated an identical
        # Recon_Suite call 4 times in a row despite it succeeding the first
        # time - the prompt's own "never repeat the same tool with the same
        # input" rule is advisory text the model doesn't reliably follow.
        # Enforce it structurally instead of trusting the model to self-police
        # - but allow exactly TWO real executions (matching the original
        # app/core/prompts.py design's own tolerance: "do not execute the
        # same tool with the same input more than TWICE") before blocking a
        # third, rather than zero-tolerance on the very first repeat. A
        # transient failure (flaky network blip, a WAF rate-limit that
        # clears seconds later) deserves one real retry if the model doubts
        # the first result - only a THIRD identical attempt is treated as
        # the model just not making progress.
        if result.get("tool_name"):
            call_key = f"{result['tool_name']}::{result.get('tool_input', '')}"
            if state.get("tool_call_history", []).count(call_key) >= 2:
                # A live run oscillated between two already-blocked tools for
                # several turns before finally giving a Final Answer - vague
                # "choose something different" guidance isn't concrete enough
                # for the model to act on reliably. List the tools it hasn't
                # touched at all this run by name, so there's always a
                # concrete next step instead of another guess.
                tried_names = {entry.partition("::")[0] for entry in state.get("tool_call_history", [])}
                untried = [name for name in tool_map if name not in tried_names]
                untried_block = (
                    ", ".join(untried) if untried
                    else "(none - every available tool has been tried at least once)"
                )
                guidance = (
                    f"Observation: You already called {result['tool_name']} with "
                    f"input '{result.get('tool_input', '')}' TWICE earlier this "
                    f"run - a third identical attempt would not produce a new "
                    f"result. Tools you have NOT tried yet this run: "
                    f"{untried_block}. Pick one of those with a relevant input, "
                    f"or a genuinely different input for a tool you've already "
                    f"used. Only give your Final Answer if every relevant tool "
                    f"for this target has truly been tried."
                )
                return {
                    "tool_error": guidance,
                    "tool_name": None,
                    "tool_input": None,
                    "phase": "duplicate_call",
                    "messages": [HumanMessage(content=guidance)],
                }

        return result

    def execute_node(state: ArgusAgentState) -> dict:
        """Run the chosen tool and feed back the Observation.

        Args:
            state (ArgusAgentState): Current graph state; reads `tool_name`/
                `tool_input` (set by `parse_node`) and `tool_call_history`.

        Returns:
            dict: A partial state update with `tool_result`/`tool_error`/
            `blackboard_summary`, an Observation `HumanMessage` appended to
            `messages`, and - on success - `tool_call_history` with this
            call's `"{name}::{input}"` key appended, so `parse_node` can
            block an identical repeat next time.
        """
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
            call_key = f"{name}::{inp}"
            update = {
                "tool_result": str(result)[:2000],
                "tool_error": None,
                "blackboard_summary": bb,
                "messages": [HumanMessage(content=obs)],
                "tool_call_history": state.get("tool_call_history", []) + [call_key],
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

    # -- Conditional routers ----------------------------
    def route_after_agent(state: ArgusAgentState) -> str:
        return "parse"

    def route_after_parse(state: ArgusAgentState) -> str:
        """Decide the next node after `parse_node`.

        Args:
            state (ArgusAgentState): Current graph state; reads `phase`,
                `tool_name`, `iteration_count`, and `max_iterations`.

        Returns:
            str: One of `"end"` (done, or a format/duplicate-call loop that
            hit `max_iterations`), `"agent"` (retry after a format error or
            blocked duplicate call), or `"execute"` (a valid new tool call).
        """
        phase = state.get("phase", "")
        if phase == "done":
            return "end"
        if phase in ("format_error", "duplicate_call"):
            # Bug fixed (specs/018): this previously routed straight back to
            # "agent" with no iteration check at all, unlike the tool-execute
            # path below. A model that never once produces valid output (the
            # exact live failure this spec fixes) would loop here forever,
            # bounded only by LangGraph's default recursion_limit (25) via an
            # ungraceful GraphRecursionError - not by max_iterations, and not
            # a clean "no final answer" result. duplicate_call (specs/018
            # addendum 2) shares this same bound for the same reason - a
            # model that keeps re-proposing the same blocked call needs the
            # same safety net a model that never produces valid output does.
            if state["iteration_count"] >= state["max_iterations"]:
                return "end"
            return "agent"  # loop back so model sees the format/duplicate-call error
        if state.get("tool_name"):
            return "execute"
        return "end"

    def route_after_execute(state: ArgusAgentState) -> str:
        if state["iteration_count"] >= state["max_iterations"]:
            return "end"
        return "agent"

    # -- Assemble ---------------------------------------
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


# =======================================================
# Helpers
# =======================================================
def _build_tool_map(tools: list) -> Dict[str, Callable]:
    """Convert a list of tools/callables to a name -> func dict."""
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
