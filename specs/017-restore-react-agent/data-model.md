# Data Model: Restore ArgusBrain as Production Driver

Retrospective documentation (2026-07-18) of the real contract change FR-004/FR-005 introduced:
the persisted agent-run result shape. `SecurityReport` itself is documented in full in
`specs/018-structured-agent-reliability/data-model.md` (the feature that made its extraction
reliable); this file documents only what changed as a result of 017's reconnection.

## Persisted result shape: before -> after

| Before (`build_tactical_graph()` era) | After (`ArgusBrain.ask()`, this feature) |
|---|---|
| `open_ports`, `vulnerabilities`, `exploit_success` (flat, pipeline-specific fields) | Real `SecurityReport` shape: `summary`, `attack_surface_stats`, `findings`, `overall_risk_score`, `next_steps`, `output` (see `018/data-model.md` for the full field list) |

`app/GUI/tabs/agent.py`'s Final Results section (CHK067) reads the new shape directly - it no
longer needs to reconstruct a report-like view from the old pipeline's narrower fields.

## Failure contract (FR-005)

If `ArgusBrain.ask()`'s output isn't a valid structured report, the persisted state must say so
explicitly via a `parse_warning` field rather than fabricating empty-looking structured fields
(Constitution VIII - Truthful Runtime). This is the same principle
`018-structured-agent-reliability` later hardened with actual structured-output extraction
(`with_structured_output`) instead of free-text parsing - 017 established the *contract*
(never fabricate), 018 made the *extraction* reliable enough to honor it consistently.
