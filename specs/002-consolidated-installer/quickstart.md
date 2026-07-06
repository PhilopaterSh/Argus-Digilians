# Quickstart: Consolidated Single-File Installer

**Phase**: 1 - Validation | **Date**: 2026-06-27 | **Spec**: `specs/002-consolidated-installer/spec.md`

---

## Purpose

How to run and validate `scripts/ARGUS_INSTALLER.ps1`. Derived from `spec.md` (User Stories,
Success Criteria SC-001..005), `tasks.md` T011-T014, and Constitution principles I-III.

## Prerequisites

- Windows 10 (build 19041+) or Windows 11 (spec Assumptions).
- Winget available (for Python).
- Internet access, unless using `-Offline` (spec Assumptions, FR-003).
- Run from the project root.

---

## Run 1: Dry run (no system changes)

```powershell
.\scripts\ARGUS_INSTALLER.ps1 -DryRun
```

**Expected**: the installer self-elevates, then exercises the full control flow and path resolution
without mutating the system; every step prints a result and a final summary table appears
(spec FR-005, FR-008; tasks T011).

---

## Run 2: Full installation

```powershell
.\scripts\ARGUS_INSTALLER.ps1
```

**Expected**:
- Self-elevation to Administrator at the very start (spec FR-001).
- Steps execute in the critical dependency order (Python -> WSL2 -> Kali -> venv -> tools -> SSH).
- Completes in under 30 minutes on a 100 Mbps connection (spec SC-002).
- Final health check reports **5/5** components OK/ONLINE: venv, Ollama, Kali, SSH, Python
  (spec SC-004).
- On first success, `Setup/` is renamed to `Setup_legacy/` (spec SC-005; tasks T009).

---

## Run 3: Idempotent re-run

```powershell
.\scripts\ARGUS_INSTALLER.ps1
```

**Expected**: all already-installed components are detected and skipped; completes in under 2 minutes;
health check still passes; `Setup_legacy/` is not recreated (spec SC-003, US3; tasks T010, T014).

---

## Run 4: Offline mode

```powershell
.\scripts\ARGUS_INSTALLER.ps1 -Offline
```

**Expected**: all network downloads are skipped; the installer clearly reports what must be
provisioned manually (spec FR-003; Constitution "Offline mode").

---

## Validation checklist

| Check | Command / observation | Expected | Source |
|-------|-----------------------|----------|--------|
| Single file, no external deps | copy only `ARGUS_INSTALLER.ps1` elsewhere and run | works | SC-001, US2 |
| Health check | end-of-run summary | 5/5 OK/ONLINE | SC-004 |
| Idempotency | run twice | 2nd run < 2 min, all skipped | SC-003 |
| Legacy archived | `Test-Path Setup_legacy` | True after first run | SC-005 |
| Timestamped log | inspect `logs/` | one log per run | Constitution V |
| PowerShell syntax gate | `[System.Management.Automation.Language.Parser]::ParseFile(...)` zero errors | passes | Constitution Dev Workflow; CI `powershell-syntax-gate` |

---

## Troubleshooting

- **Elevation declined**: the script aborts with a clear message and a non-zero exit code; it does
  not degrade into a partial run (spec Edge Cases; Constitution I).
- **WSL2 needs a reboot**: the script prompts for reboot and offers an auto-restart command
  (spec Edge Cases).
- **Insufficient disk for the model**: the model pull is skipped with a warning suggesting a smaller
  model; other steps continue (spec Edge Cases; Constitution hardware floor).
