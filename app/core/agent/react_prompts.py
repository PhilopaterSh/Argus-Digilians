"""Dynamic prompt builders for Argus LangGraph workflows.

`build_react_system_prompt`'s PHASE 1-7 progression (specs/018 CHK085
addendum) restores the intent of the original `app/core/prompts.py`
template's PHASE 1-9 structure - which ArgusBrain no longer uses directly
(specs/018 replaced it with this shorter, more reliable prompt) - adapted
to the tools `app/core/agent/brain_tools.py::build_argus_tools()` actually
provides today (`Run_Specialized_Module`/`Crawl_Target` referenced by the
old template don't exist on `WSLBridgeTools` and were dropped, not ported).
Kept deliberately terser than the original per-phase prose to avoid
reintroducing the prompt-length-driven format drift specs/018 fixed.
"""


def build_react_system_prompt(state: dict) -> str:
    """Build system prompt for the text-based ReAct agent.

    Works with any model (no native tool_calls required).
    The model outputs: Thought: / Action: / Action Input: / Final Answer:

    Args:
        state (dict): Current graph state (an `ArgusAgentState`, passed as a
            plain dict); reads `target`/`phase`/`iteration_count`/
            `max_iterations`/`blackboard_summary`/`tool_result`/`tool_error`/
            `tool_call_history`, plus `_tools` (a `{name: callable}` map
            injected by the caller, not part of the persisted graph state).

    Returns:
        str: The complete system prompt text for this turn.
    """
    tool_block = _format_tool_descriptions(state.get("_tools", {}))
    called_block = _format_call_history(state.get("tool_call_history", []))

    return (
        f"ROLE: You are Argus AI, a senior penetration testing specialist.\n"
        f"TARGET: {state.get('target', 'unknown')}\n"
        f"PHASE: {state.get('phase', 'init')}\n"
        f"ITERATION: {state.get('iteration_count', 0) + 1}\n"
        f"MAX ITERATIONS: {state.get('max_iterations', 10)}\n\n"
        f"BLACKBOARD (live intelligence):\n"
        f"{state.get('blackboard_summary', 'No findings yet.')}\n\n"
        f"LAST TOOL OUTPUT:\n{state.get('tool_result', 'None')}\n"
        f"LAST ERROR:\n{state.get('tool_error', 'None')}\n\n"
        f"TOOLS ALREADY CALLED THIS RUN (you may retry ONE of these with the\n"
        f"exact same input if you doubt the result - a THIRD identical attempt\n"
        f"will be blocked, not re-executed):\n{called_block}\n\n"
        f"TOOLS AVAILABLE:\n{tool_block}\n\n"
        f"RECOMMENDED PHASE PROGRESSION (skip a phase only if it doesn't apply -\n"
        f"e.g. no reachable service at all - not because it's inconvenient):\n"
        f"  PHASE 1 (Connectivity): Check_Reachability first, always.\n"
        f"  PHASE 2 (Surface Mapping): Subdomain_Enumeration, then Recon_Suite.\n"
        f"  PHASE 3 (Context): Query_Memory/Query_Knowledge_Graph if this target\n"
        f"    has prior history worth reviewing before scanning further.\n"
        f"  PHASE 4 (Web Intelligence): Smart_Web_Search for CVEs/exploits on any\n"
        f"    technology or version Phase 2 discovered.\n"
        f"  PHASE 5 (Vulnerability Scanning): Run_Nikto and/or Run_FFUF against a\n"
        f"    discovered web service.\n"
        f"  PHASE 6 (Exploit Research): Exploit_Suggester for any vulnerability\n"
        f"    class Phase 5 confirmed.\n"
        f"  PHASE 7 (Final Analysis): synthesize everything into the Final Answer.\n"
        f"Use Run_Kali_Command for anything the above tools can't do directly, and\n"
        f"System_Self_Heal/Archive_Research_Subagent as needed at any point.\n\n"
        f"RULES:\n"
        f"1. Choose ONE tool per response.\n"
        f"2. A tool+input pair listed above under \"TOOLS ALREADY CALLED THIS\n"
        f"   RUN\" may be retried ONCE if you genuinely doubt the result (e.g.\n"
        f"   a transient network error) - but a THIRD identical attempt will\n"
        f"   be blocked. Don't repeat just to double-check a result you\n"
        f"   already trust; use its Observation (in the Blackboard above) or\n"
        f"   the conversation history instead.\n"
        f"3. If a tool fails, analyse the error and choose a different approach.\n"
        f"4. After running a tool, wait for the Observation before deciding next step.\n"
        f"5. Reconnaissance alone (Phases 1-2) is NOT a complete analysis. Before\n"
        f"   giving a Final Answer, also attempt Phase 5 or 6 against a discovered\n"
        f"   service - a Final Answer based only on open-port data, with no\n"
        f"   vulnerability findings attempted, is incomplete for a\n"
        f"   comprehensive/deep assessment.\n"
        f"6. Your overall_risk_score MUST match the severities of your own\n"
        f"   findings - if every finding is Low severity with no remediation\n"
        f"   needed, the score must be low (e.g. 1-3), not high. Do not assign a\n"
        f"   high score to compensate for having few or inconclusive findings.\n\n"
        f"OUTPUT FORMAT (exact - choose ONE of these two formats):\n"
        f"\n"
        f"FORMAT A (JSON Action - preferred):\n"
        f"Thought: <your reasoning>\n"
        f"Action: {{\"name\": \"ToolName\", \"input\": \"value\"}}\n"
        f"\n"
        f"FORMAT B (Text Action - fallback):\n"
        f"Thought: <your reasoning>\n"
        f"Action: ToolName\n"
        f"Action Input: value\n"
        f"\n"
        f"When the objective is complete:\n"
        f"Final Answer: <comprehensive security report>\n\n"
        f"Available tool names: {list(state.get('_tools', {}).keys())}"
    )


