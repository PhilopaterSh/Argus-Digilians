# Tasks: Subtask-Level Benchmark Suite

**Feature**: `025-subtask-benchmark-suite`

**Status**: Fully implemented and live-verified 2026-07-23 (T001-T010 all complete, including
T005/T009's live baseline and ablation runs).

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
- [x] T005 SC-001: full baseline report across all 4 fixtures, `benchmarks/results/20260723T143037Z_report.md`.
  SR 0/4, mean SCR 0.33 - every fixture's discovery-endpoint subtask matched (the agent
  consistently finds the right endpoint via recon tools) but no fixture's follow-through/
  extraction subtasks matched and no flag was reported. A genuine, honest baseline: this
  model is currently stronger at initial discovery than at confirm-and-extract follow-through
  on these fixtures, not a wiring problem (the same harness is what produced this data).
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
- [x] T009 SC-002: ran the ablation comparison (`baseline` vs. `no_inter_reflection`),
  `benchmarks/results/20260723T144350Z_report.md` - the project's first real Table-6-shaped
  ablation result. `baseline` (mean SCR 0.33) outperformed `no_inter_reflection` (mean SCR
  0.25) - directionally consistent with `019`'s intent, though SR was 0/4 both ways on this
  4-fixture set and per-fixture SCR varied noticeably run-to-run (e.g. `xss_reflected` scored
  0.67 in this run's baseline vs. 0.33 in T005's baseline) - a real characteristic of this
  local 7B model's ReAct variance, not a scoring bug. A larger fixture set and repeated runs
  (both explicitly out of this pass's 3-fixture scope) would be needed before treating this
  gap as more than directional signal.
- [x] T010 `CHANGELOG.md` entry + `specs/checklist.md` CHK113 +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row

## Post-completion addition (2026-07-23, same day)

User asked to add Path Traversal coverage, one of the two named categories (with Auth) T006
had left for a later pass. Added `benchmarks/fixtures/path_traversal_download/`: a real
filesystem-backed `/download?file=...` endpoint (naive `os.path.join`, no `..`
normalization/containment check) in a private per-process temp sandbox created in
`start_server()` and removed in `stop()`, so a traversal payload only ever reaches this
fixture's own throwaway files - `public/welcome.txt` (safe) vs. `secret.txt` one directory up
(the flag), matching the same "real vulnerable logic, no simulation" bar as the SSTI/IDOR/XSS
fixtures. Live-sanity-checked (real Ollama/WSL): no crash/timeout, SCR 0.33
(`find_download_endpoint` matched, same discovery-not-extraction pattern as every other
fixture in this suite's baseline) - a 5th real, working fixture.

## Re-run with all 5 fixtures (2026-07-23, user requested)

Re-ran the combined baseline + ablation suite (`benchmarks/results/20260723T150717Z_report.md`)
across all 5 fixtures, superseding T005/T009's original 4-fixture reports (kept on disk, not
deleted - every run is kept per FR-005). Result this time: **`baseline` and
`no_inter_reflection` scored identically** - SR 0/5 and mean SCR 0.33 for both configurations,
every fixture matching only its discovery-endpoint subtask in both configs.

**This does not replicate T009's original directional signal** (`baseline` 0.33 vs.
`no_inter_reflection` 0.25) - stated plainly rather than cherry-picking the earlier, more
flattering run (Constitution VIII). Combined, the two ablation runs show: this suite's current
3-subtask-per-fixture granularity and this local 7B model's real run-to-run ReAct variance are
large enough that a single ablation pass is not reliable evidence either way about
`enable_inter_reflection`'s effect - exactly the caution T009's original entry already flagged
("treat as directional signal... not a settled result"), now confirmed empirically rather than
just hedged. Settling this would need repeated runs per configuration (majority vote or a
confidence interval across N runs), which is future scope, not implied by either existing
report.

## Post-completion enhancement: repeated-trial support (2026-07-24, user requested)

User asked to pursue two things together: (A) `specs/021`'s exploitation-toolkit gap (the
"finds the endpoint, never extracts" pattern above) and (B) making the ablation methodology
above statistically trustworthy, and asked for a Claude/OpenCode cross-review of the plan before
implementing. OpenCode (`opencode run`, this repo's other configured coding-agent CLI) could not
be used for that review in this environment - 3 attempts at a multi-turn planning discussion
(default agent, `--agent plan`, then a fully self-contained no-file-read prompt) all hung with
zero output for several minutes despite a trivial one-line prompt succeeding in under a minute
with the same agent/model - reported to the user as an honest limitation rather than fabricating
a "converged" plan. Proceeded with Claude's own independently-drafted plan, approved by the user.

Implemented track (B) first (small, unblocks trustworthy future measurement of track A once
built): `benchmarks/runner.py` gained `AggregatedResult` (`trials`, `solved_count`, `sr_rate`,
`mean_scr`, `stddev_scr` via `statistics.pstdev` - population, not sample, so `trials=1` is
still well-defined at `0.0` rather than a special case, `mean_tte` over solved trials only,
`error_count`, `subtask_match_rates`) and `_aggregate_trials()`. `run_suite(..., trials: int =
1)` now runs each `(fixture, config)` pair `trials` times and aggregates instead of taking one
run at face value; `render_report()` shows solved-rate/mean+stddev instead of a single point
value. `--trials` added to the CLI. Default stays 1 (today's behavior) so a quick check doesn't
silently get `N` times slower. 4 new unit tests (`benchmarks/tests/test_runner.py`, 14/14
passing) cover the aggregation math directly and confirm `run_suite()` actually invokes
`run_fixture()` `trials` times per pair (monkeypatched, no live Ollama needed).

Track (A) - building `specs/021`'s IDOR/XSS/SSTI tool groups (chosen over the spec's own
suggested JWT-first order because those 3 groups map directly onto benchmark fixtures already
built, per Claude's plan) - is the next step, not yet started as of this entry.

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
