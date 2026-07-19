# Quickstart: LangGraph Workflow + JSON Parser + Config-Driven Port

**Phase**: 1 - Validation | **Date**: 2026-07-05 | **Spec**: `specs/013-langgraph-workflow/spec.md`

> **Status**: Partially Superseded By `010-langgraph-agent` + `012-spec-reconciliation`. This
> quickstart validates the as-built workflow. For the canonical agent, see `010`; for the canonical
> port and structured-output parsing, see `012` (ADR-13/16).

---

## Purpose

How to validate the LangGraph workflow, the dual-format parser, and the config-driven port. Derived
from `spec.md` (Success Criteria SC-001..004, User Stories), `tasks.md` T017-T032, and the tests in
`tests/test_langgraph_workflow.py`.

## Prerequisites

- Python 3.12 (canonical per `012` section 2.6) with dependencies from `Setup/requirements.txt`
  (includes `langgraph>=0.2.0`).
- Ollama running locally for the integration checks (`spec.md` Assumptions).
- Run from the project root.

---

## Check 1: Hybrid agent routing

```bash
pytest tests/test_langgraph_workflow.py -q
```

**Expected**: unit tests pass (tool-map building, target extraction, full cycle
scan -> search -> report, max-iteration stop, unknown tool, immediate Final Answer, empty response,
JSON format, JSON variants, malformed-JSON fallback) - 10 unit tests (`spec.md` SC-001; `tasks.md`
T017-T026).

---

## Check 2: JSON Action parsing

Feed the parser `Action: {"name": "mock_scan", "input": "https://test.com"}`.

**Expected**: `tool_name = mock_scan`, `tool_input = https://test.com`; alternative keys
(`action`/`tool`, `arguments`/`arg`) are also accepted; malformed JSON falls back to text ReAct
(`spec.md` FR-006..008, US2).

---

## Check 3: --graph CLI flag

```bash
python scripts/run_argus_cli.py --graph
```

**Expected**: the LangGraph workflow is invoked via `brain.graph_ask()` (`spec.md` FR-012, SC-003;
`tasks.md` T010-T011).

---

## Check 4: Config-driven port

```bash
python scripts/get_port.py
```

**Expected**: prints the canonical port **12199**; if `config.yaml` is missing/unreadable it prints
the fail-safe default 12199 (`012` section 2.6, ADR-16; `spec.md` NFR-004 as refined). Changing
`streamlit.port` in `config.yaml` and restarting a launcher starts Streamlit on the new port
(`spec.md` US3, SC-004).

---

## Check 5: Integration (requires Ollama)

```bash
python workspace/test_full_integration.py
```

**Expected**: prebuilt mode with a tool-calling model, auto-detection, tool-map building, target
extraction, and `brain.graph_ask()` all succeed (`spec.md` SC-002; `tasks.md` T027-T031).

---

## Validation checklist

| Check | Expected | Source |
|-------|----------|--------|
| Unit tests | 10 pass | SC-001 |
| JSON parser | extracts tool/input, falls back safely | FR-006..008 |
| --graph flag | invokes LangGraph | FR-012, SC-003 |
| Port | 12199 everywhere | ADR-16, SC-004 |
| Integration | prebuilt + auto-detect pass | SC-002 |

---

## Troubleshooting

- **Invalid format error loops**: the parser returns a format error for one retry; if it recurs, the
  brain falls back to the SimpleChain path (`spec.md` FR-009; architecture section 6.1).
- **Port conflict**: change `streamlit.port` in `config.yaml`; all launchers read it via
  `get_port.py` (`spec.md` US3).
- **Migrating off this feature**: per `012`, prefer the canonical agent (`010`, `app/core/agent/`)
  and structured `format=json` decoding; this workflow is retained for compatibility only.
