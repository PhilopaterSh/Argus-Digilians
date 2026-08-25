"""Dynamic prompt builders for Argus LangGraph workflows.

`build_react_system_prompt`'s PHASE 1-8 progression (specs/018 CHK085
addendum, extended 2026-07-10) restores the intent of the original
`app/core/prompts.py` template's PHASE 1-9 structure - which ArgusBrain no
longer uses directly (specs/018 replaced it with this shorter, more
reliable prompt) - adapted to the tools
`app/core/agent/brain_tools.py::build_argus_tools()` actually provides
today (`Run_Specialized_Module` referenced by the old template's PHASE 7/8
does not exist on `WSLBridgeTools` and was dropped, not ported - confirmed
via `grep 'name="' app/core/agent/brain_tools.py`, so PHASE 7 below routes
escalation through `Run_Kali_Command`/`Secret_Scanner`/`Advanced_Evasion_Probe`
instead, the real tools that can actually do it).

2026-07-10: the old free-text-parsing agent (`app/core/prompts.py` +
`agent_factory.py`, `max_iterations=50`) sometimes ran far longer than this
one, but specs/018's own incident (a live run against cultbeauty.co.uk that
burned all 900s/26 retries with zero results because the model never once
produced a parseable line) proved that extra runtime was often a
failure-retry loop, not extra thoroughness - so depth was restored here as
an explicit PHASE 7 (Chaining & Escalation) plus a higher iteration ceiling
(see `brain.py::DEFAULT_MAX_ITERATIONS`), not by reverting structured-output
parsing or the reliability rules below. This keeps Argus's single-loop agent
grounded in the project's standing reference, Red-MIRROR
(`docs/history/2603.27127v1.pdf`) - PHASE 7 is this project's single-agent
analogue of the paper's Planner Agent aggregating global context to decide
whether to escalate an already-confirmed vulnerability class (Sec. 3.3.2),
without the paper's separate multi-agent DAG (that split is deferred to
specs/020, still proposed).
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
    reflection_block = _format_reflection_notes(state.get("reflection_notes", []))

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
        f"REFLECTION NOTES (specs/019 - concrete signals from prior attempts\n"
        f"this run; use these to change your approach, not repeat it):\n"
        f"{reflection_block}\n\n"
        f"TOOLS ALREADY CALLED THIS RUN (you may retry ONE of these with the\n"
        f"exact same input if you doubt the result - a THIRD identical attempt\n"
        f"will be blocked, not re-executed):\n{called_block}\n\n"
        f"TOOLS AVAILABLE:\n{tool_block}\n\n"
        f"RECOMMENDED PHASE PROGRESSION (skip a phase only if it doesn't apply -\n"
        f"e.g. no reachable service at all - not because it's inconvenient):\n"
        f"  PHASE 1 (Connectivity): Check_Reachability first, always.\n"
        f"  PHASE 2 (Surface Mapping): Subdomain_Enumeration, Recon_Suite, and\n"
        f"    Crawl_Target to discover internal links/entry points.\n"
        f"  PHASE 3 (Context): Query_Memory/Query_Knowledge_Graph if this target\n"
        f"    has prior history worth reviewing before scanning further.\n"
        f"  PHASE 4 (Web Intelligence & Leak Detection): Smart_Web_Search for\n"
        f"    CVEs/exploits on any technology or version Phase 2 discovered, and\n"
        f"    Secret_Scanner for leaked API keys/credentials on any page found.\n"
        f"  PHASE 5 (Vulnerability Scanning): Run_Nikto and/or Run_FFUF against a\n"
        f"    discovered web service, and Fuzz_Sensitive_Files to check common\n"
        f"    sensitive paths (.env, .git/config, backup.sql) for exposure.\n"
        f"  PHASE 6 (Exploitation): Exploit_Suggester to research payloads for any\n"
        f"    vulnerability class Phase 5 confirmed, then actually attempt the\n"
        f"    exploit - research alone (Exploit_Suggester) is not exploitation.\n"
        f"    Pick the RIGHT attempt tool for the class:\n"
        f"      - Path traversal / LFI / file inclusion, or ANY target with a\n"
        f"        file-ish parameter (filename, file, page, path, doc, include,\n"
        f"        download, template) or a page title mentioning file paths:\n"
        f"        use Path_Traversal_Scan. It is the dedicated tool - it discovers\n"
        f"        injectable endpoints itself (including ones only visible in an\n"
        f"        <img src>, e.g. /image?filename=), sweeps a full depth x encoding\n"
        f"        matrix (raw, %2f, %252f, %c0%af, backslash, ....//), and confirms\n"
        f"        by matching real file content, not an HTTP status. Pass it the\n"
        f"        target URL; it needs no payload from you. Advanced_Evasion_Probe\n"
        f"        only ever tries one fixed `?item=` parameter and is NOT a\n"
        f"        substitute for it.\n"
        f"      - SQL injection, or when a WAF was fingerprinted and you want\n"
        f"        evasion-encoded probes: use Advanced_Evasion_Probe.\n"
        f"    Do NOT hand-build traversal payloads into a URL and pass that to\n"
        f"    Advanced_Evasion_Probe - call Path_Traversal_Scan on the plain URL.\n"
        f"  PHASE 7 (Chaining & Escalation): if Phase 4-6 confirmed ANYTHING\n"
        f"    exploitable (leaked credentials, a working injection, an exposed\n"
        f"    admin/config path), don't stop at the first confirmation - chain it\n"
        f"    further with Run_Kali_Command (e.g. try leaked credentials against a\n"
        f"    discovered login endpoint, fetch a discovered backup/config file and\n"
        f"    read its contents) and re-run Secret_Scanner on anything new that\n"
        f"    chain step exposes, to reach the deepest impact you can actually\n"
        f"    demonstrate (e.g. real data exposure, not just 'this looks injectable').\n"
        f"    Skip this phase only if Phase 4-6 found nothing to chain from.\n"
        f"  PHASE 8 (Final Analysis): synthesize everything into the Final Answer.\n"
        f"Utility tools, usable at any point: Reflective_Pre_Verify (sanity-check a\n"
        f"command before running it), Task_Difficulty_Assessment (score target\n"
        f"priority), Run_Kali_Command (anything the above tools can't do directly),\n"
        f"System_Self_Heal/Archive_Research_Subagent (as needed).\n\n"
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


def build_collector_prompt(state: dict) -> str:
    """Build the Collector role's system prompt (specs/020, feature-flagged
    off by default - see config.yaml's enable_multi_agent_roles).

    Scoped to recon/discovery tools only (FR-002) - Collector proposes and
    executes exactly ONE tool call per graph visit, then control returns to
    the Planner, which decides the next role. Same Thought/Action output
    format as the single-loop prompt (`build_react_system_prompt`) for
    consistency and to reuse the same parsing code.

    Args:
        state (dict): Current graph state (an `ArgusAgentState`, passed as a
            plain dict); reads the same fields `build_react_system_prompt`
            does, plus `_tools` scoped to Collector's subset by the caller.

    Returns:
        str: The complete system prompt text for this turn.
    """
    tool_block = _format_tool_descriptions(state.get("_tools", {}))
    called_block = _format_call_history(state.get("tool_call_history", []))
    reflection_block = _format_reflection_notes(state.get("reflection_notes", []))
    return (
        f"ROLE: You are the Collector agent in Argus AI's multi-agent pentesting team.\n"
        f"Your ONLY job is reconnaissance and discovery - mapping the target's attack\n"
        f"surface, finding leaked secrets, and gathering context. You do NOT scan for\n"
        f"vulnerabilities or attempt exploitation - that's the Exploiter agent's job.\n"
        f"TARGET: {state.get('target', 'unknown')}\n\n"
        f"BLACKBOARD (live intelligence from the whole team):\n"
        f"{state.get('blackboard_summary', 'No findings yet.')}\n\n"
        f"LAST TOOL OUTPUT:\n{state.get('tool_result', 'None')}\n"
        f"LAST ERROR:\n{state.get('tool_error', 'None')}\n\n"
        f"REFLECTION NOTES:\n{reflection_block}\n\n"
        f"TOOLS ALREADY CALLED THIS RUN (may retry ONE once if you doubt the result):\n"
        f"{called_block}\n\n"
        f"YOUR TOOLS:\n{tool_block}\n\n"
        f"RULES:\n"
        f"1. Choose ONE tool per response.\n"
        f"2. Don't repeat a call you already trust the result of.\n"
        f"3. You never give a Final Answer - the Planner decides when your job here is done.\n\n"
        f"OUTPUT FORMAT (exact):\n"
        f"Thought: <your reasoning>\n"
        f"Action: {{\"name\": \"ToolName\", \"input\": \"value\"}}\n\n"
        f"Available tool names: {list(state.get('_tools', {}).keys())}"
    )


def build_exploiter_prompt(state: dict) -> str:
    """Build the Exploiter role's system prompt (specs/020, feature-flagged
    off by default). Mirrors `build_collector_prompt` but scoped to
    vulnerability-scanning/exploitation tools (FR-002).

    Args:
        state (dict): Current graph state; see `build_collector_prompt`.

    Returns:
        str: The complete system prompt text for this turn.
    """
    tool_block = _format_tool_descriptions(state.get("_tools", {}))
    called_block = _format_call_history(state.get("tool_call_history", []))
    reflection_block = _format_reflection_notes(state.get("reflection_notes", []))
    return (
        f"ROLE: You are the Exploiter agent in Argus AI's multi-agent pentesting team.\n"
        f"Your ONLY job is vulnerability scanning and exploitation - the Collector agent\n"
        f"already mapped the attack surface below. Research a payload for any\n"
        f"vulnerability class the Blackboard suggests, then actually attempt it - research\n"
        f"alone without attempting it is not exploitation.\n"
        f"TARGET: {state.get('target', 'unknown')}\n\n"
        f"BLACKBOARD (live intelligence from the whole team):\n"
        f"{state.get('blackboard_summary', 'No findings yet.')}\n\n"
        f"LAST TOOL OUTPUT:\n{state.get('tool_result', 'None')}\n"
        f"LAST ERROR:\n{state.get('tool_error', 'None')}\n\n"
        f"REFLECTION NOTES:\n{reflection_block}\n\n"
        f"TOOLS ALREADY CALLED THIS RUN (may retry ONE once if you doubt the result):\n"
        f"{called_block}\n\n"
        f"YOUR TOOLS:\n{tool_block}\n\n"
        f"RULES:\n"
        f"1. Choose ONE tool per response.\n"
        f"2. Don't repeat a call you already trust the result of.\n"
        f"3. You never give a Final Answer - the Planner decides when your job here is done.\n\n"
        f"OUTPUT FORMAT (exact):\n"
        f"Thought: <your reasoning>\n"
        f"Action: {{\"name\": \"ToolName\", \"input\": \"value\"}}\n\n"
        f"Available tool names: {list(state.get('_tools', {}).keys())}"
    )


def build_planner_prompt(state: dict) -> str:
    """Build the Planner role's system prompt (specs/020, feature-flagged
    off by default). The Planner owns the phase-transition decision (FR-003)
    - it never calls an execution tool itself, only decides which role acts
    next based on the Blackboard's current state.

    Args:
        state (dict): Current graph state; reads `target`/`blackboard_summary`/
            `reflection_notes`/`role_history`.

    Returns:
        str: The complete system prompt text for this turn.
    """
    reflection_block = _format_reflection_notes(state.get("reflection_notes", []))
    role_history = state.get("role_history", [])
    history_block = " -> ".join(role_history) if role_history else "(run just started)"
    return (
        f"ROLE: You are the Planner agent in Argus AI's multi-agent pentesting team.\n"
        f"You do not run tools yourself. You look at what the team has learned so far and\n"
        f"decide which specialist acts next.\n"
        f"TARGET: {state.get('target', 'unknown')}\n\n"
        f"BLACKBOARD (live intelligence from the whole team):\n"
        f"{state.get('blackboard_summary', 'No findings yet.')}\n\n"
        f"REFLECTION NOTES:\n{reflection_block}\n\n"
        f"ROLE HISTORY THIS RUN: {history_block}\n\n"
        f"YOUR SPECIALISTS:\n"
        f"- collector: reconnaissance, attack-surface mapping, leak detection. Send work here\n"
        f"  if the Blackboard doesn't yet show a mapped attack surface for this target.\n"
        f"- exploiter: vulnerability scanning and exploitation attempts. Send work here once\n"
        f"  the Collector has found something to scan or exploit.\n"
        f"- summarizer: produces the final report. Choose this once the team has attempted\n"
        f"  both reconnaissance AND at least one vulnerability-scanning/exploitation step -\n"
        f"  not before, and not indefinitely after (don't loop the same specialist forever\n"
        f"  if the Blackboard isn't changing).\n\n"
        f"Decide the single next specialist to act."
    )


def build_summarizer_prompt(state: dict) -> str:
    """Build the Summarizer role's system prompt (specs/020, feature-flagged
    off by default). The Summarizer is the only role that produces the
    final `SecurityReport` (FR-004) - it synthesizes the whole team's
    findings, never executes a tool.

    Args:
        state (dict): Current graph state; reads `target`/`blackboard_summary`.

    Returns:
        str: The complete system prompt text for this turn.
    """
    return (
        f"ROLE: You are the Summarizer agent in Argus AI's multi-agent pentesting team.\n"
        f"The Collector and Exploiter agents have finished their work below. Synthesize\n"
        f"everything into a comprehensive security report. You do not run tools.\n"
        f"TARGET: {state.get('target', 'unknown')}\n\n"
        f"BLACKBOARD (everything the team found):\n"
        f"{state.get('blackboard_summary', 'No findings yet.')}\n\n"
        f"RULES:\n"
        f"1. Your overall_risk_score MUST match the severities of your own findings - if\n"
        f"   every finding is Low severity with no remediation needed, the score must be\n"
        f"   low (e.g. 1-3), not high.\n"
        f"2. If the team found nothing exploitable, say so explicitly rather than inflating\n"
        f"   the assessment.\n\n"
        f"Final Answer: <comprehensive security report>"
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


def _format_reflection_notes(reflection_notes: list) -> str:
    """Format specs/019's structured reflection notes for the prompt.

    Args:
        reflection_notes (list[str]): Notes appended by `react_workflow.py`'s
            `parse_node` (Intra-reflection, on a blocked duplicate call) and
            `execute_node` (Inter-reflection majority-vote verdicts,
            early-termination flag nudges).

    Returns:
        str: One `"  - {note}"` line per entry, most recent last (natural
        append order), or `"  (none yet)"` if empty.
    """
    if not reflection_notes:
        return "  (none yet)"
    return "\n".join(f"  - {note}" for note in reflection_notes)


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
