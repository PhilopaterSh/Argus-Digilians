# Implementation Plan: Consolidated Single-File Installer

**Branch**: `fix/copy-setup-to-scripts` | **Date**: 2026-06-27 | **Spec**: `specs/002-consolidated-installer/spec.md`

---

## Summary

Merge all installation logic from `scripts/INSTALL_EVERYTHING.ps1` + `Setup/` directory (Step_*.bat, check_and_install.sh, requirements.txt, etc.) into a **single self-contained PowerShell script** with no external file dependencies. The script embeds `requirements.txt` and `check_and_install.sh` as here-strings, handles all 6 installation steps, and archives the old Setup/ directory after success.

---

## Technical Context

**Language/Version**: PowerShell 5.1+

**Current Files to Consolidate**:

| File | Size | Purpose |
|------|------|---------|
| `scripts/INSTALL_EVERYTHING.ps1` | 827 lines | Master orchestrator (references Setup/ files) |
| `Setup/Step_1_Core_Foundation.bat` | 72 lines | WSL2 + Kali + Ollama |
| `Setup/Step_2_AI_Python_Env.bat` | 194 lines | Python + venv + model |
| `Setup/Step_3_Kali_Tools_Setup.bat` | 59 lines | Kali tools via WSL |
| `Setup/check_and_install.sh` | 382 lines | Kali Linux tool installer (embedded) |
| `Setup/requirements.txt` | 15 lines | Python dependencies (embedded) |
| `Setup/setup_python_kali.sh` | 42 lines | Legacy (replaced by check_and_install.sh) |
| `Setup/argus_recon_fixed.sh` | 49 lines | Legacy recon script |
| `Setup/run_kali_setup.bat` | 17 lines | Legacy launcher |
| `Setup/README.md` | 82 lines | Legacy docs |

**Target**: Single file `scripts/ARGUS_INSTALLER.ps1` (~800-900 lines).

**Embedding Strategy**:
- `requirements.txt` → stored as `$EMBEDDED_REQUIREMENTS` here-string in the PS1
- `check_and_install.sh` → stored as `$EMBEDDED_CHECK_INSTALL_SH` here-string in the PS1
- `argus_recon_fixed.sh` → embedded as `$EMBEDDED_ARGUS_RECON_SH` in the PS1
- These are written to temp locations inside WSL (`/tmp/argus_requirements.txt`, `/tmp/argus_check_and_install.sh`) at runtime

**Testing**: Manual test on clean Windows VM + automated dry-run verification.

**Target Platform**: Windows 10/11 with WSL2.

## Project Structure

### Before
```
Argus/
├── scripts/
│   ├── INSTALL_EVERYTHING.ps1    # Master (references Setup/)
│   ├── LAUNCH_CLI.bat
│   └── LAUNCH_STUDIO.bat
├── Setup/
│   ├── Step_1_Core_Foundation.bat
│   ├── Step_2_AI_Python_Env.bat
│   ├── Step_3_Kali_Tools_Setup.bat
│   ├── check_and_install.sh
│   ├── requirements.txt
│   ├── setup_python_kali.sh
│   ├── argus_recon_fixed.sh
│   ├── run_kali_setup.bat
│   └── README.md
```

### After
```
Argus/
├── scripts/
│   ├── ARGUS_INSTALLER.ps1       # ← SINGLE FILE, self-contained
│   ├── LAUNCH_CLI.bat
│   └── LAUNCH_STUDIO.bat
├── Setup_legacy/                  # ← Archived after first run
│   ├── Step_1_Core_Foundation.bat
│   ├── Step_2_AI_Python_Env.bat
│   ├── ...
│   └── README.md
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Embedding shell script in PowerShell here-string | Self-containment eliminates file dependency risk | Keeping Setup/ files means copy-paste misses one file, breaking installation |
| Multi-step orchestration | Different privilege domains (Windows admin + WSL root) | Single step would fail on cross-boundary operations (Ollama on Windows, tools in WSL) |

## Key Design Decisions

1. **Embed, don't reference**: All external files become here-strings in the PS1. Writes them to `/tmp/` inside WSL at runtime.
2. **Keep existing step logic**: The current step functions in INSTALL_EVERYTHING.ps1 are well-tested. Rewrite them minimally — just change how they access requirements.txt and check_and_install.sh.
3. **Archive Setup/ → Setup_legacy/**: After first successful run, rename the old directory to prevent confusion, but keep it as a fallback reference.
4. **Idempotent by design**: All steps check for existing state before acting. Re-running is safe.
5. **Admin-first**: Self-elevation as the very first action, before any logging or config file writes.
6. **Commit-per-phase**: Every Spec-Kit phase MUST produce a git commit before proceeding (see Commit Strategy in `Plan.md`).
