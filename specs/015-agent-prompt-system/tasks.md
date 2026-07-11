# Tasks: Agent Prompt System (Canonical)

**Input**: `specs/015-agent-prompt-system/spec.md`, `plan.md`

**Note**: prompt text is a behavioral artifact. Content changes MUST be validated with `pytest`
(pure-builder unit tests) and AI-eval before the legacy path is deprecated. Those steps need the
runtime (langchain / Ollama), unavailable in the spec-authoring environment.

---

## Phase 0: Inventory

- [x] T001 Inventory both prompt sources and importers (`prompts.py` -> `brain.py`; `react_prompts.py` -> `react_workflow.py`, `graph.py`). Recorded in `research.md`.

## Phase 1: Port rich content into the canonical builder

- [ ] T002 Add the 9-phase methodology block to `build_react_system_prompt` (FR-002).
- [ ] T003 Add the reflective-verification mandate (never trust status codes; cross-check Content-Length/headers; validate with `head`) (FR-003; ADR-6; Constitution VIII).
- [ ] T004 Add the `SecurityReport` JSON final-answer contract to the prompt (FR-007).

## Phase 2: Align with ADR-13 and the registry

- [ ] T005 Remove any anti-JSON instruction; keep JSON Action primary, text ReAct fallback (FR-005).
- [ ] T006 Source tool names/descriptions from the live tool map (already the pattern); ensure no hard-coded tool lists remain (FR-006).

## Phase 3: Context fusion + budget

- [ ] T007 Add `STATIC KNOWLEDGE BASE` (RAG) / `LIVE TARGET STATE` (Blackboard) sections with "trust live over static" (FR-008; `001`).
- [ ] T008 Apply a context-token budget (live first, then top-similarity chunks) (`012` section 4, FR-C7).

## Phase 4: Versioning + tests

- [ ] T009 Add `PROMPT_VERSION` + ADR reference constant (FR-009).
- [ ] T010 Add `tests/test_agent/test_react_prompts.py`: required sections present, registry tool names rendered, builder purity (NFR-002). Marker `unit`.

## Phase 5: Deprecate the legacy module

- [ ] T011 Convert `app/core/prompts.py` to a deprecation shim (re-export via the canonical builder + `DeprecationWarning`); remove the unused `format_instructions` partial (FR-001, FR-010).
- [ ] T012 Repoint `app/core/agent/brain.py` and `tests/test_registry/test_agent_factory.py` to the canonical builder; run `pytest -q` (MUST be green).

## Phase 6: Evaluation

- [ ] T013 Add an AI-eval case: a full run's final answer validates against `SecurityReport`, and the loop terminates within `max_iterations` (`012` section 6). Requires Ollama.

## Phase 7: Prompt Registry (centralize all behavioral prompts)

- [ ] T014 Move the Reflective node prompt (inline `system_instruction`/`user_prompt` in `app/core/agent/nodes/reflective.py`) into the canonical prompt module as `REFLECTIVE_NEXT_PROBE_PROMPT`; import it in the node. Keep the single-token contract (sqli / path_traversal / generic_probe) (FR-011).
- [ ] T015 Move `RAG_PROMPT` and `RAG_PROMPT_SUMMARIZE` (inline in `app/core/rag/rag_engine.py`) into the canonical prompt module; import them in `RAGEngine`. Keep the "answer strictly from context" guardrail (FR-012).
- [ ] T016 Add a `PROMPT_REGISTRY` mapping (name -> {version, builder/template, consumer}) enumerating all behavioral prompts; add a unit test asserting every registered prompt is importable and versioned (FR-013).
- [ ] T017 Extend the AI-eval / doc-validation to fail if a new inline behavioral prompt is added outside the canonical module (guards against future drift).

## Dependencies & Execution Order

1. T001 (done)
2. T002 -> T003 -> T004 (content)
3. T005 -> T006 (ADR-13 + registry)
4. T007 -> T008 (fusion + budget)
5. T009 -> T010 (version + unit tests)
6. T011 -> T012 (deprecate + repoint; pytest green)
7. T013 (AI-eval; Ollama)

## Blockers

- T002-T013 modify prompt behavior and MUST be validated with `pytest` (T010/T012) and AI-eval (T013)
  in a runtime with langchain + Ollama - unavailable in the spec-authoring environment. The
  specification (this artifact set) is complete and requires no external input.
