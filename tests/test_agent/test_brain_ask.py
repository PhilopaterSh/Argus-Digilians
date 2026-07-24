"""Unit tests for ArgusBrain.ask() using an injected fake LLM.

Exercises the structured-output ReAct graph (specs/018-structured-agent-
reliability, app/core/agent/react_workflow.py's custom graph) and
RAG/Blackboard context fusion end-to-end without needing a live Ollama
server, matching the `llm=` injection seam added to ArgusBrain.__init__ for
testability.
"""
from unittest.mock import MagicMock

from langchain_core.language_models.fake import FakeListLLM
from langchain_core.messages import AIMessage
from langchain_core.tools import Tool

from app.core.agent.brain import ArgusBrain

FULL_REPORT_JSON = (
    '{"summary": "ok", "attack_surface_stats": "none", "findings": [], '
    '"overall_risk_score": 1, "next_steps": [], "output": "done"}'
)


def _make_tool():
    """Make tool."""
    return Tool(name="fake", description="A fake tool", func=lambda x="": f"executed:{x}")


class _RepeatingMalformedLLM:
    """Reproduces the live specs/018 failure: same non-ReAct output every call.

    A real production run against a real target timed out after 900s because
    WhiteRabbitNeo-V3-7B repeated an identical malformed context dump on
    every retry, never once producing a valid Thought/Action/Final Answer -
    see specs/018-structured-agent-reliability/spec.md for the full incident.
    """

    def __init__(self, content="```json\n{\"raw\": \"context dump, no Thought/Action\"}"):
        """Store the fixed malformed content every invoke() call will return.

        Args:
            content (str): The fixed non-ReAct content to always return.
        """
        self._content = content
        self.call_count = 0

    def invoke(self, messages, **kwargs):
        """Always return the same malformed AIMessage, counting calls.

        Args:
            messages: Unused - accepted for LLM-interface compatibility.
            **kwargs: Unused - accepted for LLM-interface compatibility.

        Returns:
            AIMessage: `self._content`, unchanged every call.
        """
        self.call_count += 1
        return AIMessage(content=self._content)

    def bind_tools(self, tools):
        """Bind tools."""
        raise NotImplementedError("force the custom (non-prebuilt) graph mode")


def test_ask_returns_parsed_output_via_structured_graph():
    """Verify Ask returns parsed output via structured graph."""
    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    result = brain.ask("scan example.com")

    assert "output" in result
    assert result["output"]["summary"] == "ok"


def test_ask_terminates_within_max_iterations_on_repeated_malformed_output():
    """specs/018 regression test: reproduces the exact live failure.

    Before the fix, this LLM would have made ArgusBrain hang until the
    outer process-level timeout (900s in scripts/run_agent.py) killed it,
    with zero results. It must now stop within max_iterations and report
    an honest "no final answer" error - never a fabricated report.
    """
    llm = _RepeatingMalformedLLM()
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    result = brain.ask("perform a comprehensive security analysis for https://example.com/")

    assert llm.call_count <= brain.max_iterations + 1
    assert "error" in result["output"]
    assert result["output"]["error"] in {"no_final_answer", "graph_execution_failed"}


def test_ask_streams_live_feed_events_via_on_graph_event():
    """Verify Ask streams live feed events via on graph event."""
    responses = [
        'Thought: checking.\nAction: {"name": "fake", "input": "x"}',
        f'Thought: done.\nFinal Answer: {FULL_REPORT_JSON}',
    ]

    class _ScriptedLLM:
        def __init__(self):
            """Init  ."""
            self.i = 0

        def invoke(self, messages, **kwargs):
            """Return the next scripted response, clamping at the last one once exhausted.

            Args:
                messages: Unused - accepted for LLM-interface compatibility.
                **kwargs: Unused - accepted for LLM-interface compatibility.

            Returns:
                AIMessage: The next entry in `responses`.
            """
            r = responses[min(self.i, len(responses) - 1)]
            self.i += 1
            return AIMessage(content=r)

        def bind_tools(self, tools):
            """Bind tools."""
            raise NotImplementedError

    class _RecordingCallback:
        def __init__(self):
            """Init  ."""
            self.events = []

        def on_graph_event(self, status, detail):
            """On graph event."""
            self.events.append((status, detail))

    cb = _RecordingCallback()
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=_ScriptedLLM())

    result = brain.ask("scan example.com", callbacks=[cb])

    assert result["output"]["summary"] == "ok"
    assert any(status == "running" for status, _ in cb.events)
    assert any(status == "completed" and "Observation:" in detail for status, detail in cb.events)


