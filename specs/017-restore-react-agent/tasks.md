# Tasks: Restore ArgusBrain as Production Driver

Retrospective documentation (2026-07-18) of the completed work, sourced directly from
specs/checklist.md's Phase 017 entries (CHK064-069) - no new tasks, this is the existing
completion record reorganized into this file's expected location.

- [x] T001 (CHK064) Implement `app/core/agent/brain_tools.py::build_argus_tools()` - one
  canonical 12-tool list for `ArgusBrain`, replacing the pattern of hand-copying it into every
  GUI file. Verified: `tests/test_registry/test_brain_tools.py`, 3/3 passing.
- [x] T002 (CHK065) Implement `app/core/agent/react_callback.py::LiveFeedCallbackHandler` -
  streams Thought/Action/Observation/error/finish into the existing state-file event contract.
  Verified: `tests/test_registry/test_react_callback.py`, 6/6 passing.
- [x] T003 (CHK066) Rewrite `scripts/run_agent.py` to drive `ArgusBrain.ask()` instead of
  `build_tactical_graph()`; preserve the timeout-bounding thread wrapper and demo/test fallback
  unchanged; `_build_final_state()` must never fabricate a structured report when the LLM's
  output didn't parse (`parse_warning` instead). Verified end-to-end with an injected
  `FakeListLLM` (no live Ollama/WSL needed); unit-tested:
  `tests/test_modules/test_run_agent.py`, 4/4 passing.
- [x] T004 (CHK067) Update `app/GUI/tabs/agent.py` Final Results section to render the real
  `SecurityReport` shape (risk score, findings, next steps, full report) instead of the old
  open_ports/vulnerabilities/exploit_success metrics. Verified with a real Streamlit `AppTest`
  run against a completed-run state file: zero exceptions, findings content confirmed present in
  rendered output.
- [x] T005 (CHK068) Confirm `app/core/agent/graph.py` and its nodes retained unmodified
  (Constitution VII). Verified: `tests/test_modules/test_tactical_graph_termination.py` still
  passes.
- [x] T006 (CHK069) Update `specs/010-langgraph-agent/spec.md`'s status line to record the
  supersession; update `docs/ARCHITECTURE_AUDIT_REPORT.md`'s traceability matrix (010's row
  updated, new 017 row added).

## Notes

- First real production run against a live target (`https://www.cultbeauty.co.uk/`) surfaced a
  reliability incident, formalized as a follow-up feature: see
  `specs/018-structured-agent-reliability/`.
