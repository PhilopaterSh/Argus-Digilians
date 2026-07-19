# Research: Agent Prompt System (Canonical)

**Phase**: 0 - Technical Research | **Date**: 2026-07-06 | **Spec**: `specs/015-agent-prompt-system/spec.md`

---

## Purpose

Records the evidence and decisions for unifying the two prompt sources. All evidence is drawn from
the two real files in the repository; nothing is invented.

---

## Evidence (source of truth)

| File | Role | Strength | Gap |
|------|------|----------|-----|
| `app/core/prompts.py` (`ARGUS_AGENT_TEMPLATE`) | Legacy, used by `brain.py` | 9-phase methodology, reflective-verification mandate, verbose logging, JSON report schema, few-shot | Static; forbids JSON Action (vs ADR-13); unused `format_instructions`; no dynamic state; no RAG fusion |
| `app/core/agent/react_prompts.py` (`build_react_system_prompt` / `build_prebuilt_system_prompt`) | Canonical LangGraph path | Dynamic state (target/phase/iteration/blackboard); dual-format (JSON preferred + text); tool descriptions from docstrings; prebuilt vs custom | Thin content: 4 generic rules; missing methodology, verification, report schema |

Importers confirmed: `app/core/prompts.py` -> `app/core/agent/brain.py`,
`tests/test_registry/test_agent_factory.py`. `react_prompts.py` -> `react_workflow.py`, `graph.py`.

---

## Decision 1: Canonical module

| Option | Pros | Cons |
|--------|------|------|
| A. Make `react_prompts.py` canonical; enrich it with legacy content; deprecate `prompts.py` | Modern structure kept; rich content preserved; one source | Requires porting content + repointing `brain.py` |
| B. Keep `prompts.py` as canonical | No move | Static, legacy-bound, conflicts with ADR-13 and the LangGraph path |
| C. Keep both | No work | Perpetuates the drift `012` forbids |

**Decision**: Option A. The modern state-driven structure is the correct base; the legacy content is
the valuable payload to fold in.
*Traceability*: `spec.md` FR-001/002; `012` single-source-of-truth; ADR-14.

---

## Decision 2: Structured output policy

| Option | Pros | Cons |
|--------|------|------|
| A. JSON Action / `format=json` primary, text ReAct fallback (ADR-13) | Reliable parsing; matches canonical | - |
| B. Keep legacy "NEVER provide JSON" rule | - | Directly contradicts ADR-13 and `react_prompts.py` |

**Decision**: Option A. Remove the legacy anti-JSON instruction (`prompts.py` line ~70).
*Traceability*: `spec.md` FR-005; ADR-13.

---

## Decision 3: Reflective verification stays in the prompt

**Decision**: retain the anti-false-positive mandate (never trust status codes; cross-check
Content-Length/headers; validate content with `head`) as first-class prompt rules. This is the
prompt-level expression of ADR-6 (Reflective Verification) and Constitution VIII (Truthful Runtime -
no fabricated findings).
*Traceability*: `spec.md` FR-003; ADR-6; Constitution VIII.

---

## Decision 4: Tool names from the registry, not hard-coded

| Option | Pros | Cons |
|--------|------|------|
| A. Generate the tool list/descriptions from the live tool map (as `react_prompts.py` already does via docstrings) | No drift when tools change | - |
| B. Hard-code tool names (legacy `prompts.py`) | Simple | Drifts from the 17 registered tools (`012` 2.4) |

**Decision**: Option A.
*Traceability*: `spec.md` FR-006; `012` section 2.4.

---

## Decision 5: Context fusion + budget

**Decision**: the prompt must separate `STATIC KNOWLEDGE BASE` (RAG) from `LIVE TARGET STATE`
(Blackboard) with "trust live over static", under a context-token budget (live first, then top
similarity chunks).
*Traceability*: `spec.md` FR-008; `001` data-model (fused prompt); `012` section 4 (FR-C7).

---

## Decision 6: Versioning + evaluation

**Decision**: add a `PROMPT_VERSION` constant and an ADR reference; cover the prompt with AI-eval
(final answer conforms to `SecurityReport`; agent loop terminates within `max_iterations`).
*Traceability*: `spec.md` FR-009; `012` section 6.

---

## Alternatives rejected

- **Rewriting the prompt from scratch** - rejected; the legacy content encodes hard-won pentest
  methodology and the modern file encodes the right structure. Merge beats rewrite.

---

## Decision Traceability Summary

| Decision | Spec ref | Source / ADR |
|----------|----------|--------------|
| 1 Canonical module | FR-001/002 | 012, ADR-14 |
| 2 Structured output | FR-005 | ADR-13 |
| 3 Reflective verification | FR-003 | ADR-6, Constitution VIII |
| 4 Registry-sourced tools | FR-006 | 012 s2.4 |
| 5 Context fusion + budget | FR-008 | 001, 012 s4 |
| 6 Versioning + eval | FR-009 | 012 s6 |

---

## Open Questions

None blocking. Behavioral changes require `pytest` + AI-eval in a runtime with dependencies.