class _FakeRagEngine:
    """Returns a fixed, `[Source: ...]`-tagged string, matching what
    format_combined_context() actually produces - avoids needing a real
    FAISS index/embedding backend to test source-attribution capture."""

    def __init__(self, combined_text):
        """Init  ."""
        self._combined_text = combined_text

    def format_combined_context(self, query, blackboard_context=""):
        """Format combined context."""
        return self._combined_text


def _make_brain_with_fake_rag(llm, combined_text):
    """ArgusBrain has no constructor seam for injecting a fake RAG engine
    (unlike `llm=`) - built with RAG disabled, then rag_enabled/_rag_engine
    are set directly, matching test_rag_engine_threshold.py's established
    pattern of swapping `engine.vector_store` post-construction.

    Args:
        llm: The (fake) LLM to inject into ArgusBrain.
        combined_text (str): Fixed text the fake RAG engine's
            `format_combined_context()` will return.

    Returns:
        ArgusBrain: With RAG force-enabled and `_rag_engine` swapped to
        a `_FakeRagEngine(combined_text)`.
    """
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)
    brain.rag_enabled = True
    brain._rag_engine = _FakeRagEngine(combined_text)
    return brain


def test_ask_attaches_rag_sources_actually_used_to_the_final_report():
    """RAG source attribution (2026-07-10): a source-attribution UI existed
    once (app/core/rag/rag_gui.py, commit 8e16cd4) but only on a side branch
    that was never merged - RAGResult.sources existed in rag_engine.py but
    was never threaded through to any user-facing output in mainline."""
    combined = (
        "===== STATIC KNOWLEDGE BASE =====\n"
        "[Source: argus_security_knowledge.md]\nsome static knowledge chunk\n\n---\n\n"
        "[Source: payloads_cheatsheet.md]\nanother chunk"
    )
    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = _make_brain_with_fake_rag(llm, combined)

    result = brain.ask("scan example.com")

    assert result["output"]["sources_used"] == [
        "argus_security_knowledge.md",
        "payloads_cheatsheet.md",
    ]


def test_ask_dedupes_repeated_sources_preserving_order():
    """Verify Ask dedupes repeated sources preserving order."""
    combined = (
        "[Source: a.md]\nchunk1\n\n---\n\n"
        "[Source: b.md]\nchunk2\n\n---\n\n"
        "[Source: a.md]\nchunk3"
    )
    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = _make_brain_with_fake_rag(llm, combined)

    result = brain.ask("scan example.com")

    assert result["output"]["sources_used"] == ["a.md", "b.md"]


def test_ask_omits_sources_used_when_rag_retrieved_nothing():
    """Verify Ask omits sources used when rag retrieved nothing."""
    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    result = brain.ask("scan example.com")

    # sources_used defaults to [] on the schema itself (not omitted), but
    # _attach_rag_sources must not have overwritten it with anything when
    # RAG contributed nothing this run.
    assert result["output"]["sources_used"] == []


def test_ask_streams_rag_source_retrieval_as_a_reflection_event():
    """Verify Ask streams rag source retrieval as a reflection event."""
    combined = "[Source: argus_security_knowledge.md]\nsome chunk"
    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = _make_brain_with_fake_rag(llm, combined)

    class _RecordingCallback:
        def __init__(self):
            """Init  ."""
            self.events = []

        def on_graph_event(self, status, detail):
            """On graph event."""
            self.events.append((status, detail))

    cb = _RecordingCallback()
    brain.ask("scan example.com", callbacks=[cb])

    source_events = [d for s, d in cb.events if "retrieved knowledge base sources" in d]
    assert len(source_events) == 1
    assert "argus_security_knowledge.md" in source_events[0]


def test_ask_falls_back_to_raw_output_on_unparseable_final_answer():
    """Verify Ask falls back to raw output on unparseable final answer."""
    llm = FakeListLLM(responses=["Final Answer: not json at all"])
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    result = brain.ask("scan example.com")

    assert "output" in result
    assert "not json at all" in str(result["output"])


def test_ask_enriches_query_with_blackboard_context():
    """Verify Ask enriches query with blackboard context."""
    memory = MagicMock()
    memory.get_blackboard_summary.return_value = '{"target": "example.com"}'
    memory.get_graph_insights.return_value = ""

    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, memory=memory, llm=llm)

    enriched = brain._enrich_with_rag("scan example.com")

    assert "LIVE TARGET STATE" in enriched
    assert "example.com" in enriched


def test_ask_without_memory_or_rag_passes_query_through():
    """Verify Ask without memory or rag passes query through."""
    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    assert brain._enrich_with_rag("plain query") == "plain query"


