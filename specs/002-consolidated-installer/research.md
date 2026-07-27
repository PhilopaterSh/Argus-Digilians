# Research: Consolidated Single-File Installer

**Phase**: 0 - Technical Research | **Date**: 2026-06-27 | **Spec**: `specs/002-consolidated-installer/spec.md`

---

## Purpose

Records the Phase 0 research behind the canonical decisions in `spec.md` and `plan.md`. All options
below were evaluated against the existing multi-file installer; nothing new is introduced. Grounded
in `plan.md` (Complexity Tracking, Key Design Decisions), `tasks.md` T001-T003, and Constitution
principles I-III and V.

---

## Current State Analysis

Files consolidated by this feature (from `plan.md` Technical Context):

| File | Size | Role |
|------|------|------|
| `scripts/INSTALL_EVERYTHING.ps1` | 827 lines | Master orchestrator (references `Setup/`) |
| `Setup/Step_1_Core_Foundation.bat` | 72 lines | WSL2 + Kali + Ollama |
| `Setup/Step_2_AI_Python_Env.bat` | 194 lines | Python + venv + model |
| `Setup/Step_3_Kali_Tools_Setup.bat` | 59 lines | Kali tools via WSL |
| `Setup/check_and_install.sh` | 382 lines | Kali tool installer (embedded) |
| `Setup/requirements.txt` | 15 lines | Python dependencies (embedded) |
| `Setup/argus_recon_fixed.sh` | 49 lines | Recon script (embedded) |

Key issue: prerequisite checks and file references were duplicated across the `Step_*.bat` chain,
causing version drift and path-resolution fragility (Constitution principle II rationale).

---

## Decision 1: Single-file installer vs multi-file orchestration

| Option | Pros | Cons |
|--------|------|------|
| A. Single self-contained `ARGUS_INSTALLER.ps1` | One authoritative entry point; no missing-file failures; satisfies Constitution II | Larger single file (~800-900 lines) |
| B. Keep `INSTALL_EVERYTHING.ps1` + `Setup/*` | Smaller files | Copy-paste misses one file -> broken install; duplicated prerequisite checks |

**Decision**: Option A. Constitution principle II (Single-Source Installer) mandates exactly one
authoritative entry point. `INSTALL.bat` remains only a convenience launcher.
*Traceability*: `spec.md` FR-001..002, US2; `plan.md` Complexity Tracking row 1.

---

## Decision 2: Embed dependencies vs reference external files

| Option | Pros | Cons |
|--------|------|------|
| A. Embed `requirements.txt` / `check_and_install.sh` / `argus_recon_fixed.sh` as here-strings, written to `/tmp/` inside WSL at runtime | Zero external-file risk; single copyable `.ps1` | Content lives inside the PS1 |
| B. Reference `Setup/` files at runtime | Files stay separate | A missing companion file breaks installation |

**Decision**: Option A. The installer writes embedded content to temp paths
(`/tmp/argus_requirements.txt`, `/tmp/argus_check_and_install.sh`) inside WSL.
*Traceability*: `spec.md` FR-002, FR-010; `plan.md` Embedding Strategy; `tasks.md` T005-T008.

---

## Decision 3: Archive vs delete the legacy `Setup/`

| Option | Pros | Cons |
|--------|------|------|
| A. Rename `Setup/` -> `Setup_legacy/` after first successful run | Keeps a debugging fallback (Constitution: legacy retention) | One extra directory retained |
| B. Delete `Setup/` | Cleaner tree | Loses the manual fallback |

**Decision**: Option A, guarded so it is skipped if `Setup_legacy/` already exists (idempotent).
*Traceability*: `spec.md` FR-009, SC-005; `tasks.md` T009-T010.

---

## Decision 4: Idempotency and gating

**Decision**: Every step checks whether its target is already satisfied and skips cleanly;
CRITICAL steps abort the run on failure, NON-CRITICAL steps record a warning and continue; the run
ends with an embedded health check (Constitution principle III). A `-DryRun` mode exercises the full
control flow without mutation.
*Traceability*: `spec.md` FR-005..006, US3; Constitution "Idempotent & Test-Gated", "Dry-run gate".

---

## Decision 5: Cross-platform boundary

**Decision**: Windows-host operations (PowerShell) stay separate from Kali-guest operations (shell
run via WSL as root, receiving only translated `/mnt/...` paths). SSH (port 22) is the application
bridge. This prevents silent path/permission errors (Constitution principle IV).
*Traceability*: `spec.md` FR-010; Constitution "Platform-Boundary Clarity".

---

## Alternatives rejected

- **Bash-based installer** - rejected; the host is Windows and admin elevation + Windows features
  (WSL2) require PowerShell (`spec.md` Assumptions, FR-001).
- **Dual-clone hash mirroring** (original `tasks.md` T018-T019) - superseded; the repository was
  consolidated into a single tree, so there is no second directory to sync.

---

## Decision Traceability Summary

| Decision | Spec ref | Tasks | Constitution |
|----------|----------|-------|--------------|
| 1 Single-file | FR-001..002, US2 | T004 | II |
| 2 Embed here-strings | FR-002, FR-010 | T005-T008 | II |
| 3 Archive Setup | FR-009, SC-005 | T009-T010 | Dev Workflow (legacy retention) |
| 4 Idempotent + DryRun | FR-005..006, US3 | T010b, T011 | III |
| 5 Platform boundary | FR-010 | T008 | IV |

---

## Open Questions

None. Every decision is already recorded in `spec.md`/`plan.md`; this document consolidates the
rationale.
