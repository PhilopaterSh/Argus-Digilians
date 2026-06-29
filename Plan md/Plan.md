# Argus - Single Master Installer Plan

> **Goal**: Replace the fragmented setup stack (`Setup\Step_*.bat` + `scripts\INSTALL_EVERYTHING.ps1` + `scripts\CHECK_HEALTH.bat`) with a single, self-contained PowerShell module that self-elevates up front, installs, configures, and validates the entire Argus environment, and leaves the project ready to run the moment it finishes.

**Date**: 2026-06-27
**Branch**: `fix/copy-setup-to-scripts`
**Tooling**: Spec-Kit 0.11.8 (opencode integration) - already enabled in this repository.

---

## 0. Current Spec-Kit State

Spec-Kit is **already enabled** (no installation required). The workflow is available through `.opencode/commands/speckit.*.md`:

```
/speckit.constitution  ->  /speckit.specify  ->  /speckit.clarify
       ->  /speckit.plan  ->  /speckit.tasks  ->  /speckit.implement
       ->  /speckit.analyze / /speckit.converge
```

> - **Phase 0 Complete**: `constitution.md` was filled and ratified as v1.0.0 with 6 Core Principles, plus Security/Governance/Workflow sections. The `opencode.json` now registers all `/speckit.*` commands. No further Phase 0 work is needed.

---

## 1. Current Problem Diagnosis

The current structure is **fragmented** - it is not "Setup calls scripts" as assumed:

```
scripts/INSTALL_EVERYTHING.ps1  (orchestrator)
   +-- Setup/Step_1_Core_Foundation.bat   <- requires Admin and checks it itself internally
   +-- Setup/Step_2_AI_Python_Env.bat       <- checks Python and Ollama a SECOND time
   +-- Setup/Step_3_Kali_Tools_Setup.bat    <- runs check_and_install.sh inside WSL
   +-- scripts/CHECK_HEALTH.bat             <- separate check that must be run manually
```

### Identified Defects

| # | Defect | Location |
|---|--------|----------|
| 1 | **Weak privileges** - the orchestrator only *warns* instead of self-elevating, so `Step_1` fails mid-way | `INSTALL_EVERYTHING.ps1:263` |
| 2 | **Duplicated logic** - Python is checked in the ps1 (line 102) **and** in Step_2 (line 12). Ollama is checked in Step_1 (line 56) **and** Step_2 (line 56) | multiple files |
| 3 | **File fragmentation** - 3 `.bat` files + a `.ps1` + a separate health check = 5 files for what should be one | whole project |
| 4 | **Fragile path resolution** - a three-candidate path resolver (`cand1/cand2/cand3`) because the orchestrator does not know where `Setup/` is | `INSTALL_EVERYTHING.ps1:218-239` |
| 5 | **No unified log** and a health check that is a separate file you must run by hand | `CHECK_HEALTH.bat` |

### Critical Dependency Chain (Execution Order)

```
Python 3.12  ->  Ollama  ->  WSL2  ->  Kali distro  ->  SSH bridge
                                                          |
                              Argus_venv + pip  <-  model (WhiteRabbitNeo-V3-7B)
                                       |
                              Kali tools (check_and_install.sh inside WSL)
                                       |
                              Health Check -> ready to run
```

---

## 2. The Phases

### Phase 0 - Spec-Kit Foundation (documented here; optional for automation)

- Fill in `constitution.md` with project principles:
  - **Admin-First**: the installer self-elevates before any system change.
  - **Single-Source**: one file only for the full install.
  - **Idempotent**: every step checks before it acts (re-running is safe).
  - **Test-Gated**: a step only proceeds when the previous one succeeded (with optional leniency for non-critical steps).
- Run `/speckit.specify` to produce `specs/001-single-master-installer/spec.md`.

### Phase 1 - Inventory and Analysis (done in section #1 above)

- Catalogue every script and its responsibilities.
- Map the critical dependency chain.
- Document the duplicated logic and remove it from the design.

### Phase 2 - Design of the Unified Installer

Single-file layout (`scripts/INSTALL_EVERYTHING.ps1`, fully rewritten):

```
1.  Self-Elevation    ->  auto-elevates to Admin (Start-Process -Verb RunAs)
2.  ExecutionPolicy   ->  Bypass automatically in scope
3.  System Readiness  ->  OS / RAM / Disk / Internet
4.  Python 3.12       ->  (once only)
5.  Host Foundation   ->  WSL2 + VirtualMachinePlatform + Kali distro + Ollama
6.  AI Environment    ->  Argus_venv + pip + model pull
7.  Kali Tools        ->  run check_and_install.sh inside WSL
8.  SSH Bridge        ->  configure sshd inside Kali + test port 22
9.  Health Check      ->  embedded in the file (not a separate file)
10. Final Report      ->  results table + log file logs/install_<timestamp>.log
```

