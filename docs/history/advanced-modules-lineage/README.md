# Advanced Modules Lineage (archived)

The five files under `core/` arrived in `main` with the release/unified
reconciliation merge (2026-10-30), where they lived at the repository root as
`_experimental_advanced_modules/core/`. They are an unwired, untested,
shorter-lineage sibling of the shipped `app/modules/experimental_agent/`
package: same five component names, different code (see the comparison below),
with zero references from `app/`, `scripts/`, or `tests/`.

Archived on 2026-10-30 per Constitution IX (one copy per responsibility) and
Principle III (all code lives under `app/`); the location also contradicted the
layout validated by the structure graph (Constitution XII).

| File | This lineage (lines) | app/modules/experimental_agent/ (lines) |
|---|---|---|
| agent.py | 1586 | 1787 |
| verifier.py | 334 | 384 |
| llm_engine.py | 560 | 639 |
| agent_payload_decider.py | present | 578 |
| payload_encoder.py | present | 442 |

Provenance: the pre-reorganization "Original" experimental codebase era
documented in the project-evolution history; the evolved descendant ships
opt-in under `app/modules/experimental_agent/`.
