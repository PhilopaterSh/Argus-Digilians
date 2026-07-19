# Feature Specification: Agent Prompt System (Canonical)

**Feature ID**: `015-agent-prompt-system`

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-07-06

**Status**: Draft

**Input**: Consolidate the two competing agent-prompt sources into one governed, versioned, canonical
prompt system. Preserve the rich penetration-testing methodology currently trapped in the legacy
`app/core/prompts.py` (`ARGUS_AGENT_TEMPLATE`) and fold it into the modern, state-driven builders in
`app/core/agent/react_prompts.py`, aligned with the canonical decisions in `012-spec-reconciliation`
and the ADRs.

---

## Why this feature

The repository currently has **two active prompt sources**, each holding half of the solution:

- `app/core/prompts.py` (`ARGUS_AGENT_TEMPLATE`, `get_argus_prompt`) - used by `app/core/agent/brain.py`.
  **Rich content**: 9-phase methodology, reflective-verification mandate (anti-false-positive),
  verbose technical logging, and a structured JSON final-report schema. **But**: a static string,
  tied to the legacy AgentExecutor path, forbids JSON Action input (conflicts with ADR-13), passes an
  unused `format_instructions` partial, and has no dynamic state or RAG-context integration.
- `app/core/agent/react_prompts.py` (`build_react_system_prompt`, `build_prebuilt_system_prompt`) -
  used by the canonical LangGraph path (`react_workflow.py`, `graph.py`). **Modern structure**:
  dynamic state injection (target, phase, iteration, blackboard), dual-format output (JSON preferred +
  text fallback), tool descriptions generated from docstrings. **But**: thin domain content (four
  generic rules); the methodology, reflective verification, and report schema are missing.

This violates the single-source-of-truth principle (`012`). This feature makes
`app/core/agent/react_prompts.py` the **one canonical prompt module**, enriched with the legacy
domain knowledge, and deprecates `app/core/prompts.py`.

---

## User Scenarios & Testing

### User Story 1 - One canonical prompt source (Priority: P1)

As a developer, I want a single prompt module so agent behavior is defined in one governed place.

**Acceptance Scenarios**:
1. **Given** the agent runs, **When** it builds a system prompt, **Then** it uses
   `app/core/agent/react_prompts.py` only; `app/core/prompts.py` is a deprecation shim.
2. **Given** `app/core/prompts.py` is imported, **When** loaded, **Then** it emits a
   `DeprecationWarning` pointing at the canonical module.

### User Story 2 - Preserved methodology and verification (Priority: P1)

As a security operator, I want the canonical prompt to retain the 9-phase methodology and the
reflective-verification mandate, so autonomous runs keep their anti-false-positive discipline.

**Acceptance Scenarios**:
1. **Given** the built prompt, **When** inspected, **Then** it contains the phase methodology
   (Connectivity -> Subdomains -> Discovery -> Memory -> Web Intelligence -> Vuln Scan -> Exploitation
   -> Chaining -> Final Analysis).
2. **Given** a candidate finding, **When** the prompt guides the model, **Then** it mandates a
   cross-check (Content-Length / header / `head` first-lines) before recording it (ADR-6;
   Constitution VIII - Truthful Runtime).

### User Story 3 - Structured, versioned, evaluable (Priority: P2)

As a maintainer, I want the prompt to be versioned and covered by AI-evaluation, because it is a
critical behavioral artifact.

**Acceptance Scenarios**:
1. **Given** the prompt module, **When** inspected, **Then** it carries a `PROMPT_VERSION` constant
   and an ADR reference.
2. **Given** the AI-eval suite, **When** run, **Then** it asserts the final answer conforms to the
   `SecurityReport` JSON schema (`012` section 6).

### Edge Cases

- Non-tool-calling model (WhiteRabbitNeo) -> text/JSON ReAct via `build_react_system_prompt`.
- Tool-calling model (Llama 3.1) -> native tool_calls via `build_prebuilt_system_prompt`.
- Fused context exceeds the model window -> apply the context-token budget (live state first, then
  highest-similarity RAG chunks) - `012` section 4 (FR-C7).

---

## Requirements

### Functional Requirements

- **FR-001**: `app/core/agent/react_prompts.py` MUST be the single canonical prompt module;
  `app/core/prompts.py` MUST become a deprecation shim (re-export + `DeprecationWarning`).
