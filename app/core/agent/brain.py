from langchain_core.messages import HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from app.core.schemas import SecurityReport
from app.core.llm_factory import build_chat_llm
from app.core.rag import RAGEngine, RAGConfig
from app.core.memory.memory_service import ArgusMemory
import json
import os
import re
from typing import Dict, Any, Optional

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

    def ask(self, query: str, callbacks=None) -> Dict[str, Any]:
        from app.core.agent.react_workflow import extract_target

        # Extracted from the RAW query, before enrichment - see
        # _run_structured_graph()'s docstring for why order matters here.
        target = extract_target(query)
        self._refresh_blackboard()
        augmented_query = self._enrich_with_rag(query, callbacks)
        return self._run_structured_graph(augmented_query, target, callbacks)

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
        from app.core.agent.react_workflow import _build_custom_workflow

        # specs/019-shared-memory-reflection-upgrade FR-006/NFR-002: read the
        # escape hatch from config at graph-build time, not hardcoded, so an
        # operator can disable the 3x majority-vote check if it measurably
        # pushes a run past max_iterations' time budget in practice.
        try:
            from app.core.config import ArgusConfig
            enable_inter_reflection = ArgusConfig.load().enable_inter_reflection
        except Exception:
            enable_inter_reflection = True

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
            graph = _build_custom_workflow(
                self.llm, self.tools, self.memory,
                enable_inter_reflection=enable_inter_reflection,
            )
            initial_state = {
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
        return list(self.tools)

    def get_tool_names(self):
        return list(self.tool_map.keys())

