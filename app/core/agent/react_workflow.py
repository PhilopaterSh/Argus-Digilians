"""LangGraph workflow builder for Argus AI.

Supports two modes:
1. **Prebuilt mode**: Uses create_react_agent for models with tool_calls support.
2. **Custom mode**: Custom StateGraph with text-based ReAct for any model.
"""
import json
import re
import warnings
from typing import Any, Callable, Dict, Optional
from urllib.parse import urlsplit

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
    build_collector_prompt,
    build_exploiter_prompt,
    build_planner_prompt,
    build_summarizer_prompt,
)
from app.core.memory.memory_service import ArgusMemory
from app.core.schemas import SecurityReport
from app.tools.utils import (
    to_bare_hostname,
    parse_subdomains,
    parse_tech_block,
    clean_tech_string,
    record_graph_edge,
)


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

# 2026-07-26: Phase 1-2 per react_prompts.py's own progression (Connectivity
# + Surface Mapping) - the foundation Phase 5/6 (and everything else) is
# supposed to be grounded in. Enforced the same way as PHASE_5_6_TOOLS
# above: a one-time nudge, not a hard block. Companion to the same day's
# zero_tool_check (react_workflow.py::parse_node) - that check catches the
# more severe "no tool call at all" case; this one catches a model that
# calls SOME tool(s) (so zero_tool_check doesn't fire) but skips straight
# to Phase 3+ (e.g. only Query_Memory/Smart_Web_Search) without ever
# establishing real connectivity/recon on this specific target first.
PHASE_1_2_TOOLS = frozenset({
    "Check_Reachability",
    "Subdomain_Enumeration",
    "Recon_Suite",
    "Crawl_Target",
})

# Live-discovered 2026-07-25: a real run against a PortSwigger lab called
# Recon_Suite twice (the guard's own allowed retry), got blocked on the
# third identical attempt as designed - then kept re-proposing the exact
# same blocked call (or oscillating between it and another already-blocked
# tool) 18 times in a row, burning the entire max_iterations=25 budget
# before finally hitting the existing iteration check and reporting a bare
# "no_final_answer" error. The guidance message parse_node already sends on
# a block ("pick one of those [untried tools]") is advisory text only - like
# react_prompts.py's own "never repeat" rule, nothing stops a model from
# ignoring it, which is exactly what specs/018's original duplicate-call fix
# was meant to structurally prevent for the FIRST repeat but not for
# repeatedly ignoring the block itself. Rather than silently spending the
# rest of the iteration budget on a conversation that provably cannot
# change outcome (the guard's own hard block guarantees the Nth+1 attempt
# produces the identical guidance every time), this caps how many
# *consecutive* duplicate_call turns are tolerated before the run concludes
# early with an honest, partial Final Answer summarizing what was actually
# tried - faster AND more informative than "no_final_answer" after burning
# the full budget. 3 (not 1) preserves room for the model to genuinely
# recover by trying something else in between two blocked attempts; only a
# model that is blocked three turns running - never producing a single
# valid new action in between - is treated as unrecoverable this run.
MAX_CONSECUTIVE_DUPLICATE_BLOCKS = 3

# specs/019: matches Red-MIRROR's Inter-reflection Step 2 (Algorithm 4) -
# early-termination flag check, independent of Final Answer detection.
_FLAG_PATTERN = re.compile(r"flag\{[^}]+\}", re.IGNORECASE)

# Live-discovered 2026-07-19: a tool result can be arbitrarily large (e.g.
# Subdomain_Enumeration against a domain with heavy passive-DNS noise like
# example.com returning ~3000 lines) - the `tool_result` STATE field was
# already bounded to this same length, but the Observation message actually
# shown to the LLM was not, and an unbounded observation demonstrably
# derailed the model into hallucinating an unrelated vulnerability instead
# of reasoning about the real recon data. Matches OBSERVATION_MAX_CHARS
# below to `tool_result`'s existing bound for consistency, not a new value.
OBSERVATION_MAX_CHARS = 2000


# Live-discovered 2026-07-25 (same incident as MAX_CONSECUTIVE_DUPLICATE_BLOCKS
# above, confirmed by web research on this exact failure class - agents
# calling e.g. search("auth errors") then search("login failures") never
# register as duplicates under naive exact-string matching): call_key's
# exact-string match means two calls that are semantically identical but
# textually different - "http://target.com" vs "http://target.com/" (a
# trailing slash), or an LLM inserting/dropping a stray space - never
# register as the "same" call at all, silently bypassing the duplicate-call
# guard entirely instead of tripping it, which is one credible way a model
# could reach 18 Recon_Suite calls despite the guard's own "block the 3rd
# identical attempt" rule. Deliberately NOT lowercasing or otherwise
# touching path/query content: several Phase 5/6 tools
# (Advanced_Evasion_Probe, Run_FFUF) pass case-sensitive payloads as
# tool_input where two differently-cased strings genuinely are different
# attack attempts - folding case here would make the guard wrongly collapse
# two distinct payloads into "the same call". Scoped to the one universally
# safe normalization: incidental whitespace and a single trailing slash.
def _normalize_call_input(tool_input: str) -> str:
    """Normalize a tool_input string for duplicate-call comparison only.

    Collapses incidental whitespace differences and a single trailing
    slash so semantically-identical calls (e.g. differing only by a
    trailing "/" or a stray space) are recognised as the same call by the
    duplicate-call guard. Does not lowercase or otherwise touch payload
    content, since several tools' inputs are case-sensitive payloads.

    Args:
        tool_input (str): The raw tool_input string as produced by
            `_parse_react_output`.

    Returns:
        str: The normalized string, used only as part of `call_key` for
        duplicate detection - never shown to the model or used for actual
        tool execution (the original, unnormalized `tool_input` is what
        gets passed to the tool).
    """
    normalized = re.sub(r"\s+", " ", (tool_input or "")).strip()
    if len(normalized) > 1 and normalized.endswith("/"):
        normalized = normalized.rstrip("/")
    return normalized


def _bounded_observation(result: Any) -> str:
    """Render a tool result as an Observation message, bounded so a single
    oversized result can't crowd out the model's usable context.

    Args:
        result (Any): The raw tool return value (usually a str).

    Returns:
        str: `str(result)`, truncated to `OBSERVATION_MAX_CHARS` with a
        trailing notice if truncation happened - so the model knows the
        data is partial rather than silently reasoning over a cut-off list
        as if it were complete.
    """
    text = str(result)
    if len(text) <= OBSERVATION_MAX_CHARS:
        return text
    omitted = len(text) - OBSERVATION_MAX_CHARS
    return f"{text[:OBSERVATION_MAX_CHARS]}\n... [truncated, {omitted} more characters omitted]"


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


