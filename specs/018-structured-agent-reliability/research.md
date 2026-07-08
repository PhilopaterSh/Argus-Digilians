# Research: Reliable Tool-Choosing Loops for Smaller Local LLMs

**Feature**: `018-structured-agent-reliability`
**Date**: 2026-07-08

## Question

Given a real production failure (WhiteRabbitNeo-V3-7B repeating identical malformed, non-ReAct
output on every retry until a 900s timeout), what is the best available fix for making a
tool-choosing LLM loop reliable with a smaller local model?

## Findings

### 1. Ollama structured outputs (schema-constrained decoding)

Ollama has supported structured outputs since v0.3.0: passing a JSON schema to the `format`
field constrains the model's *token sampling itself*, not just its prompt instructions. Per
Ollama's own documentation and independent write-ups:
- "Since Ollama 0.3.0, passing a JSON schema to the format parameter eliminates parsing
  problems at the root, as the model's inference itself is constrained by the schema, resulting
  in no code fences, no explanatory text, no mid-thought artifacts - just parseable JSON."
- Measured roughly 6x faster with near-100% parse success versus prompting for JSON and hoping.
- Caveat for small/quantized models: deeply nested schemas (3+ levels) can degrade reliability -
  keep response schemas flat. `_ArgusAction`/`SecurityReport` are both flat-ish (SecurityReport
  has one list-of-objects level, which is within the safe range per this guidance).

Sources:
- [Structured outputs · Ollama Blog](https://ollama.com/blog/structured-outputs)
- [Structured Outputs - Ollama docs](https://docs.ollama.com/capabilities/structured-outputs)
- [Ollama Structured Outputs in Practice — Pydantic guide](https://jangwook.net/en/blog/en/ollama-structured-outputs-pydantic-local-llm-guide-2026/)
- [Reliable Structured Output from Local LLMs](https://markaicode.com/ollama-structured-output-pipeline/)

### 2. LangChain/LangGraph free-text ReAct parsing is a known unreliable pattern for local models

LangChain's own community discussions repeatedly document "Could not parse LLM output" /
"Invalid Format" failures specifically with local/smaller models, with the consistent
root-cause diagnosis: *"local LLMs typically don't consistently produce properly formatted
outputs, so retry mechanisms and format-fixing parsers are the recommended best practice."*
Recommended mitigations in order of robustness: (a) constrain output format at generation time
(structured/JSON mode - see #1), (b) `OutputFixingParser`/`RetryWithErrorOutputParser` wrapping
a base parser to re-prompt on failure, (c) `handle_parsing_errors=True` on `AgentExecutor` (what
this codebase already had) - the weakest option, since it only feeds the error back as an
observation and hopes the model self-corrects, with no guarantee it ever will.

Sources:
- [LangChain: handle_parsing_errors docs](https://python.langchain.com/v0.1/docs/modules/agents/how_to/handle_parsing_errors/)
- [GitHub Discussion #22614: intermittent "Could not parse LLM output"](https://github.com/langchain-ai/langchain/discussions/22614)
- [GitHub Discussion #20688: "Could not parse LLM output" with Llama 3](https://github.com/langchain-ai/langchain/discussions/20688)

### 3. LangGraph's own recommended reliability pattern matches this repo's existing (unused) implementation

LangGraph documentation/write-ups on structured output and self-correcting agents describe
exactly the pattern already implemented in `app/core/agent/react_workflow.py`: a `StateGraph`
with an agent node that attempts structured/schema-validated output first, a parse/validation
node, and a conditional edge that either proceeds, retries with the error fed back, or ends -
with an explicit iteration/step cap so a still-failing model produces a clean error rather than
looping or crashing.

Sources:
- [LangGraph Structured Output & Self-Correcting Agents](https://machinelearningplus.com/gen-ai/langgraph-structured-output-validation-self-correcting/)
- [LangGraph Error Handling: Retries & Fallback Strategies](https://machinelearningplus.com/gen-ai/langgraph-error-handling-retries-fallback-strategies/)

## In-repo discovery (more directly actionable than any external source)

Grepping this codebase turned up that the *exact* recommended technique (#1 + #3 combined) was
already implemented and unit-tested here, just not wired to production:

- `app/core/agent/react_workflow.py::_try_structured_action()` - `llm.with_structured_output(_ArgusAction)`
  first, text-regex fallback second. Built for `013-langgraph-workflow` specifically because
  "WhiteRabbitNeo has format issues with ReAct" (its own comments/commit history say so).
- `app/core/agent/brain.py::ArgusBrain`'s docstring already *claimed* an equivalent fallback
  ("automatically falls back to a simpler sequential execution model") but the code never
  implemented it - `_get_react_agent()`/`_get_simple_chain()` both built the identical
  `agent_factory.py::build_agent_executor()` (classic free-text `AgentExecutor`), differing only
  in a `verbose` flag. This was a **pre-existing latent bug**, invisible until `017` made
  `ArgusBrain` the production driver and a real run exposed it.
- A second, independent bug found while reading `react_workflow.py` to reuse it:
  `route_after_parse()`'s `format_error` branch routed back to `"agent"` with **no
  `max_iterations` check**, unlike the tool-execution path 8 lines below it. A model that never
  once produces valid output (this exact incident) would have looped there unbounded except by
  LangGraph's default `recursion_limit` (25), raising an ungraceful `GraphRecursionError`
  instead of a clean, honest result. Fixed as part of this phase - see `spec.md` FR-005.

## Decision

Reuse `react_workflow.py`'s custom graph as `ArgusBrain`'s internal executor (Option: reuse
existing, well-tested in-repo code) rather than either (a) patching `agent_factory.py`'s
`AgentExecutor` to add retry/format-fixing wrappers from scratch, or (b) switching to a
different agent framework entirely. This is the same "check for an existing implementation
before writing new code" principle Constitution IX already establishes, applied to a
reliability fix instead of a duplication fix.
