"""Dynamic prompt builders for Argus LangGraph workflows."""


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
        f"TOOLS ALREADY CALLED THIS RUN (calling one of these again with the\n"
        f"same input will be blocked, not re-executed):\n{called_block}\n\n"
        f"TOOLS AVAILABLE:\n{tool_block}\n\n"
        f"RULES:\n"
        f"1. Choose ONE tool per response.\n"
        f"2. NEVER repeat a tool+input pair listed above under \"TOOLS ALREADY\n"
        f"   CALLED THIS RUN\" - it will not run again; use its Observation\n"
        f"   (in the Blackboard above) or the conversation history instead.\n"
        f"3. If a tool fails, analyse the error and choose a different approach.\n"
        f"4. After running a tool, wait for the Observation before deciding next step.\n\n"
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
