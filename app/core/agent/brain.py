from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from app.core.schemas import SecurityReport
from app.core.llm_factory import build_chat_llm
from app.core.rag import RAGEngine, RAGConfig
from app.core.memory.memory_service import ArgusMemory
import json
import os
import re
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
]

# Chaining limits - kept small since each extra call is a real network
# operation (and each subdomain re-check multiplies runtime).
MAX_CHAINED_SUBDOMAINS = 2
MAX_CHAINED_PATHS = 3
_INTERESTING_PATH_KEYWORDS = (
    "login", "admin", "register", "search", "upload",
    "config", "backup", "account", "user",
)
_TECH_BLOCK_RE = re.compile(r"Tech:\s*(.+?)(?:\nPorts:|\Z)", re.DOTALL)

# WhatWeb-style "Tech:" lines are noisy (cookies, IP, page title, country)
# alongside the actually useful tech identifiers. Searching the whole raw
# line returns nothing because it's not a real query anyone would write -
# these keys get dropped before building a Smart_Web_Search query.
_TECH_NOISE_KEYS = {"Cookies", "Country", "IP", "Title"}
_TECH_TOKEN_RE = re.compile(r"[A-Za-z][\w\-\.]*(?:\[[^\]]*\])?")

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
        try:
            from app.core.config import ArgusConfig
            cfg = ArgusConfig.load()
            return cfg.to_rag_dict() if cfg.rag.enabled else None
        except Exception:
            pass
        return None

    def _refresh_blackboard(self):
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
        Runs the fixed recon pipeline directly, then makes exactly one LLM call
        to synthesize the results into a SecurityReport.
        """
        self._refresh_blackboard()
        clean_target = self._extract_target(target)
        if clean_target != target.strip():
            print(f"[BRAIN] Extracted target '{clean_target}' from input text.")
        observations = self.run_deterministic_recon(clean_target, on_phase=on_phase)

        tool_observations = "\n\n".join(
            f"--- {name} ---\n{obs}" for name, obs in observations.items()
        )

        prompt_text = SYNTHESIS_PROMPT_TEMPLATE.format(
            target=clean_target,
            blackboard_context=self._blackboard_context or "(none)",
            tool_observations=tool_observations or "(no tools returned data)",
        )

        MAX_SYNTHESIS_RETRIES = 2
        last_raw_response = None
        for attempt in range(MAX_SYNTHESIS_RETRIES + 1):
            try:
                raw_response = self.llm.invoke(prompt_text)
                response_content = getattr(raw_response, "content", raw_response)
            except Exception as e:
                return {
                    "output": {
                        "error": "synthesis_llm_failed",
                        "message": str(e),
                        "raw_tool_observations": observations,
                    }
                }

            last_raw_response = response_content
            processed = self._process_output(response_content, str(response_content))
            output = processed.get("output")

            if self._looks_like_schema_echo(output):
                print(
                    f"[BRAIN] Synthesis attempt {attempt + 1} echoed the JSON "
                    f"schema/instructions instead of writing a real report."
                )
                if attempt < MAX_SYNTHESIS_RETRIES:
                    prompt_text += (
                        "\n\nSTOP. Your previous answer repeated the field "
                        "names / schema definition instead of writing real "
                        "values. Do not include the words '$defs', "
                        "'properties', or 'required'. Replace every field "
                        "with an actual sentence or number based on the "
                        "RAW TOOL OUTPUT above."
                    )
                    continue

            if isinstance(output, dict):
                output["_raw_tool_observations"] = observations
            return processed

        return {
            "output": {
                "error": "synthesis_echoed_schema",
                "message": (
                    "The model repeated the JSON schema/instructions "
                    f"{MAX_SYNTHESIS_RETRIES + 1} times instead of writing "
                    "an actual report. Raw tool data is included below so "
                    "nothing is lost."
                ),
                "raw_llm_response": str(last_raw_response),
                "raw_tool_observations": observations,
            }
        }

    _BARE_HOSTNAME_TOOLS = {"Check_Reachability"}

    @staticmethod
    def _to_bare_hostname(target: str) -> str:
        """
        http://testasp.vulnweb.com/some/path?x=1  ->  testasp.vulnweb.com
        testasp.vulnweb.com                        ->  testasp.vulnweb.com
        """
        from urllib.parse import urlparse

        parsed = urlparse(target if "://" in target else f"http://{target}")
        host = parsed.hostname or target
        return host

    _COMMAND_NOT_FOUND_RE = re.compile(r"(\S+):\s*command not found")
    _SELF_HEAL_TOOL_NAME = "System_Self_Heal"

    def _invoke(self, tool, arg: str) -> str:
        if hasattr(tool, "run"):
            return str(tool.run(arg))
        return str(tool.invoke(arg))

    def _try_self_heal(self, tool_name: str, observation: str) -> bool:
        """
        If `observation` contains one or more "X: command not found"
        errors, ask System_Self_Heal (if registered) to install each
        missing binary. Returns True if at least one heal attempt ran
        without raising, so the caller knows a retry is worth trying.
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
        """Persist a single knowledge-graph edge during recon so that
        Query_Knowledge_Graph has real data to return. No-op (and never
        fatal) when memory is disabled or a write fails.

        entity: (entity_type, entity_value) for the new node this edge
        introduces - always equal to whichever of source_val/target_val
        isn't the already-registered graph root, so it's bundled here
        rather than passed as two more separate positional strings.
        """
        entity_type, entity_value = entity
        if self.memory is None:
            return
        value = (entity_value or "").strip()
        if not value:
            return
        try:
            self.memory.upsert_entity(entity_type, value)
            self.memory.add_relation(source_val, target_val, rel_type)
        except Exception as e:
            print(f"[BRAIN] graph edge write skipped ({rel_type}): {e}")

    def _run_tool_safely(self, tool_name: str, target: str) -> str:
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
        """Pulls plausible hostnames out of Subdomain_Enumeration's raw
        (possibly fenced) line-per-subdomain output, excluding the root
        host we already scanned and de-duping while preserving order."""
        candidates = []
        for line in observation.splitlines():
            line = line.strip().strip("`")
            if not line or " " in line or "/" in line or "." not in line:
                continue
            if line == exclude_hostname:
                continue
            candidates.append(line)
        seen = set()
        out = []
        for c in candidates:
            if c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def _parse_tech(self, observation: str) -> str:
        """Pulls the raw 'Tech: ...' line out of Recon_Suite's output.
        This is the noisy WhatWeb-style line (cookies, IP, title and all) -
        use _clean_tech_string() before using it as a search query."""
        match = _TECH_BLOCK_RE.search(observation)
        if not match:
            return ""
        return match.group(1).strip()[:500]

    def _clean_tech_string(self, raw_tech: str) -> str:
        """
        Strips a WhatWeb-style tech line down to just the useful
        identifiers. Raw input looks like:
          "http://x.com/ [200 OK] ASP_NET, Cookies[...], Country[US],
           HTTPServer[Microsoft-IIS/8.5], IP[1.2.3.4], Title[...], ..."
        Searching that whole line returns nothing - no one has ever
        written that as a search query. This keeps only tokens whose key
        isn't in _TECH_NOISE_KEYS, and prefers the bracket VALUE (e.g.
        "Microsoft-IIS/8.5") over the raw token when there is one.
        """
        if not raw_tech:
            return ""
        text = raw_tech
        if "] " in text:
            # drop the "http://.../ [200 OK] " prefix if present
            text = text.split("] ", 1)[1]

        values = []
        for tok in _TECH_TOKEN_RE.findall(text):
            if "[" in tok:
                key, _, rest = tok.partition("[")
                if key in _TECH_NOISE_KEYS:
                    continue
                value = rest.rstrip("]").strip()
                values.append(value if value else key)
            elif tok not in _TECH_NOISE_KEYS and not re.fullmatch(r"[A-Z]{1,3}", tok):
                # Skip short all-caps remnants like a leftover "US" from
                # "Country[UNITED STATES][US]" - a stray bracket fragment,
                # not a real technology token.
                values.append(tok)

        deduped = list(dict.fromkeys(values))
        cleaned = " ".join(deduped)
        return cleaned[:200] if cleaned else raw_tech[:200]

    def _parse_interesting_paths(self, observation: str) -> List[str]:
        """Pulls endpoints matching common sensitive-path keywords out of
        Crawl_Target's 'Top findings:' list."""
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

        on_phase: optional callable(phase_index, total_phases, tool_name,
        observation) invoked immediately after each phase finishes.
        """
        observations: Dict[str, str] = {}
        counter = {"i": 0, "total": len(DETERMINISTIC_PHASES)}

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

        for tool_name in DETERMINISTIC_PHASES:
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
        """Extract and structure the graph's Final Answer, if it reached one."""
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
        return result

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
        """
        if not self._last_rag_sources:
            return
        output = result.get("output")
        if isinstance(output, dict) and "error" not in output:
            output["sources_used"] = list(self._last_rag_sources)

    def _process_output(self, output: Any, raw_output: str = "") -> Dict[str, Any]:
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
        """Direct, single-turn LLM call bypassing the ReAct graph entirely."""
        response = self.llm.invoke(prompt)
        # self.llm is a ChatOllama (build_chat_llm()) in production, whose
        # .invoke() returns an AIMessage, not a bare string like OllamaLLM's
        # does - normalize so callers always get a plain string regardless
        # of which is injected (tests inject string-returning fakes).
        content = getattr(response, "content", response)
        return {"output": content}

    def dispatch(self, tool_name: str, **kwargs) -> Any:
        """Invoke a single registered tool directly by name, bypassing the LLM executor."""
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

