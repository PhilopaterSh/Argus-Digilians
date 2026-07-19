# Implementation Plan: Spec Consolidation & Architecture Reconciliation

**Feature ID**: `012-spec-reconciliation` | **Date**: 2026-07-05 | **Spec**: `specs/012-spec-reconciliation/spec.md`

**Status**: Active — Canonical

---

## Summary

Documentation-level consolidation of specs `001`–`011`/`013` into one coherent design. No code changes. This plan records the canonical decisions, the supersession map, and the sequence of documentation edits applied.

---

## Technical Context

**Scope**: Spec-Kit artifacts only (specs, plans, tasks, contracts, ADRs, architecture doc).
**Constitution Check**: PASS — this effort is documentation hygiene; principles I–VI are unaffected except that it *improves* VI (English-only) and observability/testing coverage. No Complexity-Tracking violations.

---

## Canonical Source-of-Truth Map

| Subsystem | Canonical owner spec | Canonical design authority |
|---|---|---|
| Cross-cutting naming, ports, python, testing, CI/CD | `012` (this) | `012` §2/§6/§7 |
| RAG embedding + index integrity | `012` §3 | `012` §3 (supersedes `001` FR-005..007, `004` FR-002) |
| RAG modules + chunking | `001` (foundation) + `004` (hardening) | canonical names in `012` §2.1 |
| Agent topology (node graph) | `010-langgraph-agent` | `012` §4 |
| Agent mechanisms (parser, hooks, port, capability probe) | `013-langgraph-workflow` (retained parts) | `012` §2.2/§5 |
| Brain + Agent-Factory (single) | `012` §2.2 | supersedes `brain_v2`/`agent_factory_v2` |
| Memory / Blackboard | `003-sqlite-blackboard` | unchanged |
| Tool registry | `005-tool-registry` | count corrected to 17 in `012` §2.4 |
| Reflective verification | `007` | unchanged |
| Self-healing | `008` | unchanged |
| Primary GUI | `011-gui-enhancement` | `012` §2.5 (Tkinter `009` = optional fallback) |
| Installer | `002-consolidated-installer` | unchanged (best-in-class) |

## Supersession Map (applied)

| Spec | New status | Marker |
|---|---|---|
| `001-rag-integration` | Implemented — **Refined By** `012` §3 (embedding) | header added |
| `004-rag-pipeline` | Draft — **Refined By** `012` §3 (embedding/integrity) | header added |
| `013-langgraph-workflow` | Implemented — **Partially Superseded By** `010` + `012` | header added; folder renamed from `003` |
| `005-tool-registry` | Implemented — Input note updated (`brain_v2` now consolidated per `012` §2.2) | note added |
| `009-gui` | Implemented — **Superseded (primary UI) By** `011`; Tkinter retained as fallback | note added |
| `010-langgraph-agent` | Draft — **Canonical agent**; module names aligned to `012` §2.1 | header + name fixes |

## Commit Strategy

Per constitution / AGENTS.md: one commit per consolidation phase (below).

## Phases

| Phase | Description | Status |
|---|---|---|
| 0 | Renumber duplicate `003` → `013`; fix self-refs | ✅ Done |
| 1 | Author `012` canonical spec/plan/tasks | ✅ Done |
| 2 | Add supersession/refined headers to `001`, `004`, `005`, `009`, `010`, `013` | ✅ Done |
| 3 | Apply embedding-manifest design to `001`, `004`, `010` | ✅ Done |
| 4 | Align `010` module names + chunking to canonical | ✅ Done |
| 5 | Update architecture doc: ADRs, ports, python, single brain, manifest, tool count | ✅ Done |
| 6 | (Future) wire the §7 CI/CD plan into an actual pipeline | ⏳ Pending |
| 7 | (Future) implement `010` against this reconciled design | ⏳ Pending |

## Risks & Mitigations

- **Risk**: Historical "Completed" specs (`001`,`013`) now describe partly-superseded code. **Mitigation**: headers state exactly what is retained vs superseded; code is not rewritten by this effort.
- **Risk**: Arabic `converge.md` files violate English-only (constitution VI). **Mitigation**: flagged in Remaining Issues; not rewritten here to avoid destroying convergence history — scheduled as a follow-up doc task.
