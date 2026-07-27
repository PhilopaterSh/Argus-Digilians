# Data Model: Consolidated Single-File Installer

**Phase**: 1 - Design | **Date**: 2026-06-27 | **Spec**: `specs/002-consolidated-installer/spec.md`

---

## Purpose

The installer is a script, not a data service, so its "data model" is the set of structured
artifacts it defines at runtime: the embedded content blocks, the ordered step sequence, the
per-step result record, and the run log. Derived from `spec.md` Key Entities, `plan.md` Embedding
Strategy, `tasks.md` T005-T009, and Constitution principle V (Observability).

---

## Entity 1: ArgusInstaller (script)

The single self-contained entry point.

| Field | Type | Description |
|-------|------|-------------|
| path | file | `scripts/ARGUS_INSTALLER.ps1` |
| flags | set | `-Offline`, `-Interactive`, `-DryRun` (spec FR-003..005) |
| language | PowerShell 5.1+ | host-side execution (plan Technical Context) |

**Invariants**: self-elevates to Administrator as the very first action (spec FR-001,
Constitution I); has zero external file dependencies (spec SC-001).

---

## Entity 2: EmbeddedContentBlock

External files stored as PowerShell here-strings and written to temp paths at runtime.

| Block variable | Source file | Runtime target | Consumer step |
|----------------|-------------|----------------|---------------|
| `$EMBEDDED_REQUIREMENTS` | `Setup/requirements.txt` | venv temp / `/tmp/argus_requirements.txt` | `Invoke-StepAiEnvironment` |
| `$EMBEDDED_CHECK_INSTALL_SH` | `Setup/check_and_install.sh` | `/tmp/argus_check_and_install.sh` (WSL) | `Invoke-StepKaliTools` |
| `$EMBEDDED_ARGUS_RECON_SH` | `Setup/argus_recon_fixed.sh` | WSL temp | recon setup |

**Invariant**: WSL-side blocks are written inside WSL, never referenced from the Windows side
(spec FR-010, Constitution IV).

---

## Entity 3: StepSequence

The ordered critical dependency chain (spec Key Entities; Constitution III).

| # | Step | Criticality |
|---|------|-------------|
| 0 | Self-elevate to Administrator | CRITICAL |
| 1 | System Readiness (hardware/OS checks) | NON-CRITICAL (warn) |
| 2 | Python | CRITICAL |
| 3 | WSL2 / Kali / Ollama | CRITICAL |
| 4 | venv + Model pull | CRITICAL (model guarded by disk) |
| 5 | Kali Tools | NON-CRITICAL |
| 6 | SSH Bridge (port 22) | NON-CRITICAL |
| 7 | Health Check | CRITICAL |
| 8 | Cleanup: `Setup/` -> `Setup_legacy/` | NON-CRITICAL, idempotent |

**Invariant**: a failed CRITICAL step aborts the run; a failed NON-CRITICAL step records a warning
and does not block the final health check (spec US1 AC-3, Constitution III).

---

## Entity 4: StepResult

Structured record produced by every step (Constitution principle V).

| Field | Type | Description |
|-------|------|-------------|
| step_id | str | Stable identifier |
| name | str | Human-readable step name |
| status | enum(`OK`,`SKIPPED`,`WARN`,`FAILED`) | Outcome |
| detail | str | Diagnostic detail feeding the final summary table |

---

## Entity 5: RunLog

| Field | Type | Description |
|-------|------|-------------|
| path | file | Timestamped file under `logs/` (Constitution V) |
| console_mirror | bool | Every action is also written to console |

---

## Entity 6: HealthCheckResult

Final embedded verification (spec SC-004).

| Component | Expected |
|-----------|----------|
| venv | OK |
| Ollama | ONLINE |
| Kali | OK |
| SSH | OK |
| Python | OK |

**Invariant**: reports 5/5 components on a healthy system (spec SC-004).

---

## Relationships

```text
ArgusInstaller --contains--> EmbeddedContentBlock (3)
ArgusInstaller --executes--> StepSequence (0..8)
each Step --produces--> StepResult --aggregated into--> final summary table
ArgusInstaller --writes--> RunLog
Step 7 --produces--> HealthCheckResult
```

---

## Acceptance Criteria (data model)

- **AC-1**: The installer has no external file dependency (spec SC-001); all three EmbeddedContentBlocks resolve internally.
- **AC-2**: Every step yields a StepResult; the run ends with a summary table (spec FR-008).
- **AC-3**: HealthCheckResult reports 5/5 on a healthy system (spec SC-004).
- **AC-4**: Re-running is idempotent - existing components produce `SKIPPED`, not errors (spec US3, SC-003).

---

## Implementation Notes

- `Write-EmbeddedFile` (tasks T006) is the helper that materializes an EmbeddedContentBlock to a
  Windows or WSL temp path.
- The cleanup step (Entity 3, step 8) is guarded so `Setup_legacy/` is created at most once
  (tasks T010).
