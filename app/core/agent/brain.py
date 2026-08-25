from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from app.core.schemas import SecurityReport
from app.core.llm_factory import build_chat_llm
from app.core.rag import RAGEngine, RAGConfig
from app.core.memory.memory_service import ArgusMemory
from app.tools.utils import (
    to_bare_hostname,
    normalize_domain_for_memory,
    parse_subdomains,
    parse_tech_block,
    clean_tech_string,
    record_graph_edge,
)
import json
import os
import re
from datetime import datetime
from typing import Dict, Any, Optional, List

# Ordered, deterministic recon phases. These run directly in Python -
# the LLM never chooses which tool fires next, so there is no ReAct
# format for a weak local model to get wrong. Each tool is called with
# the raw target string, matching the "Action Input is the raw value
# only" convention already used elsewhere in this project.
#
# Phase chaining: a few phases feed their real findings into follow-up
# tool calls automatically (see run_deterministic_recon) - discovered
# subdomains get a quick reachability re-check, detected tech gets
# looked up via Smart_Web_Search, and interesting crawled endpoints get
# sent to Exploit_Suggester. This is plain Python string-parsing of
# real tool output, not another LLM decision, so it's exactly as
# reliable as the rest of this pipeline.
DETERMINISTIC_PHASES: List[str] = [
    "Check_Reachability",
    "Subdomain_Enumeration",
    "Recon_Suite",
    "Crawl_Target",
    "Query_Memory",
    "Query_Knowledge_Graph",
    "Run_Nikto",
    "Run_FFUF",
    # Exploitation phases. Until these were added, no deterministic run ever
    # attempted an exploit, so no finding was ever confirmed and
    # specs/029's screenshot evidence could never trigger - the whole
    # pipeline stopped at reconnaissance. These are guaranteed to run in
    # every deterministic pass so detection never depends on a weak local
    # LLM choosing the right tool. Path_Traversal_Scan self-discovers the
    # vulnerable endpoint (e.g. /image?filename=) from the live page, so it
    # works even when recon/nikto/ffuf surfaced no explicit traversal hint -
    # which is exactly the case for PortSwigger's file-path-traversal lab.
    "Path_Traversal_Scan",
    "Advanced_Evasion_Probe",
]

# The "fast" profile: reach the target, learn its real endpoints, then try to
# exploit them. It deliberately drops the slow recon phases (subdomain
# enumeration, Nikto, FFUF) that can each add minutes without contributing to
# a confirmed finding on a single-target run.
#
# Advanced_Evasion_Probe is what captures proof-of-concept screenshots
# (specs/029), so it must be present in every profile or a scan produces a
# report with no evidence attached.
DETERMINISTIC_PHASES_FAST: List[str] = [
    "Check_Reachability",
    "Crawl_Target",
    "Path_Traversal_Scan",
    "Advanced_Evasion_Probe",
]

# Environment variable selecting between the two profiles above.
SCAN_PROFILE_ENV = "ARGUS_SCAN_PROFILE"

# Recon tools store *every* output line with data_type "vulnerability" -
# server banners, open ports, "host tested", connect failures. Filtering on
# data_type alone would fill a report with lines that confirm nothing, so
# these sources are excluded from the deterministic report entirely. Real
# exploitation tools (path_traversal, evasion_probe) are not listed here.
_RECON_NOISE_TOOLS = frozenset({
    "nikto", "recon", "recon_suite", "ffuf", "run_ffuf",
    "crawler", "reachability", "subdomain_enumeration",
})

_TRAVERSAL_TERMS = ("traversal", "lfi", "file inclusion", "etc/passwd", "win.ini")
_SQLI_TERMS = ("sqli", "sql injection")

_TRAVERSAL_REMEDIATION = (
    "Do not build filesystem paths from user input. Resolve the requested "
    "path, then verify the canonical result is still inside the intended "
    "directory before opening it, and serve files through an allow-list of "
    "known identifiers rather than raw filenames."
)
_SQLI_REMEDIATION = (
    "Use parameterized queries (prepared statements) for every database "
    "call so user input is never concatenated into SQL. Apply least-"
    "privilege database accounts and validate input against an allow-list."
)
_GENERIC_REMEDIATION = (
    "Validate and sanitise the affected input, then re-test the endpoint to "
    "confirm the behaviour no longer reproduces."
)


def _selected_deterministic_phases() -> List[str]:
    """Return the phase list for the configured scan profile.

    Fast is the default: a first run should reach a confirmed finding (and
    therefore a screenshot) in a reasonable time. Set
    `ARGUS_SCAN_PROFILE=full` for the complete recon-plus-exploit sweep.

    Returns:
        List[str]: `DETERMINISTIC_PHASES` when the profile is `"full"`,
        otherwise `DETERMINISTIC_PHASES_FAST`.
    """
    profile = os.environ.get(SCAN_PROFILE_ENV, "fast").strip().lower()
    return DETERMINISTIC_PHASES if profile == "full" else DETERMINISTIC_PHASES_FAST

# Chaining limits - kept small since each extra call is a real network
# operation (and each subdomain re-check multiplies runtime).
MAX_CHAINED_SUBDOMAINS = 2
MAX_CHAINED_PATHS = 3
_INTERESTING_PATH_KEYWORDS = (
    "login", "admin", "register", "search", "upload",
    "config", "backup", "account", "user",
)
# Tech-line parsing regexes/constants moved to app/tools/utils.py
# (parse_tech_block/clean_tech_string) - single source of truth,
# react_workflow.py's live ReAct path needs the identical logic.

# Maps a keyword found in a crawled path to plain vulnerability-class terms,
# since Exploit_Suggester almost certainly matches against a payload
# repository by vulnerability class (e.g. folder names like "SQL
# Injection"), not by literal URLs with query strings - the raw endpoint
# text isn't a query that repository search would ever match.
_PATH_KEYWORD_TO_VULN_CLASS = {
    "login": "authentication bypass SQL injection",
    "register": "SQL injection input validation",
    "admin": "directory traversal privilege escalation",
    "search": "SQL injection XSS",
    "upload": "file upload vulnerabilities",
    "config": "information disclosure directory traversal",
    "backup": "information disclosure",
    "account": "authentication bypass",
    "user": "authentication bypass",
}

SYNTHESIS_PROMPT_TEMPLATE = """You are Argus AI, a senior security researcher.
Below are the RAW RESULTS of reconnaissance tools that were already executed
against the target. You are NOT choosing or running any tools - that already
happened. Your only job is to read these real results and write the final
structured security report.

===== TARGET =====
{target}

===== LIVE TARGET STATE (blackboard / knowledge graph) =====
{blackboard_context}

===== RAW TOOL OUTPUT (ground truth - base every finding on this) =====
{tool_observations}

Rules:
- Every finding must be traceable to something in RAW TOOL OUTPUT above. If a
  tool failed, errored, or found nothing, say so honestly instead of
  inventing a finding.
- If RAW TOOL OUTPUT is empty or all tools failed, your summary must say
  reconnaissance could not be completed and overall_risk_score should be 1.
- Do not use placeholder or example text. Every field must reflect this
  specific target and this specific tool output.
- Output ONLY a single JSON object. Do not print a schema, do not print
  field types, do not print the words "$defs", "properties", or
  "required" anywhere - those are meta-terms describing a format, not
  something that belongs in your answer. Write real sentences as values.
- IMPORTANT - do not fixate on whichever tool's output happens to appear
  last above. Read ALL of RAW TOOL OUTPUT as one connected picture, not
  as a list where the most recent entry matters most. In particular:
  - "summary" and "output" must reflect the OVERALL target profile - not
    just whichever single tool ran last (e.g. do not write a report that
    is really just about Run_FFUF's results if Check_Reachability,
    Subdomain_Enumeration, and Recon_Suite also produced real findings).
  - "attack_surface_stats" specifically MUST pull from Check_Reachability
    (is it up), Subdomain_Enumeration (how many subdomains), and
    Recon_Suite (open ports, tech stack) - name actual numbers/values
    from those three tools' output, not just the last tool that ran.
  - Never title the report after one specific tool (e.g. do not call
    "output" a "FFUF Discovery Report" or a "Nikto Report" - it is a
    security report covering everything discovered, so title it
    accordingly, e.g. "# Security Assessment Report").

Fill in ACTUAL VALUES for each of these six fields (this is not a schema,
just the field names - replace the < > with your own real analysis):

{{
  "summary": <one paragraph, your own words, about this specific target's security posture>,
  "attack_surface_stats": <one sentence covering reachability status, subdomain count, open ports, AND tech stack - pulled from Check_Reachability, Subdomain_Enumeration, and Recon_Suite specifically>,
  "findings": [
    {{
      "target": <the specific host/URL this finding applies to>,
      "issue": <the specific issue found, from the raw tool output above>,
      "severity": <one of: Low, Medium, High, Critical>,
      "description": <technical explanation, citing what the tool actually reported>,
      "suggested_payload": <a real example if applicable, else the word "None">,
      "remediation": <concrete fix steps>
    }}
  ],
  "overall_risk_score": <an integer from 1 to 10>,
  "next_steps": [<list of recommended follow-up actions as strings>],
  "output": <the full report written out as Markdown text>
}}
"""