- **FR-002**: The canonical prompt MUST preserve the 9-phase methodology from `ARGUS_AGENT_TEMPLATE`.
- **FR-003**: The canonical prompt MUST include the reflective-verification mandate (never trust
  status codes; cross-check Content-Length/headers; validate content with `head`) - ADR-6,
  Constitution VIII.
- **FR-004**: The prompt MUST inject dynamic state (target, phase, iteration, max_iterations,
  blackboard_summary, last tool_result/tool_error) - as already done in `react_prompts.py`.
- **FR-005**: The prompt MUST use structured output as the primary path (JSON Action / `format=json`),
  with the text ReAct format as fallback - ADR-13. The legacy "NEVER provide JSON" instruction MUST
  be removed.
- **FR-006**: Tool names in the prompt MUST be sourced from the live tool registry / tool map, not
  hard-coded (canonical count 17; `012` section 2.4).
- **FR-007**: The final-answer contract MUST be the `SecurityReport` schema (`app/core/schemas.py`):
  summary, attack_surface_stats, findings[], overall_risk_score, next_steps, output.
- **FR-008**: The fused prompt MUST separate `STATIC KNOWLEDGE BASE` (RAG) from `LIVE TARGET STATE`
  (Blackboard) with the priority rule "trust live over static" (`001` data-model), under a
  context-token budget (`012` section 4).
- **FR-009**: The prompt module MUST carry a `PROMPT_VERSION` and be covered by AI-evaluation
  (`012` section 6).
- **FR-010**: The unused `format_instructions` partial in the legacy template MUST be removed during
  deprecation.

#### Prompt Registry scope (all behavioral prompts)

This feature governs EVERY behavioral prompt in the codebase, not only the main agent prompt. The
canonical home is a single prompt package (`app/core/agent/react_prompts.py`, or a dedicated
`app/core/agent/prompts/` package if it grows); each prompt below MUST be defined there and imported
by its consumer, so no behavioral prompt text lives inline elsewhere.

- **FR-011**: The Reflective node prompt (currently the inline `system_instruction` +
  `user_prompt` in `app/core/agent/nodes/reflective.py`) MUST be defined in the canonical prompt
  module and imported by the node. It stays a constrained single-token classifier (output exactly one
  of `sqli` / `path_traversal` / `generic_probe`), carrying its own `PROMPT_VERSION` entry.
- **FR-012**: The RAG prompts (`RAG_PROMPT`, `RAG_PROMPT_SUMMARIZE` currently inline in
  `app/core/rag/rag_engine.py`) MUST be registered in the canonical prompt module and imported by
  `rag_engine.py`. `RAG_PROMPT` MUST keep the "answer strictly from context; say so if insufficient"
  guardrail (anti-hallucination; Constitution VIII).
- **FR-013**: A single Prompt Registry MUST enumerate all behavioral prompts (agent ReAct,
  prebuilt, reflective-node, RAG query, RAG summarize) with a name, version, and consumer, so the set
  is discoverable and evaluable in one place (`012` single-source-of-truth).

### Non-Functional Requirements

- **NFR-001**: All prompt text MUST be ASCII/English-only (Constitution VI).
- **NFR-002**: Building a prompt MUST be a pure function of state (no I/O), so it is unit-testable
  without Ollama.

### Key Entities

- `app/core/agent/react_prompts.py` - canonical builders (enriched).
- `app/core/prompts.py` - deprecation shim (Replaced By the above).
- `app/core/schemas.py` - `SecurityReport` (the final-answer contract).

---

## Success Criteria

- **SC-001**: Exactly one prompt module is used by the agent; the legacy module only warns (US1).
- **SC-002**: The built prompt contains the 9-phase methodology and the reflective-verification
  mandate (US2, FR-002/003).
- **SC-003**: Structured output is primary; no "NEVER provide JSON" instruction remains (FR-005).
- **SC-004**: Tool names in the prompt equal the registered tool set (FR-006).
- **SC-005**: The final answer validates against `SecurityReport` (FR-007), asserted by AI-eval.
- **SC-006**: `PROMPT_VERSION` present; prompt builders are pure and unit-tested (FR-009, NFR-002).

---

## Assumptions

- The canonical model default is `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest` (`012` section 2.6).
- `SecurityReport` in `app/core/schemas.py` is the report contract (already present).
- Behavioral changes to prompt text require `pytest` + AI-eval validation in a runtime with the
  dependencies (out of scope for the documentation of this spec).
