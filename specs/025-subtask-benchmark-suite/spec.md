# Feature Specification: Subtask-Level Benchmark Suite (SR/SCR/TTE + Ablation)

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `025-subtask-benchmark-suite`

**Created**: 2026-07-10

**Status**: Proposed — spec kit only, not yet implemented.

**Input**: Gap analysis of `docs/history/2603.27127v1.pdf` against Argus's current codebase,
requested by the user 2026-07-10.

---

## Why this feature

Argus has exactly one benchmark-shaped artifact today, confirmed by reading it directly:
`tests/ai_benchmark.py`. It is a single hand-written scenario (one mock HTTP server exposing
`/.env` and `/config.php.bak` as true positives, `/admin.php` and `/secrets.txt` as
false-positive traps) run as a standalone script (`if __name__ == "__main__"`, not collected by
`pytest.ini`), computing precision/recall/hallucination-rate for that one scenario, and — worth
flagging directly — it calls `ArgusBrain` with a hand-picked 2-tool subset
(`Run_FFUF`, `Run_Kali_Command`), not the real 17-tool list `build_argus_tools()` actually wires
into production. It has no notion of subtasks, no comparison across configurations, and cannot
answer "did this week's change to `react_workflow.py` make the agent better or worse."

Red-MIRROR's contribution 3 (Abstract) is exactly this gap: "a fine-grained subtask-level
benchmark derived from XBOW subsets and real-world Vulhub CVEs" with three metrics — Success
Rate (flag retrieval), Subtask Completion Rate (manual decomposition into 2-17 sub-steps per
challenge, Section 4.4.2), and Time-to-Exploit (agent steps to solve, Section 4.4.4) — plus an
ablation methodology (Table 6/7/8) that is the paper's own strongest evidence for its core
design choice. Without an equivalent, every other proposed phase in this gap analysis (`019`,
`020`, `021`) can claim "should help" but Argus has no way to measure whether it actually did.

## Requirements

### Functional Requirements

- **FR-001**: A new `benchmarks/` directory MUST hold a small, curated set of locally-hostable
  vulnerable-target fixtures (mock HTTP servers or Dockerized known-vulnerable apps, following
  `tests/ai_benchmark.py`'s existing mock-server pattern where possible to avoid new
  infrastructure, and reusing `specs/014-containerized-lab`'s existing Docker-based lab
  infrastructure where a mock server cannot represent the vulnerability class realistically
  e.g. real SSTI/SQLi behavior). Full external-benchmark parity (mirroring all 50 XBOW
  challenges) is explicitly not the goal — a smaller, growable, in-repo set covering the same
  major categories (XSS, SQLi, IDOR, Auth, SSTI, Command Injection) is (see Explicitly out of
  scope).
- **FR-002**: Each fixture MUST ship a manually-authored subtask decomposition (a JSON/YAML
  list of named sub-steps, mirroring the paper's XBEN-005-24 worked example in Section 4.4.2 —
  e.g. `["find_login_form", "find_default_creds", "login", "find_hidden_param",
  "exploit_privilege_escalation", "retrieve_flag"]`) plus a ground-truth flag string the agent
  must retrieve.
