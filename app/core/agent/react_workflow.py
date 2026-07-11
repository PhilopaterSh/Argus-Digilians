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

# specs/019-shared-memory-reflection-upgrade: tools whose raw output requires
# judgment to interpret as success/failure (Red-MIRROR's Exploiter-Agent-
# owned action space, Section 3.6.2) - scoped Inter-reflection (3x
# self-consistency majority vote) to these only. Deliberately excludes purely
# informational/deterministic tools (Check_Reachability, Query_Memory, etc.)
# where a single pass already suffices and tripling LLM calls would add
# latency for no benefit. Matches the exact tool names in
# app/core/agent/brain_tools.py::build_argus_tools() - kept here as the one
# place other modules should import from (Constitution IX), not re-listed.
EXPLOITATION_TOOLS = frozenset({
    "Advanced_Evasion_Probe",
    "Secret_Scanner",
    "Run_Nikto",
    "Run_FFUF",
})

# react_prompts.py's Rule 5 ("Reconnaissance alone (Phases 1-2) is NOT a
# complete analysis... also attempt Phase 5 or 6 before giving a Final
# Answer") was advisory text only - a live run against scanme.nmap.org
# concluded after just Check_Reachability/Subdomain_Enumeration/Recon_Suite
# (Phases 1-2), never touching any of these, because nothing in the code
# actually required it. Enforced structurally below (parse_node) as a
# ONE-TIME nudge, not a hard block - forcing a scan against a target with no
# reachable web service at all would be pointless, so the model is given one
# chance to either use one of these or explicitly justify skipping them.
PHASE_5_6_TOOLS = frozenset({
    "Run_Nikto",
    "Run_FFUF",
    "Exploit_Suggester",
    "Advanced_Evasion_Probe",
})

# specs/019: matches Red-MIRROR's Inter-reflection Step 2 (Algorithm 4) -
# early-termination flag check, independent of Final Answer detection.
_FLAG_PATTERN = re.compile(r"flag\{[^}]+\}", re.IGNORECASE)


def _check_early_termination(text: str) -> Optional[str]:
    """Return the first `flag{...}`-shaped match in `text`, or None.

    Args:
        text (str): Tool result / observation text to scan.

    Returns:
        Optional[str]: The matched flag string, or None if no flag-shaped
        substring is present.
    """
    match = _FLAG_PATTERN.search(text or "")
    return match.group(0) if match else None


def _build_reflection_note(prior_action: str, prior_response: str) -> str:
    """Structured Intra-reflection note (specs/019 FR-005; Red-MIRROR Algorithm 3
    `ReflectAndUpdate`), replacing the previous generic "try something
    different" guidance with a response-aware suggestion.

    A lightweight keyword heuristic, not a second LLM call - keeps this on
    the hot path of every blocked duplicate-call without adding latency.

    Args:
        prior_action (str): The `"{tool}::{input}"` call being blocked.
        prior_response (str): The most recent tool_result/tool_error text
            for that action, if available.

    Returns:
        str: A one-line note naming a concrete dimension to change.
    """
    text = (prior_response or "").lower()
    if "403" in text or "blocked" in text or "forbidden" in text:
        suggestion = "try a different encoding or bypass technique - the request appears to have been blocked (WAF/filter)"
    elif "timeout" in text or "timed out" in text:
        suggestion = "try a different endpoint or method - the previous attempt timed out"
    elif "404" in text or "not found" in text:
        suggestion = "try a different path/endpoint - the previous target path was not found"
    elif "500" in text or "error" in text:
        suggestion = "try a different payload - the server returned an error, which may itself be a signal worth investigating differently"
    else:
        suggestion = "try a genuinely different input or technique, not a repeat of the same request"
    return f"Reflection: prior attempt '{prior_action}' -> {suggestion}."


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