**Design principles:**
- A single **Config Block** at the top (PYTHON_REQUIRED, MODEL, MIN_RAM_GB, paths...).
- Every step **checks before it acts** (idempotent) with **retry**.
- A **unified log** written to `logs/argus_install_<timestamp>.log`.
- Options: `-Offline`, `-Interactive`, `-DryRun`, `-SkipHealthCheck`, `-RetryCount`.

**Failure handling strategy:**

| Severity | Behavior | Example |
|----------|----------|---------|
| CRITICAL | Step failure immediately aborts the pipeline. Exit code != 0. | Python not found, cannot create venv |
| NON-CRITICAL | Failure recorded as WARN, pipeline continues. Reported in final summary. | Ollama model pull fails, SSH bridge not reachable |
| RETRY | Each step uses `Invoke-WithRetry` (default 2 retries, 5s gap). Configurable via `-RetryCount`. | winget install timeout, pip network blip |
| SKIP | Interactive mode (`-Interactive`) prompts before each step. | User declines step |
| DRY-RUN | No mutation. Prints what would happen. Validates path resolution. | `-DryRun` flag |
| ROLLBACK | Not implemented. The installer is idempotent (re-running skips completed steps) instead of rolling back. This is an explicit trade-off: rollback of WSL/Kali changes is destructive and unreliable. | Re-run the installer to retry failed steps |

### Phase 3 - Implementation

- Rewrite `scripts/INSTALL_EVERYTHING.ps1` to be self-contained (embeds the logic of the three `.bat` files).
- The only external dependency: `check_and_install.sh` (run inside WSL only).
- Create `INSTALL.bat` at the root that calls the ps1 with bypass and self-elevation.

### Phase 4 - Testing and Validation

- A `-DryRun` mode to verify logic without any system change.
- **Syntax validation** via `powershell -NoProfile -Command` to guarantee there are no parse errors.
- Confirm idempotency: re-running skips completed steps.
- Confirm the embedded Health Check is complete (venv + Ollama + Kali + SSH).

### Phase 5 - Cleanup and Documentation

- Archive the legacy `.bat` steps (kept as a manual debugging fallback per `INSTALLATION_GUIDE`).
- Update: `README.md`, `INSTALLATION_GUIDE.md`, `scripts/README.md`, `Setup/README.md`.
- **End result**: a single command only -> `INSTALL.bat`.

---

## 3. Measurable Success Criteria

| Criterion | How it is measured |
|-----------|--------------------|
| Single file only for install | `scripts/INSTALL_EVERYTHING.ps1` contains all logic |
| Automatic privilege elevation | No need to launch PowerShell as Admin manually |
| Idempotent | Re-running skips completed items without errors |
| Embedded health check | No separate `CHECK_HEALTH.bat` file required |
| Unified log | One log file written automatically |
| Single click | `INSTALL.bat` at the root is sufficient |
| Syntax correctness | passes `powershell -Command` with no errors |

---

## 4. Implementation Notes

- Nothing in the legacy `Setup/` is deleted in this phase; it is kept as a manual debugging fallback (documented as "legacy").
- `check_and_install.sh` is **not touched** (the internal Kali logic is stable).
- **WSL caution**: enabling Windows features may require a reboot - handled with a clear message to the user.

### Commit Strategy (per Spec-Kit Phase)

Every Spec-Kit phase **MUST** produce at least one `git commit` before moving to the next phase. This ensures a clean, auditable history and enables safe rollback.

| Spec-Kit Phase | Commit Pattern | Example Message |
|----------------|----------------|-----------------|
| `/speckit.specify` | `spec: <feature> <file>` | `spec: 002-consolidated-installer spec.md` |
| `/speckit.plan` | `plan: <feature> <file>` | `plan: 002-consolidated-installer plan.md` |
| `/speckit.tasks` | `tasks: <feature> <file>` | `tasks: 002-consolidated-installer tasks.md` |
| `/speckit.implement` | `feat: <feature> - <task>` | `feat: 002-installer - T005 embedded here-strings` |
| `/speckit.analyze` | `analyze: <feature> <detail>` | `analyze: 002-installer cross-artifact check` |
| `/speckit.converge` | `converge: <feature> <detail>` | `converge: 002-installer remaining work appended` |

**Rules:**
1. Always `git status` + `git diff` before committing to verify only intended files are staged.
2. Never commit secrets, tokens, or large binaries.
3. If a phase produces multiple files, commit each logically grouped change separately.
4. After `/speckit.implement`, commit **after each completed Task**, not only at the end of the phase.
