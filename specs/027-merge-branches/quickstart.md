# Quickstart: Validating the Branch Unification

How to prove, at each Integration Step (see plan.md), that the unification is actually working —
not just that it "merged without conflicts."

## Prerequisites

- Windows 10/11 host with WSL2 + `kali-linux` distro running (`wsl -l -v` shows it Running or
  startable).
- `Argus_venv` present and activatable at the repo root.
- Working directory: `D:\TEAM PROJECT\Main\Argus-Digilians` (or the relevant `branches/*` worktree
  during early, pre-merge steps).

## After every Integration Step (1–6 in plan.md)

1. **App still starts**:
   ```
   Argus_venv\Scripts\python.exe run_argus_cli.py
   ```
   Expected: reaches its normal startup prompt/menu without a stack trace. (Streamlit path:
   `scripts\LAUNCH_STUDIO.bat`, expected to reach `http://localhost:12199`.)

2. **Tests collect and run**:
   ```
   Argus_venv\Scripts\python.exe -m pytest --collect-only
   Argus_venv\Scripts\python.exe -m pytest -q
   ```
   Expected: zero collection errors; pass rate does not regress versus the previous Integration
   Step's recorded pass rate (spec.md SC-002 / data-model.md `Unified Branch.test_pass_rate`).

3. **No original branch was touched**:
   ```
   git branch -a
   git worktree list
   ```
   Expected: all 9 original contributor branches (or their worktrees) are still present and
   resolvable — spec.md FR-004 / SC-003.

## Step-specific checks

- **After Step 3 (installer)**: run `scripts\ARGUS_INSTALLER.ps1 -DryRun` first, then a real run on
  a clean environment (fresh WSL Kali instance or VM). Expected: full install completes, embedded
  health check passes, and a second run (`-DryRun` or real) shows idempotent skip behavior — this is
  what closes `fix/copy-setup-to-scripts`'s own open tasks T013/T014.
- **After Step 4 (momen)**: run momen's ported tests specifically:
  ```
  Argus_venv\Scripts\python.exe -m pytest tests/test_argus_comprehensive.py tests/test_xss_scanner.py -q
  ```
  Expected: pass under pytest (not momen's original custom runner).
- **After every step that resolves a conflict**: check `data-model.md`'s `Conflict Decision` records
  exist for every file git flagged as conflicting in that step — spec.md FR-003, SC-005 (100%
  rationale coverage, not just the contentious ones).

## Final acceptance (maps to spec.md Success Criteria)

| Success Criteria | How to check here |
|---|---|
| SC-001 (all 10 branches classified) | `research.md` §3 — read confirms all 9 contributor branches classified (corrected 2026-07-17: `main` is the baseline, not itself a classified row, so §3's table has 9 rows, not 10) |
| SC-002 (unified branch starts on first attempt) | Quickstart step 1, after Step 6 |
| SC-003 (0 branches deleted/force-overwritten) | Quickstart step 3, after Step 6 |
| SC-004 (exactly one installer entry point) | `scripts/` contains only `ARGUS_INSTALLER.ps1`, no `INSTALL_EVERYTHING.ps1` remaining |
| SC-005 (100% conflict rationale coverage) | Every `Conflict Decision` in data-model.md has a non-empty `rationale` |