# 2026-07-11: live testing against a real PortSwigger Web Security Academy
# lab found Recon_Suite's own tech-fingerprint output contained
# `Title[File path traversal, simple case...]` - the target's actual
# vulnerability class, stated outright - and the model never acted on it,
# running a generic Nikto scan instead. Research on this exact failure mode
# ("Looking Is Not Picking: An Attention-Segment Account of Tool-Selection
# Failures in LLM Agents", arXiv:2606.16364) found the model can attend to
# the right information and still pick wrong, and that prompt-only fixes
# recover at most ~23% of such failures - the higher-recovery fixes need
# access to model internals (attention/logit steering) not exposed by
# Ollama's standard API for this model. So this doesn't rely on the model
# noticing on its own: it's a deterministic, code-level scan that hands the
# model an explicit, unambiguous directive instead.
_TITLE_PATTERN = re.compile(r"Title\[([^\]]+)\]", re.IGNORECASE)
_VULN_CLASS_KEYWORDS = (
    "path traversal", "directory traversal", "sql injection", "cross-site scripting",
    "cross-site request forgery", "server-side request forgery", "xml external entity",
    "insecure direct object", "authentication bypass", "access control",
    "insecure deserialization", "template injection", "command injection", "file upload",
    "clickjacking", "open redirect", "race condition", "json web token",
    "cors misconfiguration", "prototype pollution", "ldap injection", "nosql injection",
    "request smuggling", "cache poisoning", "information disclosure",
)


def _matched_vuln_keywords(text: str) -> list[str]:
    """Return the `_VULN_CLASS_KEYWORDS` entries that appear verbatim
    (case-insensitive) in `text`, sorted alphabetically.

    Factored out of `_extract_vulnerability_hints` so `_live_test_directive`
    below can build a tool-specific instruction from the same matched set
    instead of re-parsing the human-readable hint sentences.

    Args:
        text (str): Tool result / observation text to scan.

    Returns:
        list[str]: Matched keywords, or `[]` if none matched.
    """
    if not text:
        return []
    lower = text.lower()
    return sorted({kw for kw in _VULN_CLASS_KEYWORDS if kw in lower})


def _extract_vulnerability_hints(text: str) -> list[str]:
    """Scan a tool result for explicit signals of a specific vulnerability
    class - a page title naming it (whatweb-style `Title[...]` fingerprint
    output, as real training labs often do) or a known vulnerability-class
    keyword appearing verbatim.

    Args:
        text (str): Tool result / observation text to scan.

    Returns:
        list[str]: Human-readable hint strings (one for a title match, one
        for any matched keywords), or `[]` if neither is present.
    """
    if not text:
        return []
    hints = []
    title_match = _TITLE_PATTERN.search(text)
    if title_match:
        hints.append(f"the page title mentions '{title_match.group(1).strip()}'")
    matched = _matched_vuln_keywords(text)
    if matched:
        hints.append(f"the output mentions vulnerability-class keyword(s): {', '.join(matched)}")
    return hints


# 2026-08-01: `Exploit_Suggester` (bridge.suggest_payloads -> PayloadsAllTheThings
# local mirror) returns static reference payload text and never sends a
# request to the target - it is not a live test. `Advanced_Evasion_Probe` is
# the only tool in this agent's toolset that actually attempts exploitation,
# and its own Tool description (brain_tools.py) scopes that to SQL injection
# and Path Traversal only - no other class has a dedicated live-test tool.
# A prior version of the nudge below read "e.g. Advanced_Evasion_Probe or
# Exploit_Suggester for that specific class", which the model took as two
# interchangeable ways to "test it directly". Observed live 2026-08-01
# (run bc915491, PortSwigger path-traversal lab, Recon_Suite page title
# literally said "File path traversal"): the model called Exploit_Suggester
# three times in a row with the identical input, got the same canned
# PayloadsAllTheThings snippet each time, tripped the duplicate-call guard,
# and gave an honest "stopped early" Final Answer - Advanced_Evasion_Probe
# was never called, so the real, live-testable vulnerability went unverified.
_LIVE_TEST_TOOL_BY_KEYWORD = {
    "path traversal": "Advanced_Evasion_Probe",
    "directory traversal": "Advanced_Evasion_Probe",
    "sql injection": "Advanced_Evasion_Probe",
}

# 2026-08-23 live-run finding (agent runs 1099dc95, 765c243c, b4762be3 -
# see _already_confirmed_exploitation()'s docstring): the set of tools this
# directive can name, factored out so the call site can recognize "this
# tool's OWN result already confirmed the finding" instead of blindly
# re-issuing "call it now" against a result that already IS the live test.
_LIVE_TEST_TOOLS = frozenset(_LIVE_TEST_TOOL_BY_KEYWORD.values())

# The exact header evasion.py's advanced_vuln_probe() prints (see
# app/tools/evasion.py) only when `results` is non-empty - i.e. only on a
# genuine confirmed hit, never on "No vulnerabilities detected...". Reusing
# this literal instead of re-deriving confirmation from keywords keeps the
# two modules from silently drifting apart (Constitution IX).
_EVASION_PROBE_SUCCESS_MARKER = "ADVANCED EVASION PROBE REPORT"


def _already_confirmed_exploitation(tool_name: str, result_text: str) -> bool:
    """True when `result_text` is a live-test tool's OWN confirmed-finding
    output, not just a result that happens to mention a vulnerability-class
    keyword.

    Root cause of a real, observed failure mode (agent run b4762be3,
    2026-08-23, a PortSwigger path-traversal lab): `Advanced_Evasion_Probe`
    confirmed the vulnerability and captured real screenshots - but its own
    success text still contains the words "Path Traversal", so the generic
    keyword check in `_extract_vulnerability_hints` matched it too and
    re-issued "Call Advanced_Evasion_Probe now" right after the tool had
    just done exactly that. The model called it again (a second genuine,
    also-successful confirmation), then a third time with no new signal to
    stop, tripped the duplicate-call guard, and the run's fallback
    "stopped early" Final Answer discarded both real, evidence-backed
    confirmations entirely - the same failure independently reproduced
    against a second target (run 1099dc95, an SQLi lab) that same day.

    Args:
        tool_name (str): The tool that produced `result_text`.
        result_text (str): That tool's raw Observation text.

    Returns:
        bool: True only for a live-test tool (`_LIVE_TEST_TOOLS`) whose own
        result carries `_EVASION_PROBE_SUCCESS_MARKER` - i.e. a genuine,
        already-confirmed hit from that exact tool, not a keyword mention
        in someone else's (e.g. Recon_Suite's) output.
    """
    return tool_name in _LIVE_TEST_TOOLS and _EVASION_PROBE_SUCCESS_MARKER in (result_text or "")


