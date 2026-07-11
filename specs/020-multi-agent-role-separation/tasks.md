# Tasks: Multi-Agent Role Separation

**Feature**: `020-multi-agent-role-separation`

**Status**: Proposed, **not scheduled**. Do not start T001 without an explicit team decision to
proceed, per spec.md's recommendation to ship `019` first and measure the residual gap.

- [ ] T000 (gate) Team decision: proceed with this phase, informed by `019`'s measured results
  and this spec's cost analysis — record the decision (go/no-go/defer) here before T001
- [ ] T001 Split `react_prompts.py`'s single system prompt into 4 role-scoped prompts
- [ ] T002 Add `role` parameter to `build_argus_tools()` for FR-002's tool partitioning —
  `app/core/agent/brain_tools.py`
- [ ] T003 Add `current_role`/`role_history` fields to `ArgusAgentState` —
  `app/core/agent/react_state.py`
- [ ] T004 Implement the `planner` -> `{collector, exploiter}` -> `planner` -> `summarizer`
  graph topology — `app/core/agent/react_workflow.py`
- [ ] T005 Add `enable_multi_agent_roles` config flag (default `false`) —
  `config.yaml`, `app/core/config.py`
- [ ] T006 Build the head-to-head wall-clock comparison test harness (mocked tool latency,
  this topology vs. `019`-only baseline)
- [ ] T007 Run NFR-001's measurement; record result in this file regardless of outcome
  (Constitution VIII — report honestly even if it's a regression)
- [ ] T008 If NFR-001/SC-002 fail: document why and stop here, feature flag stays `false`
- [ ] T009 If NFR-001/SC-002 pass: SC-001 benchmark comparison (depends on `025`), then consider
  flipping the default
- [ ] T010 `CHANGELOG.md` entry + `specs/checklist.md` CHK series +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row, once T007's outcome is known either way

## Explicitly out of scope (see spec.md)

- Independently-scaled per-role model deployments
- Full DAG-based path planning with branch pruning
