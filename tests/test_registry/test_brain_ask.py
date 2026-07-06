"""Unit tests for ArgusBrain.ask() using an injected fake LLM.

Exercises the SimpleChain (ReAct AgentExecutor) path and RAG/Blackboard
context fusion end-to-end without needing a live Ollama server, matching
the `llm=` injection seam added to ArgusBrain.__init__ for testability.
"""
from unittest.mock import MagicMock

from langchain_core.language_models.fake import FakeListLLM
from langchain_core.tools import Tool

from app.core.agent.brain import ArgusBrain

FULL_REPORT_JSON = (
    '{"summary": "ok", "attack_surface_stats": "none", "findings": [], '
    '"overall_risk_score": 1, "next_steps": [], "output": "done"}'
)


def _make_tool():
    return Tool(name="fake", description="A fake tool", func=lambda x="": f"executed:{x}")


def test_ask_returns_parsed_output_via_simple_chain():
    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    result = brain.ask("scan example.com")

    assert "output" in result
    assert result["output"]["summary"] == "ok"


def test_ask_falls_back_to_raw_output_on_unparseable_final_answer():
    llm = FakeListLLM(responses=["Final Answer: not json at all"])
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    result = brain.ask("scan example.com")

    assert "output" in result
    assert "not json at all" in str(result["output"])


def test_ask_enriches_query_with_blackboard_context():
    memory = MagicMock()
    memory.get_blackboard_summary.return_value = '{"target": "example.com"}'
    memory.get_graph_insights.return_value = ""

    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, memory=memory, llm=llm)

    enriched = brain._enrich_with_rag("scan example.com")

    assert "LIVE TARGET STATE" in enriched
    assert "example.com" in enriched


def test_ask_without_memory_or_rag_passes_query_through():
    llm = FakeListLLM(responses=[f"Final Answer: {FULL_REPORT_JSON}"])
    brain = ArgusBrain("test-model", [_make_tool()], rag_config={"enabled": False}, llm=llm)

    assert brain._enrich_with_rag("plain query") == "plain query"


def test_simple_ask_uses_injected_llm_directly():
    llm = FakeListLLM(responses=["direct response"])
    brain = ArgusBrain("test-model", [], rag_config={"enabled": False}, llm=llm)

    result = brain.simple_ask("hello")

    assert result["output"] == "direct response"