# Structured decoding needs far fewer retries than free-text ReAct parsing
# ever could reliably use (agent_factory.py's old AgentExecutor path defaulted
# to 50) - see specs/018-structured-agent-reliability. Also bounds worst-case
# wall-clock time better, since each iteration can be a slow real tool call.
# Raised 15 -> 25 (2026-07-10) once PHASE 7 (Chaining & Escalation, see
# react_prompts.py) gave the agent a real reason to keep going past Phase 6 -
# 15 was tuned for the old 7-phase prompt and left no room for a multi-step
# chain (try leaked creds -> fetch a file -> rescan it) on top of recon.
# Still far below the old 50: structured-output's near-100% parse success
# (specs/018) means iterations here are real progress, not failure retries.
DEFAULT_MAX_ITERATIONS = 25

# Live testing (specs/018) hit this exact Ollama-on-Windows crash twice,
# independent of context size (once at num_ctx=8192 before KV-cache
# quantization, once again afterward with a tiny ~400-char context) -
# a known, intermittent llama.cpp/CUDA/Windows driver bug (matches upstream
# ollama/ollama GitHub issues, e.g. #16650), not something fixable from
# application code. One retry is a pragmatic mitigation since the crash
# appears transient - Ollama reloads the model fresh on the next request.
_TRANSIENT_INFRA_ERROR_MARKERS = ("llama-server process has terminated", "CUDA error")
_MAX_INFRA_RETRIES = 1


