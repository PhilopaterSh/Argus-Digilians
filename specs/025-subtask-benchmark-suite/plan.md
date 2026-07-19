# Implementation Plan: Subtask-Level Benchmark Suite

**Feature**: `025-subtask-benchmark-suite` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

A new `benchmarks/` directory: fixture definitions (mock servers + optional `014`-lab Docker
targets, each with a subtask decomposition + ground-truth flag), a runner that drives real
`ArgusBrain` + real `build_argus_tools()` against each, computes SR/SCR/TTE, and supports
multi-configuration comparison for ablation-style studies.

## Design

### `benchmarks/fixtures/` (new)
- One subdirectory per fixture, e.g. `benchmarks/fixtures/info_disclosure_env_leak/`
  (`tests/ai_benchmark.py`'s scenario, migrated per SC-003), each containing:
  - `server.py` (a mock `http.server` handler, or a `docker-compose.yml` reusing `014`'s lab
    pattern for fixtures needing real app behavior)
  - `subtasks.yaml`: ordered list of `{name, detector_regex}` pairs (FR-002) —
    `detector_regex` matched against the run's tool-call-history text to determine completion,
    the automated SCR proxy research.md discusses.
  - `flag.txt`: the ground-truth flag string (SR target).
  - `query.txt`: the natural-language task given to `ArgusBrain.ask()`.

### `benchmarks/runner.py` (new)
- `run_fixture(fixture_dir, config_overrides=None) -> FixtureResult`: starts the fixture's
  mock server (or Docker target), builds a real `WSLBridgeTools()` + `build_argus_tools()`
  (FR-003's fix), calls `ArgusBrain.ask(query, ...)` under a wall-clock timeout (NFR-002),
  captures `tool_call_history`, computes SR (flag substring match), SCR (per-subtask regex
  match against the trace), TTE (index of the first tool-call step where the flag appears, or
  `None` if unsolved).
- `config_overrides` is a plain dict merged into `ArgusConfig` before the run (e.g.
  `{"enable_inter_reflection": False}`) — this is what makes FR-004's ablation comparisons
  possible without duplicating the runner per configuration.
- `run_suite(fixture_dirs, configs: dict[str, dict]) -> SuiteReport`: runs every fixture under
  every named configuration, aggregates SR/SCR/TTE per configuration (mirroring Table 6's
  structure), writes `benchmarks/results/<timestamp>_report.md` (FR-005).

### `tests/ai_benchmark.py`
- Migrated into `benchmarks/fixtures/info_disclosure_env_leak/` (SC-003); the original file is
  removed once the migration is verified equivalent, not left as a stale duplicate
  (Constitution IX) — its existing 4-path ground-truth/false-target logic maps directly onto
  the new `subtasks.yaml`/`flag.txt` format.

### `benchmarks/README.md` (new)
- How to add a fixture, how to run the suite, how to read a report — explicit onboarding so
  this doesn't become a write-only tool nobody else on the team knows how to extend.

## Testing Strategy

The runner's own logic (SR/SCR/TTE computation, config-override merging, report formatting) is
unit-tested with a **fake** `ArgusBrain`/fixed trace (`benchmarks/tests/test_runner.py`) — fast,
no live Ollama needed, verifies the scoring math itself is correct independent of any real
agent behavior. The fixture suite's actual execution against real `ArgusBrain` is the
benchmark's whole purpose and is run manually/on-demand (NFR-003), not part of automated CI.

## Rollout

Additive; `tests/ai_benchmark.py`'s removal (once migrated) is the only deletion, and only after
its replacement fixture is confirmed to reproduce equivalent results.
