# Tasks: Subtask-Level Benchmark Suite

**Feature**: `025-subtask-benchmark-suite`

**Status**: Proposed — no tasks started.

- [ ] T001 `benchmarks/fixtures/info_disclosure_env_leak/` — migrate `tests/ai_benchmark.py`'s
  scenario into the new fixture format (`server.py`, `subtasks.yaml`, `flag.txt`, `query.txt`)
- [ ] T002 `benchmarks/runner.py::run_fixture()` — real `build_argus_tools()`, wall-clock
  timeout, SR/SCR/TTE computation
- [ ] T003 `benchmarks/runner.py::run_suite()` — multi-configuration ablation comparison,
  report generation
- [ ] T004 Unit tests for the scoring/config-merge/report logic with a fake `ArgusBrain` —
  `benchmarks/tests/test_runner.py`
- [ ] T005 SC-001: baseline report against current, unmodified production Argus
- [ ] T006 Author 5-9 more fixtures covering XSS, IDOR, SSTI, Command Injection, Auth
  categories (some via `014`'s Docker lab, some as new mock servers)
- [ ] T007 `benchmarks/README.md` — fixture-authoring and run instructions
- [ ] T008 Remove `tests/ai_benchmark.py` once T001's migration is verified equivalent
- [ ] T009 (depends on `019`) SC-002: run the ablation comparison once `enable_inter_reflection`
  exists, producing a Table-6-shaped report
- [ ] T010 `CHANGELOG.md` entry + `specs/checklist.md` CHK series +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row, once implemented

## Explicitly out of scope (see spec.md)

- Reproducing the actual XBOW/Vulhub benchmark sets
- Human-graded SCR at the paper's level of rigor
- Cost-per-challenge tracking
