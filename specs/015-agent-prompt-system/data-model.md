# Data Model: Agent Prompt System (Canonical)

**Phase**: 1 - Design | **Date**: 2026-07-06 | **Spec**: `specs/015-agent-prompt-system/spec.md`

---

## Purpose

The prompt system's "data model" is the set of inputs the builders consume (agent state), the
required prompt sections, and the final-answer contract. Derived from `app/core/agent/react_prompts.py`
(state keys), the legacy `ARGUS_AGENT_TEMPLATE`, and `app/core/schemas.py` (`SecurityReport`).

---

## Entity 1: PromptState (builder input)

Consumed by `build_react_system_prompt(state)` / `build_prebuilt_system_prompt(state)`.

| Field | Type | Source | Purpose |
|-------|------|--------|---------|
| `target` | str | agent state | Current target |
| `phase` | str | agent state | Current methodology phase |
| `iteration_count` | int | agent state | Loop counter |
| `max_iterations` | int | agent state | Loop bound (010 termination) |
| `blackboard_summary` | str | ArgusMemory | LIVE TARGET STATE |
| `tool_result` | str | last node | Last tool output |
| `tool_error` | str | last node | Last error |
| `_tools` | dict[name, fn] | tool registry | Tool map (names + docstrings) |
| `static_knowledge` | str | RAG engine | STATIC KNOWLEDGE BASE (fused; FR-008) |

**Invariant**: builders are pure functions of `PromptState` (no I/O; NFR-002).

---

## Entity 2: PromptSections (required content blocks)

The canonical prompt MUST contain these sections (merged from both sources).

| Section | Origin | Requirement |
|---------|--------|-------------|
| Role / identity | both | "Argus AI, senior penetration testing specialist" |
| Dynamic status (target/phase/iteration) | react_prompts | FR-004 |
| STATIC KNOWLEDGE BASE (RAG) | 001 fusion | FR-008 |
| LIVE TARGET STATE (Blackboard) | 001 fusion | FR-008 |
| 9-phase methodology | prompts.py | FR-002 |
| Reflective-verification mandate | prompts.py | FR-003 (ADR-6, Constitution VIII) |
| Loop-prevention rules | both | never repeat same tool+input |
| Output format (JSON preferred + text fallback) | react_prompts | FR-005 (ADR-13) |
| Available tool names (from registry) | react_prompts | FR-006 |
| Final-answer contract (SecurityReport JSON) | prompts.py | FR-007 |

---

## Entity 3: MethodologyPhase

The 9 phases preserved from `ARGUS_AGENT_TEMPLATE` (FR-002).

| # | Phase | Primary tools (from registry) |
|---|-------|-------------------------------|
| 1 | Connectivity | Check_Reachability |
| 2 | Subdomains | Subdomain_Enumeration (subfinder/assetfinder) |
| 3 | Discovery | Recon_Suite, Crawl_Target |
| 4 | Memory | Query_Memory, Query_Knowledge_Graph |
| 5 | Web Intelligence | Smart_Web_Search (CVE lookup) |
| 6 | Vulnerability Scanning | Run_Nikto |
| 7 | Exploitation | Run_FFUF, Run_Specialized_Module |
| 8 | Chaining & Escalation | combine findings -> RCE / exfil |
| 9 | Final Analysis | synthesize SecurityReport |

**Note**: tool names are illustrative and MUST be resolved from the live registry (FR-006), not
hard-coded in the prompt.

---

## Entity 4: SecurityReport (final-answer contract)

Owned by `app/core/schemas.py`. The prompt instructs the model to emit exactly this JSON (FR-007).

| Field | Type | Purpose |
|-------|------|---------|
| `summary` | str | Executive summary |
| `attack_surface_stats` | str | Discovered subdomains/services |
| `findings` | list[Finding] | target, issue, severity, description, suggested_payload, remediation |
| `overall_risk_score` | int | Aggregate risk |
| `next_steps` | list[str] | Recommended follow-ups |
| `output` | str | Full Markdown report |

---

## Entity 5: PromptVersion

| Field | Type | Purpose |
|-------|------|---------|
| `PROMPT_VERSION` | str | Version tag for the canonical prompt (FR-009) |
| `adr_ref` | str | ADR-6/13; feature 015 |

---

## Entity 6: PromptRegistry (all behavioral prompts)

The complete inventory of behavioral prompts the feature governs (FR-011..013). Each MUST live in the
canonical prompt module and be imported by its consumer.

| Prompt | Canonical name | Current inline location | Consumer | Notes |
|--------|----------------|-------------------------|----------|-------|
| Agent ReAct (text/JSON) | `build_react_system_prompt` | `app/core/agent/react_prompts.py` | `react_workflow.py`, `graph.py` | primary; enriched (FR-002/003/007) |
| Agent prebuilt (tool_calls) | `build_prebuilt_system_prompt` | `app/core/agent/react_prompts.py` | prebuilt path | native tool_calls |
| Reflective node classifier | `REFLECTIVE_NEXT_PROBE_PROMPT` | `app/core/agent/nodes/reflective.py` (inline) | Reflective node | single token: sqli / path_traversal / generic_probe (FR-011) |
| RAG query | `RAG_PROMPT` | `app/core/rag/rag_engine.py` (inline) | `RAGEngine` | answer strictly from context (FR-012) |
| RAG summarize | `RAG_PROMPT_SUMMARIZE` | `app/core/rag/rag_engine.py` (inline) | `RAGEngine` | technical summary (FR-012) |
| Legacy agent template | `ARGUS_AGENT_TEMPLATE` | `app/core/prompts.py` | `brain.py` (legacy) | Deprecated / Replaced By the above (FR-001) |

**Invariant**: no behavioral prompt text is defined inline in a consumer module; each is imported from
the canonical prompt module and carries a `PROMPT_VERSION` (FR-013).

---

## Relationships

```text
PromptRegistry --contains--> {ReAct, prebuilt, reflective, RAG query, RAG summarize} (+ legacy: deprecated)
PromptState --consumed by--> build_*_system_prompt --produces--> PromptSections
PromptSections --include--> MethodologyPhase (9) + reflective-verification + fusion(STATIC/LIVE)
model final answer --must conform to--> SecurityReport (schemas.py)
PROMPT_VERSION --tags--> the canonical prompt (AI-eval)
```

---

## Acceptance Criteria (data model)

- **AC-1**: The built prompt contains all rows of Entity 2 (SC-002).
- **AC-2**: Tool names rendered equal the registry set (SC-004, FR-006).
- **AC-3**: A model final answer parses into `SecurityReport` (SC-005, FR-007).
- **AC-4**: Builders are pure functions of `PromptState` (NFR-002).

---

## Implementation Notes

- The authoritative builders live in `app/core/agent/react_prompts.py`; this document is the
  conceptual model and is updated if the builders change.
- Fusion (`static_knowledge`, `blackboard_summary`) is assembled by the RAG/brain layer and passed
  in via `PromptState`; the prompt only formats it under the token budget.
