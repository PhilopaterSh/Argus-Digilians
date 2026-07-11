# Research: Subtask-Level Benchmark Suite

**Feature**: `025-subtask-benchmark-suite`

## Primary source

`docs/history/2603.27127v1.pdf`, Sections 4.3 (Datasets/Benchmarks), 4.4 (Evaluation Metrics —
SR Eq. 18, SCR Eq. 19, TTE Eq. 20-21), 4.5.3 (RQ3 ablation methodology, Table 6/7/8's filter-type
stratification). The XBEN-005-24 subtask decomposition worked example (Section 4.4.2) is the
direct template for this spec's FR-002 fixture format.

## Current Argus implementation reviewed (confirmed by direct file read)

`tests/ai_benchmark.py`: one `MockVulnerableServer` (stdlib `http.server`), one hardcoded query
string, a **hand-picked 2-tool list** (`Run_FFUF`, `Run_Kali_Command`) passed directly to
`ArgusBrain(model, tools)` — notably **not** `build_argus_tools()`, meaning this existing
benchmark does not actually exercise the same tool surface production runs use. Computes
precision/recall/hallucination-rate via simple substring matching on the final output text
against a 4-item ground-truth/false-target list. Runs as `python tests/ai_benchmark.py`
directly — confirmed not collected by `pytest.ini` (grep for `ai_benchmark` in that file found
nothing), consistent with it being a manual/exploratory script, not a maintained regression
suite.

## Why FR-003 explicitly calls out and fixes the tool-subset gap

This is a genuine, if minor, existing correctness issue independent of the Red-MIRROR gap
analysis: a benchmark that doesn't exercise the same tools production uses cannot detect
regressions in any of the other 15 tools, and cannot detect the exact class of bug `018`'s
CHK090 found (a tool silently missing from the wired-up list) because it never wired up the
full list in the first place. Migrating it into this suite's fixture format (SC-003) both
gains this spec's benefit and fixes that pre-existing gap in one motion.

## Relationship to `014-containerized-lab`

`specs/014-containerized-lab` (present in this session's git status as an in-progress/untracked
area) already exists to provide Dockerized vulnerable-app targets — this spec's FR-001
deliberately reuses that infrastructure for fixtures where a plain mock HTTP server cannot
represent the real vulnerability mechanics (e.g., a real Jinja2 app for a genuine SSTI fixture,
vs. a mock server that can only fake an SQLi response). Building a second, parallel
containerization mechanism inside `benchmarks/` would violate Constitution IX.

## Why automated SCR grading is an explicit, disclosed simplification

The paper's SCR methodology (Section 4.4.2) is manual: a human inspects agent logs/tool outputs
per challenge and marks each of that challenge's annotated subtasks as complete/incomplete based
on judgment. Argus has no equivalent research team to do this per benchmark run, and the whole
point of this suite is *repeatable, cheap-to-run regression testing* across many future code
changes — a keyword/regex-based automated proxy (FR-003) is the only way to make that
repeatable, at the cost of being a less rigorous signal than the paper's own number. This
tradeoff is stated in the spec's Assumptions rather than left implicit, consistent with
Constitution VIII (don't claim more rigor than what was actually built).