def _live_test_directive(matched_keywords: list[str]) -> str:
    """Build an unambiguous "what to call next" instruction for a matched
    vulnerability-class keyword set, naming the one tool (if any) that
    actually sends a live request - and explicitly ruling out
    `Exploit_Suggester`, which only returns reference payload text.

    Args:
        matched_keywords (list[str]): Keywords from `_matched_vuln_keywords`
            (may be empty - callers should only invoke this when non-empty).

    Returns:
        str: A directive sentence naming the specific live-test tool when
        `_LIVE_TEST_TOOL_BY_KEYWORD` covers the matched class, or a generic
        fallback (manual `Run_Kali_Command` probe) when it doesn't.
    """
    for kw in matched_keywords:
        tool = _LIVE_TEST_TOOL_BY_KEYWORD.get(kw)
        if tool:
            return (
                f"Call {tool} now against the real target - it is the only "
                f"tool that actually sends a live request for this "
                f"vulnerability class. Exploit_Suggester only returns "
                f"reference payload text from a local mirror; it does NOT "
                f"touch the target, and calling it again will not test "
                f"anything new."
            )
    return (
        "No dedicated live-test tool covers this specific class - use "
        "Run_Kali_Command to send a real, crafted request against the "
        "actual endpoint (e.g. curl with the suspected payload), or "
        "Run_Nikto/Run_FFUF for broader coverage. Exploit_Suggester only "
        "returns reference payload text; it does NOT touch the target and "
        "does not count as testing."
    )


_URL_IN_INPUT_RE = re.compile(r"https?://[^\s\"']+", re.IGNORECASE)


def _hostname(text: str) -> Optional[str]:
    """Extract a hostname from a tool-input string, whether it's a full URL
    or a bare domain.

    Args:
        text (str): A tool-input string - may be a full `http(s)://` URL, a
            bare domain (`Recon_Suite`/`Check_Reachability` are sometimes
            called with just the domain, no scheme), or free text.

    Returns:
        str or None: The lowercased hostname (port stripped), or `None` if
        no URL or domain-like token is found.
    """
    if not text:
        return None
    text = text.strip()
    match = _URL_IN_INPUT_RE.search(text)
    if match:
        netloc = urlsplit(match.group(0)).netloc
        return netloc.split(":")[0].lower() or None
    first_token = text.split()[0] if text.split() else ""
    if first_token and "/" not in first_token and "." in first_token:
        return first_token.split(":")[0].lower()
    return None


# 2026-08-01: scope guard - observed live (run b84499b0, PortSwigger
# path-traversal lab) that when the duplicate-call guard tells the model to
# "try a genuinely different input", a 7B local model satisfied that
# instruction by inventing an entirely different, unauthorized hostname (a
# plausible-looking but fabricated web-security-academy.net lab ID) instead
# of varying the technique/path/parameter against the real target. This
# isn't just wasted budget - the hallucinated Recon_Suite call was still
# running its own ~3-4 min nmap probe when the 900s wall-clock ceiling
# killed the run - it's a scope-safety issue: left unchecked, it would have
# sent real network probes to a host the user never authorized. Checked in
# execute_node before dispatch, so an out-of-scope call is rejected without
# ever actually running (no wasted network cost either).
def _is_out_of_scope(tool_input: str, target: str) -> bool:
    """Check whether a tool-input's hostname differs from the run's
    authorized target hostname.

    Deliberately an exact-hostname allowlist of one (the original target) -
    no subdomain carve-out. A model that has a genuine reason to test a
    discovered subdomain should say so in its Thought and the user can
    decide to start a new, separately-scoped run for it; this guard's job
    is only to stop a silent, hallucinated target swap mid-run.

    Args:
        tool_input (str): The proposed tool call's input string.
        target (str): This run's authorized target (`state["target"]`).

    Returns:
        bool: `True` if `tool_input` names a different host than `target`
        (both hostnames must be resolvable from the strings for this to
        fire - a non-URL input like a Query_Memory search term never
        triggers it).
    """
    call_host = _hostname(tool_input)
    target_host = _hostname(target)
    return bool(call_host and target_host and call_host != target_host)


# Cap on how many discovered subdomains become graph edges per
# Subdomain_Enumeration call. Unlike ArgusBrain.run_deterministic_recon's
# MAX_CHAINED_SUBDOMAINS (which bounds extra network calls), this is a pure
# DB write with no network cost - kept modest anyway so a target with heavy
# passive-DNS noise (the same "example.com -> ~3000 lines" case
# OBSERVATION_MAX_CHARS above already guards against) doesn't flood the
# graph with low-value nodes.
_MAX_GRAPH_SUBDOMAIN_EDGES = 10


def _record_recon_graph_edges(
    memory: Optional[ArgusMemory], target: str, tool_name: str, result: Any
) -> None:
    """Populate the entities/relations Knowledge Graph (Query_Knowledge_Graph's
    data source) from a completed Subdomain_Enumeration/Recon_Suite call.

    Before this, the only code path that ever wrote SUBDOMAIN_OF/USES_TECH
    edges was `ArgusBrain.run_deterministic_recon` - reachable only via
    `ask_deterministic()`, which nothing in production actually calls (every
    real caller uses the live ReAct path, `ask()`). Query_Knowledge_Graph was
    a fully wired agent tool with no data ever behind it. Mirrors
    `run_deterministic_recon`'s own edge logic exactly via
    `app/tools/utils.py`'s parse_subdomains/parse_tech_block/
    clean_tech_string/record_graph_edge (single source of truth - both
    brain.py and this module call the same functions).

    VULNERABLE_TO edges are deliberately NOT written here yet -
    `_extract_vulnerability_hints` above is a heuristic hint (a keyword or
    page-title match), not a confirmed finding, and turning a hint into a
    graph edge would overstate confidence beyond what was actually verified
    (Constitution VIII - Truthful Runtime). Left as a documented follow-up,
    not silently dropped.

    Args:
        memory (Optional[ArgusMemory]): Blackboard/knowledge-graph store;
            no-op (never raises) if `None`.
        target (str): The run's target (URL or bare host).
        tool_name (str): The tool that just executed.
        result (Any): The tool's raw return value.

    Returns:
        None
    """
    if memory is None or tool_name not in ("Subdomain_Enumeration", "Recon_Suite"):
        return
    root = to_bare_hostname(target)
    if not root:
        return
    try:
        memory.upsert_entity("domain", root)
    except Exception as e:
        print(f"[GRAPH] could not seed graph root '{root}': {e}")
        return

    text = str(result)
    if tool_name == "Subdomain_Enumeration":
        subs = parse_subdomains(text, exclude_hostname=root)[:_MAX_GRAPH_SUBDOMAIN_EDGES]
        for sub in subs:
            record_graph_edge(memory, ("domain", sub), sub, root, "SUBDOMAIN_OF")
    elif tool_name == "Recon_Suite":
        tech = clean_tech_string(parse_tech_block(text))
        for token in tech.split():
            record_graph_edge(memory, ("tech", token), root, token, "USES_TECH")


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

    Args:
        llm (Any): The chat LLM to invoke (must support `with_structured_output`
            for the structured path; falls back to `None` otherwise).
        system_text (str): The fully-rendered ReAct system prompt.
        messages (list): The conversation history to invoke the LLM with.

    Returns:
        Optional[str]: A synthesized `Thought:`/`Action:`/`Final Answer:` string
        on success, or `None` if structured decoding is unavailable/fails.
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


