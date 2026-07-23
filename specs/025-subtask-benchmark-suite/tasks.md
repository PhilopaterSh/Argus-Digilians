# Tasks: Subtask-Level Benchmark Suite

**Feature**: `025-subtask-benchmark-suite`

**Status**: Implemented 2026-07-23 (T001-T004, T006-T008 complete; T005/T009 unblocked and
left for the user to run on their own schedule - each is a 15-30 min live-Ollama run per
fixture per configuration, not something to trigger unattended).

- [x] T001 `benchmarks/fixtures/info_disclosure_env_leak/` — migrated `tests/manual/ai_benchmark.py`'s
  scenario (moved 2026-07-10, not `tests/ai_benchmark.py`) into the fixture format
  (`server.py`, `subtasks.yaml`, `flag.txt`, `query.txt`); flag reformatted to `flag{...}` shape
- [x] T002 `benchmarks/runner.py::run_fixture()` — real `build_argus_tools()` (fixes the
  original script's 2-tool subset), wall-clock timeout, SR/SCR/TTE computation
- [x] T003 `benchmarks/runner.py::run_suite()` — multi-configuration ablation comparison,
  report generation (`benchmarks/results/<ts>_report.md`)
- [x] T004 Unit tests for the scoring/config-merge/report logic with a fake LLM injected via
  `ArgusBrain`'s real `llm=` seam (never mocks `ArgusBrain` itself) —
  `benchmarks/tests/test_runner.py`, 10/10 passing, no live Ollama/WSL needed
- [ ] T005 SC-001: full baseline report across all 4 fixtures against current, unmodified
  production Argus — unblocked, left for the user to run (`python benchmarks/runner.py`)
- [x] T006 Authored 3 new fixtures (`xss_reflected`, `idor_object_access`,
  `ssti_template_injection` — user-scoped down from the spec's 5-9 to 3 for this pass; Auth and
  Command Injection left for a later pass, consistent with the spec's own "grows over time"
  assumption). All real in-process vulnerable logic (no Docker, no `subprocess`) - genuine
  `jinja2.Template(...).render()` for SSTI, an unauthenticated lookup for IDOR, unescaped
  reflection for XSS.
- [x] T007 `benchmarks/README.md` — fixture-authoring contract, run instructions, report format
- [x] T008 Removed `tests/manual/ai_benchmark.py` and its `tests/manual/README.md` bullet,
  after a live sanity run of `info_disclosure_env_leak` confirmed the migrated fixture's
  *wiring* is correct end-to-end (real Ollama, real WSL bridge/tool execution, real target
  reachability, real trace capture, real SR/SCR scoring - no crash, no hang, no timeout).
  This run itself did not solve the challenge (SR=False, SCR=0.33 - found `/.env` but the
  final report didn't include its content/flag): a real, honest baseline data point, not a
  wiring failure - the agent used broad recon tools (Nikto, subdomain enum) rather than
  directly requesting the known `/.env`/`/config.php.bak` paths. This is exactly the kind of
  result this benchmark suite exists to surface, not a defect to hide (Constitution VIII).
- [ ] T009 (depends on `019`) SC-002: run the ablation comparison once `enable_inter_reflection`
  exists (it already does) — unblocked, left for the user to run
  (`python benchmarks/runner.py --configs-json '{"baseline": {}, "no_inter_reflection": {"enable_inter_reflection": false}}'`)
- [x] T010 `CHANGELOG.md` entry + `specs/checklist.md` CHK113 +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row

## Real bug found and fixed during implementation (not in the original plan)

The live sanity run for T008 initially failed (SR=False, SCR=0.0 on `info_disclosure_env_leak`)
with no tool activity in the trace. Root-caused live, not assumed: fixture servers bound to
`127.0.0.1` on the Windows host are **not reachable from inside the WSL/Kali guest** where
Argus's tools actually execute (confirmed via `wsl -d kali-linux -- curl 127.0.0.1:<port>/.env`
→ curl exit code 7, "failed to connect"; the same request via WSL's own default-gateway IP,
with the server rebound to `0.0.0.0`, succeeded). Fixed in `benchmarks/fixture_base.py`'s new
`_wsl_reachable_host()` (resolves the gateway IP live via `wsl -d <distro> -- ip route show
default`, cached per-process, `127.0.0.1` fallback if WSL is unavailable) plus rebinding all
four fixture servers to `0.0.0.0`. This was a latent bug in the original
`tests/manual/ai_benchmark.py` too (same `127.0.0.1`/`WSLBridgeTools` combination) - not a
regression introduced by this migration.

## Explicitly out of scope (see spec.md)

- Reproducing the actual XBOW/Vulhub benchmark sets
- Human-graded SCR at the paper's level of rigor
- Cost-per-challenge tracking