- **FR-003**: A benchmark runner MUST invoke `ArgusBrain` (through the **real**
  `build_argus_tools()`, fixing `ai_benchmark.py`'s existing tool-subset gap per FR-003) against
  each fixture, capture the full run trace (`tool_call_history`, matching `019`'s
  `reflection_notes` if that phase exists), and compute:
  - **SR**: exact ground-truth flag string found in the final output (Section 4.4.1, Eq. 18).
  - **SCR**: fraction of FR-002's named subtasks whose evidence appears in the run trace —
    detected via a per-subtask keyword/regex matcher authored alongside each fixture's
    decomposition (a lighter-weight, automatable stand-in for the paper's own manual log
    inspection, since Argus does not have a research team to manually grade every run — this is
    an explicit, honest simplification of the paper's methodology, not a claim of equivalence).
  - **TTE**: count of tool-call steps from run start to the step where SR's flag was found
    (Section 4.4.4, Eq. 20-21) — only computed for solved fixtures.
- **FR-004**: The runner MUST support running the same fixture set under different
  **configurations** (e.g., `019`'s `enable_inter_reflection` flag on/off, `020`'s
  `enable_multi_agent_roles` flag on/off, once those exist) and produce a comparison table —
  this is what makes an ablation study (mirroring Table 6/7/8) possible at all; without
  configuration-parameterized runs, this is just a one-off scorer, not an ablation tool.
- **FR-005**: Results MUST be written to a timestamped report file (`benchmarks/results/
  <timestamp>_report.md`) with per-fixture and aggregate SR/SCR/TTE — every run's result is
  kept, not just the latest, so trends over time (across commits/phases) are visible.

### Non-Functional Requirements

- **NFR-001**: The full fixture set MUST be runnable without any external network dependency
  beyond what Argus's own tools already need (local mock servers / local Docker containers via
  `014`'s lab) — no dependency on XBOW's or Vulhub's actual hosted infrastructure, both to keep
  this reproducible offline and to avoid any risk of this benchmark being mistaken for testing
  against systems Argus is not authorized to test.
- **NFR-002**: A single fixture run MUST have an explicit wall-clock budget (matching the
  paper's own 15-30 minute per-challenge time budget, Section 4.4.3) enforced via
  `ArgusBrain`'s existing `max_iterations` bound plus an outer wall-clock timeout — a hung
  benchmark run is a benchmark bug, not a finding.
- **NFR-003**: This suite MUST NOT be part of the default `pytest` collection
  (`tests/ai_benchmark.py`'s existing precedent of living outside `pytest.ini`'s collected path
  is correct and should be preserved) — it requires live Ollama/WSL and is slow by nature
  (multiple full agent runs), unsuitable for routine CI.

## Success Criteria

- **SC-001**: Running the benchmark against the current, unmodified production Argus (no `019`/
  `020` features yet) produces a baseline SR/SCR/TTE report — this is the number every future
  proposed phase should be measured against, not a theoretical estimate.
- **SC-002**: FR-004's configuration comparison, run once `019` exists, produces a table in the
  same shape as the paper's Table 6 (per-configuration SR/SCR/TTE) — proving the harness itself
  works for its intended ablation purpose, independent of what the actual numbers turn out to
  say about `019`.
- **SC-003**: `tests/ai_benchmark.py`'s existing single scenario is migrated into FR-001's
  fixture format (not duplicated) as the suite's first fixture, closing the "hand-picked
  2-tool subset instead of real production tools" gap identified above as part of this
  migration.

## Assumptions

- FR-002's SCR keyword/regex matchers are a known-imperfect proxy for the paper's manual
  human-graded subtask inspection — this is disclosed explicitly (FR-003) rather than presented
  as equivalent rigor, per Constitution VIII.
- The fixture set starts small (proposed: 6-10 fixtures covering the major OWASP categories
  Argus's existing tools target) and grows over time; it does not need to reach 50+ fixtures to
  be useful for its primary purpose (regression-testing proposed changes), which is a lower bar
  than academic benchmark parity.

## Explicitly out of scope

- Reproducing the actual XBOW (50 challenges) or Vulhub (8 CVEs) benchmark sets — those are
  external, third-party benchmark suites with their own licensing/access terms; this spec
  builds an **Argus-owned, equivalent-in-kind** benchmark, not a redistribution of theirs.
- Human-graded SCR at the paper's level of rigor — FR-003's automated proxy is the pragmatic
  substitute; a human-review pass on the automated grader's accuracy is a valid future addition,
  not required for v1.
- Cost-per-challenge tracking (the paper's own "$0.20/challenge" style metric) — not meaningful
  for Argus's local-GGUF-inference model, which has no per-token API cost to track.
