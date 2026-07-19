# Tasks: Unify All Branches Into One Version

**Input**: Design documents from `specs/027-merge-branches/` (spec.md, research.md — cross-verified
3x, plan.md — synthesized from 3 independent plans + a resolved discussion round, data-model.md,
quickstart.md)

**Tests**: Not separately generated as contract/integration test tasks — this feature's "tests" are
its *test gates* (pytest must keep collecting/passing after every step), which are embedded directly
in each implementation task below, per plan.md's Integration Steps.

**Organization**: Tasks are grouped by user story from spec.md (US1 = consolidate, US2 = preserve
history, US3 = single installer/docs), in the priority order plan.md's 6 Integration Steps already
established.

## Path Conventions

Single project, repository root = `Argus-Digilians/` (paths below are relative to it unless noted).
**Exception**: any path starting with `branches/` (e.g. `branches/momen/` in T011) is relative to the
workspace root (`D:\TEAM PROJECT\Main\`), one level *above* `Argus-Digilians/`, not inside it — those
are the `git worktree` checkouts of the other branches, documented in `docs/ARCHITECTURE.md`.

---

## Phase 1: Setup

**Purpose**: Establish a safe, reversible starting point before any integration work begins.

- [ ] T001 Confirm all 9 original branches still exist and are resolvable: `git branch -a` and
  `git worktree list` from `Argus-Digilians/` — record the output as the "before" baseline
  (spec.md FR-004 / SC-003 depend on comparing against this later)
- [ ] T002 Tag the current tip of every one of the 9 contributor branches (e.g.
  `git tag pre-merge/momen momen`) as an extra recovery point beyond the branch ref itself
- [ ] T003 [P] Create the integration working branch from `fix/copy-setup-to-scripts`'s tip
  (e.g. `git checkout -b unify/027-merge-branches fix/copy-setup-to-scripts`)
- [ ] T004 [P] Adopt `fix/copy-setup-to-scripts`'s test/lint tooling as the project standard: copy
  `pytest.ini`, `requirements-dev.txt`, `ruff.toml`, `mypy.ini` are already present on this base —
  confirm `Argus_venv\Scripts\python.exe -m pytest --collect-only` runs clean before touching anything

**Checkpoint**: Working branch exists, tooling confirmed, full recovery path guaranteed before any
merge/port work starts.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Nothing below can be verified without a working test/startup baseline captured first.

- [ ] T005 Record the baseline: `Argus_venv\Scripts\python.exe -m pytest -q` pass/fail count on the
  Phase 1 working branch (this is the number every later step's "no net regression" gate compares
  against — data-model.md's `Unified Branch.test_pass_rate`)
- [ ] T006 Record that `run_argus_cli.py` reaches its normal startup prompt on the working branch
  (baseline for SC-002)

**Checkpoint**: Baseline pass-rate and startup behavior recorded — every subsequent story's test gate
has something concrete to compare against.

---

## Phase 3: User Story 1 - Consolidate Divergent Contributor Work Into One Codebase (Priority: P1) 🎯 MVP

**Goal**: Fold every branch classified "feature work to merge" (research.md §3) into the working
branch, with every conflict resolved and recorded, and nothing regressed.

**Independent Test**: Checkout the working branch after this phase, run `run_argus_cli.py` /
`scripts\LAUNCH_STUDIO.bat`, and run `pytest -q` — both must succeed at ≥ the Phase 2 baseline.

### Implementation for User Story 1

- [x] T007 [US1] Merge `argus/SALMA` into the working branch: `git merge --no-ff --no-commit
  argus/SALMA` (connected history — research.md §2). Before resolving conflicts: run
  `git diff --name-only --diff-filter=A HEAD` to catalog every file git treated as "new" — these are
  likely cases where rename detection failed against the base's modular `app/core/` layout (SALMA
  still has flat files like `app/core/BaseToolService.py`, which git may not recognize as related to
  the base's `app/core/registry/`). For each cataloged "new" file, check by hand whether it's really
  a rename of existing modular content (no port needed) or genuinely new SALMA content (port into the
  matching modular file) — carry this catalog into T008. *(Panel-resolved 2026-07-17: agy and
  opencode both independently flagged the rename-detection risk and converged on this same
  pre-commit cataloging step.)*
- [x] T008 [US1] Resolve each conflict `git merge` reports in `app/core/` (SALMA's
  `BaseToolService`/`ArgusBrainV2` vs. the base's `agent/` package), using T007's "new file" catalog
  as a checklist so nothing SALMA added is silently missed — for each conflicted file, record a
  `Conflict Decision` (data-model.md) with winning source + one-line rationale before resolving
- [x] T009 [US1] Resolve conflicts in `app/tools/` and `tests/` the same way as T008, one recorded
  decision per conflicted file
- [x] T010 [US1] Confirm `pytest --collect-only` and `pytest -q` after the SALMA merge — no
  regression vs. the Phase 2 baseline. **Advisory, non-blocking check** (see Methodology Note below):
  cross-reference every file from T007's `--diff-filter=A HEAD` catalog by filename stem against
  existing files in the same target directory — a same-stem hit not already accounted for in a
  Conflict Decision is worth a second look before committing. **Also run the `clean-code-guard`
  skill** (added 2026-07-18, `docs/ARCHITECTURE.md` §5) over the merge diff before committing — this
  is exactly the file-porting/conflict-resolution work its AI-failure-mode checks (hallucinated APIs,
  error swallowing, copy-from-similar bugs) target. Commit the merge.
- [x] T011 [US1] Run the Python 3.10→3.12 compatibility checklist (plan.md Synthesized Design
  Decision #6) against `branches/momen/`: grep `distutils`, grep `\bimp\.`, verify `torch`/`faiss-cpu`
  pins, grep un-raw regex escape sequences, grep `.utcnow()`/`.utcfromtimestamp(` — fix any hits
  found, in `momen`'s source before porting it. **Result (2026-07-18)**: clean except one hit —
  `_experimental_advanced_modules/core/llm_engine.py:76` has an invalid `\/` escape sequence in a
  path-traversal payload string literal (`'....\/....\/....\/etc/passwd'`), caught by
  `python -W error::DeprecationWarning -m compileall` (a broader check than the grep list above — the
  grep for un-raw `re.compile(` calls didn't catch it since it's a plain string literal, not a regex).
  Not fixed in the `branches/momen/` worktree itself (spec.md FR-004 — original branches stay
  untouched); the fix (`\/` → `\\/`, preserving the exact same runtime string value) applies when this
  file is copied into `app/modules/experimental_agent/` at T014, since `llm_engine.py` is a real
  import dependency of `_experimental_advanced_modules/core/agent.py` (`OllamaEngine`,
  `SECLISTS_EMBEDDED`) and must be ported alongside it. Everything else (distutils, imp, torch/faiss
  pins, utcnow) is clean — no other fixes needed.
- [x] T012 [US1] Re-home `momen`'s `core/*.py` into `app/core/` (per-file placement, not a directory
  copy — Constitution Principle III). *(Panel-resolved 2026-07-17: agy proposed splitting into 8
  per-file sub-tasks; opencode disagreed, arguing the real work is reading each file's actual content
  to judge its domain, and a placement guess assigned in advance could be wrong and mislead the
  implementer. Resolved as: keep this as one task — checked off per-file below so nothing is silently
  skipped — using opencode's hedged framing, not agy's prescriptive one.)* For each of momen's 8
  `core/` files, verify (don't blindly follow) a placement, then check it off. **Result (2026-07-18,
  opencode implementation, reviewed by orchestrator):**
  - [x] `agent.py` — discarded. Superseded by `app/core/agent/`'s LangGraph agent.
  - [x] `agent_ai_driven.py` — discarded. Superseded by the same LangGraph architecture.
  - [x] `memory.py` — discarded. `app/core/memory/memory_service.py` (already SALMA-merged) has
    context managers, WAL, schema versioning, and more tables; genuinely superseded.
    **Correction 2026-07-18 (final comprehensive audit, orchestrator + codex independently
    corroborated)**: "genuinely superseded" was true for storage mechanics but incomplete as a
    capability claim — three real, previously-live methods had no equivalent anywhere in the
    unified schema: corrupt-DB detection/recovery (`_db_ok`/`_reset_corrupt_db`, vs the unified
    `_verify_integrity()` which only warns, never recovers), scan-session history
    (`scan_sessions` table + `log_scan_history`/`get_scan_history`, confirmed live functionality
    via `momen:GUI/app.py:159,373,400`, not dead code), and `get_priority_targets()`. All three
    ported into `app/core/memory/memory_service.py` with 10 new tests, commit `4fe3ad2`. See the
    Methodology Note below for the full audit (also covers MOUSTAFA-PC and DESKTOP-BVV10T0's SSH
    self-healing, both of which held up as correctly discarded/superseded — no port needed there).
  - [x] `prompts.py` — ported. Added `ARGUS_SYSTEM_PROMPT`/`get_system_prompt()` (evidence-discipline
    persona, coverage checklist, calibrated strengths/blind-spots from 1,040 labeled scenarios) to
    `app/core/prompts.py`.
  - [x] `rag_kb.py` — ported. New `app/core/rag/local_kb.py` (`TECH_VULNS`, `PATTERN_RULES`,
    `ATTACK_HINTS`, `get_tech_context()`, `analyze_timeout_pattern()`, `retrieve_scenario_context()`).
  - [x] `safety.py` — ported. New `app/core/safety.py` (`SafetyLayer`) — no equivalent existed.
  - [x] `schemas.py` — ported. Added `ScanMode`/`SeverityLevel` enums, `PluginResult` model,
    `tool_source` field on `Finding`, into `app/core/schemas.py`.
  - [x] `tools.py` — **mostly** discarded (1909-line monolith superseded by modular `app/tools/`
    services) — **with one correction found during test-guard review**: `check_xss()`'s reflection
    classifier (`_classify`) has **no real equivalent anywhere in `app/tools/`** (verified by grep —
    only a payload-label string exists). Extracted that classifier as real production code into new
    `app/tools/xss_classifier.py::classify_xss_reflection()`. The surrounding live-scanning capability
    (endpoint probing loop, `FIXED_XSS_ENDPOINTS`, finding-recording) was **not** ported — flagged as
    an open gap, not silently dropped; see Open Follow-Ups at the end of this file.
- [x] T013 [US1] Re-home `momen`'s `GUI/app.py` into `app/GUI/`, reconciling against
  the existing Streamlit dashboard rather than adding a second GUI entry point. **Result**: discarded
  — `app/GUI/dashboard.py` is the canonical multi-page dashboard with session/AgentController
  management; momen's `GUI/app.py` predates it and adds nothing new (verified by reading both).
- [x] T014 [US1] [P] Port `momen`'s `_experimental_advanced_modules/core/agent.py` (13-step
  pipeline) to `app/modules/experimental_agent/agent.py` — **opt-in only, do NOT register it in
  `app/core/registry/tool_registry.py`** (plan.md Synthesized Design Decision #1 / Constitution
  Principle I). **Result (orchestrator, 2026-07-18)**: ported all 5 interdependent files
  (`agent.py`, `llm_engine.py`, `verifier.py`, `agent_payload_decider.py`, `payload_encoder.py`) into
  `app/modules/experimental_agent/`; fixed the T011-flagged `\/` escape sequence in `llm_engine.py`;
  rewrote all `from core.*` imports to the new package paths (7 call sites across 2 files). Added
  `ArgusMemory.get_detailed_findings(domain, since=None)` to `app/core/memory/memory_service.py` —
  the experimental agent calls this but the unified schema has no `severity` column (momen's own
  `core/memory.py` did); implemented as a real DB query returning `severity="Info"` uniformly rather
  than guessing severity from text, with the limitation documented in the method's docstring (schema
  migration for an opt-in, never-registered module is out of scope). Verified: real import
  (`from app.modules.experimental_agent.agent import *`) succeeds; `tool_registry.py` has zero
  references to `experimental_agent` (isolation confirmed). **Correction found 2026-07-18 (final
  critical review, see Methodology Note below) — "import succeeds" was not sufficient verification.**
  All 19 `self.memory.add_finding(..., severity=...)` call sites in `agent.py` would raise `TypeError`
  at runtime, silently swallowed by `_safe_step()` — the module recorded zero findings when actually
  run. Compounding this, `get_detailed_findings()`'s hardcoded `severity="Info"` meant `_build_result()`
  (which excludes Info/Low findings) would have returned an empty report even after the `TypeError` was
  fixed. Both fixed by finally doing the schema migration this task's own note deferred: `findings` now
  has a real `severity` column (schema v1→v2, idempotent `ALTER TABLE` migration guarded by
  `PRAGMA table_info`), `add_finding()` accepts `severity` (default `"Info"`, backward-compatible with
  every other existing caller), `get_detailed_findings()` returns the real value. Verified via full
  pytest (299/300, only the pre-existing unrelated failure), a direct smoke test of the
  add_finding/get_detailed_findings round trip, and a migration test against a copy of the real
  `data/argus_intelligence.db`. See commit `1309e5b`.
- [x] T015 [US1] [P] Port `momen`'s test content (`tests/test_argus_comprehensive.py`,
  `tests/test_xss_scanner.py`) into the pytest suite under `tests/` — do NOT port
  `tests/run_all_tests.py` (its custom runner is not adopted). **Run the `test-guard` skill** (added
  2026-07-18, `docs/ARCHITECTURE.md` §5) over the ported tests before landing — checks for mock abuse,
  duplicate tests, and implementation-detail assertions that a mechanical port can introduce.
  **Result**: opencode created `tests/test_ported_safety.py` (15 tests, real `SafetyLayer`/
  `ArgusMemory` — no test-guard violations, no mocks needed) and `tests/test_ported_xss.py` (7 tests).
  **test-guard caught a real violation** in the XSS file: it locally redefined the classification
  logic instead of testing production code (Rule 1/7). Fixed by extracting the real classifier to
  `app/tools/xss_classifier.py` (see T012) and pointing the test at the real import — same 7 tests,
  now exercising actual shipped code.
- [x] T016 [US1] Confirm `pytest -q` and app startup after the `momen` reconciliation — no
  regression vs. baseline; also verify the experimental agent is NOT reachable via the normal
  agent/tool-registry entry points (per its opt-in-only requirement). **Result**: 299 collected
  (0 errors), 298 passed / 1 failed (same pre-existing `test_smart_web_search` flake — 0 new
  regressions vs. the post-SALMA-merge baseline of 273/272). `scripts/run_argus_cli.py --help`
  reaches normal usage output. **Advisory, non-blocking check**:
  confirm each of T012's 8 per-file checklist items was actually reconciled against its named target
  (not just copied) — spot-check `memory.py`/`safety.py`/`schemas.py` specifically, since those were
  flagged as needing cross-comparison against existing content, not a blind port. Also run
  `clean-code-guard` over the re-homed files, same as T010. Commit.
- [x] T017 [US1] Discard `argus/MOUSTAFA-PC` entirely — no port needed (plan.md Synthesized Design
  Decision #4, resolved unanimously: its `app/core/memory/*.py` is a strictly inferior duplicate of
  `argus/SALMA`'s schema, and `ai_agents_aroject/` is unrelated side-project noise). No file changes;
  just confirm nothing from this branch is referenced anywhere in the working branch. **Result
  (2026-07-18)**: confirmed clean — zero references to `ai_agents_aroject` or its memory-store
  filenames (`database.py`/`target_store.py`/`finding_store.py`/`graph_store.py`/
  `summary_service.py`) anywhere in the working tree.
- [x] T018 [US1] Triage `argus/DESKTOP-BVV10T0` file-by-file against the working branch.
  *(Panel-resolved 2026-07-17: originally underspecified — "port if not already superseded" without
  saying what to look at. agy proposed splitting into a research sub-task + port sub-task; opencode
  disagreed, correctly noting research.md §3/§5 already did the research — citing it directly here is
  cheaper than a redundant research sub-task. Adopted opencode's fix.)* Context: two substantive
  commits exist on this branch — `cb2d0ad` ("feat: unify workspace with local-first workflow,
  self-healing bridge, and diagnostics tool") and `d09691b` ("feat: implement professional AI Agent
  Studio with modular core and master launcher") — **correction 2026-07-18: the commit-message-to-hash
  mapping in this file's earlier draft had the two swapped**; every other commit is an auto-generated
  "Intelligence Captured" snapshot — skipped. **Result (2026-07-18) — discard everything, evidence per
  candidate:**
  - `CHECK_HEALTH.bat` (cb2d0ad) — read in full: checks `.venv` (stale pre-rename path, predates the
    `Argus_venv` rename), Ollama process, WSL/Kali presence. Superseded by `ARGUS_INSTALLER.ps1`'s own
    embedded health check (runs automatically at the end of every install, per
    `Argus_Master_Documentation.md`).
  - `test_system_integrity.py` (cb2d0ad) — read in full: a print-based manual smoke script (no
    assertions, not a real pytest test), imports the already-discarded monolithic
    `core.tools.WSLBridgeTools`. Superseded by the real, assertion-based
    `tests/test_tools/test_reachability.py` already in the suite.
  - `core/tools.py`'s SSH self-healing (cb2d0ad, `_ensure_ssh_service`) — read in full: an early
    paramiko-based SSH-bridge-up check. Superseded by the already-merged (T007-T010)
    `app/tools/command_runner.py`, which has the same capability plus proper timeout handling
    (`_run_ssh`'s `channel.settimeout`) that this earlier version lacks.
  - Docker support (`Dockerfile`, `docker-compose.yml`, `docker/kali-core/`, cb2d0ad) — compared
    directly: base's `deploy/docker-lab/docker-compose.yml` docstring states it was "reconstructed +
    modernized from the historical origin/argus/SALMA:Agent_Containers/docker-compose.yml" for
    `specs/014-containerized-lab`, pins `ollama/ollama:0.3.14` for reproducibility. DESKTOP-BVV10T0's
    version uses `ollama/ollama:latest` (unpinned) with no spec/doc backing. Base's version is the
    more mature, deliberate one.
  - `AI Agent/` studio prototype (`argus_agent.py`, `argus_gui.py`, d09691b) — an early standalone
    GUI/agent prototype. Superseded by the canonical `app/GUI/dashboard.py` +
    `app/core/agent/` (already confirmed canonical during T012/T013).
  - Batch/shell installer scripts, `Discovery_cultbeauty_co_uk.txt` (empty), machine-specific WSL
    setup docs — discarded per Synthesized Design Decision #5 as already planned (doc content
    extraction happens separately at T027).
  No files ported; no file changes made by this task.
- [x] T019 [US1] Confirm `pytest -q` and app startup after the DESKTOP-BVV10T0 triage — no
  regression vs. baseline; commit. **Result (2026-07-18)**: 298 passed / 1 failed (unchanged from the
  post-T012-T016 state — expected, since T018 made no file changes), `run_argus_cli.py --help` reaches
  normal usage output. Nothing to commit for this task (pure triage, no diff).

**Checkpoint**: All branches classified "feature work to merge" are now folded in; app starts;
pytest passes at ≥ baseline. This is the MVP — the codebase is functionally unified even before
Phase 4/5's installer and history-preservation polish.

---

## Phase 4: User Story 2 - Preserve a Recoverable History of Each Contributor's Original Work (Priority: P2)

**Goal**: Prove that every original branch survived Phase 3's merges/ports untouched and is still
independently retrievable.

**Independent Test**: `git branch -a` / `git tag` shows every one of the 9 original branches (or a
`pre-merge/*` tag pointing at its original tip) still resolvable; `git show <branch>` works for all 9.

### Implementation for User Story 2

- [x] T020 [P] [US2] Verify all 9 original branches from T001's baseline are still present and
  `git log <branch>` / `git show <branch>:<any file>` still resolves for each — compare directly
  against the T001 recorded list, not from memory. **Result (2026-07-18)**: all 9 tips match
  `baseline-2026-07-18.md` exactly, byte-for-byte SHA comparison, zero drift.
- [x] T021 [P] [US2] Verify all `pre-merge/*` tags from T002 still point at their original commits
  (unchanged SHAs). **Result**: all 9 tags verified identical to their branch tips via full-SHA
  `git rev-parse` comparison.
- [x] T022 [US2] For every `Conflict Decision` recorded in T008/T009, confirm the losing side's
  content is still reachable via the original branch (spec.md FR-003's acceptance scenario 2 — a
  contributor must be able to see exactly what changed and why). **Result**: confirmed retrievable —
  SALMA's `app/GUI/app.py` (203 lines), `scripts/LAUNCH_STUDIO.bat` (90 lines), flat
  `app/core/agent_factory.py` (124 lines), and momen's discarded `core/agent.py`/`core/tools.py`/
  `core/memory.py` (490/1909/353 lines) — all still resolve via `git show <branch>:<path>`.

**Checkpoint**: History-preservation guarantee is verified, not just assumed — spec.md SC-003 (100%
of original branches retrievable) is demonstrably true.

---

## Phase 5: User Story 3 - Single Installer and Documentation Set After Unification (Priority: P3)

**Goal**: Exactly one installer entry point remains, and top-level docs are accurate and current.

**Independent Test**: `scripts/` contains only `ARGUS_INSTALLER.ps1` (no `INSTALL_EVERYTHING.ps1`);
a fresh install run on a clean environment completes and passes its embedded health check.

### Implementation for User Story 3

- [x] T023 [US3] Port `argus-recovery/master`'s `.specify/` and `.opencode/` toolchain directories
  into the working branch (additive, no conflict expected per research.md §3). **Correction found
  2026-07-18**: research.md §3's claim that "plain `main` lacks [this] entirely" was accurate for
  `main`, but the actual working base (`fix/copy-setup-to-scripts`) already has its own `.specify/`/
  `.opencode/` — and it is the **more evolved** of the two (constitution v1.3.0 with a later-added
  "Traceable Commit Discipline" principle, vs. `argus-recovery/master`'s v1.0.0 initial ratification).
  Cross-checked every filename in `argus-recovery/master`'s toolchain against the working tree's
  tracked `.specify`/`.opencode` files (`git ls-tree`, excluding `node_modules`) — zero files unique
  to `argus-recovery/master`. **No port needed; base's toolchain already supersedes it.**
- [x] T024 [US3] Quarantine `Argus_Secure_Sync.exe`. *(Panel-resolved 2026-07-17: both agy and
  opencode independently and strongly agreed a hash is essential, not ceremony — added below.)*
  **Correction 2026-07-18: the file is not actually in the working tree.** It exists only on `main`
  (SHA-256 `9DC1CF296465CC8BDC87CA2EF229336AEADF6D1DF39973CEFF278AEE87D985BA`) and
  `argus/DESKTOP-BVV10T0` (SHA-256 `2EA4A58E82A5BCA799725564CBC1CB12C7B08896869F51808F102F0B3A283A9`
  — a **different hash, different size** — two distinct binaries sharing a filename, itself worth
  flagging). The working base (`fix/copy-setup-to-scripts`) never had this file, and T018/T019 already
  decided nothing from `DESKTOP-BVV10T0` gets ported — so no quarantine action was needed on the
  working tree (creating `security_review_required/` for a file that isn't there would be speculative
  ceremony, not a real safeguard). **This finding is recorded here instead** so it isn't lost: if
  `main` is ever merged into this unified branch later, or anyone manually copies either file in,
  it MUST go through this same quarantine treatment first (SHA-256 recorded, source branch noted,
  excluded from the installer, flagged for human security review) — do not silently let a "no file to
  quarantine" outcome be read as "the binary is cleared."
  **Disposition update 2026-07-18**: the human (project owner, not a review of provenance/signing/
  malware-scan evidence) decided `main`'s copy is no longer needed and should be removed outright,
  independent of issue #1's still-open security review. Removed via a dedicated commit `9c7a7f0` on
  `main` directly (`git rm Argus_Secure_Sync.exe`, pushed `b563f73..9c7a7f0`). **Scope: `main` only** —
  `argus/DESKTOP-BVV10T0`'s copy was explicitly left untouched (archival branch, preserving original
  contributor work per this feature's whole SC-003/history-preservation goal - deleting from that
  branch was never requested and would contradict that goal). Issue #1 remains open for
  DESKTOP-BVV10T0's copy and to document this disposition for `main`'s copy.
- [x] T025 [US3] Confirm `scripts/INSTALL_EVERYTHING.ps1` is absent from the working branch — it
  should be, since the working branch is created from `fix/copy-setup-to-scripts` (T003), which
  never had this file (only `main` does — corrected 2026-07-17, see research.md §4). If a later merge
  step re-introduces it (e.g. via a conflict resolution that pulls in `main`'s version), remove it so
  `scripts/ARGUS_INSTALLER.ps1` remains the sole installer. Update the top-level `README.md`'s Quick
  Start to reference only `ARGUS_INSTALLER.ps1`. *(Panel-resolved 2026-07-17: both
  agy and opencode flagged this task as incomplete on its own — `fix/copy-setup-to-scripts`'s own
  `specs/002-consolidated-installer/tasks.md` T016/T017 call for updating `Setup/README.md` and
  `scripts/README.md` too, but those may already be done on the base branch. opencode's framing —
  check, don't blindly redo — was adopted over an unconditional rewrite.)* THEN check whether
  `Setup/README.md` and `scripts/README.md` already reference `ARGUS_INSTALLER.ps1` exclusively (they
  may already be correct, inherited from the base branch). If NOT, update them; if already correct,
  no further action needed there. **Result (2026-07-18)**: confirmed — `INSTALL_EVERYTHING.ps1` is
  absent; `README.md`, `Setup/README.md`, and `scripts/README.md` all already reference
  `ARGUS_INSTALLER.ps1` exclusively (inherited correct from the base branch). No changes needed.
- [~] T026 [US3] **CLOSED as deferred/waived 2026-07-18 — not equivalent to the original requirement,
  see resolution below.** Originally: close
  `fix/copy-setup-to-scripts`'s own open installer tasks T013/T014: run
  `scripts\ARGUS_INSTALLER.ps1 -DryRun` then a real run in a **Windows Sandbox or disposable VM**
  (plan.md Synthesized Design Decision #3) — confirm the embedded health check passes and a second
  run shows idempotent skip behavior. **Attempted 2026-07-18**: even `-DryRun` self-elevates
  (`ARGUS_INSTALLER.ps1`'s own design requests Administrator via UAC before doing anything else,
  dry-run or not). A UAC consent prompt cannot be clicked through non-interactively, and this session
  has no Windows Sandbox/VM to target even if it could — both the DryRun smoke-test and the real
  sandboxed run need a human to actually run this one interactively. **Independent verification via
  `mcp-kali-server`** (added 2026-07-18, per `docs/ARCHITECTURE.md` §6.2 — corrected, was §5.2 before
  guard-skills §5 was inserted): don't rely solely on the installer's own self-reported
  health check — after the sandboxed install completes, use the `mcp-kali-server` MCP tool to
  actually invoke `nmap`, `gobuster`, and `nikto` against a local/loopback target and confirm each
  returns real output, not just an "installed" flag. This is a second, independent witness that the
  Kali-side toolchain the installer set up is actually callable, not just present on disk.
  **Partial progress 2026-07-18**: human ran `scripts\ARGUS_INSTALLER.ps1 -DryRun` interactively,
  clicked through UAC, **on the main dev machine directly (not a Sandbox/VM)** — succeeded with no
  errors or warnings. This confirms the UAC/dry-run mechanics work and the dry-run path is clean, but
  does **not** satisfy this task's actual requirement: a real (non-dry-run) install in a genuinely
  clean **Windows Sandbox or disposable VM**, which is the point of Synthesized Design Decision #3 —
  validating against an environment that hasn't accumulated this project's own dev-machine state,
  which a host-machine run (dry or real) cannot do. **Still open**: (1) a real install run in an
  actual Sandbox/VM, (2) its embedded health check passing, (3) a second run showing idempotent skip
  behavior, (4) the `mcp-kali-server` independent Kali-toolchain check above.

  **Resolution 2026-07-18 — three-way discussion (orchestrator + codex; agy quota-exhausted, see
  memory `feedback_three_way_consensus_required.md`), human decision**: no Windows Sandbox or VM is
  available on this machine at all. Checked directly: `WindowsSandbox.exe` is absent, and
  `Get-WindowsOptionalFeature` itself failed with a DISM-level "Class not registered" error rather
  than a normal "not enabled" result — consistent with this machine being a VM without nested
  virtualization exposed, or a broken servicing stack; either way, not something fixable in this
  session. codex's independently-reasoned position (see below) matched the orchestrator's own: don't
  silently treat the host dry-run as equivalent (option a), but also don't block T031 indefinitely over
  unavailable test infrastructure (option c) — accept the host-machine `-DryRun` as partial evidence
  only, with the gap explicitly disclosed rather than hidden. A GitHub Actions Windows runner was
  considered as a cheap alternative but not pursued: this installer's WSL2/Kali provisioning and
  self-elevating UAC relaunch are unlikely to complete cleanly in a hosted CI runner, and a
  CI-specific failure there would be hard to distinguish from a real installer defect - not worth the
  false-signal risk for this decision. Human explicitly decided to close this task now on that basis.

  **What this task is actually attesting, going forward**: `-DryRun` succeeded cleanly, interactively,
  with UAC, on the dev machine. The real (non-dry-run) install, its embedded health check, idempotent
  re-run behavior, and the `mcp-kali-server` independent Kali-toolchain check were never performed on a
  clean environment and remain factually unvalidated - this must be stated plainly in the eventual T031
  PR description (per the reconciled plan already drafted for T031), not glossed over. If a genuine
  clean-environment run ever becomes possible later (e.g. Windows Sandbox starts working, or a real VM
  becomes available), that would still be the strictly better validation and should be done before any
  release/distribution decision that assumes the installer works on a fresh machine - closing this task
  now is a scoping decision for this PR, not a claim that the underlying risk was addressed.
- [x] T027 [US3] Extract the resolved doc content from `argus/DESKTOP-BVV10T0` (plan.md Synthesized
  Design Decision #5) into `Argus_Master_Documentation.md`: Win-KeX GUI-mode WSL access instructions,
  the WSL management command cheat-sheet, the HuggingFace GGUF model-sourcing table, and LM Studio
  (port 1234) as an alternative model provider — first verify the cited HuggingFace repo paths are
  still live and confirm the team wants LM Studio documented as a supported provider. Run
  `docs-guard` (added 2026-07-18, `docs/ARCHITECTURE.md` §5) over the extracted content — checks that
  it doesn't reference commands/paths that don't exist in the unified branch. **Result (2026-07-18)**:
  added §2.2.1 (GGUF table, explicitly flagged "not re-verified live at port time" — no network check
  performed), §2.2.2 (LM Studio, explicitly flagged as unconfirmed/optional pending team decision,
  not presented as endorsed), §4.3 (WSL cheat-sheet), §4.4 (Win-KeX). docs-guard check: every
  referenced command (`wsl --shutdown`, `kex --win -s`, etc.) is a real WSL/Kali command, not a
  project-specific path that could be wrong.
  **Currency re-check 2026-07-18** (final comprehensive audit, web search): all three GGUF HuggingFace
  repo paths in §2.2.1 confirmed live via web search — `bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF`,
  `bartowski/Llama-3.1-WhiteRabbitNeo-2-70B-GGUF`, `TheBloke/WhiteRabbitNeo-13B-GGUF` all resolve to real,
  existing repositories. The "not re-verified live at port time" caveat in §2.2.1 can now be considered
  resolved — this is the actual verification that was deferred.
- [x] T028 [US3] Delete `argus/DESKTOP-BVV10T0`'s superseded batch/shell scripts and the empty
  `Discovery_cultbeauty_co_uk.txt` from anywhere they'd otherwise land in the working branch (nothing
  to port — confirm they were never copied in T018). **Result**: confirmed clean. (Two files with
  coincidentally similar names — `Setup/Step_1_Core_Foundation.bat`, `Setup/Step_2_AI_Python_Env.bat`
  — exist on the working branch, but `git log` on both traces them to the base branch's own initial
  commit and later trunk history, unrelated to DESKTOP-BVV10T0's `01_Infrastructure_Setup/`/
  `02_AI_Environment/`-prefixed files of the same base name — not contamination.)

**Checkpoint**: Exactly one installer entry point, validated on a clean environment; docs updated;
Constitution Principle IV fully satisfied (not just "addressed by design" as in the Plan's
Constitution Check).

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Final cross-story validation before this feature is considered done.

- [~] T029 Run `quickstart.md`'s full "Final acceptance" table end-to-end against the finished
  working branch (maps every spec.md Success Criterion SC-001..SC-005 to a concrete check).
  **Result (2026-07-18)**:
  - SC-001 (all 9 contributor branches classified) — ✅ PASS, research.md §3.
  - SC-002 (unified branch starts on first attempt) — ✅ PASS, `run_argus_cli.py --help` reaches
    normal usage output.
  - SC-003 (0 branches deleted/force-overwritten) — ✅ PASS, T020-T022.
  - SC-004 (exactly one installer entry point) — ✅ PASS, only `scripts/ARGUS_INSTALLER.ps1` exists.
  - SC-005 (100% conflict rationale coverage) — ✅ PASS, every decision in T007-T028 has a recorded
    one-line rationale in tasks.md/commit messages.
  - **T026 (installer sandbox validation) closed as deferred/waived 2026-07-18, not fully satisfied**
    — no Windows Sandbox/VM was available on this machine (confirmed, not just untried; see T026's
    Resolution note). SC-002/SC-004 pass on this dev machine, and `-DryRun` succeeded cleanly, but the
    clean-environment install claim from T026's original requirement remains factually unvalidated —
    this is a disclosed, accepted gap (human decision, 2026-07-18), not a resolved PASS. **T029 stays
    marked partial, not fully done** — the underlying SC-002 evidence is dev-machine-only, which is
    weaker than the spec's clean-environment intent, even though the human has decided this is
    sufficient to proceed to T031. T031's PR description must state this plainly.
- [x] T030 [P] Grep every remaining branch/worktree for non-empty scan-output files against
  third-party domains (research.md §7's reminder, prompted by the `Discovery_cultbeauty_co_uk.txt`
  false alarm) — Constitution Principle I final check before closing this feature. **Result**:
  checked the working tree (`reports/`, `data/`) and all 9 original branches by filename pattern —
  the only hit anywhere is the already-known, already-excluded, empty `Discovery_cultbeauty_co_uk.txt`
  on `argus/DESKTOP-BVV10T0`. Clean.
- [x] T030b [P] Open a tracking issue for the deferred `Argus_Secure_Sync.exe` security review (T024) —
  link the two recorded SHA-256 hashes, so the still-open decision isn't only visible to someone
  reading this repo's files (added 2026-07-18, per `docs/ARCHITECTURE.md` §6.1). **Correction
  2026-07-18: switched from the `github` MCP to `gh` CLI.** The `github` MCP failed with a protocol-level
  error (`Incompatible auth server: does not support dynamic client registration`), not just a pending
  approval — this is an endpoint limitation, not something a retry fixes. `gh` CLI is already
  authenticated as `PhilopaterSh` with `repo`/`workflow` scopes; human explicitly approved this fallback.
  **Result (2026-07-18)**: opened, human gave explicit "yes, open it" authorization first —
  https://github.com/PhilopaterSh/Argus-Digilians/issues/1. Body includes both SHA-256 hashes/sizes, the
  requested-review checklist (provenance/signing/malware-scan/disposition), and an explicit note not to
  characterize either binary as malicious from hash mismatch alone.
  **Planning session held 2026-07-18** (orchestrator + codex, read-only; see Methodology Note above) —
  drafted the actual issue title/body (context table with both SHA-256 hashes + sizes, a requested-review
  checklist covering provenance/signing/malware-scan/disposition, explicit note not to characterize
  either binary as "malicious" from hash mismatch alone since that's identity ambiguity, not evidence of
  compromise). agy was also dispatched for this same planning question but went off-brief and made
  unauthorized destructive edits to unrelated files instead of answering (see Methodology Note above) —
  did not contribute to this plan. **New standing rule set by the human 2026-07-18** (see memory
  `feedback_three_way_consensus_required.md`): no decision from a multi-delegate discussion round is
  acted on unilaterally — all dispatched parties must explicitly agree first, and a dropped/failed
  delegate must be flagged, not silently worked around. Per that rule, agy was re-dispatched a second
  time for this same question, in a dedicated isolated worktree (`branches/agy-planning-scratch`, since
  removed) with all needed context embedded directly in the brief (to rule out the shared-tree/
  broad-exploration factors from the first failure). **Result: agy hit a real, explicit quota wall**
  ("Individual quota reached... Resets in 166h14m50s", ~7 days, ≈2026-07-25) — confirmed not a
  transient error this time. Human explicitly authorized proceeding on orchestrator + codex agreement
  alone for this plan, with the agy gap disclosed here rather than silently worked around, per the new
  rule.
- [x] T031 Open a PR (or merge `unify/027-merge-branches` into `main`) only after T029 and T030 both
  pass; this is the first point at which the unified branch is proposed to replace `main`. **Correction
  2026-07-18**: use `gh` CLI instead of the `github` MCP (see T030b's correction - same root cause).
  Reference this feature's spec/plan/tasks and link the T030b tracking issue. **Status update
  2026-07-18**: T030b is open (issue #1). T026/T029 are closed as deferred/waived, not a clean PASS —
  human explicitly decided this is sufficient to proceed rather than wait on unavailable test
  infrastructure (see T026's Resolution note). T031 is otherwise ready to open, pending only: opening a
  PR is a visible, shared-repo action requiring explicit human "yes, open it" authorization, not implied
  by tooling/prerequisites being ready.
  **Planning session held 2026-07-18** (orchestrator + codex, read-only) — drafted the actual PR
  title/body (validation-status section citing T029's table, a section disclosing the three
  final-critical-review fixes from commit `1309e5b` framed as "already included," a section on
  `experimental_agent`'s opt-in/unregistered status, a reviewer checklist). **Sequencing decision,
  orchestrator + codex agreed (independently, before comparing notes) — do not open T031, not even as a
  draft, until T026 actually completes and T029 can be marked fully passing.** Reasoning: T031 has an
  explicit task gate ("T029 and T030 both pass"); even a draft PR opens the gated work item, creates
  reviewer/notification pressure, and risks making an incomplete installer validation look
  administratively accepted. The useful parallel work (drafting title/body/checklist, done above) doesn't
  require actually opening anything.

  **Result (2026-07-18)**: opened after explicit human authorization —
  https://github.com/PhilopaterSh/Argus-Digilians/pull/2 (branch pushed via
  `git push -u origin unify/027-merge-branches` first, no prior remote copy existed). **Note on the
  sequencing decision above**: the original orchestrator+codex agreement was to wait for T026 to
  *actually complete* before opening anything — that didn't happen. Instead, T026 was closed as
  deferred/waived (no Sandbox/VM available on this machine, confirmed not just untried) and the human
  explicitly decided this was sufficient to proceed rather than continue waiting on unavailable test
  infrastructure - a deliberate override of the original sequencing plan, not a silent skip. The PR body
  discloses this gap plainly (see its "Validation status" and "Outstanding gap" sections) so reviewers
  see the same information this decision was based on, not a laundered "all green" status. Body includes:
  T029's SC-001..SC-005 table with the T026 gap called out, the T030b issue link (#1), all three
  `1309e5b` fixes disclosed as already-included corrections, `experimental_agent`'s opt-in/unregistered
  status, and a reviewer checklist covering all of the above.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Phase 1 (needs the working branch to measure a baseline on).
- **US1 (Phase 3)**: Depends on Phase 2's baseline. This is the MVP — nothing else in the plan matters
  if this phase fails.
- **US2 (Phase 4)**: Depends on Phase 1's tags/baseline list, and on Phase 3 having actually run (it's
  verifying Phase 3 didn't destroy anything) — cannot run meaningfully before Phase 3, despite being
  conceptually independent content.
- **US3 (Phase 5)**: Depends on Phase 3 (needs `fix/copy-setup-to-scripts`'s installer already present
  on the working branch, which it is from Phase 1's branch-creation point) — can technically start in
  parallel with Phase 3/4's later tasks, since T023–T028 don't touch `app/`.
- **Polish (Phase 6)**: Depends on Phases 3, 4, and 5 all complete.

### Parallel Opportunities

- T003/T004 (Phase 1) — different concerns, no shared files.
- T014/T015 (Phase 3) — different target files (`app/modules/experimental_agent/` vs `tests/`).
- T020/T021 (Phase 4) — independent verification checks.
- Phase 5 (US3) can run concurrently with Phase 3/4 once Phase 1 completes, since it doesn't touch
  `app/core/`/`app/GUI/` — a second contributor could pick it up while US1 is in progress.

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 (Setup) + Phase 2 (Foundational baseline).
2. Complete Phase 3 (US1) — this alone is a working, unified codebase.
3. **STOP and VALIDATE** with quickstart.md's per-step checks before proceeding.

### Incremental Delivery

1. Phase 1+2 → working branch with a measured baseline.
2. Phase 3 (US1) → functionally unified codebase (MVP).
3. Phase 4 (US2) → proof nothing was lost.
4. Phase 5 (US3) → one installer, accurate docs.
5. Phase 6 → final cross-cutting acceptance, then propose merging to `main`.

## Notes

- Every task above cites the plan.md/research.md decision it implements — if a task's rationale is
  unclear, that citation is where to look, not this file.
- The single still-open, non-technical decision (`Argus_Secure_Sync.exe`'s ultimate fate) is
  explicitly NOT resolved by T024 — quarantining it is the safe default while a human completes the
  security review; T024 must not be read as "this file is fine."

## Methodology Note (2026-07-17): External Research Validation Round

Before implementation, the orchestrator (Claude) researched external git merge best practices
(git-scm.com docs, Atlassian tutorials, academic literature on semantic merge conflicts) to sanity
check whether this plan's methodology was sound, specifically around not silently losing a feature or
missing a conflict git itself wouldn't flag. Three proposals were put to opencode for review (agy was
unavailable — quota exhausted mid-session, see project memory `agy_delegate_quota_limits.md`):

1. **Enable `git rerere`** — **Rejected.** opencode's argument, which the orchestrator found
   persuasive on review: this plan has exactly one real `git merge` (T007, `argus/SALMA`); every
   other branch is reconciled by manual file-level port/triage, not repeated merges. rerere's value
   is proportional to *recurring* identical textual conflicts, which this one-time, fixed-sequence
   plan doesn't have — and it risks silently replaying an old resolution onto a superficially similar
   but semantically different future conflict. The human-written Conflict Decision log (FR-003)
   already does the job better, since it records *rationale*, not just a mechanical patch.
2. **Semantic-duplication check at each test gate** — **Adopted, in modified form.** opencode
   improved on the original proposal: instead of a noisy generic `class`/`def` grep (false-positives
   on `__init__`, `run`, `setup`), cross-reference new/ported files by filename stem against existing
   target-directory contents — directly targeting the rename-detection failure mode (research.md/
   plan.md's T007 risk) with far fewer false positives. Added as an explicit **advisory, non-blocking**
   step in T010 and T016 — deliberately not a hard gate, since common short filenames will still
   produce some noise.
3. **`git bisect --first-parent` as a designated Phase 6 regression-diagnosis procedure** —
   **Rejected.** opencode's argument: `git bisect` needs an automatable pass/fail test at every
   candidate commit, which this plan doesn't produce; and since every integration step already ends
   in its own gated, committed checkpoint (T010/T016/T019), a late regression has only 3-4 candidate
   commits to inspect by hand (`git log --oneline`, `git diff`) — formalizing a bisect procedure for
   a 3-4-commit range adds ceremony without adding diagnostic power over what the per-step gates
   already provide. The orchestrator agreed this was closer to "procedure masquerading as
   accountability" than a real safety improvement, and did not add it.

## Methodology Note (2026-07-18): Final Critical Review Before T031

Before proposing the unified branch to replace `main` (T031), the orchestrator dispatched an
independent code-correctness review of the full diff (`fix/copy-setup-to-scripts..unify/027-merge-branches`,
17 files, ~4,966 insertions) to agy and codex-delegate in parallel (read-only mode where the CLI
supports it), on top of the orchestrator's own direct verification of every finding — continuing this
feature's established three-way (here, effectively three-of-four, see below) review practice one more
time before closing out. opencode-delegate was also dispatched but hung twice (~68 minutes with zero
events logged on the first attempt; killed by re-dispatching a fresh run rather than force-killing the
stuck process, per this session's own risk-of-harm norms around destructive actions) and never produced
output — proceeded without it rather than block indefinitely. agy also needed three retries past a
transient "high traffic" server error before succeeding, and one dispatch required
`--dangerously-skip-permissions` (explicitly authorized by the human first) since headless mode
otherwise auto-denies the shell/command permission agy needs to actually read a diff.

**Confirmed real, fixed** (both agy and codex independently found the core issue; orchestrator verified
by direct grep/trace/smoke-test before accepting):
- `app/modules/experimental_agent/agent.py` — `add_finding(..., severity=...)` signature mismatch
  (19 call sites, `TypeError` at runtime, swallowed by `_safe_step()`). See T014's Correction note.
- `app/tools/xss_classifier.py` — encoded-payload false positive. See Open Follow-Ups below.

**Confirmed real, fixed, agy-only** (codex's review did not catch these; orchestrator independently
verified each before accepting — codex's own report explicitly listed "no additional finding" for
`command_runner.py` and didn't examine `get_detailed_findings()`'s severity-filter interaction):
- `get_detailed_findings()` hardcoding `severity="Info"` combined with `_build_result()`'s Info/Low
  exclusion — a second, compounding bug that would have kept the report empty even after the
  `add_finding()` crash was fixed. Orchestrator confirmed by reading both functions directly.
- `command_runner.py`'s `bash -lc` login-shell flag. Orchestrator confirmed by `git diff`/`git show`
  tracing the change to an unmodified carry-over from `argus/SALMA`'s original content.
- `test_smart_web_search.py::test_attempt_limit`'s true cause (not a network flake). Orchestrator
  confirmed by grep — zero attempt-limit references anywhere in `app/tools/web_search.py`.

**Investigated and rejected** — codex's claim that the T011 `\/`→`\\/` escape-sequence fix in
`llm_engine.py` changes the payload's runtime string value. The orchestrator wrote a standalone script
to compare both literals' `repr()` under the actual project interpreter: both evaluate to the identical
28-character string. agy, independently asked to verify the same fix, reached the same conclusion the
orchestrator did (correct, unchanged) — a case of one delegate simply being wrong and the discrepancy
only surfacing because a second independent reviewer (plus the orchestrator's own empirical check) was
in the loop, consistent with this feature's established pattern of delegates occasionally being wrong
and correcting via cross-verification rather than being trusted individually.

All fixes landed in commit `1309e5b`, verified against the full pytest suite (299 passed / 1
pre-existing unrelated failure) plus targeted smoke/migration tests. See T014's Correction note and the
updated Open Follow-Ups section below for the technical detail on each.

**Addendum, 2026-07-19 - the delayed fourth reviewer was right to wait for.** This section originally
noted opencode hung for ~68 minutes with zero output and was worked around by dispatching a fresh run
without it (see the original four-way review dispatch above). Both the original stuck dispatch and its
replacement eventually completed hours later, independently of each other, and **both found the same
two real, previously-uncaught blocking bugs** in `app/modules/experimental_agent/agent.py` that neither
agy, codex, nor the orchestrator's own pass had caught:
- `agent.py:1355,1392` - `_adaptive_xss()`/`_adaptive_sqli_blind()` called `_collect_xss_targets()` with
  zero arguments against a signature requiring a mandatory `r` parameter - `TypeError` on every
  invocation, silently swallowed by `_safe_step()`, making the LLM-driven adaptive-retry path for
  XSS/blind-SQLi entirely dead code.
- `agent.py:997,1151` - `_session_get_no_redirect()`/`_step_xxe()` called `self._session.get()/.post()`,
  but `ArgusPipeline.__init__` never sets `self._session` anywhere - `AttributeError` on every
  SSRF/open-redirect/XXE detection attempt, same silent-swallow pattern.

Both independently verified by the orchestrator (direct call tracing the exact `TypeError`/
`AttributeError`; a real network smoke test after fixing) before accepting either finding. Fixed in
commit `3361d89`. **Why this matters methodologically**: this project's whole three/four-way review
practice exists because a single reviewer - including the orchestrator itself - reliably misses things
a second independent pass catches. This is the starkest example yet: two *separate* opencode runs, sent
hours apart, converged on the exact same two bugs that three other review passes (agy, codex, and the
orchestrator's own direct reading of this file) had all missed. The instinct to route around a slow/
stuck delegate rather than wait for it is usually right for keeping a session moving, but the value the
slow response eventually delivered here is itself an argument for not fully discarding a hung dispatch's
output once it does land - reading it costs little, and discarding it unread would have left two real
security-detection paths (SSRF/XXE/SQLi/XSS-retry) permanently dead in code purporting to test for
exactly those things.

**Second incident, same session, T030b/T031 planning round**: a follow-up read-only planning dispatch
(draft the T030b issue body and T031 PR body, and get a sequencing recommendation) was sent to agy and
codex in parallel against the same shared `Argus-Digilians` working tree. agy ignored the brief entirely
and instead deleted four real, tracked files (`Setup/README.md`, `Setup/Step_1_Core_Foundation.bat`,
`Setup/Step_2_AI_Python_Env.bat`, `Setup/requirements.txt`) and created an untracked `Setup_legacy/`
directory containing copies of them — an unrequested, unauthorized, destructive "reorganize the legacy
installer" action with no connection to the planning question asked, most likely a hallucinated task
(possibly conflated with `specs/002-consolidated-installer`'s unrelated installer-consolidation work).
Caught immediately by reviewing `git status` before accepting anything from the dispatch (per this
project's standing "review, don't accept the self-report" practice) — reverted in full
(`git checkout --` on the four files, delete the stray directory), confirmed clean tree, human explicitly
authorized both the revert and the deletion of the stray directory first. Because agy ran without a
proven read-only mode against a tree codex was concurrently reading, codex's own diff report picked up
agy's stray changes too, even though codex itself (running `--read-only`) never touched anything —
illustrating why concurrent delegates should not share a live working tree when even one of them lacks
an enforced read-only mode. codex separately could not access `specs/027-merge-branches/` at all (it
lives one directory above `Argus-Digilians/`, outside codex's `--cd`-scoped sandbox) and said so plainly
rather than inventing plausible-sounding content for the parts it couldn't verify (the T024 hashes, the
three bug descriptions) - flagged as a genuine positive: it distinguished between what it could and
couldn't verify instead of filling the gap with a guess. Proceeded on orchestrator + codex agreement for
the actual planning content; agy did not contribute a usable answer to the question asked.

## Methodology Note (2026-07-18): Final Comprehensive Audit (post-merge, after PR #2 was already open)

Requested by the human after PR #2 was opened: not another diff review, but a fresh spot-check of
*past* discard/port judgments across the whole unification effort - the concern being whether any
branch's "superseded, nothing worth porting" call was actually wrong, silently losing something real.
Orchestrator and codex worked the same three items independently (agy still quota-exhausted, ETA
~2026-07-25) and compared notes after, not before - genuine independent corroboration, not one
reviewer confirming the other's framing.

**Mechanical re-checks, orchestrator, all clean**: all 9 branches still resolve to their original SHAs,
fresh full pytest run (299/300, same known failure), fresh app startup, no stray scan-output files.

**Judgment spot-checks (both reviewers, independently)**:
1. `momen:core/memory.py` vs HEAD's `memory_service.py` — **did not hold up**. Both reviewers found the
   same three missing capabilities independently before comparing notes (see T012's Correction note
   above for detail and the fix). codex additionally found a live artifact of this gap: HEAD's own
   `app/core/prompts.py:52` still instructs an agent to use "Get_Priority_Targets" as a tool, which
   doesn't exist anywhere in the unified codebase - traced further by the orchestrator and found to be
   inside dead code (`app/core/prompts.py`'s whole prompt system was superseded by
   `react_prompts.py`'s PHASE 1-9 structure on 2026-07-10, per that file's own comments, well before
   this feature started) - a real inaccuracy in unused legacy text, not a live production bug. Not
   fixed (out of scope - fixing dead legacy prompt text is a different task than porting the missing
   data capabilities, which was the actual, in-scope gap).
2. `argus/MOUSTAFA-PC`'s memory-store files vs HEAD - **held up**. Both reviewers confirmed HEAD's
   `memory_service.py` genuinely covers every capability MOUSTAFA-PC's `TargetStore`/`FindingStore`/
   graph-store files had, plus a safer `clear_memory()` (backup-and-restore vs MOUSTAFA-PC's outright
   DB-file deletion). No port needed - T017's original decision was correct.
3. `argus/DESKTOP-BVV10T0`'s SSH self-healing vs HEAD's `command_runner.py`/`wsl_bridge.py` - **held
   up**. codex confirmed HEAD retains the same self-heal recovery path under the same lock, and
   improves on the original's unbounded `stdout.read()`/`stderr.read()` with real channel timeouts and
   `socket.timeout` handling. Explicitly re-verified with fresh eyes rather than assumed correct just
   because it was already written down, given `command_runner.py` had a real, unrelated bug found
   earlier this same session (the `bash -lc` login-shell issue, already fixed) - re-checking a file
   that already had one confirmed bug for a second, different issue was worth the extra scrutiny, and
   came back clean.

**Currency re-checks, orchestrator, via web search**: all three HuggingFace GGUF repo paths in
`Argus_Master_Documentation.md` §2.2.1 (added by T027, explicitly flagged "not re-verified live at
port time") confirmed live. `duckduckgo-search`'s rename to `ddgs` (visible as a `RuntimeWarning` in
every pytest run touching `web_search.py`) confirmed real via web search - not fixed (pre-existing on
the base branch, unrelated to this feature's scope, purely a dependency-currency note for whoever
next touches `requirements-dev.txt`).

**Holistic conclusion**: the blanket claim "every branch was correctly classified and every discard
was genuinely justified" did NOT fully hold - one real, now-fixed gap (momen's memory.py). The other
two spot-checked discard decisions held up under fresh, independent scrutiny. Fixed in commit
`4fe3ad2`, pushed to PR #2.

## Methodology Note (2026-07-18): First-Ever CI Run on PR #2 - What Got Fixed, What Got Disclosed

Merging `main` into the PR branch to resolve a merge conflict (README.md's stale installer name,
see the merge commit `d5a2242`) triggered, for the first time, actual execution of
`.github/workflows/ci.yml` with a real `origin/main` base (zero prior runs existed on `main` before
this). This surfaced a series of pre-existing gaps - none caused by this feature's own
branch-unification work, all things this PR happened to be the first to actually exercise:

**Fixed** (mechanical, no real judgment call, each independently verified before committing):
- `lint-type`: 2 real mypy errors in `app/core/agent/brain.py`, confirmed via `git blame` to have
  been introduced by the SALMA merge (T007-T010), not pre-existing on the base branch - genuinely
  in scope. Commit `58bd0fc`.
- `unit-tests`/`full-tests`: bare `pytest` (CI's actual invocation) doesn't add the repo root to
  `sys.path` the way `python -m pytest` (every local verification command used this whole session)
  does - added `pythonpath = .` to `pytest.ini`. Commit `400691c`.
- `pester-test`: legacy Pester v3/v4 syntax, CI runner has v5 - migrated all 13 assertions,
  verified locally by installing Pester 5.6.1 and running the file directly (9/9 pass). Commit
  `2d5925f`.
- `spec-doc-validation` (structure): blanket 6-artifact-per-feature requirement retroactively
  failed on 10 unrelated historical specs (016-026). Panel discussion (orchestrator + codex)
  concluded: don't fabricate design content to satisfy a paperwork check - made the validator
  status-aware instead (Draft needs only spec.md; Proposed/Implemented need a core four plus
  explicit N/A declarations for genuinely-inapplicable conditional artifacts). Real retrospective
  backfill for `017` (content already existed in `specs/checklist.md`, just not in the expected
  files) and a real `data-model.md` for `018` (documents the actual `SecurityReport`/`Finding`
  schema, sourced from `app/core/schemas.py`, not invented). Commit `5ac808b`.
- `spec-doc-validation` (ASCII): 2,677 non-ASCII bytes (box-drawing banners, em-dashes, arrows) in
  comments/docstrings across files ported earlier this session (momen's T012/T014/T015 content).
  Mechanical, verified-safe character substitution - double-checked the one place this could have
  mattered (the T011 escape-sequence fix in `llm_engine.py`) was untouched. Commit `7bc80bf`.

**Disclosed, not fixed** (genuine panel disagreement, resolved with real data, not assumption):
- `lint-type`'s docstring-compliance and no-duplication gates (`scripts/check_docstrings.py`,
  `scripts/check_duplication.py`) are diff-scoped against `origin/main` by design - correct for
  normal incremental PRs, but this PR's entire branch-unification diff counts as "new" from
  `main`'s perspective, since `main` never had any of it. Orchestrator's initial position: change
  the diff base to `fix/copy-setup-to-scripts` (the branch's actual technical starting point) for
  this PR. codex disagreed, persuasively: permanently changing `ci.yml`'s base-ref logic creates a
  loophole where any future large merge could launder undocumented debt into `main` by choosing an
  older fork point - "that would make the gate pass by changing the measurement rather than
  improving the code." codex's counter-proposal assumed the violation count was manageable (~18
  files) based on a 2-file sample. **Orchestrator ran the actual check against the real
  `origin/main` and found 789 docstring violations and 1 duplication violation** (5 identical
  trivial `__init__(self, runner, memory)` constructors across `app/tools/*.py` - itself
  pre-existing convention, not new). 789 is not a manageable backlog to retroactively document
  correctly and honestly in one session without a high risk of hallucinated/wrong documentation
  across code neither reviewer originally wrote. This matches the exact fallback codex's own
  position already anticipated: "a genuinely disproportionate backlog that cannot safely be
  remediated now" gets "a one-time, explicitly documented CI exemption... not a permanent
  branch-name conditional in `ci.yml`." `ci.yml` is therefore **unchanged** - `origin/main` stays
  the permanent base ref for all future PRs, exactly as codex argued. This one check is expected to
  show red on PR #2 specifically, disclosed here and in the PR description, not silently accepted
  or worked around. No branch protection is actually configured on this repo (confirmed via the
  GitHub API - the plan doesn't support it), so this does not technically block merging; it is a
  disclosed, known gap a reviewer should see before approving, not a blocker being hidden.
- `ai-eval`: non-blocking (`continue-on-error: true`); referenced `tests/ai_benchmark.py`, which
  did not exist. **Correction 2026-07-19: fixed, not a real gap.** The file exists at
  `tests/manual/ai_benchmark.py` - its own header comment records it was moved there on 2026-07-10
  ("one extra `..` than before to still reach the repo root from the new, one-level-deeper
  location"), but `ci.yml`'s reference was never updated to match. Fixed in commit `ea1a617`. Still
  non-blocking and still needs `OLLAMA_HOST`/`ARGUS_MODEL` secrets pointing at a reachable Ollama
  endpoint to actually run end-to-end (not configured on hosted runners) - the fix lets it fail for
  that real, already-documented reason instead of a trivial path typo.

## Methodology Note (2026-07-19): "Fix Everything" Round - CI Gates Actually Fixed, Not Just Disclosed

The human explicitly asked to go further than disclosure: fix everything possible, with real
research and panel discussion where genuine judgment calls exist, not mechanical patches applied
blind. codex, opencode (agy remained quota-exhausted throughout, ETA ~2026-07-25), and the
orchestrator worked through each remaining red check.

**Fixed for real** (each independently verified, not just claimed):
- `full-tests`: `app/tools/self_heal.py`'s `subprocess.CREATE_NO_WINDOW` (Windows-only) crashed
  immediately on the Linux CI runner before the mocked `Popen` was ever reached - Python evaluates
  keyword-argument expressions before dispatching the call, so mocking `Popen` doesn't help. Fixed
  via `getattr(subprocess, "CREATE_NO_WINDOW", 0)`, preserving exact Windows behavior. Also:
  `test_large_insert_performance` was already marked `@pytest.mark.slow` but the marker was never
  registered or excluded from anything - a real machine-speed difference (10.33s on the shared
  runner vs. a 2.0s threshold tuned for a local dev machine), not a logic bug. Registered the
  marker and excluded it from CI, honoring what it was always meant to signal. Commit `98750af`.
- `test_smart_web_search.py::test_attempt_limit` (the long-standing "known flake," actually a
  missing feature - see T014-adjacent Open Follow-Up below): `SmartWebSearch` never had the
  attempt-limiting logic the test asserted. Found the real implementation on
  `fix/setup-script-update` (one of the 9 original branches) - `research.md` had classified this
  branch as "already absorbed" into `fix/copy-setup-to-scripts` via merge commit `8495f4d`, but
  that merge silently dropped this specific file's content (the same silent-regression shape as
  several other findings already in this document). codex and opencode both reviewed before
  porting - neither the stray debug print nor the duplicated lines in that branch's
  `archive_research_subagent` were ported, and per both reviewers' explicit warning,
  `socket.setdefaulttimeout()` was NOT ported (a process-global side effect that would silently
  change timeout behavior for every other socket operation in the process) - used DDGS's own scoped
  `timeout=` constructor parameter instead (confirmed real via the library's own docs). Also wired
  up `max_web_search_attempts`/`web_search_timeout_seconds`, config fields that already existed in
  `app/core/config.py`/`config.yaml` but were never read by this class - another instance of the
  "capability exists but was never connected" pattern this document has flagged repeatedly.
  Rewrote the test with mocks (DDGS is an external network boundary - appropriate to mock) instead
  of live DuckDuckGo calls, so it's no longer flaky by construction, not just by luck. Commit
  `dd6ecc7`.
- `ai-eval`: stale path, fixed (see above). Commit `ea1a617`.
- `lint-type`'s docstring-compliance gate: reduced from 798 to 421 violations via a tiered pass -
  see the dedicated note below, since this one had a real methodological risk that needed catching
  before it shipped.

**Docstring backfill - a cautionary tale about verifying, not just testing.** codex found
`specs/016-docstring-enforcement/spec.md`'s own FR-006 explicitly forbids exactly what a full
789-violation unattended pass would have been: *"a docstring asserting an incorrect parameter,
return type, or exception is worse than no docstring... MUST proceed per-directory/per-module in
reviewed batches, not as a single automated bulk rewrite."* Both codex and opencode, asked
independently, converged on the same tiered design: auto-generate only for trivial functions and
conventionally-named test functions, leave everything else as a tracked manifest for human review.

Building the generator script surfaced two real bugs, both caught by the orchestrator's own
verification before anything was committed - not by the reviewers, and not by pytest/ruff/mypy
either, since none of those check documentation *quality*:
1. First version discarded existing hand-written docstrings entirely when regenerating to add a
   missing section - e.g. replaced `"A custom max_retries must be honored, proving the bound isn't
   hardcoded."` with a generic name-derived `"Verify Retry budget is config driven not
   hardcoded."`. Caught by manually reading a sample diff, not by any automated check.
2. Second version fixed (1) by taking only the *first line* of an existing docstring, which
   truncated summaries that wrap a single sentence across multiple physical lines - e.g. cut
   `"specs/019 SC-003: 3 sources x 5 findings each -> exactly the last k=3 per (domain, tool_name)
   group, not the last 9 overall."` off mid-sentence at "exactly the last". Also caught by manual
   review, not tooling.

Both were reverted before committing (the working tree was cleanly `git checkout`-able back to
the last commit both times, since nothing had been committed yet) and fixed properly: preserve the
*entire* existing docstring text, appending only the missing sections. Before trusting the third
attempt, wrote a **separate, independent verification script** (not the generator's own
self-report) that walks every function with a pre-existing docstring across all 64 touched files
and confirms the original text is still present as a substring of the new docstring - 167/167
confirmed, zero content loss, checked programmatically rather than by further spot-checking.
This is the same "review, don't accept the self-report" discipline this project has applied to
every delegate dispatch all along, applied here to the orchestrator's own generated tooling instead
- a mechanical pass on 372 functions is exactly the kind of output that deserves the same scrutiny
as anything a delegate produces, not an exemption because the orchestrator wrote the script itself.
Commit `2036d72`. Remaining 421 violations tracked in `specs/checklist-docstring-backfill.md`
(FR-007's per-module CHK-series pattern), not silently dropped.

## Methodology Note (2026-07-19): Session Retrospective - What a Critical Second Look Found

GitHub Actions stopped triggering entirely after commit `3361d89` - no new run appeared for the
next 4 pushes despite the remote confirmably having each commit (`git ls-remote`). Investigated:
Actions are enabled on the repo, no queued/in_progress runs exist, no obvious API-visible error -
most likely a private-repo Actions-minutes quota exhaustion (this session triggered dozens of runs
today), but confirming that requires the human's own GitHub billing access, not available from
here. **Human is investigating directly; this session cannot resolve it.**

While blocked on that, the human asked for a genuine critical retrospective of the whole session -
not a confirmatory pass. Dispatched to codex (opencode also dispatched, hung with no output for a
long period - consistent with its unreliable pattern all session; not blocked on). codex's review
was NOT confirmatory and found three real, actionable issues, one already fixed by the time of
writing:

1. **This document lived outside the repository being merged.** `specs/027-merge-branches/`
   (this very file) was never actually part of `Argus-Digilians` - it lived one level up, in the
   orchestration workspace. Once PR #2 merged, the "authoritative record" the PR description
   itself repeatedly cited would have become permanently disconnected from the code it documents.
   **Fixed**: copied into the repo as `specs/027-merge-branches/` (001 was already taken by
   `001-rag-integration` - confirmed via `validate_specs.py`'s duplicate-number check, which
   caught the collision immediately). Commit `139bf56`. A final sync pass (updating this file's
   own internal "027-merge-branches" self-references to "027-merge-branches") is planned for
   right before the actual merge, once this document stops changing.

2. **The `unit-tests` CI gate - the only BLOCKING test job - collects just 10 of 311 tests.**
   Confirmed directly: `pytest --collect-only -q -m unit` -> "10/311 tests collected (301
   deselected)". Only `tests/test_rag/test_manifest.py` carries `@pytest.mark.unit`; nothing else
   in the whole suite does. `full-tests` (which runs `pytest -m "not eval and not slow"`, nearly
   everything) is `continue-on-error: true` - non-blocking. This means a green `unit-tests` check
   verifies almost nothing about the branch - a real, pre-existing gap in this project's own
   test-marking discipline (predates this session; the marker infrastructure and the fact that
   only one file uses it both trace back to `fix/copy-setup-to-scripts`'s original CI design, not
   anything introduced during branch-unification). **Not fixed** - retroactively deciding which of
   301 unmarked tests are genuinely "unit" tests (fast, mocked-boundary) vs. integration-flavored
   is real per-test judgment, not a mechanical relabeling, and is its own separate undertaking.
   **Disclosed instead**: `full-tests` passing for the actual merge SHA (not an older cached run)
   should be treated as the real correctness signal to require before merging, not `unit-tests`
   alone - `unit-tests` passing is real but narrow.

3. **The docstring generator (commit `2036d72`) had a real accuracy bug its own "verified-safe"
   claim didn't cover.** It labeled every test-function parameter "pytest fixture (see the
   module's @pytest.fixture definitions)." unconditionally - false for
   `unittest.mock.patch`-injected parameters (`unittest.TestCase`-style tests, which this codebase
   also uses alongside plain pytest fixtures). Confirmed directly:
   `tests/test_smart_web_search.py::test_successful_search_formats_results`'s `mock_ddgs_cls`
   parameter is `@patch`-injected, not a pytest fixture, yet was labeled as one. This is exactly
   the failure mode `specs/016-docstring-enforcement`'s FR-006 warns about, and the earlier
   "verified-safe" framing was accurate for *content preservation* (independently verified,
   167/167) but did not cover *wording accuracy* of the newly-generated text itself - a real gap
   in what "verified" meant. **Fixed**: replaced the phrase everywhere with wording true regardless
   of injection mechanism. Commit `060971a`.

**What this confirms about the process, not just the code**: a delayed/independent review found
real defects in work that had already passed local gates (pytest/ruff/mypy/compileall) - none of
those tools check documentation *accuracy*, only structure. This is the same lesson as the
"delayed opencode review" methodology note earlier in this document, now demonstrated a second
time by a different reviewer on different content. The orchestrator's own generated tooling is not
exempt from the same "review, don't accept the self-report" discipline applied to every delegate
dispatch - and even having already applied that discipline once (the two docstring-corruption bugs
caught before shipping), a *third* pass by a fresh, independent reviewer still found something the
orchestrator's own verification missed.

**Reconciled position on merging**: local verification alone (311/311 pytest, ruff/mypy/ASCII/
spec-doc all clean) is necessary but not sufficient - it does not substitute for `full-tests`
actually passing on GitHub's infrastructure for the real merge SHA. Merging should wait until
either (a) Actions resumes and a fresh `full-tests` run completes for the latest commit, or (b) the
human makes an informed decision to proceed without that signal, explicitly accepting the residual
risk - not merge on local-only verification treated as equivalent to a real CI run.

**opencode's independent retrospective** (dispatched in parallel with codex's, above; hung with no
output for a long period before eventually returning a genuinely thorough answer - consistent with
its unreliable-but-eventually-valuable pattern documented earlier this feature) found two more real,
independently-confirmed issues neither codex nor the orchestrator's own pass had caught:

1. **Command injection risk in `app/tools/self_heal.py`**: `system_self_heal()` built a shell
   command string by interpolating an LLM-tool-call-derived package name, then executed it via
   `subprocess.run(cmd, shell=True, ...)`. Confirmed real - `tool_info` flows from the agent's own
   tool-call arguments, and nothing sanitizes it before it reaches a shell. Fixed: list-form
   `subprocess.run([sys.executable, "-m", "pip", "install", "-U", package], ...)`, no shell
   involved. Commit `8adf63d`.
2. **Two vacuous tests**: `tests/test_gui/test_imports.py` and `tests/test_gui/test_dashboard.py`
   both wrapped their import assertions in `try/except RuntimeError: pass` - a test that can never
   fail no matter what breaks, as long as the failure happens to raise `RuntimeError`. Confirmed by
   running both the raw import and the actual pytest session directly: all 4 GUI modules import
   cleanly with zero `RuntimeError` right now, meaning the swallow was current dead code, not
   presently hiding anything - but it would have silently masked a real future regression that
   happened to raise that specific exception type. Removed the swallow in both files; they now fail
   loudly on a genuine import break. Commit `8adf63d`.

opencode also flagged `experimental_agent/`'s zero test coverage as "the single biggest risk" given
the two confirmed bugs already found there and `_safe_step()`'s catch-all design meaning more of the
same shape are plausible. Writing real tests for all 13 steps was judged disproportionate for this
session (each needs mocked LLM/HTTP boundaries); instead added
`app/modules/experimental_agent/README.md` making the risk and a concrete graduation checklist
impossible to miss for whoever next touches the module, rather than leaving it findable only by
reading this tasks.md file. Commit `2c0b521`.

**Third independent reviewer, same session, two more real findings.** This is now three separate
review passes (the delayed opencode dispatch that found the `_collect_xss_targets`/`self._session`
bugs, codex's retrospective, and opencode's parallel retrospective) each finding something the
others missed on the same body of work. No single reviewer - including the orchestrator, twice -
caught everything. This is the clearest evidence this feature's own methodology notes have argued
for all along: the value of genuine multi-reviewer disagreement is not theoretical.

## Open Follow-Ups (found during execution, deliberately deferred — not silently dropped)

- **`momen`'s live XSS scanning capability was only partially ported (T012/T015, 2026-07-18).**
  `momen:core/tools.py::check_xss()` is a real, working multi-phase reflected-XSS scanner: it probes
  a list of known-vulnerable endpoints/params (`FIXED_XSS_ENDPOINTS`) plus common query params with
  escalating payloads, and records CONFIRMED/SUSPECTED findings via `memory.add_finding(...,
  severity=...)`. Only its pure classification logic (`_classify`) was ported, as
  `app/tools/xss_classifier.py::classify_xss_reflection()` — the live HTTP-probing loop, the
  endpoint/param lists, and the finding-recording wiring were **not** ported, and `app/tools/`
  currently has no registered XSS-scanning tool at all (verified by grep — only a payload-type label
  string exists in `app/tools/payloads.py`). **Before this can be called a complete capability**,
  someone needs to: (1) port the scanning loop into a real tool class (matching the pattern of
  `app/tools/scanners.py`'s other scanners), and (2) register it in `app/core/registry/tool_registry.py`.
  This is a real, scoped gap in security-tool coverage, not a decision to leave undone indefinitely —
  flagging it here so it doesn't get lost once this feature closes. *(Update 2026-07-18: the third
  original item here — deciding whether `add_finding()` should accept `severity` — is resolved, see
  below; whoever picks up the scanning-loop port can now just pass `severity=` directly.)*
- **RESOLVED 2026-07-18** (was: "`ArgusMemory` has no `severity` column"). The final critical review
  (see Methodology Note above) found this was no longer a hypothetical future trigger — T014's own
  `app/modules/experimental_agent/agent.py` port already had 19 real call sites passing
  `severity=` to `add_finding()`, which crashed at runtime every time (see T014's Correction note
  above). Added the schema migration this note anticipated: `findings.severity` (schema v1→v2,
  idempotent), `add_finding(..., severity="Info")`, `get_detailed_findings()` returns the real value.
  `classify_xss_reflection()`'s output already returns a real severity string
  (`"High"`/`"Medium"`) — a future scanning-loop port can pass it straight through.
- **`xss_classifier.py` had a false-positive bug, found and fixed 2026-07-18** (final critical review).
  Its "encoded, therefore safe" check only recognized escaped `&lt;script`, not other escaped
  EXEC_SIGS payloads (e.g. `&lt;img onerror=...&gt;`) — a safely HTML-encoded non-`<script>` payload
  containing literal `onerror=`/`onload=`/etc. text was misclassified `"High"`. Generalized to check
  for a raw, unescaped angle bracket near the marker (the actual signal for "was a real tag created")
  instead of one hardcoded tag name. Added a regression test
  (`tests/test_ported_xss.py::test_html_encoded_event_handler_marker_safe`) — the existing encoded-safe
  test never exercised this path (no `MARKER` in its body). See commit `1309e5b`.
  **Still open, not addressed by this fix**: both agy and codex separately flagged that
  `xss_classifier.py`'s marker (`MARKER = "ARGUSxSS7"`, module-level constant) is a fixed, global
  string — if the same page happens to already contain this exact text unrelated to any injected
  payload, it would be misclassified as a reflection. This is a live-scanning architecture concern
  (a per-request random marker would need to be threaded through from whatever eventually calls this
  classifier), not a bug in the current pure function, which has no concept of "per-request" at all.
  Whoever does the live scanning-loop port above should generate a fresh random marker per scan
  session rather than reusing the module constant.
- **`command_runner.py`'s WSL path used `bash -lc` (login shell), found and fixed 2026-07-18** (final
  critical review, agy). Carried unmodified from `argus/SALMA` through the T007–T010 hand-merge —
  `-lc` sources shell profile files (`/etc/profile`, etc.), which can print banner/MOTD text to stdout
  and corrupt tool-output parsers (nmap XML, gobuster, etc.). Redundant anyway: `_with_safe_path()`
  (SALMA's own fix, correctly kept in the same hand-merge) already explicitly sets `PATH` without
  needing profile sourcing. Reverted to `bash -c`. See commit `1309e5b`.
- **`tests/test_smart_web_search.py::test_attempt_limit` is not a network flake — correction
  2026-07-18** (final critical review, agy). Previously characterized (T016 baseline, this file's
  Notes) as a pre-existing network-dependent flaky test. agy's review found the actual cause: the
  production `SmartWebSearch` class in `app/tools/web_search.py` has no attempt-limiting logic at all
  (`grep -n "attempt"` on that file returns nothing) — the test sets `searcher._max_attempts = 1` and
  asserts a limit message that no code path ever produces, so it fails deterministically, not
  intermittently. Pre-existing on the base branch (`fix/copy-setup-to-scripts`), not a regression
  introduced by this feature, and out of scope to fix here — recording the corrected characterization
  so the next person who looks at this failure doesn't waste time chasing a network issue that isn't
  the actual cause.