class _PlannerDecision(BaseModel):
    """Structured routing decision (specs/020, feature-flagged off by
    default) - the Planner role never calls an execution tool, only
    decides which specialist acts next (FR-003)."""
    reasoning: str = Field(description="Brief reasoning for this routing decision")
    next_role: str = Field(description='One of: "collector", "exploiter", "summarizer"')


def _try_planner_decision(llm: Any, system_text: str) -> Optional[str]:
    """Attempt structured decoding of the Planner's next-role decision.

    Mirrors `_try_structured_action`'s exact pattern (schema-constrained
    decoding first, regex-friendly text fallback) but targets
    `_PlannerDecision` instead of `_ArgusAction` - the Planner's output
    shape (a routing choice, not a tool call) doesn't fit `_ArgusAction`'s
    schema.

    Args:
        llm (Any): The chat LLM to invoke (must support `with_structured_output`
            for the structured path; falls back to `None` otherwise).
        system_text (str): The Planner's fully-rendered system prompt.

    Returns:
        Optional[str]: One of `"collector"`/`"exploiter"`/`"summarizer"` on
        success, or `None` if structured decoding is unavailable/fails -
        callers fall back to a regex search over a plain `llm.invoke()`
        response for one of those three words.
    """
    if not hasattr(llm, "with_structured_output"):
        return None
    try:
        structured_llm = llm.with_structured_output(_PlannerDecision)
        result = structured_llm.invoke([SystemMessage(content=system_text)])
        decision = result if isinstance(result, _PlannerDecision) else _PlannerDecision(**result)
    except Exception:
        return None
    role = decision.next_role.strip().lower()
    return role if role in ("collector", "exploiter", "summarizer") else None


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


