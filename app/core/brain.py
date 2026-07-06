from langchain_core.output_parsers import PydanticOutputParser
from app.core.schemas import SecurityReport
from app.core.llm_factory import build_llm
from app.core.prompts import get_argus_prompt
from app.core.rag import RAGEngine, RAGConfig
from app.core.memory.memory_service import ArgusMemory
from app.core.agent_factory import build_agent_executor
import json
import os
import re
from typing import Dict, Any, Optional, List

# Ordered, deterministic recon phases. These run directly in Python -
# the LLM never chooses which tool fires next, so there is no ReAct
# format for a weak local model to get wrong. Each tool is called with
# the raw target string, matching the "Action Input is the raw value
# only" convention already used elsewhere in this project. Tools that
# depend on earlier discoveries (Smart_Web_Search needs a detected
# tech/version, Run_Specialized_Module needs an exact filename) are
# intentionally left out of this fixed sequence - they still make sense
# as manual/agentic follow-ups later, once you have a model that can
# reliably decide when to use them.
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

Fill in ACTUAL VALUES for each of these six fields (this is not a schema,
just the field names - replace the < > with your own real analysis):

{{
  "summary": <one paragraph, your own words, about this specific target's security posture>,
  "attack_surface_stats": <one sentence describing what was actually discovered - ports, subdomains, tech>,
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


class ArgusBrain:
    """
    Enhanced brain with deterministic tool orchestration + RAG + Blackboard
    context fusion.

    Tool selection is no longer delegated to the LLM. WhiteRabbitNeo-7B
    reliably fails to follow ReAct's Thought/Action/Action Input format -
    even after being told exactly what it did wrong, it reproduces the
    same incorrect output verbatim. Rather than keep patching prompts
    around that ceiling, `ask()` now runs a fixed recon pipeline in plain
    Python and calls the LLM exactly once, to synthesize a report from
    real tool output. The old agent-based path is kept as `ask_agentic()`
    for use with a stronger/tool-calling-capable model later.
    """

    def __init__(self, model_name, tools_list, rag_config: Optional[dict] = None, memory: Optional[ArgusMemory] = None):
        self.llm = build_llm(model_name)
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

        # Lazy load executors (kept for ask_agentic / future stronger models)
        self._react_agent = None
        self._simple_chain = None
        self.use_react = False

        print(f"[BRAIN] Using deterministic tool pipeline for model: {model_name}")

    def _get_react_agent(self):
        if self._react_agent is not None:
            return self._react_agent

        try:
            format_instructions = self.output_parser.get_format_instructions()
            prompt = get_argus_prompt(format_instructions)
            self._react_agent = build_agent_executor(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            return self._react_agent
        except Exception as e:
            print(f"[BRAIN] Failed to load ReAct agent: {e}")
            return None

    def _get_simple_chain(self):
        if self._simple_chain is not None:
            return self._simple_chain

        try:
            self._simple_chain = build_agent_executor(
                llm=self.llm,
                tools=self.tools,
                prompt=get_argus_prompt(self.output_parser.get_format_instructions()),
                verbose=False
            )
            return self._simple_chain
        except Exception as e:
            print(f"[BRAIN] Failed to load Simple Chain: {e}")
            return None

    @staticmethod
    def _load_rag_config() -> Optional[Dict[str, Any]]:
        try:
            import yaml
            config_path = os.getenv("ARGUS_CONFIG", "config.yaml")
            if os.path.exists(config_path):
                with open(config_path) as f:
                    cfg = yaml.safe_load(f)
                return cfg.get("rag")
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
        self._refresh_blackboard()

    def _enrich_with_rag(self, query: str) -> str:
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

    _URL_RE = re.compile(r"https?://[^\s'\"]+", re.IGNORECASE)
    _DOMAIN_RE = re.compile(
        r"\b(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.){1,}"
        r"[a-zA-Z]{2,24}\b"
    )

    def _extract_target(self, query: str) -> str:
        """
        The GUI sends a full instruction paragraph ("CONSULT MEMORY FIRST
        using 'Query_Memory'. Then perform a comprehensive security
        analysis for http://example.com/. ..."), written for the old
        LLM-driven agent that could parse instructions itself. The
        deterministic pipeline hands its target straight to tools like
        Check_Reachability, so it needs the actual URL/domain pulled out
        first - otherwise every tool gets the whole sentence as its input.
        """
        query = query.strip()

        url_match = self._URL_RE.search(query)
        if url_match:
            # Strip trailing sentence punctuation the regex can't tell
            # apart from a real URL path/query character (e.g. the
            # period ending "...for http://example.com/. If findings...")
            return url_match.group(0).rstrip(".,;:!?)\"'")

        domain_match = self._DOMAIN_RE.search(query)
        if domain_match:
            bare_domain = domain_match.group(0).rstrip(".,;:!?)\"'")
            # Web-facing tools (Recon_Suite, Run_Nikto, Run_FFUF, ...) were
            # exercised with a scheme-prefixed URL and expect one. A bare
            # domain match had no scheme in the original text at all, so
            # add one rather than silently handing tools something they
            # weren't tested against.
            return f"http://{bare_domain}"

        # No URL/domain found anywhere in the text - this is a real
        # problem, not something to silently paper over.
        print(
            f"[BRAIN] WARNING: could not find a URL or domain inside the "
            f"input text: {query[:200]!r}. Passing it through as-is, but "
            f"tool results are likely to be meaningless."
        )
        return query

    # Tools that shell out to something like `ping <target>` need a bare
    # hostname - they don't parse URLs themselves. Add tool names here as
    # you discover more of them behaving the same way (check the tool's
    # own source/log output: if it prints back exactly what you gave it
    # instead of a stripped hostname, it needs to be in this set).
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

    def run_deterministic_recon(
        self,
        target: str,
        on_phase: Optional[Any] = None,
    ) -> Dict[str, str]:
        """
        Executes DETERMINISTIC_PHASES in fixed order via direct Python
        calls - no LLM involved in choosing or sequencing tools. Returns
        {tool_name: raw_observation} for every phase that ran.

        on_phase: optional callable(phase_index, total_phases, tool_name,
        observation) invoked immediately after each phase finishes, so a
        caller (e.g. the Streamlit GUI) can render live progress instead
        of waiting for the whole pipeline to finish.
        """
        observations: Dict[str, str] = {}
        total = len(DETERMINISTIC_PHASES)
        for i, tool_name in enumerate(DETERMINISTIC_PHASES, start=1):
            print(f"[BRAIN] Running phase: {tool_name}({target})")
            observation = self._run_tool_safely(tool_name, target)
            observations[tool_name] = observation

            if self.memory is not None:
                try:
                    self.memory.add_finding(
                        domain=target,
                        tool_name=tool_name,
                        data_type="recon",
                        raw_data=observation,
                        summary=observation[:500],
                    )
                except Exception as e:
                    print(f"[BRAIN] Could not persist finding for {tool_name}: {e}")

            if on_phase is not None:
                try:
                    on_phase(i, total, tool_name, observation)
                except Exception as e:
                    print(f"[BRAIN] on_phase callback raised (ignored): {e}")

        return observations

    def ask(self, target: str, callbacks=None, on_phase: Optional[Any] = None) -> Dict[str, Any]:
        """
        Default entrypoint. Runs the fixed recon pipeline directly, then
        makes exactly one LLM call to synthesize the results into a
        SecurityReport. No agent loop, no ReAct parsing, nothing for a
        weak local model to get stuck repeating.

        `target` may arrive as a bare URL, or as a full instruction
        paragraph from the GUI - _extract_target() pulls the actual
        URL/domain out either way before any tool is called.

        `on_phase`: optional callable(index, total, tool_name, observation)
        - see run_deterministic_recon(). Pass this from the GUI to show
        live per-phase progress instead of only the final report.
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
            except Exception as e:
                return {
                    "output": {
                        "error": "synthesis_llm_failed",
                        "message": str(e),
                        "raw_tool_observations": observations,
                    }
                }

            last_raw_response = raw_response
            processed = self._process_output(raw_response, str(raw_response))
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

        # Exhausted retries without a usable report - fail loudly instead
        # of silently shipping the schema dict as if it were a real report.
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

    @staticmethod
    def _looks_like_schema_echo(output: Any) -> bool:
        """
        Detects the model copying the JSON Schema / field-instructions
        text back verbatim instead of producing filled-in report data -
        e.g. a dict with '$defs'/'properties'/'required' keys, or missing
        the 'summary' field a real SecurityReport always has.
        """
        if not isinstance(output, dict):
            return False
        if any(k in output for k in ("$defs", "properties", "required")):
            return True
        if "summary" not in output:
            return True
        return False

    def ask_agentic(self, query: str, callbacks=None) -> Dict[str, Any]:
        """
        The old ReAct-agent-driven path. Kept for future use with a
        model that actually follows tool-calling formats reliably -
        WhiteRabbitNeo-7B does not (it reproduces the same malformed
        output even after being told exactly what it did wrong), so this
        is no longer the default.
        """
        self._refresh_blackboard()
        augmented_query = self._enrich_with_rag(query)

        if self.use_react:
            try:
                react_agent = self._get_react_agent()
                if react_agent:
                    print("[BRAIN] Attempting ReAct agent...")
                    result = react_agent.invoke(
                        {"input": augmented_query},
                        config={"callbacks": callbacks}
                    )

                    if isinstance(result, dict):
                        output = result.get("output", result)

                        if isinstance(output, dict) and "error" in output:
                            error_msg = str(output.get("message", ""))
                            if "Invalid Format" in error_msg or "Missing 'Action:'" in error_msg or "parsing_error" in output.get("error", ""):
                                print(f"[BRAIN] ReAct format error detected: {error_msg}")
                                self.use_react = False
                                return self._ask_simple_chain(augmented_query, callbacks)

                        return self._process_output(output, str(result))

            except Exception as e:
                error_msg = str(e)
                if "Invalid Format" in error_msg or "Missing 'Action:'" in error_msg:
                    print(f"[BRAIN] ReAct format error exception: {error_msg}")
                    self.use_react = False
                    return self._ask_simple_chain(augmented_query, callbacks)
                print(f"[BRAIN] ReAct attempt failed: {error_msg}")

        print("[BRAIN] Using Simple Chain as primary or fallback executor...")
        return self._ask_simple_chain(augmented_query, callbacks)

    MIN_ACTIONS_BEFORE_ACCEPT = 3
    MAX_SHORTCUT_RETRIES = 2

    def _ask_simple_chain(self, query: str, callbacks=None, _retry: int = 0) -> Dict[str, Any]:
        try:
            simple_chain = self._get_simple_chain()
            if not simple_chain:
                return {
                    "output": {
                        "error": "executor_unavailable",
                        "message": "Neither ReAct nor Simple Chain could be initialized. Check logs."
                    }
                }

            print("[BRAIN] Using Simple Chain executor...")
            result = simple_chain.invoke(
                {"input": query},
                config={"callbacks": callbacks} if callbacks else {}
            )

            steps_taken = len(result.get("intermediate_steps", []))
            print(f"[BRAIN] Agent executed {steps_taken} real tool action(s) before finishing.")

            if steps_taken < self.MIN_ACTIONS_BEFORE_ACCEPT and _retry < self.MAX_SHORTCUT_RETRIES:
                print(
                    f"[BRAIN] Rejecting shortcut answer - only {steps_taken} tool "
                    f"call(s) happened (need {self.MIN_ACTIONS_BEFORE_ACCEPT}). "
                    f"Retrying with a stronger instruction ({_retry + 1}/{self.MAX_SHORTCUT_RETRIES})..."
                )
                nudge = (
                    f"\n\nSTOP. Your previous attempt tried to finish after only "
                    f"{steps_taken} real tool call(s). That is not acceptable - you "
                    f"skipped the recon phases. You MUST call Check_Reachability, "
                    f"then at least two more tools (e.g. Subdomain_Enumeration, "
                    f"Recon_Suite, Crawl_Target, Run_Nikto) and use their real "
                    f"Observations before you are allowed to write a Final Answer."
                )
                return self._ask_simple_chain(query + nudge, callbacks, _retry=_retry + 1)

            if steps_taken < self.MIN_ACTIONS_BEFORE_ACCEPT:
                print(
                    "[BRAIN] Model still won't use tools after retries - "
                    "returning result but flagging it as unverified."
                )

            processed = self._process_output(result.get("output", result), str(result))
            if isinstance(processed.get("output"), dict) and steps_taken < self.MIN_ACTIONS_BEFORE_ACCEPT:
                processed["output"]["_warning"] = (
                    f"Only {steps_taken} tool call(s) were executed - this report "
                    f"may not reflect real reconnaissance and should be verified manually."
                )
            return processed

        except Exception as e:
            return {
                "output": {
                    "error": "simple_chain_failed",
                    "message": str(e)
                }
            }

    def _process_output(self, output: Any, raw_output: str = "") -> Dict[str, Any]:
        if isinstance(output, dict) and "error" in output:
            return {"output": output}

        try:
            parsed = self.output_parser.parse(str(output))
            return {"output": parsed.dict()}
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
        response = self.llm.invoke(prompt)
        return {"output": response}