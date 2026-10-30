# Tasks: Human-in-the-Loop Escalation on Detected Stuck Loops

**Feature**: `027-human-in-the-loop-escalation`

**Status**: Proposed — no tasks started.

- [ ] T000 (gate) Verify LangGraph's `interrupt()`/`Command(resume=...)`/checkpointer API
  against the actually-installed version in `Argus_venv` (`pip show langgraph`) - record the
  exact call shapes here before writing code against possibly-stale documentation, matching this
  project's established "verify before implementing" discipline
- [ ] T001 `_detect_stuck_pattern()` — `app/core/agent/react_workflow.py` (pure function, unit
  tested standalone before wiring into `execute_node`)
- [ ] T002 Wire `_detect_stuck_pattern()` + `interrupt()` into `execute_node`, gated on
  `enable_hitl_escalation`; add a `MemorySaver` checkpointer to `_build_custom_workflow`'s
  `StateGraph.compile()` (NFR-003)
- [ ] T003 `HITLEscalationSettings` dataclass + `enable_hitl_escalation` flag —
  `config.yaml`, `app/core/config.py`
- [ ] T004 `brain.py::_run_structured_graph`'s bounded-wait-then-`Command(resume=...)` loop
  around an `interrupt()` stream event, with FR-005's timeout-to-empty-hint fallback
- [ ] T005 `on_needs_input` callback — `app/core/agent/react_callback.py` (mirrors
  `on_graph_event`'s existing thin-wrapper pattern)
- [ ] T006 `"needs_input"` status + hint-input UI + `pending_resume` state-file field —
  `app/GUI/tabs/agent.py`/`AgentController`
- [ ] T007 Unit tests for `_detect_stuck_pattern()` (both trigger conditions, negative case) —
  `tests/test_langgraph_workflow.py`
- [ ] T008 SC-001 test: non-repetitive-but-non-converging mock scenario reaches `interrupt()`
  before `max_iterations`
- [ ] T009 SC-002 test: supplied hint resumes and appears in the next prompt's reflection notes
- [ ] T010 SC-003 test: no hint supplied -> auto-resume within the configured timeout
- [ ] T011 SC-004 (safety-critical): a real `scripts/run_argus_cli.py` invocation hitting T008's
  same stuck pattern completes with zero observable behavior change from today - run live, not
  just mocked, before this feature is considered for anything beyond
  `enable_hitl_escalation: false`
- [ ] T012 `CHANGELOG.md` entry + `specs/checklist.md` CHK series +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row, once implemented

## Explicitly out of scope (see spec.md)

- Approval-gate-before-every-action (conflicts with Argus's autonomy goal)
- Trusting the model's own self-report of being stuck as the trigger signal
- Multi-operator approval routing / audit-signed sign-off workflows