def test_simple_ask_uses_injected_llm_directly():
    """Verify Simple ask uses injected llm directly."""
    llm = FakeListLLM(responses=["direct response"])
    brain = ArgusBrain("test-model", [], rag_config={"enabled": False}, llm=llm)

    result = brain.simple_ask("hello")

    assert result["output"] == "direct response"


def test_ask_extracts_target_before_blackboard_enrichment_not_after():
    """specs/018 regression test: a live run passed a corrupted "target"
    (a JSON key like `www.example.com:80":`, complete with stray quote/
    colon) to every tool call, because the target was extracted from the
    RAG/Blackboard-enriched query - which prepends the Blackboard JSON
    block (containing exactly the kind of dot-separated, space-free token
    extract_target() searches for) BEFORE the actual "Question: ..." text.
    The real target must come from the raw, pre-enrichment query.

    Returns:
        None
    """
    memory = MagicMock()
    memory.get_blackboard_summary.return_value = '{"www.example.com:80": {"vulnerability": "x"}}'
    memory.get_graph_insights.return_value = ""

    captured = {}

    def fake_tool(x=""):
        """Record the tool-call input it received.

        Args:
            x (str): The tool-call input.

        Returns:
            str: A fixed "ok" string.
        """
        captured["input"] = x
        return "ok"

    llm = FakeListLLM(responses=[
        'Thought: check it.\nAction: {"name": "fake", "input": ""}',
        f'Thought: done.\nFinal Answer: {FULL_REPORT_JSON}',
    ])
    brain = ArgusBrain(
        "test-model",
        [Tool(name="fake", description="A fake tool", func=fake_tool)],
        rag_config={"enabled": False}, memory=memory, llm=llm,
    )

    brain.ask("Perform a comprehensive security analysis for https://real-target.com/")

    # An empty Action Input falls back to state["target"] (execute_node) -
    # this must be the real target, never the Blackboard JSON key.
    assert captured["input"] == "https://real-target.com/"


class _CrashOnceThenSucceedLLM:
    """Simulates the real live crash (specs/018): Ollama's llama-server
    subprocess terminating outright with a CUDA error - a known,
    intermittent Windows/CUDA driver bug (matches upstream ollama/ollama
    GitHub issues), reproduced twice during live testing independent of
    context size. The server reloads the model fresh on the next request,
    so one retry is a reasonable, pragmatic mitigation."""

    def __init__(self):
        """Init  ."""
        self.call_count = 0

    def invoke(self, messages, **kwargs):
        """Raise the transient CUDA-crash signature on the first call, then succeed.

        Args:
            messages: Unused - accepted for LLM-interface compatibility.
            **kwargs: Unused - accepted for LLM-interface compatibility.

        Returns:
            AIMessage: A Final Answer message, on the second and later calls.

        Raises:
            RuntimeError: On the first call only (the transient-infra
                crash signature `_run_structured_graph` retries on).
        """
        self.call_count += 1
        if self.call_count == 1:
            raise RuntimeError(
                "llama-server process has terminated: exit status 0xc0000409: "
                "The system detected an overrun of a stack-based buffer...: CUDA error"
            )
        return AIMessage(content=f"Thought: done.\nFinal Answer: {FULL_REPORT_JSON}")

    def bind_tools(self, tools):
        """Bind tools."""
        raise NotImplementedError


def test_ask_retries_once_on_transient_ollama_cuda_crash():
    """Verify Ask retries once on transient ollama cuda crash."""
    llm = _CrashOnceThenSucceedLLM()
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    result = brain.ask("scan example.com")

    assert llm.call_count == 2
    assert result["output"]["summary"] == "ok"


class _PersistentErrorLLM:
    def __init__(self):
        """Init  ."""
        self.call_count = 0

    def invoke(self, messages, **kwargs):
        """Always raise a persistent (non-transient) error.

        Args:
            messages: Unused - accepted for LLM-interface compatibility.
            **kwargs: Unused - accepted for LLM-interface compatibility.

        Raises:
            ValueError: Every call - not the transient-infra signature,
                so `_run_structured_graph` must not retry this.
        """
        self.call_count += 1
        raise ValueError("some unrelated persistent bug")

    def bind_tools(self, tools):
        """Bind tools."""
        raise NotImplementedError


def test_ask_does_not_retry_non_infra_errors():
    """Only the specific known transient Ollama/CUDA crash signature should
    trigger a retry - an unrelated persistent error must fail immediately,
    not be silently masked behind a retry."""
    llm = _PersistentErrorLLM()
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    result = brain.ask("scan example.com")

    assert llm.call_count == 1
    assert result["output"]["error"] == "graph_execution_failed"