def build_prebuilt_system_prompt(state: dict) -> str:
    """Build system prompt for the create_react_agent path.

    The model uses native tool_calls instead of text format.
    """
    return (
        f"You are Argus AI, a senior penetration testing specialist.\n"
        f"Target: {state.get('target', 'unknown')}\n"
        f"Phase: {state.get('phase', 'init')}\n"
        f"Blackboard Intelligence:\n{state.get('blackboard_summary', 'No findings yet.')}\n\n"
        f"Use the tools provided to perform reconnaissance and vulnerability assessment.\n"
        f"Analyse results step by step. When you have sufficient data, provide a final report."
    )


def _format_call_history(tool_call_history: list) -> str:
    """Format the run's already-executed (tool, input) pairs for the prompt.

    Args:
        tool_call_history (list[str]): Entries in `"{tool}::{input}"` form,
            as appended by `react_workflow.py`'s `execute_node`.

    Returns:
        str: One `"  - {tool}(\"{input}\")"` line per entry, or
        `"  (none yet)"` if the run hasn't executed any tool yet.
    """
    if not tool_call_history:
        return "  (none yet)"
    lines = []
    for entry in tool_call_history:
        tool, _, inp = entry.partition("::")
        lines.append(f'  - {tool}("{inp}")')
    return "\n".join(lines)


def _format_tool_descriptions(tool_map: dict) -> str:
    """Format tool map into a readable block for prompts.

    Args:
        tool_map (dict): `{name: callable}` map of available tools.

    Returns:
        str: One `"  {name}: {docstring}"` line per tool, sorted by name, or
        `"(no tools available)"` if `tool_map` is empty.
    """
    if not tool_map:
        return "(no tools available)"
    lines = []
    for name, fn in sorted(tool_map.items()):
        desc = fn.__doc__ or "No description"
        lines.append(f"  {name}: {desc}")
    return "\n".join(lines)