class ArgusBrain:
    """
    Runs a structured-output ReAct loop (app/core/agent/react_workflow.py's
    custom graph) with RAG + Blackboard context fusion.

    specs/018-structured-agent-reliability: this used to route through
    agent_factory.py's classic create_react_agent + AgentExecutor (free-text
    Thought/Action/Observation parsing), which a live production run proved
    unreliable for WhiteRabbitNeo - it repeated the same malformed output on
    every retry until the 900s timeout killed it, producing zero results.
    react_workflow.py's graph tries Ollama's schema-constrained structured
    output first (near-100% parse success per Ollama's own 0.3.0+ docs),
    falling back to regex text parsing only if that's unavailable.
    """
    _URL_RE = re.compile(r"https?://[^\s'\"]+", re.IGNORECASE)
    _DOMAIN_RE = re.compile(
        r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.){1,}"
        r"[a-zA-Z]{2,24}\b"
    )

    def __init__(
        self,
        model_name,
        tools_list,
        rag_config: Optional[dict] = None,
        memory: Optional[ArgusMemory] = None,
        llm: Optional[Any] = None,
    ):
        """`llm` is an optional override of the Ollama-backed default from `build_chat_llm()`.

        Exists so tests can inject a fake/fake-list LLM (e.g. langchain_core's
        FakeListLLM) without needing a live Ollama server; production callers
        never pass it and get the normal Ollama-backed model.

        Uses `build_chat_llm()` (ChatOllama), not `build_llm()` (OllamaLLM) -
        specs/018-structured-agent-reliability found, via direct live
        testing, that `OllamaLLM.with_structured_output()` raises
        `NotImplementedError`, silently defeating this class's entire
        structured-decoding reliability fix on every call. `ChatOllama`
        verified working against the live model - see
        `app/core/llm_factory.py::build_chat_llm()`.

        Args:
            model_name (str): Ollama model tag, passed to `build_chat_llm()`
                unless `llm` overrides it.
            tools_list (list): Tools the ReAct graph/deterministic pipeline
                can call; also indexed by name into `self.tool_map`.
            rag_config (dict | None): RAG settings; defaults to
                `_load_rag_config()`'s result (from `ArgusConfig`) if
                omitted. RAG is disabled if this ends up `None` or lacks
                `enabled: True`.
            memory (ArgusMemory | None): Blackboard/knowledge-graph
                backing store; RAG/graph-edge features are no-ops if
                `None`.
            llm: Optional LLM override (see above); defaults to
                `build_chat_llm(model_name)`.
        """
        self.llm = llm if llm is not None else build_chat_llm(model_name)
        self.tools = tools_list
        self.tool_map = {tool.name: tool for tool in tools_list}
        self.output_parser = PydanticOutputParser(pydantic_object=SecurityReport)
        self.memory = memory

        if rag_config is None:
            rag_config = self._load_rag_config()
        self.rag_enabled = rag_config is not None and rag_config.get("enabled", False)

        self._rag_engine = None
        if self.rag_enabled:
            try:
                config = RAGConfig.from_dict(rag_config or {})
                self._rag_engine = RAGEngine(config=config, model_name=model_name)
                self._rag_engine.initialize()
                print(f"[BRAIN] RAG initialized with {self._rag_engine.vector_store.index_size} indexed chunks")
            except Exception as e:
                print(f"[BRAIN] RAG initialization skipped: {e}")
                self.rag_enabled = False

        self._blackboard_context = ""
        self._refresh_blackboard()

        # RAG source attribution (2026-07-10): which knowledge_base/ documents
        # were actually retrieved and fused into the most recent query's
        # context. A source-attribution UI existed once
        # (app/core/rag/rag_gui.py, commit 8e16cd4) but only on a teammate's
        # side branch that was never merged - RAGResult.sources existed in
        # rag_engine.py but was never threaded through to any user-facing
        # output in mainline. Populated by _enrich_with_rag(), consumed by
        # _attach_rag_sources().
        self._last_rag_sources: list = []

        self.max_iterations = DEFAULT_MAX_ITERATIONS

        print(f"[BRAIN] Using structured-output ReAct graph for model: {model_name}")

    @staticmethod
    def _load_rag_config() -> Optional[Dict[str, Any]]:
        """Load RAG settings from the project-wide ArgusConfig, if RAG is enabled there.

        Returns:
            Optional[Dict[str, Any]]: `ArgusConfig.load().to_rag_dict()` if
            `cfg.rag.enabled` is True, else `None` - also `None` if
            loading the config raises for any reason.
        """
        try:
            from app.core.config import ArgusConfig
            cfg = ArgusConfig.load()
            return cfg.to_rag_dict() if cfg.rag.enabled else None
        except Exception:
            pass
        return None

    def _refresh_blackboard(self):
        """Re-read the Blackboard summary/graph insights into `self._blackboard_context`.

        Sets `self._blackboard_context` to `""` if `self.memory` is `None`
        or the read fails (logged, not raised).
        """
        if self.memory is None:
            self._blackboard_context = ""
            return
        try:
            blackboard = self.memory.get_blackboard_summary()
            insights = self.memory.get_graph_insights()
            parts = []
            if blackboard and blackboard != "{}":
                parts.append(f"[Blackboard Intelligence]\n{blackboard}")
            if insights:
                parts.append(f"[Knowledge Graph Relations]\n{insights}")
            self._blackboard_context = "\n\n".join(parts)
        except Exception as e:
            print(f"[BRAIN] Blackboard refresh failed: {e}")
            self._blackboard_context = ""

    def refresh_blackboard(self):
        """Refresh blackboard."""
        self._refresh_blackboard()

    def _enrich_with_rag(self, query: str, callbacks=None) -> str:
        """Fuse RAG (knowledge base) and Blackboard context into the query text.

        Args:
            query (str): The raw question/instruction.
            callbacks (list | None): Forwarded to `_emit_graph_step` to
                announce which RAG sources were retrieved, if any.

        Returns:
            str: `query` prefixed with fused RAG+Blackboard context if RAG
            is enabled and retrieval succeeded; `query` prefixed with just
            Blackboard context if RAG is disabled/unavailable/failed but
            Blackboard context exists; `query` unchanged otherwise. Also
            sets `self._last_rag_sources` to the retrieved source
            basenames (empty if none).
        """
        self._last_rag_sources = []

        if not self.rag_enabled or self._rag_engine is None:
            if self._blackboard_context:
                return (
                    f"===== LIVE TARGET STATE (current findings) =====\n"
                    f"{self._blackboard_context}\n\n"
                    f"Question: {query}"
                )
            return query

        try:
            combined = self._rag_engine.format_combined_context(
                query=query,
                blackboard_context=self._blackboard_context,
            )
            if combined:
                # RAG source attribution: format_context() (called inside
                # format_combined_context()) already tags each retrieved
                # chunk with "[Source: <basename>]" in the fused text -
                # extracted here rather than re-querying the vector store a
                # second time (retrieve() + format_context() would otherwise
                # duplicate the same similarity search).
                sources = re.findall(r"\[Source: ([^\]]+)\]", combined)
                self._last_rag_sources = list(dict.fromkeys(sources))  # dedup, preserve order
                if self._last_rag_sources:
                    self._emit_graph_step(
                        callbacks,
                        HumanMessage(content=f"Reflection: retrieved knowledge base sources: {', '.join(self._last_rag_sources)}"),
                    )

                enriched = (
                    f"{combined}\n\n"
                    f"Question: {query}\n\n"
                    f"Instructions:\n"
                    f"- STATIC KNOWLEDGE is general pentest techniques, cheatsheets, and reference material.\n"
                    f"- LIVE TARGET STATE is what Argus has actively discovered about the current target.\n"
                    f"- When answering, prioritize live target state over generic knowledge.\n"
                    f"- If live data contradicts static knowledge, note the discrepancy."
                )
                print(f"[BRAIN] Fusion context: RAG + Blackboard ({len(combined)} chars)")
                return enriched
        except Exception as e:
            print(f"[BRAIN] RAG enrichment failed: {e}")

        if self._blackboard_context:
            return (
                f"===== LIVE TARGET STATE =====\n"
                f"{self._blackboard_context}\n\n"
                f"Question: {query}"
            )
        return query

    def ask(self, query: str, callbacks=None, on_phase: Optional[Any] = None) -> Dict[str, Any]:
        """Run a security analysis for `query`, choosing the deterministic
        pipeline if `on_phase` is given, else the modular ReAct workflow.

        Args:
            query (str): The user's request text (target is extracted
                from this via `react_workflow.extract_target`).
            callbacks (list | None): Forwarded to the chosen path for
                live step reporting.
            on_phase (callable | None): If given, explicitly selects
                `ask_deterministic` (see that method's own docstring for
                its signature); if omitted, runs the ReAct graph instead.

        Returns:
            Dict[str, Any]: `{"output": ...}`, shaped per whichever path
            ran (see `ask_deterministic`/`_run_structured_graph`).
        """
        if on_phase is not None:
            # Explicitly requested the deterministic pipeline
            return self.ask_deterministic(query, callbacks=callbacks, on_phase=on_phase)

        # Otherwise, run modular ReAct workflow
        from app.core.agent.react_workflow import extract_target
        target = extract_target(query)
        self._refresh_blackboard()
        augmented_query = self._enrich_with_rag(query, callbacks)
        return self._run_structured_graph(augmented_query, target, callbacks)

    def ask_agentic(self, query: str, callbacks=None) -> Dict[str, Any]:
        """Thin wrapper delegating to the modular ReAct workflow to fulfill GUI calls."""
        return self.ask(query, callbacks=callbacks)

    def ask_deterministic(self, target: str, callbacks=None, on_phase: Optional[Any] = None) -> Dict[str, Any]:
        """
        Runs the fixed pipeline directly, then builds the SecurityReport
        deterministically from the confirmed findings the tools recorded in
        memory - NO LLM synthesis. A weak local model both (a) added 30-360s
        of latency and retries here and (b) routinely failed to emit valid
        report JSON, dropping real findings. Building the report straight from
        the scanner findings makes it fast and truthful: a confirmed
        `[signature: root:x:0:0:]` traversal always surfaces.
        """
        self._refresh_blackboard()
        clean_target = self._extract_target(target)
        if clean_target != target.strip():
            print(f"[BRAIN] Extracted target '{clean_target}' from input text.")
        # Capture the run start BEFORE any tool fires so the report includes
        # only THIS run's findings. The blackboard is a persistent SQLite DB -
        # without this bound, get_detailed_findings() returns every finding
        # ever recorded for this host (stale Nikto dumps, prior runs), which
        # would falsely appear as results of the current scan.
        run_started = datetime.now().isoformat()
        observations = self.run_deterministic_recon(clean_target, on_phase=on_phase)
        return {"output": self._build_deterministic_report(clean_target, observations, run_started)}

    # Keyword -> (severity, remediation) mapping for deterministic findings.
    _VULN_CLASSIFIERS = (
        (("traversal", "lfi", "passwd", "shadow", "file inclusion", "web.config", "win.ini"),
         "High", "Canonicalize and validate file-path input; reject '../' and encoded "
         "traversal sequences; serve files from an allowlist, never from user input."),
        (("rce", "command execution", "id command"),
         "Critical", "Never pass user input to a shell/eval; use safe APIs and strict input validation."),
        (("sqli", "sql injection", "sql syntax", "sql error"),
         "High", "Use parameterized queries / prepared statements; never concatenate user input into SQL."),
        (("secret", "api key", "credential", "password", "db_password"),
         "High", "Rotate the exposed secret immediately; remove secrets from responses and source."),
    )

    _SEVERITY_SCORE = {"Critical": 10, "High": 9, "Medium": 6, "Low": 3, "Info": 1}

    # Only these tools produce a *content-verified* exploit finding (a real
    # /etc/passwd read, a SQL-error signature, a leaked secret). Recon/scanner
    # tools like Nikto store every "+" output line - including pure info
    # (Server banner, Start Time, "1 host tested", "[FAIL] Unable to connect")
    # - as data_type "vulnerability", which is noise, not a confirmed finding.
    # The report lists only verified exploits; raw recon output stays in
    # `_raw_tool_observations` for context.
    _CONFIRMED_VULN_TOOLS = frozenset({
        "path_traversal", "evasion_probe", "reflective_verification", "secrets",
    })

    def _classify_finding(self, text: str):
        """Map a finding's text to (severity, remediation) deterministically."""
        low = (text or "").lower()
        for keywords, severity, remediation in self._VULN_CLASSIFIERS:
            if any(k in low for k in keywords):
                return severity, remediation
        return "Medium", "Review and sanitize the affected input; validate against an allowlist."

    def _build_deterministic_report(
        self, target: str, observations: Dict[str, str], since: Optional[str] = None
    ) -> Dict[str, Any]:
        """Assemble a SecurityReport-shaped dict from confirmed memory findings.

        Reads back the content-verified exploit findings the active probes
        persisted THIS run (`since` bounds out stale findings from the
        persistent blackboard) and renders them directly - no model in the
        loop, so nothing a confirmed scan proved can be lost or hallucinated,
        and nothing it did not prove can be fabricated.
        """
        from app.tools.utils import normalize_domain_for_memory

        findings: list[dict] = []
        seen: set[str] = set()
        if self.memory is not None:
            try:
                raw = self.memory.get_detailed_findings(
                    normalize_domain_for_memory(target), since=since
                )
            except Exception as e:
                print(f"[BRAIN] could not read findings for report: {e}")
                raw = []
            for f in raw or []:
                if f.get("data_type") not in ("vulnerability", "high_severity_vulnerability"):
                    continue
                # Only content-verified exploit tools count as confirmed
                # findings; recon/Nikto info lines are excluded (kept in raw
                # observations) so metadata never masquerades as a vuln.
                if f.get("tool_name") not in self._CONFIRMED_VULN_TOOLS:
                    continue
                raw_data = (f.get("raw_data") or "").strip()
                summary = (f.get("summary") or raw_data).strip()
                dedupe_key = f"{f.get('tool_name')}::{raw_data}"
                if not raw_data or dedupe_key in seen:
                    continue
                seen.add(dedupe_key)
                severity, remediation = self._classify_finding(f"{summary} {raw_data}")
                payload = raw_data.split("=", 1)[1].strip() if "=" in raw_data else "n/a"
                findings.append({
                    "target": target,
                    "issue": summary,
                    "severity": severity,
                    "description": raw_data,
                    "suggested_payload": payload,
                    "remediation": remediation,
                })

        risk = max((self._SEVERITY_SCORE.get(f["severity"], 1) for f in findings), default=1)
        sev_counts: Dict[str, int] = {}
        for f in findings:
            sev_counts[f["severity"]] = sev_counts.get(f["severity"], 0) + 1
        counts_str = ", ".join(f"{n} {sev}" for sev, n in sev_counts.items()) or "none"

        phases_run = ", ".join(observations.keys()) or "(none)"
        summary = (
            f"Deterministic security scan of {target} complete. "
            f"Phases executed: {phases_run}. "
            f"Confirmed findings: {len(findings)} ({counts_str})."
        )
        next_steps = (
            ["Remediate the confirmed findings above, highest severity first.",
             "Re-run with ARGUS_SCAN_PROFILE=full for deep recon (nmap/nikto/ffuf/subdomains)."]
            if findings else
            ["No vulnerabilities were confirmed by the active probes.",
             "Re-run with ARGUS_SCAN_PROFILE=full for a deeper sweep."]
        )

        return {
            "summary": summary,
            "attack_surface_stats": f"Phases run: {len(observations)} | confirmed findings: {len(findings)}",
            "findings": findings,
            "overall_risk_score": risk,
            "next_steps": next_steps,
            "output": summary,
            "_raw_tool_observations": observations,
        }

    _BARE_HOSTNAME_TOOLS = {"Check_Reachability"}

    @staticmethod
    def _to_bare_hostname(target: str) -> str:
        """Delegates to `app.tools.utils.to_bare_hostname` (single source
        of truth - `react_workflow.py`'s live ReAct path needs the same
        logic).

        Args:
            target (str): A URL or bare host; a missing scheme is treated
                as `http://`.

        Returns:
            str: The bare hostname, or `target` unchanged if it has no
            parseable hostname.
        """
        return to_bare_hostname(target)

    _COMMAND_NOT_FOUND_RE = re.compile(r"(\S+):\s*command not found")
    _SELF_HEAL_TOOL_NAME = "System_Self_Heal"

    def _invoke(self, tool, arg: str) -> str:
        """Call a tool with a single string argument, regardless of its calling convention.

        Args:
            tool: A LangChain `Tool` (has `.run`) or a plain callable
                (has `.invoke`).
            arg (str): The single string argument to pass.

        Returns:
            str: The tool's result, stringified.
        """
        if hasattr(tool, "run"):
            return str(tool.run(arg))
        return str(tool.invoke(arg))

    def _try_self_heal(self, tool_name: str, observation: str) -> bool:
        """
        If `observation` contains one or more "X: command not found"
        errors, ask System_Self_Heal (if registered) to install each
        missing binary. Returns True if at least one heal attempt ran
        without raising, so the caller knows a retry is worth trying.

        Args:
            tool_name (str): Name of the tool whose output is being
                checked (used only in log/print messages).
            observation (str): The tool's raw output to scan for
                "X: command not found" errors.

        Returns:
            bool: True if at least one self-heal attempt ran without
            raising; False if no missing-command errors were found, or
            `System_Self_Heal` isn't registered.
        """
        missing = self._COMMAND_NOT_FOUND_RE.findall(observation)
        if not missing:
            return False

        heal_tool = self.tool_map.get(self._SELF_HEAL_TOOL_NAME)
        if heal_tool is None:
            print(
                f"[BRAIN] {tool_name} is missing {missing}, but "
                f"'{self._SELF_HEAL_TOOL_NAME}' isn't registered - can't auto-fix. "
                f"Install manually inside WSL/Kali."
            )
            return False

        healed_any = False
        for missing_cmd in dict.fromkeys(missing):  # dedupe, keep order
            print(f"[BRAIN] {tool_name} is missing '{missing_cmd}' - attempting self-heal...")
            try:
                heal_result = self._invoke(heal_tool, missing_cmd)
                print(f"[BRAIN] Self-heal result for '{missing_cmd}': {heal_result[:300]}")
                healed_any = True
            except Exception as e:
                print(f"[BRAIN] Self-heal attempt for '{missing_cmd}' raised: {e}")
        return healed_any

    def _record_graph_edge(
        self,
        entity: tuple[str, str],
        source_val: str,
        target_val: str,
        rel_type: str,
    ) -> None:
        """Delegates to `app.tools.utils.record_graph_edge` (single source
        of truth - `react_workflow.py`'s live ReAct path needs the same
        logic).

        Args:
            entity (tuple[str, str]): `(entity_type, entity_value)` for
                the new node this edge introduces - always equal to
                whichever of source_val/target_val isn't the
                already-registered graph root, so it's bundled here
                rather than passed as two more separate positional strings.
            source_val (str): The relation's source node value.
            target_val (str): The relation's target node value.
            rel_type (str): The relation type (e.g. "USES_TECH").

        Returns:
            None
        """
        record_graph_edge(self.memory, entity, source_val, target_val, rel_type)

    # ------------------------------------------------------------------
    # Deterministic report
    # ------------------------------------------------------------------
    @staticmethod
    def _classify_finding(text: str) -> tuple:
        """Map a finding's text to `(issue, remediation)`.

        Args:
            text (str): The finding's summary and raw data, lowercased.

        Returns:
            tuple[str, str]: Human-readable issue title and its remediation.
        """
        if any(term in text for term in _TRAVERSAL_TERMS):
            return "Path Traversal / Local File Inclusion", _TRAVERSAL_REMEDIATION
        if any(term in text for term in _SQLI_TERMS):
            return "SQL Injection", _SQLI_REMEDIATION
        return "Confirmed vulnerability", _GENERIC_REMEDIATION

    @staticmethod
    def _extract_payload(raw_data: str) -> Optional[str]:
        """Recover the payload string a finding was confirmed with.

        Findings are stored as free text by the tool that found them, in two
        shapes: a full request URL (`Traversal: https://x/image?filename=P`)
        or a bare label plus payload (`SQLi: 1 OR 1=1`). The query-string
        form is checked first, since splitting that one on ": " would return
        the whole URL rather than the payload.

        Args:
            raw_data (str): The finding's stored raw text.

        Returns:
            str or None: The payload, or None when none can be recovered.
        """
        if not raw_data:
            return None
        if "?" in raw_data:
            query = raw_data.split("?", 1)[1].strip()
            last_param = query.split("&")[-1]
            if "=" in last_param:
                value = last_param.split("=", 1)[1].strip()
                if value:
                    return value
        if ": " in raw_data:
            return raw_data.split(": ", 1)[1].strip() or None
        return raw_data.strip() or None

    def _build_deterministic_report(
        self,
        target: str,
        observations: Dict[str, str],
        since: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build the run's report directly from confirmed findings in memory.

        No LLM is involved. The tools already decided what counts as
        confirmed (content-based signature matches, see
        `app/tools/utils.py::find_sensitive_content_match`); this method only
        renders those decisions, so a weak local model can neither invent a
        finding nor drop a real one.

        Args:
            target (str): The scan target, used as each finding's `target`.
            observations (Dict[str, str]): `{phase_label: raw_observation}`
                from `run_deterministic_recon`, summarised in
                `attack_surface_stats`.
            since (str, optional): ISO timestamp of this run's start. The
                blackboard is persistent and holds earlier runs' findings, so
                without this the report would replay old results.

        Returns:
            Dict[str, Any]: A `SecurityReport`-shaped dict with `summary`,
            `attack_surface_stats`, `findings`, `overall_risk_score` and
            `next_steps`.
        """
        if self.memory is None:
            stored = []
        else:
            try:
                # Findings are keyed by the same normalisation the tools used
                # when writing them (evasion.py / path_traversal.py both call
                # normalize_domain_for_memory), so the report must look them
                # up under that exact key or it finds nothing.
                stored = self.memory.get_detailed_findings(
                    normalize_domain_for_memory(target), since=since
                ) or []
            except Exception as e:
                print(f"[BRAIN] Could not read findings for the report: {e}")
                stored = []

        findings: List[Dict[str, Any]] = []
        seen: set = set()

        for entry in stored:
            if (entry.get("data_type") or "").lower() != "vulnerability":
                continue
            tool_name = (entry.get("tool_name") or "").lower()
            if tool_name in _RECON_NOISE_TOOLS:
                continue

            raw_data = entry.get("raw_data") or ""
            summary = entry.get("summary") or ""
            issue, remediation = self._classify_finding(f"{summary} {raw_data}".lower())
            payload = self._extract_payload(raw_data)

            key = (issue, payload)
            if key in seen:
                continue
            seen.add(key)

            findings.append({
                "target": target,
                "issue": issue,
                "severity": "High",
                "description": summary or raw_data,
                "suggested_payload": payload,
                "remediation": remediation,
                "tool_source": entry.get("tool_name"),
            })

        if findings:
            risk = 9
            summary_text = (
                f"{len(findings)} confirmed vulnerability finding(s) on {target}, "
                f"each verified from real response content."
            )
            next_steps = [
                "Review the proof-of-concept screenshots saved under artifacts/screenshots/.",
                "Apply the remediation listed for each finding, then re-run the scan to confirm it no longer reproduces.",
            ]
        else:
            risk = 1
            summary_text = (
                f"No vulnerabilities were confirmed on {target} in this run."
            )
            next_steps = [
                "No vulnerabilities were confirmed. Re-run with ARGUS_SCAN_PROFILE=full "
                "for the deeper recon sweep, or widen the scope to other endpoints.",
            ]

        return {
            "target": target,
            "scan_target": target,
            "summary": summary_text,
            "attack_surface_stats": (
                f"{len(observations)} scan phase(s) completed against {target}."
            ),
            "findings": findings,
            "overall_risk_score": risk,
            "next_steps": next_steps,
        }

    def _run_tool_safely(self, tool_name: str, target: str) -> str:
        """Call a registered tool by name, converting to a bare hostname
        for tools that need one and retrying once after a self-heal
        attempt if the first call reports a missing command.

        Args:
            tool_name (str): Name of the tool to call, looked up in
                `self.tool_map`.
            target (str): The raw target string to pass (converted to a
                bare hostname first for tools in `_BARE_HOSTNAME_TOOLS`).

        Returns:
            str: The tool's output, or a `[SKIPPED]`/`[TOOL ERROR]`
            message if the tool isn't registered or raises.
        """
        tool = self.tool_map.get(tool_name)
        if tool is None:
            return f"[SKIPPED] Tool '{tool_name}' is not registered in this build."

        call_target = target
        if tool_name in self._BARE_HOSTNAME_TOOLS:
            call_target = self._to_bare_hostname(target)
            if call_target != target:
                print(f"[BRAIN] {tool_name} needs a bare hostname - using '{call_target}' instead of '{target}'")

        try:
            result = self._invoke(tool, call_target)
        except Exception as e:
            return f"[TOOL ERROR] {tool_name} raised: {e}"

        if self._try_self_heal(tool_name, result):
            print(f"[BRAIN] Retrying {tool_name} after self-heal...")
            try:
                retry_result = self._invoke(tool, call_target)
                return retry_result
            except Exception as e:
                return f"[TOOL ERROR after self-heal] {tool_name} raised: {e}"

        return result

    def _parse_subdomains(self, observation: str, exclude_hostname: str) -> List[str]:
        """Delegates to `app.tools.utils.parse_subdomains` (single source
        of truth - `react_workflow.py`'s live ReAct path needs the same
        logic).

        Args:
            observation (str): Raw Subdomain_Enumeration tool output.
            exclude_hostname (str): The already-scanned root host to
                exclude from the results.

        Returns:
            List[str]: Candidate subdomains, in first-seen order, with
            `exclude_hostname` and any line containing a space or slash
            (or lacking a `.`) filtered out.
        """
        return parse_subdomains(observation, exclude_hostname)

    def _parse_tech(self, observation: str) -> str:
        """Delegates to `app.tools.utils.parse_tech_block` (single source
        of truth - `react_workflow.py`'s live ReAct path needs the same
        logic). Use `_clean_tech_string()` before using the result as a
        search query.

        Args:
            observation (str): Raw Recon_Suite tool output.

        Returns:
            str: The raw `Tech:` block's text (up to 500 chars), or `""`
            if no `Tech:` block is found.
        """
        return parse_tech_block(observation)

    def _clean_tech_string(self, raw_tech: str) -> str:
        """Delegates to `app.tools.utils.clean_tech_string` (single source
        of truth - `react_workflow.py`'s live ReAct path needs the same
        logic).

        Args:
            raw_tech (str): The raw `Tech:` line text (as returned by
                `_parse_tech`).

        Returns:
            str: A space-joined, deduplicated string of useful tech
            tokens (up to 200 chars); `""` if `raw_tech` is empty, or
            `raw_tech[:200]` unchanged if no tokens survive filtering.
        """
        return clean_tech_string(raw_tech)

    def _parse_interesting_paths(self, observation: str) -> List[str]:
        """Pulls endpoints matching common sensitive-path keywords out of
        Crawl_Target's 'Top findings:' list.

        Args:
            observation (str): Raw Crawl_Target tool output.

        Returns:
            List[str]: Up to `MAX_CHAINED_PATHS` lines from the "Top
            findings:" section that contain a keyword from
            `_INTERESTING_PATH_KEYWORDS`; empty if no such section/lines
            exist.
        """
        capture = False
        paths = []
        for line in observation.splitlines():
            line = line.strip()
            if "top findings" in line.lower():
                capture = True
                continue
            if not capture or not line:
                continue
            if any(kw in line.lower() for kw in _INTERESTING_PATH_KEYWORDS):
                paths.append(line)
        return paths[:MAX_CHAINED_PATHS]

    def _build_exploit_query(self, paths: List[str]) -> str:
        """
        Turns crawled paths into vulnerability-class search terms instead
        of a sentence containing literal URLs/query-strings, which almost
        certainly doesn't match however Exploit_Suggester's payload
        repository search actually works.

        Args:
            paths (List[str]): Crawled endpoint lines (as returned by
                `_parse_interesting_paths`).

        Returns:
            str: Space-joined, sorted vulnerability-class terms matched
            via `_PATH_KEYWORD_TO_VULN_CLASS`; falls back to
            "common web vulnerabilities" if no keyword matched.
        """
        terms = set()
        for path in paths:
            low = path.lower()
            for keyword, vuln_terms in _PATH_KEYWORD_TO_VULN_CLASS.items():
                if keyword in low:
                    terms.update(vuln_terms.split())
        if not terms:
            terms = {"common", "web", "vulnerabilities"}
        return " ".join(sorted(terms))

    def run_deterministic_recon(
        self,
        target: str,
        on_phase: Optional[Any] = None,
    ) -> Dict[str, str]:
        """
        Executes DETERMINISTIC_PHASES in fixed order via direct Python
        calls - no LLM involved in choosing or sequencing tools. Also
        chains a few real findings into automatic follow-up calls. Returns
        {label: raw_observation} for every phase (core + chained) that ran.

        Args:
            target (str): The target to run recon against.
            on_phase (callable | None): Optional
                `callable(phase_index, total_phases, tool_name, observation)`
                invoked immediately after each phase finishes (including
                chained follow-ups); exceptions from it are logged and
                ignored, never propagated.

        Returns:
            Dict[str, str]: `{label: raw_observation}` for every core
            phase in `DETERMINISTIC_PHASES` plus any chained follow-up
            calls (subdomain reachability re-checks, a tech-based
            Smart_Web_Search, an Exploit_Suggester lookup) that actually ran.
        """
        phases = _selected_deterministic_phases()
        print(
            f"[BRAIN] Scan profile: "
            f"{os.environ.get(SCAN_PROFILE_ENV, 'fast')} ({len(phases)} phases)"
        )

        observations: Dict[str, str] = {}
        counter = {"i": 0, "total": len(phases)}

        # Seed the knowledge graph with the root domain up front. add_relation
        # only writes an edge when BOTH endpoints already exist as entities,
        # so the root must be registered before any USES_TECH / SUBDOMAIN_OF
        # edge can attach to it.
        graph_root = self._to_bare_hostname(target)
        if self.memory is not None and graph_root:
            try:
                self.memory.upsert_entity("domain", graph_root)
            except Exception as e:
                print(f"[BRAIN] could not seed graph root '{graph_root}': {e}")

        def emit(label: str, obs: str, domain: str = target) -> None:
            """Record one phase's observation into `observations`, persist
            it as a finding, and notify `on_phase` if given.

            Args:
                label (str): Key to store this observation under (may
                    differ from the raw tool name for chained calls, e.g.
                    "Check_Reachability[sub.example.com]").
                obs (str): The raw tool observation text.
                domain (str): Domain to attribute the finding to; defaults
                    to the outer `target`.

            Returns:
                None
            """
            counter["i"] += 1
            observations[label] = obs
            if self.memory is not None:
                try:
                    self.memory.add_finding(
                        domain=domain,
                        tool_name=label,
                        data_type="recon",
                        raw_data=obs,
                        summary=obs[:500],
                    )
                except Exception as e:
                    print(f"[BRAIN] Could not persist finding for {label}: {e}")
            if on_phase is not None:
                try:
                    on_phase(counter["i"], counter["total"], label, obs)
                except Exception as e:
                    print(f"[BRAIN] on_phase callback raised (ignored): {e}")

        for tool_name in phases:
            print(f"[BRAIN] Running phase: {tool_name}({target})")
            observation = self._run_tool_safely(tool_name, target)
            emit(tool_name, observation)

            # --- Phase chaining: real findings feed real follow-ups ---

            if tool_name == "Subdomain_Enumeration":
                subs = self._parse_subdomains(
                    observation, exclude_hostname=self._to_bare_hostname(target)
                )
                chosen = subs[:MAX_CHAINED_SUBDOMAINS]
                if chosen:
                    counter["total"] += len(chosen)
                    for sub in chosen:
                        print(f"[BRAIN] Chaining: re-checking discovered subdomain '{sub}'")
                        sub_obs = self._run_tool_safely("Check_Reachability", sub)
                        emit(f"Check_Reachability[{sub}]", sub_obs, domain=sub)
                        # Persist the edge so Query_Knowledge_Graph has data.
                        self._record_graph_edge(("domain", sub), sub, graph_root, "SUBDOMAIN_OF")

            elif tool_name == "Recon_Suite":
                raw_tech = self._parse_tech(observation)
                tech = self._clean_tech_string(raw_tech)
                if tech:
                    # Persist each detected technology as a graph edge.
                    for token in tech.split():
                        self._record_graph_edge(("tech", token), graph_root, token, "USES_TECH")
                if tech and "Smart_Web_Search" in self.tool_map:
                    counter["total"] += 1
                    query = f"known CVEs and exploits for {tech}"
                    print(f"[BRAIN] Chaining: looking up known vulnerabilities for '{tech}'")
                    lookup_obs = self._run_tool_safely("Smart_Web_Search", query)
                    emit("Smart_Web_Search[tech_lookup]", lookup_obs)

            elif tool_name == "Crawl_Target":
                paths = self._parse_interesting_paths(observation)
                if paths and "Exploit_Suggester" in self.tool_map:
                    counter["total"] += 1
                    query = self._build_exploit_query(paths)
                    print(f"[BRAIN] Chaining: requesting exploit suggestions for '{query}' ({len(paths)} matching endpoint(s))")
                    sugg_obs = self._run_tool_safely("Exploit_Suggester", query)
                    emit("Exploit_Suggester[endpoint_lookup]", sugg_obs)

        return observations

    def _extract_target(self, query: str) -> str:
        """
        Extract the target URL/domain from an instruction paragraph,
        applying scheme inference (prepending http:// to bare domains).

        Args:
            query (str): The instruction text to search.

        Returns:
            str: The first matched URL (as-is), or `http://` + the first
            matched bare domain, or `query` unchanged (with a warning
            printed) if neither pattern matches anywhere in the text.
        """
        query = query.strip()

        url_match = self._URL_RE.search(query)
        if url_match:
            return url_match.group(0).rstrip(".,;:!?)\"'")

        domain_match = self._DOMAIN_RE.search(query)
        if domain_match:
            bare_domain = domain_match.group(0).rstrip(".,;:!?)\"'")
            return f"http://{bare_domain}"

        # No URL/domain found anywhere in the text
        print(
            f"[BRAIN] WARNING: could not find a URL or domain inside the "
            f"input text: {query[:200]!r}. Passing it through as-is, but "
            f"tool results are likely to be meaningless."
        )
        return query

    @staticmethod
    def _looks_like_schema_echo(output: Any) -> bool:
        """
        Detects the model copying the JSON Schema / field-instructions
        text back verbatim instead of producing filled-in report data.

        Args:
            output (Any): The parsed synthesis output to check.

        Returns:
            bool: True if `output` isn't a dict, contains a `$defs`/
            `properties`/`required` key (schema-echo signature), or is
            missing the required `summary` key; False otherwise.
        """
        if not isinstance(output, dict):
            return False
        if any(k in output for k in ("$defs", "properties", "required")):
            return True
        if "summary" not in output:
            return True
        return False

    def _run_structured_graph(self, query: str, target: str, callbacks=None) -> Dict[str, Any]:
        """Run react_workflow.py's structured-output ReAct graph to completion.

        Args:
            query (str): The (RAG/Blackboard-enriched) question/instruction -
                used as the graph's initial message content only.
            target (str): The target being analyzed. MUST be extracted from
                the raw, pre-enrichment query, not this enriched one - a
                live run found `extract_target()` grabbing a JSON key like
                `"www.example.com:80":` out of the prepended Blackboard
                context block instead of the real target, because that
                block sorts before the actual "Question: ..." text and
                itself contains dot-separated, space-free tokens that look
                exactly like what `extract_target()` searches for. That
                corrupted "target" then got passed as tool input, breaking
                every tool call downstream (observed live: a shell syntax
                error from the stray embedded quote character).
            callbacks (list | None): Objects exposing an `on_graph_event(status,
                detail)` method (e.g. `app/core/agent/react_callback.py`'s
                `LiveFeedCallbackHandler`) - called once per new message the
                graph produces, so callers get the same live step-by-step
                visibility the old AgentExecutor callbacks gave, without
                relying on LangChain's AgentExecutor-specific dispatch (a raw
                `StateGraph` doesn't go through that).

        Returns:
            Dict[str, Any]: `{"output": ...}` - a `SecurityReport`-shaped
            dict on successful structured extraction, the raw final-answer
            text if structured extraction wasn't possible, or
            `{"output": {"error": ..., "message": ...}}` if the graph
            never reached a Final Answer within `self.max_iterations`
            (never fabricated - Constitution VIII).
        """
        from app.core.agent.react_workflow import _build_custom_workflow, _build_multi_role_workflow

        # specs/019-shared-memory-reflection-upgrade FR-006/NFR-002: read the
        # escape hatch from config at graph-build time, not hardcoded, so an
        # operator can disable the 3x majority-vote check if it measurably
        # pushes a run past max_iterations' time budget in practice.
        # specs/020-multi-agent-role-separation: enable_multi_agent_roles
        # reads the same way - default False, an experimental alternate
        # graph, not the production default (NFR-001 not yet measured).
        try:
            from app.core.config import ArgusConfig
            _cfg = ArgusConfig.load()
            enable_inter_reflection = _cfg.enable_inter_reflection
            enable_multi_agent_roles = _cfg.enable_multi_agent_roles
        except Exception:
            enable_inter_reflection = True
            enable_multi_agent_roles = False

        # build_workflow() would route here via _supports_tool_calls(llm) -
        # but ChatOllama (build_chat_llm()) reports True for tool-calling-
        # capable models like WhiteRabbitNeo, which would silently switch to
        # _build_prebuilt_workflow()'s ArgusPrebuiltState shape (no phase/
        # tool_name/tool_result fields). This class's _finalize_graph_output()/
        # _emit_graph_step() are only written against ArgusAgentState (the
        # custom-mode shape) - confirmed live: routing to prebuilt mode made
        # _finalize_graph_output() report "no_final_answer" unconditionally,
        # even when the underlying prebuilt agent likely completed a real
        # tool call correctly. Call the custom graph directly until prebuilt
        # mode gets its own tested integration.

        last_error: Optional[Exception] = None
        for attempt in range(_MAX_INFRA_RETRIES + 1):
            if enable_multi_agent_roles:
                from app.core.agent.brain_tools import partition_tools_by_role
                graph = _build_multi_role_workflow(
                    self.llm, partition_tools_by_role(self.tools), self.memory,
                    enable_inter_reflection=enable_inter_reflection,
                )
            else:
                graph = _build_custom_workflow(
                    self.llm, self.tools, self.memory,
                    enable_inter_reflection=enable_inter_reflection,
                )
            initial_state: Dict[str, Any] = {
                "messages": [HumanMessage(content=query)],
                "target": target,
                "phase": "init",
                "blackboard_summary": self._blackboard_context,
                "iteration_count": 0,
                "max_iterations": self.max_iterations,
                "tool_name": None,
                "tool_input": None,
                "tool_result": None,
                "tool_error": None,
                "tool_call_history": [],
                "reflection_notes": [],
                "phase56_nudged": False,
                "zero_tool_final_answer_nudged": False,
                "phase12_nudged": False,
                "consecutive_duplicate_blocks": 0,
                "current_role": "",
                "role_history": [],
            }
            seen_messages = len(initial_state["messages"])
            final_state: Dict[str, Any] = initial_state
            try:
                for state in graph.stream(initial_state, stream_mode="values"):
                    final_state = state
                    messages = state.get("messages", [])
                    for message in messages[seen_messages:]:
                        self._emit_graph_step(callbacks, message)
                    seen_messages = len(messages)
                return self._finalize_graph_output(final_state)
            except Exception as e:
                last_error = e
                print(f"[BRAIN] Structured graph execution failed (attempt {attempt + 1}/{_MAX_INFRA_RETRIES + 1}): {e}")
                # Ollama's llama-server subprocess crashing outright (a known,
                # intermittent Windows/CUDA driver bug - not something app
                # code can fix, confirmed via live testing and upstream
                # GitHub issues, specs/018-structured-agent-reliability) is
                # the ONE failure worth retrying: the server auto-reloads the
                # model on the next request. Anything else (a real, likely
                # persistent bug) fails immediately rather than masking it
                # behind a retry.
                is_transient_infra_crash = any(
                    marker in str(e) for marker in _TRANSIENT_INFRA_ERROR_MARKERS
                )
                if not is_transient_infra_crash or attempt >= _MAX_INFRA_RETRIES:
                    break
                print("[BRAIN] Detected a transient Ollama/CUDA infrastructure crash - retrying once...")

        return {"output": {"error": "graph_execution_failed", "message": str(last_error)}}

    @staticmethod
    def _emit_graph_step(callbacks, message) -> None:
        """Forward one new graph message to each callback's `on_graph_event`.

        specs/019-shared-memory-reflection-upgrade FR-008: Intra/Inter-
        reflection notes are appended to `state["messages"]` as regular
        `HumanMessage`s prefixed with `"Reflection:"` (see
        `react_workflow.py`'s `parse_node`/`execute_node`), rather than
        requiring new callback plumbing threaded into the node functions
        themselves - they flow through this same per-message loop
        (`_run_structured_graph`) and are tagged with their own status here
        so callers can distinguish them from ordinary tool observations
        (Constitution VIII - a reflection step's outcome must be visible,
        not hidden overhead).

        Args:
            callbacks (list | None): Objects exposing an
                `on_graph_event(status, detail)` method; a no-op if
                falsy.
            message: The new graph message (its `.content`, or itself if
                no `.content` attribute, is forwarded).

        Returns:
            None
        """
        if not callbacks:
            return
        content = str(getattr(message, "content", message))
        if content.startswith("Reflection:"):
            status = "reflecting"
        elif content.startswith("Observation:"):
            status = "completed"
        else:
            status = "running"
        for cb in callbacks:
            handler = getattr(cb, "on_graph_event", None)
            if handler:
                handler(status, content)

    def _finalize_graph_output(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and structure the graph's Final Answer, if it reached one.

        Args:
            state (Dict[str, Any]): The graph's final streamed state.

        Returns:
            Dict[str, Any]: `{"output": <SecurityReport-shaped dict>}` via
            structured/Pydantic/regex-JSON extraction (see
            `_process_output`), or `{"output": {"error":
            "no_final_answer", "message": ...}}` if the graph never
            reached `phase == "done"` with a "Final Answer:" message.
        """
        from app.core.agent.react_workflow import _try_structured_final_answer

        messages = state.get("messages", [])
        last_content = str(messages[-1].content) if messages else ""
        if state.get("phase") != "done" or "Final Answer:" not in last_content:
            return {
                "output": {
                    "error": "no_final_answer",
                    "message": f"Agent did not produce a Final Answer within {state.get('max_iterations')} iterations.",
                }
            }

        raw_answer = last_content.split("Final Answer:", 1)[1].strip()
        structured = _try_structured_final_answer(self.llm, raw_answer)
        if structured is not None:
            result = {"output": structured}
        else:
            # Falls back further to _process_output's Pydantic/regex-JSON
            # extraction (e.g. the model wrote valid JSON inline despite
            # structured decoding being unavailable) before giving up and
            # returning the raw text.
            result = self._process_output(raw_answer, raw_answer)
        self._attach_rag_sources(result)
        # `target` lives on the graph state here, not as a parameter - this
        # method only receives `state` (see `_run_structured_graph`, which
        # seeds `initial_state["target"]`).
        self._reconcile_findings_with_blackboard(result, state.get("target", ""))
        return result

    @staticmethod
    def _parse_vulnerability_finding(raw_data: str) -> Dict[str, str]:
        """Split a recorded `vulnerability` row into endpoint/param/payload.

        Tools store the proof as a single string - `path_traversal.py` writes
        `"Traversal: https://host/image?filename=....//etc/passwd"`,
        `evasion.py` writes `"Traversal: <payload>"` or `"SQLi: <payload>"`.
        Only the parts actually present are returned.

        Args:
            raw_data (str): The finding's `raw_data` column.

        Returns:
            Dict[str, str]: Any of `kind`, `endpoint`, `param`, `payload`.
        """
        parsed: Dict[str, str] = {}
        text = (raw_data or "").strip()
        if ":" in text:
            kind, _, remainder = text.partition(":")
            parsed["kind"] = kind.strip()
            text = remainder.strip()
        if text.startswith("http") and "?" in text:
            endpoint, _, query = text.partition("?")
            parsed["endpoint"] = endpoint
            name, sep, value = query.partition("=")
            if sep:
                parsed["param"] = name
                parsed["payload"] = value
            else:
                parsed["payload"] = query
        elif text:
            parsed["payload"] = text
        return parsed

    def _reconcile_findings_with_blackboard(
        self, result: Dict[str, Any], target: str
    ) -> None:
        """Restore tool-recorded evidence the model dropped from its report.

        `SecurityReport.findings` is written free-hand by the LLM in its Final
        Answer and copied verbatim by `scripts/run_agent.py::_build_final_state`.
        Nothing previously checked it against the Blackboard, and the model
        summarises rather than transcribes. Observed live 2026-07-27 against a
        PortSwigger lab: `Path_Traversal_Scan` confirmed
        `/image?filename=....//....//....//etc/passwd` with a real
        `root:x:0:0:` read and recorded it, yet the delivered finding carried
        `suggested_payload: ""`, `tool_source: null` and the bare site root as
        its target - so the UI showed "Suggested payload: n/a" and the one
        piece of reproducible proof the whole run existed to produce was lost.
        An earlier run on the same class dropped the finding entirely.

        This is provenance repair, not generation (Constitution VIII -
        Truthful Runtime): every value written here was recorded by a tool
        that actually confirmed it. Nothing is invented, and a field the model
        already filled is never overwritten.

        Args:
            result (Dict[str, Any]): The `{"output": ...}` dict to mutate in
                place.
            target (str): The analyzed target, used to key the Blackboard.

        Returns:
            None
        """
        output = result.get("output")
        if self.memory is None or not isinstance(output, dict) or "error" in output:
            return

        try:
            from app.tools.utils import normalize_domain_for_memory
            recorded = self.memory.get_detailed_findings(
                normalize_domain_for_memory(target)
            ) or []
        except Exception as exc:
            print(f"[BRAIN] Blackboard reconciliation skipped: {exc}")
            return

        confirmed = [
            row for row in recorded
            if str(row.get("data_type", "")).endswith("vulnerability")
        ]
        if not confirmed:
            return

        findings = output.get("findings")
        if not isinstance(findings, list):
            findings = []
            output["findings"] = findings

        for row in confirmed:
            evidence = self._parse_vulnerability_finding(row.get("raw_data", ""))
            payload = evidence.get("payload", "")
            endpoint = evidence.get("endpoint", "")
            tool_name = row.get("tool_name") or "unknown"
            summary = row.get("summary") or "Confirmed by tool evidence."

            # Match on the payload, which is unique per confirmation; fall back
            # to the vulnerability class so a differently-worded finding for
            # the same issue is enriched rather than duplicated.
            match = None
            for finding in findings:
                if not isinstance(finding, dict):
                    continue
                blob = " ".join(
                    str(finding.get(k, "")) for k in
                    ("issue", "description", "suggested_payload", "target")
                ).lower()
                if payload and payload.lower() in blob:
                    match = finding
                    break
                if evidence.get("kind", "").lower() in blob:
                    match = finding
                    break

            if match is None:
                # The model omitted a vulnerability a tool genuinely confirmed.
                findings.append({
                    "target": endpoint or target,
                    "issue": evidence.get("kind") or "Confirmed vulnerability",
                    "severity": row.get("severity") or "High",
                    "description": (
                        f"{summary} Recorded by {tool_name} during this run; "
                        f"omitted from the model's own report and restored "
                        f"from the Blackboard."
                    ),
                    "suggested_payload": payload,
                    "remediation": "",
                    "tool_source": tool_name,
                })
                print(f"[BRAIN] Restored dropped finding from Blackboard: "
                      f"{tool_name} -> {row.get('raw_data', '')[:120]}")
                continue

            # Fill only what the model left blank.
            if payload and not str(match.get("suggested_payload") or "").strip():
                match["suggested_payload"] = payload
            if not str(match.get("tool_source") or "").strip():
                match["tool_source"] = tool_name
            current_target = str(match.get("target") or "").strip().rstrip("/")
            if endpoint and current_target in ("", target.rstrip("/")):
                # The model names the site root; the tool knows the endpoint.
                match["target"] = endpoint
            if evidence.get("param") and "param" not in str(
                match.get("description", "")
            ).lower():
                match["description"] = (
                    f"{str(match.get('description', '')).rstrip()} "
                    f"Vulnerable parameter: `{evidence['param']}`."
                ).strip()

    def _attach_rag_sources(self, result: Dict[str, Any]) -> None:
        """Record which knowledge_base/ documents this run's RAG context
        actually pulled from, into the final report - see `__init__`'s
        `_last_rag_sources` docstring for why this didn't already exist.
        Overwrites any value the model itself produced for `sources_used`
        (per `SecurityReport.sources_used`'s own field description - this is
        Argus-tracked provenance, not something the model should invent).
        No-op if RAG retrieved nothing this run, or if `output` isn't a real
        report dict (e.g. the `no_final_answer` error path, or a raw-text
        fallback with no structure to attach metadata to).

        Args:
            result (Dict[str, Any]): The `{"output": ...}` dict to mutate
                in place.

        Returns:
            None
        """
        if not self._last_rag_sources:
            return
        output = result.get("output")
        if isinstance(output, dict) and "error" not in output:
            output["sources_used"] = list(self._last_rag_sources)

    def _process_output(self, output: Any, raw_output: str = "") -> Dict[str, Any]:
        """Coerce raw LLM output into a `{"output": ...}` dict, trying
        Pydantic parsing, then regex-extracted inline JSON, then raw text.

        Args:
            output (Any): The value to structure - already-error dicts
                pass through unchanged.
            raw_output (str): Currently unused by this method's own body -
                accepted for call-site compatibility.

        Returns:
            Dict[str, Any]: `{"output": <parsed dict or original value>}`
            - never raises; each parsing attempt's failure is logged and
            falls through to the next.
        """
        if isinstance(output, dict) and "error" in output:
            return {"output": output}

        try:
            parsed = self.output_parser.parse(str(output))
            return {"output": parsed.model_dump()}
        except Exception as e:
            print(f"[BRAIN] Pydantic parsing failed: {e}")

        try:
            output_str = str(output)
            for pattern in [r'\{[\s\S]*\}', r'\[[\s\S]*\]']:
                match = re.search(pattern, output_str)
                if match:
                    obj = json.loads(match.group(0))
                    return {"output": obj}
        except Exception:
            pass

        return {"output": output}

    def simple_ask(self, prompt):
        """Direct, single-turn LLM call bypassing the ReAct graph entirely.

        Args:
            prompt: The prompt to send directly to `self.llm.invoke()`.

        Returns:
            Dict[str, Any]: `{"output": <response text>}`, normalized to
            a plain string whether `self.llm` returns an `AIMessage`
            (ChatOllama) or a bare string.
        """
        response = self.llm.invoke(prompt)
        # self.llm is a ChatOllama (build_chat_llm()) in production, whose
        # .invoke() returns an AIMessage, not a bare string like OllamaLLM's
        # does - normalize so callers always get a plain string regardless
        # of which is injected (tests inject string-returning fakes).
        content = getattr(response, "content", response)
        return {"output": content}

    def dispatch(self, tool_name: str, **kwargs) -> Any:
        """Invoke a single registered tool directly by name, bypassing the LLM executor.

        Args:
            tool_name (str): Name of the tool to call, looked up in
                `self.tool_map`.
            **kwargs: Forwarded as keyword arguments to the tool's
                underlying `.func`.

        Returns:
            Any: Whatever the tool's `.func(**kwargs)` returns.

        Raises:
            KeyError: If `tool_name` isn't registered in `self.tool_map`.
        """
        tool = self.tool_map.get(tool_name)
        if tool is None:
            raise KeyError(f"Tool not found: {tool_name}")
        return tool.func(**kwargs)

    def get_available_tools(self):
        """Get available tools."""
        return list(self.tools)

    def get_tool_names(self):
        """Get tool names."""
        return list(self.tool_map.keys())