def _parse_react_output(content: str, default_input: str) -> dict:
    """Parse LLM output: try JSON Action, then text format.

    Module-level (moved out of `_build_custom_workflow`'s `parse_node`
    closure 2026-07-11, specs/020) since it's a pure function with no
    closure dependencies - both the single-loop graph and the multi-role
    graph's collector/exploiter nodes call this identically.

    Args:
        content (str): The raw LLM response text to parse.
        default_input (str): Fallback `tool_input` value when the parsed
            action doesn't specify one explicitly.

    Returns:
        dict: Optional keys `tool_name`, `tool_input`, `phase` - whichever
        the parsed content actually specifies.
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
    """Build workflow using create_react_agent (requires tool_calls support).

    Args:
        llm (ChatOllama): The chat LLM to bind tools to (must support native
            tool-calling).
        tools (list): The tool list to bind and expose to the agent.
        memory (Optional[ArgusMemory]): Blackboard memory for context refresh
            before each LLM call; skipped entirely if `None`.

    Returns:
        Any: Compiled LangGraph graph with the standard `.invoke()`/`.stream()` contract.
    """
    from langgraph.prebuilt import create_react_agent
    from app.core.agent.react_state import ArgusPrebuiltState

    llm_with_tools = llm.bind_tools(tools)

    def prompt_fn(state: dict) -> list:
        """Dynamic prompt that injects blackboard context.

        Args:
            state (dict): Current graph state; reads `messages`.

        Returns:
            list: A `SystemMessage` (built via `build_prebuilt_system_prompt`)
            followed by `state["messages"]`.
        """
        msg = build_prebuilt_system_prompt(state)
        return [SystemMessage(content=msg)] + state["messages"]

    def pre_hook(state: dict) -> dict:
        """Refresh blackboard before LLM call.

        Args:
            state (dict): Current graph state; reads `iteration_count`.

        Returns:
            dict: `{"iteration_count": <incremented>}`, plus
            `"blackboard_summary"` if `memory` is set and has a
            non-empty summary to offer (silently omitted on any
            memory-read failure).
        """
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
        """Save tool decisions after LLM response.

        Args:
            state (dict): Current graph state; reads `messages`/`target`.

        Returns:
            dict: Empty dict (no state update - this hook's effect is
            persisting findings to `memory` as a side effect, not returning
            new state).
        """
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

    Returns:
        Any: Compiled LangGraph graph with the standard `.invoke()`/`.stream()` contract.
    """
    tool_map = _build_tool_map(tools)

    # -- Nodes ------------------------------------------
    def agent_node(state: ArgusAgentState) -> dict:
        """LLM generates the next Action: format=json structured decoding first
        (012 FR-C9), falling back to free-text ReAct output for parse_node's
        regex parser when structured decoding is unavailable/fails (FR-C10).

        Args:
            state (ArgusAgentState): Current graph state; reads `messages`
                and `iteration_count`.

        Returns:
            dict: `{"messages": [response], "iteration_count": <incremented>}`.
        """
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
            call_key = f"{result['tool_name']}::{_normalize_call_input(result.get('tool_input', ''))}"
            if state.get("tool_call_history", []).count(call_key) >= 2:
                tried_names = {entry.partition("::")[0] for entry in state.get("tool_call_history", [])}

                # 2026-07-25: a model blocked here has, by definition, no
                # way to make this exact attempt succeed differently next
                # time - the guard's own hard block guarantees an identical
                # guidance message on every subsequent try. Rather than
                # trusting the model to eventually pick something else
                # (three consecutive blocks with zero real progress in
                # between is treated as it won't), conclude the run early
                # with an honest partial answer instead of silently burning
                # the rest of max_iterations on a conversation that provably
                # cannot change outcome - see MAX_CONSECUTIVE_DUPLICATE_BLOCKS'
                # own comment for the live incident this fixes.
                consecutive_blocks = state.get("consecutive_duplicate_blocks", 0) + 1
                if consecutive_blocks >= MAX_CONSECUTIVE_DUPLICATE_BLOCKS:
                    give_up_note = (
                        f"Final Answer: Agent stopped early after being blocked "
                        f"from repeating the same or another already-tried tool "
                        f"call {consecutive_blocks} times in a row without "
                        f"proposing a genuinely new action - continuing would "
                        f"not have produced a different result. Tools actually "
                        f"executed this run: {', '.join(sorted(tried_names)) or 'none'}. "
                        f"This is a partial, honest result reflecting a "
                        f"tool-selection loop, not a fully completed security "
                        f"assessment - re-running against the same target may "
                        f"produce a different outcome."
                    )
                    # 2026-08-23 (defense-in-depth for the same live-run
                    # failure _already_confirmed_exploitation() targets at
                    # the source): the loop guard above fires on ANY
                    # repeated tool call, including one where an earlier
                    # call in this same run already confirmed a real
                    # vulnerability with evidence - the model just kept
                    # circling back to it (or another tool) instead of
                    # stopping. Without this, a genuinely confirmed,
                    # screenshot-backed finding is silently swallowed by a
                    # generic "partial assessment, no findings" message.
                    # Surface it explicitly rather than losing it.
                    if _EVASION_PROBE_SUCCESS_MARKER in state.get("blackboard_summary", ""):
                        give_up_note += (
                            f" IMPORTANT: despite this early stop, a vulnerability "
                            f"WAS already confirmed earlier in this run with "
                            f"real evidence captured - see the "
                            f"Advanced_Evasion_Probe result above for the "
                            f"confirmed payload and screenshot/report paths. "
                            f"Do not treat this run as clean."
                        )
                    return {
                        "tool_error": None,
                        "tool_name": None,
                        "tool_input": None,
                        "phase": "done",
                        "consecutive_duplicate_blocks": 0,
                        "reflection_notes": state.get("reflection_notes", []) + [give_up_note],
                        "messages": [AIMessage(content=give_up_note)],
                    }

                # A live run oscillated between two already-blocked tools for
                # several turns before finally giving a Final Answer - vague
                # "choose something different" guidance isn't concrete enough
                # for the model to act on reliably. List the tools it hasn't
                # touched at all this run by name, so there's always a
                # concrete next step instead of another guess.
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
                    "consecutive_duplicate_blocks": consecutive_blocks,
                    "reflection_notes": state.get("reflection_notes", []) + [reflection_note],
                    "messages": [HumanMessage(content=guidance)],
                }

        if result.get("phase") == "done":
            tried_names = {entry.partition("::")[0] for entry in state.get("tool_call_history", [])}

            # Live-discovered 2026-07-26, TWICE independently (a PortSwigger
            # lab, then a real production site - cultbeauty.co.uk - a
            # different day): the model sometimes writes "Final Answer:"
            # directly inside or right after its very first Thought,
            # before ever executing a single tool - then the synthesized
            # report that follows contains plausible-sounding but entirely
            # fabricated findings (specific paths like "/login.php", named
            # CVE-style payloads, severities) with zero real tool_result
            # backing any of it. This directly violates this project's own
            # Constitution VIII ("never fabricate a report"), which
            # `_finalize_graph_output()`'s "Final Answer:" requirement was
            # meant to uphold but doesn't on its own - a bare string match
            # on "Final Answer:" can't distinguish a genuine,
            # evidence-backed conclusion from this. This used to be an
            # explicitly documented gap right here ("out of scope for this
            # check") - it no longer is. Nudged exactly once per run
            # (mirroring the Phase 5/6 nudge below) rather than hard-blocked:
            # a target CAN legitimately turn out to need no further tooling,
            # but only after genuinely checking, not before ever trying.
            if not tried_names and not state.get("zero_tool_final_answer_nudged", False):
                zero_tool_nudge = (
                    "Observation: You provided a Final Answer without executing "
                    "a single tool this run - any vulnerability, path, or payload "
                    "named in it has NOT actually been verified against the real "
                    "target and would be a fabricated finding, not a genuine one "
                    "(Constitution VIII: never fabricate a report). Start with "
                    "Check_Reachability or Recon_Suite against the real target "
                    "before drawing any conclusion. If, after genuinely "
                    "investigating, nothing is found, state that explicitly - do "
                    "not invent findings to fill out the report."
                )
                return {
                    "tool_error": zero_tool_nudge,
                    "tool_name": None,
                    "tool_input": None,
                    "phase": "zero_tool_check",
                    "zero_tool_final_answer_nudged": True,
                    "reflection_notes": state.get("reflection_notes", []) + [zero_tool_nudge],
                    "messages": [HumanMessage(content=zero_tool_nudge)],
                }

            # 2026-07-26: companion to the zero_tool_check above - that one
            # catches "no tool call at all"; this one catches a model that
            # called SOME tool(s) (so tried_names is non-empty) but skipped
            # straight to Phase 3+ without ever establishing real
            # connectivity/recon on THIS target first (e.g. only ever
            # calling Query_Memory or Smart_Web_Search). One-time nudge,
            # same pattern as phase56_nudged below - checked first since
            # Phase 1-2 logically precedes Phase 5/6 in the recommended
            # progression (react_prompts.py).
            if tried_names and not (tried_names & PHASE_1_2_TOOLS) and not state.get("phase12_nudged", False):
                phase12_nudge = (
                    "Observation: Before concluding, note that you have not yet "
                    "established basic connectivity/reconnaissance for this "
                    "specific target (Check_Reachability, Subdomain_Enumeration, "
                    "Recon_Suite, or Crawl_Target). Try one of these now so any "
                    "later findings are grounded in real data about this target, "
                    "not general knowledge. If recon genuinely does not apply, "
                    "state that explicitly in your Final Answer instead of "
                    "omitting it silently."
                )
                return {
                    "tool_error": phase12_nudge,
                    "tool_name": None,
                    "tool_input": None,
                    "phase": "phase12_check",
                    "phase12_nudged": True,
                    "reflection_notes": state.get("reflection_notes", []) + [phase12_nudge],
                    "messages": [HumanMessage(content=phase12_nudge)],
                }

            # Only nudge a run that attempted at least one tool - a Final
            # Answer with zero tool calls at all is handled above instead.
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

        # See _is_out_of_scope's docstring for the live-run failure this
        # guards against - reject before dispatch, so nothing is ever sent
        # to an unauthorized host.
        if _is_out_of_scope(str(inp), str(state["target"])):
            scope_obs = (
                f"Observation: REJECTED - this input targets a different "
                f"host than the one authorized for this run "
                f"('{state['target']}'). You may only test the original "
                f"target. If you need a genuinely different next action, "
                f"vary the technique, path, or parameter against the SAME "
                f"target - do not substitute a different hostname."
            )
            return {
                "tool_error": scope_obs,
                "tool_name": None,
                "tool_input": None,
                "messages": [HumanMessage(content=scope_obs)],
            }

        try:
            result = tool_map[name](inp)
            obs = f"Observation: {_bounded_observation(result)}"
            bb = (
                f"{state['blackboard_summary']}\n"
                f"- [{name}] {str(inp)[:80]} -> {str(result)[:200]}"
            ).strip()
            call_key = f"{name}::{_normalize_call_input(str(inp))}"
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

            # 2026-07-11: deterministic evidence-extraction check (see
            # _extract_vulnerability_hints' docstring) - hands the model an
            # explicit directive instead of relying on it to notice a
            # signal like a page title on its own. 2026-08-01: the directive
            # now names the specific live-test tool (see
            # _live_test_directive's docstring for why) instead of listing
            # Exploit_Suggester as an equivalent alternative.
            if _already_confirmed_exploitation(name, str(result)):
                hint_note = (
                    f"Reflection: {name} above already CONFIRMED a real "
                    f"vulnerability against the live target, with evidence "
                    f"captured (see the screenshot/report paths in the "
                    f"Observation above). Calling {name} - or any other "
                    f"tool - again will not add anything; the finding is "
                    f"already proven. Provide your Final Answer now, "
                    f"citing exactly what was confirmed and the evidence "
                    f"paths shown above."
                )
                extra_messages.append(HumanMessage(content=hint_note))
                reflection_notes.append(hint_note)
            else:
                vuln_hints = _extract_vulnerability_hints(str(result))
                if vuln_hints:
                    matched_keywords = _matched_vuln_keywords(str(result))
                    hint_note = (
                        f"Reflection: the {name} result above {' and '.join(vuln_hints)} - "
                        f"this strongly suggests the target's likely vulnerability class. "
                        f"{_live_test_directive(matched_keywords)}"
                    )
                    extra_messages.append(HumanMessage(content=hint_note))
                    reflection_notes.append(hint_note)

            # specs/019 FR-006 (Red-MIRROR Algorithm 4 Step 1): 3x
            # self-consistency majority vote, scoped to EXPLOITATION_TOOLS
            # only (informational/deterministic tools don't need it).
            if enable_inter_reflection and name in EXPLOITATION_TOOLS:
                verdict = _inter_reflect(llm, call_key, str(result))
                if verdict is not None:
                    if verdict:
                        # 2026-08-23: a bare "= SUCCESS" note gave the model
                        # no reason to stop - live runs (b4762be3, 1099dc95)
                        # both treated it as encouragement to re-run the
                        # same already-successful tool "to be sure",
                        # eventually tripping the duplicate-call guard and
                        # losing the confirmed finding. Say explicitly that
                        # no further call is needed.
                        reflect_msg = (
                            f"Reflection: majority-vote assessment of {name} "
                            f"result = SUCCESS. This finding is confirmed - "
                            f"do not call {name} again for this target. "
                            f"Provide your Final Answer now."
                        )
                    else:
                        reflect_msg = f"Reflection: majority-vote assessment of {name} result = INCONCLUSIVE/NO FINDING."
                    extra_messages.append(HumanMessage(content=reflect_msg))
                    reflection_notes.append(reflect_msg)

            update = {
                "tool_result": str(result)[:2000],
                "tool_error": None,
                "blackboard_summary": bb,
                "messages": [HumanMessage(content=obs)] + extra_messages,
                "tool_call_history": state.get("tool_call_history", []) + [call_key],
                "reflection_notes": reflection_notes,
                # A real, allowed execution (not a blocked repeat) is
                # genuine progress - reset the consecutive-duplicate-block
                # counter so a model that gets blocked once, recovers with a
                # real new action, then gets blocked again later isn't
                # unfairly close to MAX_CONSECUTIVE_DUPLICATE_BLOCKS from
                # unrelated, already-resolved blocks earlier in the run.
                "consecutive_duplicate_blocks": 0,
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
                _record_recon_graph_edges(memory, state["target"], name, result)
            return update
        except Exception as e:
            obs = f"Observation: Error executing {name}: {e}"
            return {"tool_error": obs, "messages": [HumanMessage(content=obs)]}

    # -- Conditional routers ----------------------------
    def route_after_agent(state: ArgusAgentState) -> str:
        """Route after agent."""
        return "parse"

    def route_after_parse(state: ArgusAgentState) -> str:
        """Decide the next node after `parse_node`.

        Args:
            state (ArgusAgentState): Current graph state; reads `phase`,
                `tool_name`, `iteration_count`, and `max_iterations`.

        Returns:
            str: One of `"end"` (done, or a
            format/duplicate-call/phase56-check/zero-tool-check/phase12-check
            loop that hit `max_iterations`), `"agent"` (retry after a format
            error, blocked duplicate call, phase1/2 nudge, phase5/6 nudge,
            or zero-tool-call nudge), or `"execute"` (a valid new tool call).
        """
        phase = state.get("phase", "")
        if phase == "done":
            return "end"
        if phase in ("format_error", "duplicate_call", "phase56_check", "zero_tool_check", "phase12_check"):
            # Bug fixed (specs/018): this previously routed straight back to
            # "agent" with no iteration check at all, unlike the tool-execute
            # path below. A model that never once produces valid output (the
            # exact live failure this spec fixes) would loop here forever,
            # bounded only by LangGraph's default recursion_limit (25) via an
            # ungraceful GraphRecursionError - not by max_iterations, and not
            # a clean "no final answer" result. duplicate_call (specs/018
            # addendum 2), phase56_check (specs/019 follow-up), and
            # zero_tool_check/phase12_check (2026-07-26 follow-up) share this
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
        """Loop back to the agent, or end at the iteration budget.

        Args:
            state (ArgusAgentState): Current graph state.

        Returns:
            str: The next node name - "agent" or "end".
        """
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


def _build_multi_role_workflow(
    llm: Any,
    tools_by_role: Dict[str, list],
    memory: Optional[ArgusMemory] = None,
    enable_inter_reflection: bool = True,
) -> Any:
    """Build the specs/020 multi-role StateGraph (feature-flagged off by
    default - see `config.yaml`'s `enable_multi_agent_roles`).

    Topology: `planner` decides which specialist acts next (FR-003);
    `collector`/`exploiter` each execute exactly ONE tool call per visit
    (FR-002's tool partition), then control returns unconditionally to
    `planner`; `summarizer` is terminal and produces the final report
    (FR-004) via `build_summarizer_prompt`.

    Deliberately a standalone graph rather than a generalization of
    `_build_custom_workflow`'s closures - the single-loop path is the
    proven production default (NFR-002) and must stay completely
    unaffected by this experimental path's existence. Reuses every
    already-extracted, stateless module-level helper
    (`_parse_react_output`, `_try_structured_action`,
    `_check_early_termination`, `_extract_vulnerability_hints`,
    `_inter_reflect`, `_build_tool_map`) rather than duplicating them.

    Known, intentional scope reduction versus the single-loop graph (v1 of
    this experimental path - not silently missing, documented per
    Constitution VIII): does not replicate `parse_node`'s "block a call
    repeated 3+ times" duplicate-call guard. If NFR-001's wall-clock
    measurement (specs/020 T006/T007) justifies keeping this path, that
    guard should be added before any live/production use.

    Args:
        llm (Any): Shared model instance for all four roles (FR-001 - one
            model, not four separate model loads).
        tools_by_role (Dict[str, list]): `{"collector": [...], "exploiter":
            [...]}` - each built via `build_argus_tools(bridge, role=...)`.
            Planner/Summarizer call no execution tools at all (FR-002).
        memory (Optional[ArgusMemory]): Shared Blackboard, written by
            Collector/Exploiter tool executions exactly as
            `_build_custom_workflow`'s `execute_node` does.
        enable_inter_reflection (bool): Same meaning as
            `_build_custom_workflow`'s - 3x majority vote on
            `EXPLOITATION_TOOLS` results (only reachable from `exploiter`,
            since `EXPLOITATION_TOOLS` are all Exploiter-partitioned tools).

    Returns:
        Any: Compiled LangGraph graph with the same external
        `.invoke()`/`.stream()` contract as `_build_custom_workflow`'s.
    """
    collector_tool_map = _build_tool_map(tools_by_role.get("collector", []))
    exploiter_tool_map = _build_tool_map(tools_by_role.get("exploiter", []))

    def planner_node(state: ArgusAgentState) -> dict:
        """Decide which specialist (Collector/Exploiter/Summarizer) acts next.

        Args:
            state (ArgusAgentState): Current graph state.

        Returns:
            dict: State updates - `current_role`, appended `role_history`,
            incremented `iteration_count`.
        """
        system_text = build_planner_prompt({**state})
        decision = _try_planner_decision(llm, system_text)
        if decision is None:
            raw = llm.invoke([SystemMessage(content=system_text)])
            content = str(getattr(raw, "content", raw)).lower()
            decision = next(
                (c for c in ("collector", "exploiter", "summarizer") if c in content),
                None,
            )
        # An inconclusive routing decision ends the run with whatever's
        # known so far rather than spinning silently (Constitution VIII).
        decision = decision or "summarizer"
        return {
            "current_role": decision,
            "role_history": state.get("role_history", []) + [decision],
            "iteration_count": state["iteration_count"] + 1,
        }

    def _run_specialist_step(
        state: ArgusAgentState, role_name: str, tool_map: Dict[str, Callable], prompt_builder: Callable
    ) -> dict:
        """Shared propose -> parse -> execute logic for Collector/Exploiter -
        exactly one tool call per visit, then control returns to Planner.

        Args:
            state (ArgusAgentState): Current graph state.
            role_name (str): The specialist role invoking this step
                ("collector" or "exploiter"), used for logging/Blackboard entries.
            tool_map (Dict[str, Callable]): This role's own tool subset.
            prompt_builder (Callable): The role-scoped prompt builder to render
                the system prompt with (`build_collector_prompt` or
                `build_exploiter_prompt`).

        Returns:
            dict: State updates - `messages`, `blackboard_summary`,
            `tool_call_history`, `reflection_notes`, incremented
            `iteration_count`, and (on a real tool call) `tool_result`/`tool_error`.
        """
        system_text = prompt_builder({**state, "_tools": tool_map})
        structured_content = _try_structured_action(llm, system_text, state["messages"])
        if structured_content is not None:
            content = structured_content
        else:
            raw = llm.invoke([SystemMessage(content=system_text)] + state["messages"])
            content = str(getattr(raw, "content", raw))
        agent_message = AIMessage(content=content)
        parsed = _parse_react_output(content, state["target"])

        if parsed.get("phase") == "done" or "tool_error" in parsed:
            note = f"Reflection: {role_name} did not produce a usable tool call this turn."
            return {
                "iteration_count": state["iteration_count"] + 1,
                "messages": [agent_message, HumanMessage(content=note)],
                "reflection_notes": state.get("reflection_notes", []) + [note],
            }

        name = parsed.get("tool_name")
        inp = parsed.get("tool_input", state["target"])
        if not name or name not in tool_map:
            obs = f"Observation: Unknown tool '{name}' for {role_name}. Available: {list(tool_map.keys())}"
            return {
                "iteration_count": state["iteration_count"] + 1,
                "messages": [agent_message, HumanMessage(content=obs)],
            }

        if _is_out_of_scope(str(inp), str(state["target"])):
            scope_obs = (
                f"Observation: REJECTED - this input targets a different "
                f"host than the one authorized for this run "
                f"('{state['target']}'). You may only test the original "
                f"target. If you need a genuinely different next action, "
                f"vary the technique, path, or parameter against the SAME "
                f"target - do not substitute a different hostname."
            )
            return {
                "iteration_count": state["iteration_count"] + 1,
                "messages": [agent_message, HumanMessage(content=scope_obs)],
            }

        try:
            result = tool_map[name](inp)
        except Exception as e:
            result = f"Error executing {name}: {e}"

        bb = (
            f"{state['blackboard_summary']}\n"
            f"- [{role_name}/{name}] {str(inp)[:80]} -> {str(result)[:200]}"
        ).strip()
        call_key = f"{name}::{_normalize_call_input(str(inp))}"
        reflection_notes = list(state.get("reflection_notes", []))
        extra_messages = []

        found_flag = _check_early_termination(str(result))
        if found_flag:
            nudge = (
                f"Reflection: a flag-shaped string was found in this "
                f"result ({found_flag})."
            )
            extra_messages.append(HumanMessage(content=nudge))
            reflection_notes.append(nudge)

        if _already_confirmed_exploitation(name, str(result)):
            hint_note = (
                f"Reflection: {name} above already CONFIRMED a real "
                f"vulnerability against the live target, with evidence "
                f"captured (see the screenshot/report paths in the "
                f"Observation above). Calling {name} - or any other "
                f"tool - again will not add anything; the finding is "
                f"already proven. Provide your Final Answer now, "
                f"citing exactly what was confirmed and the evidence "
                f"paths shown above."
            )
            extra_messages.append(HumanMessage(content=hint_note))
            reflection_notes.append(hint_note)
        else:
            vuln_hints = _extract_vulnerability_hints(str(result))
            if vuln_hints:
                matched_keywords = _matched_vuln_keywords(str(result))
                hint_note = (
                    f"Reflection: the {name} result above {' and '.join(vuln_hints)} - "
                    f"this strongly suggests the target's likely vulnerability class. "
                    f"{_live_test_directive(matched_keywords)}"
                )
                extra_messages.append(HumanMessage(content=hint_note))
                reflection_notes.append(hint_note)

        if enable_inter_reflection and name in EXPLOITATION_TOOLS:
            verdict = _inter_reflect(llm, call_key, str(result))
            if verdict is not None:
                if verdict:
                    reflect_msg = (
                        f"Reflection: majority-vote assessment of {name} "
                        f"result = SUCCESS. This finding is confirmed - "
                        f"do not call {name} again for this target. "
                        f"Provide your Final Answer now."
                    )
                else:
                    reflect_msg = f"Reflection: majority-vote assessment of {name} result = INCONCLUSIVE/NO FINDING."
                extra_messages.append(HumanMessage(content=reflect_msg))
                reflection_notes.append(reflect_msg)

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
            _record_recon_graph_edges(memory, state["target"], name, result)

        return {
            "tool_result": str(result)[:2000],
            "tool_error": None,
            "blackboard_summary": bb,
            "messages": [agent_message, HumanMessage(content=f"Observation: {_bounded_observation(result)}")] + extra_messages,
            "tool_call_history": state.get("tool_call_history", []) + [call_key],
            "reflection_notes": reflection_notes,
            "iteration_count": state["iteration_count"] + 1,
        }

    def collector_node(state: ArgusAgentState) -> dict:
        """Run one Collector (recon/discovery) tool call via `_run_specialist_step`.

        Args:
            state (ArgusAgentState): Current graph state.

        Returns:
            dict: See `_run_specialist_step`'s return contract.
        """
        return _run_specialist_step(state, "collector", collector_tool_map, build_collector_prompt)

    def exploiter_node(state: ArgusAgentState) -> dict:
        """Run one Exploiter (scanning/exploitation) tool call via `_run_specialist_step`.

        Args:
            state (ArgusAgentState): Current graph state.

        Returns:
            dict: See `_run_specialist_step`'s return contract.
        """
        return _run_specialist_step(state, "exploiter", exploiter_tool_map, build_exploiter_prompt)

    def summarizer_node(state: ArgusAgentState) -> dict:
        """Produce the terminal Final Answer report from the accumulated Blackboard.

        Args:
            state (ArgusAgentState): Current graph state.

        Returns:
            dict: State updates - the final `messages` entry (guaranteed to
            contain "Final Answer:"), `phase` set to "done", incremented
            `iteration_count`.
        """
        system_text = build_summarizer_prompt({**state})
        raw = llm.invoke([SystemMessage(content=system_text)])
        content = str(getattr(raw, "content", raw))
        if "Final Answer:" not in content:
            content = f"Final Answer: {content}"
        return {
            "messages": [AIMessage(content=content)],
            "phase": "done",
            "iteration_count": state["iteration_count"] + 1,
        }

    def route_after_planner(state: ArgusAgentState) -> str:
        """Route to the Planner's chosen specialist, or force Summarizer at budget.

        Args:
            state (ArgusAgentState): Current graph state.

        Returns:
            str: The next node name - "collector", "exploiter", or "summarizer".
        """
        if state["iteration_count"] >= state["max_iterations"]:
            return "summarizer"
        return state.get("current_role") or "summarizer"

    def route_after_specialist(state: ArgusAgentState) -> str:
        """Route back to the Planner after a specialist step, or force Summarizer at budget.

        Args:
            state (ArgusAgentState): Current graph state.

        Returns:
            str: The next node name - "planner" or "summarizer".
        """
        if state["iteration_count"] >= state["max_iterations"]:
            return "summarizer"
        return "planner"

    builder = StateGraph(ArgusAgentState)
    builder.add_node("planner", planner_node)
    builder.add_node("collector", collector_node)
    builder.add_node("exploiter", exploiter_node)
    builder.add_node("summarizer", summarizer_node)

    builder.add_edge(START, "planner")
    builder.add_conditional_edges(
        "planner", route_after_planner,
        {"collector": "collector", "exploiter": "exploiter", "summarizer": "summarizer"},
    )
    builder.add_conditional_edges(
        "collector", route_after_specialist, {"planner": "planner", "summarizer": "summarizer"},
    )
    builder.add_conditional_edges(
        "exploiter", route_after_specialist, {"planner": "planner", "summarizer": "summarizer"},
    )
    builder.add_edge("summarizer", END)

    return builder.compile()


# =======================================================
# Helpers
# =======================================================
def _build_tool_map(tools: list) -> Dict[str, Callable]:
    """Convert a list of tools/callables to a name -> func dict.

    Args:
        tools (list): A mix of `BaseTool` instances, plain callables (with
            an optional `.name` attribute), or `{"name": ..., "func": ...}`
            dicts.

    Returns:
        Dict[str, Callable]: Tool name to callable, ready for lookup by
        name during action execution.
    """
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
    """Extract target URL/domain from a user query.

    Args:
        query (str): The user's request text.

    Returns:
        str: The first whitespace-separated token that starts with
        `http://`/`https://`, or the first token containing a `.` with
        no internal space; the whole `query` unchanged if neither is found.
    """
    for part in query.split():
        part = part.strip(".,;!?\"'")
        if part.startswith(("http://", "https://")):
            return part
        if "." in part and " " not in part:
            return part
    return query
