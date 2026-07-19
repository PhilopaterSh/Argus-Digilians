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

## Addendum: what the mock-LLM tests couldn't catch (live re-run, 2026-07-09)

Every finding below required a real Ollama server and a real target - none is reachable by
injecting a fake/mock LLM, since each is about the *plumbing* around the LLM call, not the
LLM's output content.

1. **`OllamaLLM` vs `ChatOllama`**: direct live test - `OllamaLLM(...).with_structured_output(Schema)`
   raises `NotImplementedError` immediately (LangChain's completion-style wrapper never
   implemented it); `ChatOllama(...).with_structured_output(Schema)` works. `llm_factory.py`'s
   only builder (`build_llm()`) returned `OllamaLLM` - so every `_try_structured_action`/
   `_try_structured_final_answer` call in production was silently falling through to the
   weaker regex-fallback path this whole time, undetected by mocks that don't distinguish the
   two LangChain wrapper classes.
2. **Unbounded Blackboard context**: `get_blackboard_summary()`'s SQL query had no `LIMIT` and
   no size cap - fine with an empty test DB, but after a few real scans (`data/argus_intelligence.db`
   accumulates every finding from every prior run) it produced a 6123-char JSON blob, fused with
   RAG context into a single prompt. Confirmed via live `[BRAIN] Fusion context` log line.
3. **Tool-support auto-detection**: `react_workflow.py::build_workflow()` calls
   `llm.bind_tools([])` in a try/except to decide prebuilt-vs-custom graph. `OllamaLLM.bind_tools()`
   fails (confirmed live), so all prior testing (mock LLMs also lack `bind_tools`, or raise
   `NotImplementedError` by test design) exercised only the custom graph. Switching to
   `ChatOllama` for FR-007 made `bind_tools()` succeed live, silently flipping the auto-detected
   path to the prebuilt graph - which was built for `013-langgraph-workflow` and never
   integration-tested against `ArgusBrain`'s output-parsing code.
4. **`extract_target()` ordering**: only reachable with a real Blackboard containing real prior
   findings whose domain keys are shaped like `host:port` - a mock memory in a unit test would
   need to specifically construct this shape to reproduce it (the regression test added,
   `test_ask_extracts_target_before_blackboard_enrichment_not_after`, does exactly this once the
   bug was found live, but nothing before this pointed at it).
5. **The CUDA crash**: `llama-server process has terminated: ... CUDA error`, reproduced twice
   independently of context size. Searched for the exact error signature: matches
   [ollama/ollama#16650](https://github.com/ollama/ollama/issues/16650) and related upstream
   reports, generally attributed by llama.cpp/Ollama maintainers to insufficient GPU memory
   headroom interacting with a Windows/CUDA driver bug, not an application-level bug -
   confirmed via `nvidia-smi`/`ollama show` that VRAM headroom was razor-thin (~500MB-1GB free
   on a 16GB card with the full F16 model loaded). Not fixable from `app/` code; mitigated with
   a scoped retry (see spec.md FR-011) and `OLLAMA_KV_CACHE_TYPE=q8_0`/`OLLAMA_FLASH_ATTENTION=1`
   to reduce VRAM pressure as a contributing factor.

### Follow-up research: is a lighter quantization or a different base model the better fix?

Given finding 5 is fundamentally a VRAM-headroom problem, researched whether switching away
from the F16 `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest` (~15GB) helps more directly than the
KV-cache mitigation alone:
- GGUF re-quantization quality across reputable uploaders (bartowski, mradermacher, unsloth) is
  roughly equivalent at the same quant level (~6% variance); unsloth's "Dynamic 2.0" per-layer
  quantization sometimes edges ahead, but the difference is minor for a 7B model.
- WhiteRabbitNeo itself was renamed "DeepHat" by Kindo in 2024 and is now developed as a
  proprietary product - the open `WhiteRabbitNeo-V3-7B` weights are effectively the last open
  release of this lineage; no further open-source updates should be expected under this name.
- Considered swapping the base model entirely to Qwen3-7B (cited in 2026 benchmarks as the most
  reliable small local model for native tool-calling) instead of re-quantizing WhiteRabbitNeo.
  Rejected: no mature small (7B) uncensored/pentest-tuned Qwen3 variant exists (uncensored Qwen3
  variants found are all the much larger 35B-A3B MoE model), so swapping would trade away
  WhiteRabbitNeo's cybersecurity-domain fine-tuning and compliance with the aggressive,
  security-testing-specific instructions in `app/core/prompts.py` for a general-purpose model
  likely to hedge or refuse those same instructions - the opposite of this phase's reliability
  goal. Also, per the same research, "the scaffolding around the model matters more than the
  base model itself" - and this phase's FR-007-011 fixes are exactly that scaffolding work.
- **Decision (user-confirmed)**: keep `WhiteRabbitNeo-V3-7B`, switch only the quantization to a
  lighter GGUF (Q5_K_M, ~4.8GB, ~95% of F16 quality) via `ollama pull hf.co/bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M`,
  freeing ~10GB of VRAM headroom versus the F16 original.
