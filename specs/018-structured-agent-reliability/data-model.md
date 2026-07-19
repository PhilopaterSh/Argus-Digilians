# Data Model: Structured-Output Reliability for ArgusBrain's ReAct Loop

Retrospective documentation (2026-07-18) of the real data contract FR-002 introduced: the
agent's final answer is now extracted via `llm.with_structured_output(SecurityReport)` instead
of free-text parsing. Both models already exist in `app/core/schemas.py`; this file documents
them as the structured-output contract, it does not define new schema.

## `SecurityReport` (`app/core/schemas.py`)

The structured target for `_try_structured_final_answer()`. Fields:

| Field | Type | Notes |
|---|---|---|
| `summary` | `str` | Executive summary of the security posture |
| `attack_surface_stats` | `str` | Summary of discovered subdomains/services |
| `findings` | `List[Finding]` | See `Finding` below |
| `overall_risk_score` | `int` (1-10) | Bounded via Pydantic `ge=1, le=10` |
| `next_steps` | `List[str]` | Recommended follow-up actions |
| `scan_mode` | `Optional[str]` | Defaults to `"passive"` |
| `scan_target` | `Optional[str]` | Primary scan target |
| `output` | `Optional[str]` | Full Markdown report body |
| `sources_used` | `List[str]` | RAG document filenames actually fused into context - populated by `app/core/agent/brain.py::_attach_rag_sources` after generation, not model-authored (any value the model fills in here is overwritten) |

## `Finding` (`app/core/schemas.py`)

One entry in `SecurityReport.findings`:

| Field | Type | Notes |
|---|---|---|
| `target` | `str` | Subdomain/IP under analysis |
| `issue` | `str` | The identified security issue |
| `severity` | `str` | `Low` / `Medium` / `High` / `Critical` |
| `description` | `str` | Technical explanation |
| `suggested_payload` | `Optional[str]` | Sample test payload/methodology |
| `remediation` | `str` | Fix instructions |
| `tool_source` | `Optional[str]` | Which tool produced this finding |

## Failure contract (FR-006)

If the graph never reaches a valid Final Answer within `max_iterations` (15, per NFR-001), no
`SecurityReport` is fabricated - `ArgusBrain.ask()` returns an honest
`no_final_answer`/`graph_execution_failed` error state instead (Constitution VIII - Truthful
Runtime). This is a contract property, not a separate schema: absence of a valid
`SecurityReport` is itself meaningful state, not an edge case papered over with a default value.