def _inter_reflect(llm: Any, action: str, response: str) -> Optional[bool]:
    """3x self-consistency majority vote on whether a tool call succeeded
    (specs/019 FR-006; Red-MIRROR Algorithm 4 Step 1 / Eq. 10).

    Invokes `llm.invoke()` three times with a fixed, low-variance prompt and
    takes the majority (>=2/3) "yes" as the success verdict - reduces
    single-pass hallucination in judging ambiguous tool output, per the
    paper's own cited technique (Wang et al., ICLR 2023).

    Args:
        llm (Any): The LLM in use.
        action (str): The `"{tool}::{input}"` call being judged.
        response (str): The tool's raw result text.

    Returns:
        Optional[bool]: Majority verdict, or None if all 3 calls raised
        (e.g. LLM unreachable) - callers must treat None as inconclusive,
        never silently treat it as success (Constitution VIII).
    """
    prompt = (
        f"A penetration-testing tool was invoked: {action}\n"
        f"Its result was:\n{str(response)[:1500]}\n\n"
        f"Did this tool call achieve a genuine security finding or successful "
        f"exploitation step (not just execute without error)? Answer with "
        f"exactly one word: yes or no."
    )
    votes = []
    for _ in range(3):
        try:
            reply = llm.invoke([HumanMessage(content=prompt)])
            content = str(getattr(reply, "content", reply)).strip().lower()
            votes.append("yes" in content)
        except Exception:
            continue
    if not votes:
        return None
    yes_count = sum(1 for v in votes if v)
    return yes_count > len(votes) / 2


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
    llm: Any,
    tools: list,
    memory: Optional[ArgusMemory] = None,
    enable_inter_reflection: bool = True,
) -> Any:
    """Build a custom StateGraph with text-based ReAct parsing.

    Works with any LLM (no native tool_calls needed).
    The LLM outputs: Thought/Action/Action Input/Final Answer.

    Args:
        enable_inter_reflection (bool): specs/019 FR-006/NFR-002 escape
            hatch - when False, `execute_node` skips the 3x majority-vote
            check for `EXPLOITATION_TOOLS` entirely, restoring the
            pre-specs/019 single-pass behavior. Read from
            `ArgusConfig.enable_inter_reflection` by callers; defaults True
            here only for direct/test callers that don't thread config
            through.
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
                # specs/019 FR-005: structured, response-aware Intra-reflection
                # note - replaces the purely repetition-based guidance above
                # with a concrete "why did this fail, what to change" signal
                # drawn from the last real result for this exact call.
                prior_response = state.get("tool_error") or state.get("tool_result") or ""
                reflection_note = _build_reflection_note(call_key, str(prior_response))
                guidance = (
                    f"Observation: You already called {result['tool_name']} with "
                    f"input '{result.get('tool_input', '')}' TWICE earlier this "
                    f"run - a third identical attempt would not produce a new "
                    f"result. {reflection_note} Tools you have NOT tried yet "
                    f"this run: {untried_block}. Pick one of those with a "
                    f"relevant input, or a genuinely different input for a "
                    f"tool you've already used. Only give your Final Answer if "
                    f"every relevant tool for this target has truly been tried."
                )
                return {
                    "tool_error": guidance,
                    "tool_name": None,
                    "tool_input": None,
                    "phase": "duplicate_call",
                    "reflection_notes": state.get("reflection_notes", []) + [reflection_note],
                    "messages": [HumanMessage(content=guidance)],
                }

        if result.get("phase") == "done":
            tried_names = {entry.partition("::")[0] for entry in state.get("tool_call_history", [])}
            # Only nudge a run that attempted at least one tool - a Final
            # Answer with zero tool calls at all is a different, broader
            # problem (skipping every phase, not specifically 5/6) out of
            # scope for this check.
            if tried_names and not (tried_names & PHASE_5_6_TOOLS) and not state.get("phase56_nudged", False):
                nudge = (
                    "Observation: Before concluding, note that you have not yet "
                    "attempted vulnerability scanning or exploitation research "
                    "(Run_Nikto, Run_FFUF, Exploit_Suggester, "
                    "Advanced_Evasion_Probe) against this target. If a reachable "
                    "web service exists, try one of these now. If Phase 5/6 "
                    "genuinely does not apply (e.g. no reachable web service was "
                    "found), state that explicitly in your Final Answer instead "
                    "of omitting it silently."
                )
                return {
                    "tool_error": nudge,
                    "tool_name": None,
                    "tool_input": None,
                    "phase": "phase56_check",
                    "phase56_nudged": True,
                    "reflection_notes": state.get("reflection_notes", []) + [nudge],
                    "messages": [HumanMessage(content=nudge)],
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
            extra_messages = []
            reflection_notes = list(state.get("reflection_notes", []))

            # specs/019 FR-007 (Red-MIRROR Algorithm 4 Step 2): early-termination
            # flag check, independent of "Final Answer:" detection - a nudge
            # via the message stream, not a forced structural exit, so
            # _finalize_graph_output()'s existing "Final Answer:" requirement
            # (Constitution VIII - never fabricate a report) stays the single
            # source of truth for when the graph is actually done.
            found_flag = _check_early_termination(str(result))
            if found_flag:
                nudge = (
                    f"Reflection: a flag-shaped string was found in this "
                    f"result ({found_flag}). Provide your Final Answer now "
                    f"if this satisfies the objective."
                )
                extra_messages.append(HumanMessage(content=nudge))
                reflection_notes.append(nudge)

            # specs/019 FR-006 (Red-MIRROR Algorithm 4 Step 1): 3x
            # self-consistency majority vote, scoped to EXPLOITATION_TOOLS
            # only (informational/deterministic tools don't need it).
            if enable_inter_reflection and name in EXPLOITATION_TOOLS:
                verdict = _inter_reflect(llm, call_key, str(result))
                if verdict is not None:
                    verdict_text = "SUCCESS" if verdict else "INCONCLUSIVE/NO FINDING"
                    reflect_msg = f"Reflection: majority-vote assessment of {name} result = {verdict_text}."
                    extra_messages.append(HumanMessage(content=reflect_msg))
                    reflection_notes.append(reflect_msg)

            update = {
                "tool_result": str(result)[:2000],
                "tool_error": None,
                "blackboard_summary": bb,
                "messages": [HumanMessage(content=obs)] + extra_messages,
                "tool_call_history": state.get("tool_call_history", []) + [call_key],
                "reflection_notes": reflection_notes,
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
            str: One of `"end"` (done, or a format/duplicate-call/phase56-check
            loop that hit `max_iterations`), `"agent"` (retry after a format
            error, blocked duplicate call, or phase5/6 nudge), or `"execute"`
            (a valid new tool call).
        """
        phase = state.get("phase", "")
        if phase == "done":
            return "end"
        if phase in ("format_error", "duplicate_call", "phase56_check"):
            # Bug fixed (specs/018): this previously routed straight back to
            # "agent" with no iteration check at all, unlike the tool-execute
            # path below. A model that never once produces valid output (the
            # exact live failure this spec fixes) would loop here forever,
            # bounded only by LangGraph's default recursion_limit (25) via an
            # ungraceful GraphRecursionError - not by max_iterations, and not
            # a clean "no final answer" result. duplicate_call (specs/018
            # addendum 2) and phase56_check (specs/019 follow-up) share this
            # same bound for the same reason - any soft-block/nudge path that
            # loops back to "agent" needs the same safety net a model that
            # never produces valid output does.
            if state["iteration_count"] >= state["max_iterations"]:
                return "end"
            return "agent"  # loop back so model sees the format/duplicate-call/nudge message
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
