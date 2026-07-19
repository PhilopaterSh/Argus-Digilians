# Installation Guide - Argus Security Framework

This guide covers the supported installation approach using the unified master
installer, as well as the legacy manual fallback. For the underlying manual
steps the installer automates (useful for offline/air-gapped provisioning or
understanding what each step does), see `docs/Argus_Master_Documentation.md`.

---

## Quick Summary

| Aspect | Unified Installer | Legacy Manual Steps |
|--------|-------------------|-------------------|
| **Status** | **Recommended** | Fallback only |
| **Entry Point** | `INSTALL.bat` (root) | `Setup/Step_*.bat` (manual) |
| **Execution** | Automatic (one command) | Manual (step-by-step) |
| **Admin Handling** | Auto-elevates via UAC | Must run as Admin manually |
| **Health Check** | Embedded at end of install | `INSTALL.bat health` (same script) |
| **Logging** | Unified log file | Console only |

---

## Supported Path: Unified Master Installer

### What It Does

`scripts/ARGUS_INSTALLER.ps1` is a single, self-contained PowerShell module that:

1. **Self-elevates** to Administrator (UAC prompt)
2. **Verifies system readiness** (OS, RAM, disk, internet)
3. **Bootstraps Python 3.12** (via winget or existing installation)
4. **Enables WSL2** + installs Kali Linux distribution
5. **Installs Ollama** (AI engine)
6. **Creates Argus_venv** + installs Python packages
7. **Pulls the AI model** (WhiteRabbitNeo-V3-7B)
8. **Installs Kali security tools** (via check_and_install.sh inside WSL)
9. **Configures SSH bridge** (sshd inside Kali, port 22)
10. **Runs embedded health check** (venv, Ollama, Kali, SSH)
11. **Writes a timestamped log** to `logs/argus_install_<timestamp>.log`
12. **Prints a summary table** of all step results

### How to Use

**Option A: Single Click (Recommended)**

Double-click `INSTALL.bat` at the project root. A UAC prompt will appear.

**Option B: From Terminal**

```powershell
cd C:\AI_PenTest_Project\remote_Argus_PhilopaterSh
.\INSTALL.bat
```

**Option C: Direct PowerShell**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ARGUS_INSTALLER.ps1
```

### Installation Modes

```powershell
# Full install (default)
.\INSTALL.bat

# Simulate without system changes
.\INSTALL.bat dryrun

# Skip all network downloads
.\INSTALL.bat offline

# Confirm before each step
.\INSTALL.bat interactive

# Skip the final health check
.\INSTALL.bat skiphealth
```

### Design Principles

- **Admin-First:** Self-elevates before any system modification. No partial runs.
- **Single-Source:** All logic in one file. No fragmented multi-file orchestration.
- **Idempotent:** Safe to re-run. Completed steps are skipped automatically.
- **Test-Gated:** Critical step failure aborts the pipeline. Non-critical failures
  are recorded as warnings.

### Architecture

```text
INSTALL.bat (root launcher, no logic)
    |
    v
scripts/ARGUS_INSTALLER.ps1 (unified self-elevating installer)
    |
    +-- Step 0: System Readiness (RAM, Disk, Internet)
    +-- Step 1: Python 3.12 bootstrap
    +-- Step 2: Host Foundation (WSL2 + Kali + Ollama)
    +-- Step 3: AI Environment (Argus_venv + pip + model)
    +-- Step 4: Kali Tools (check_and_install.sh in WSL)
    +-- Step 5: SSH Bridge (sshd + port 22)
    +-- Step 6: Embedded Health Check
    +-- Final Report + Log File
```

### What Happens After Installation

```text
installer finishes
    |
    +-- logs/argus_install_20260627_143000.log  (full audit trail)
    +-- Argus_venv/                              (Python virtual environment)
    +-- WSL2 + Kali Linux                        (security tools ready)
    +-- Ollama + WhiteRabbitNeo model            (AI engine ready)
    +-- SSH bridge on port 22                    (Windows <-> Kali)
    |
    v
READY TO RUN -> scripts\LAUNCH_STUDIO.bat or scripts\LAUNCH_CLI.bat
```

---

## Legacy Path: Manual Step-by-Step

> Use only for debugging or CI/CD scenarios. See `Setup/README.md` for details.

```batch
cd Setup/
Step_1_Core_Foundation.bat
Step_2_AI_Python_Env.bat
Step_3_Kali_Tools_Setup.bat
```

Each script has its own Admin check and must be run as Administrator.

---

## Troubleshooting

### Unified Installer Issues

```
"UAC prompt declined"         -> Accept the elevation prompt and rerun
"WSL2 not available"          -> Reboot after Windows feature enablement, then rerun
"Python 3.12 not found"        -> Install from python.org, then rerun
"Kali distro not detected"     -> Run Step 1 or re-run installer after reboot
"Ollama not starting"          -> Check LAUNCH_STUDIO.bat R for clean restart
"SSH bridge port 22 down"      -> Re-run installer (auto-starts sshd in Kali)
"Model pull failed"            -> Check disk space; set ARGUS_MODEL for a smaller model
```

### Environment Variable Overrides

| Variable | Default | Description |
|----------|---------|-------------|
| `ARGUS_MODEL` | `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest` | AI model name |
| `ARGUS_MODEL_MIN_GB` | `8` | Minimum disk space (GB) for model pull |
| `ARGUS_MODEL_PULL_RETRIES` | `3` | Retry attempts for model download |
| `ARGUS_OFFLINE` | *(unset)* | Set to `1` to skip network downloads |
| `ARGUS_AUTO_INSTALL` | *(unset)* | Set to empty for interactive mode |

---

## Decision Tree

```
START: Do you want to install Argus?
    |
    +-- First time on a new system?
    |       +-- YES -> INSTALL.bat (unified installer)
    |       +-- NO  -> continue
    |
    +-- Debugging a specific step?
    |       +-- YES -> Setup/Step_*.bat (manual)
    |       +-- NO  -> continue
    |
    +-- CI/CD pipeline?
    |       +-- YES -> scripts/ARGUS_INSTALLER.ps1 -DryRun (validate)
    |       +-- NO  -> INSTALL.bat
```

---

## References

- `scripts/README.md` - Launch scripts and installer guide
- `Setup/README.md` - Legacy step scripts reference
- `docs/Argus_Master_Documentation.md` - Full technical documentation
- `docs/history/Plan.md` - Unified installer design plan

---

*Maintained by: Argus Security Framework Team | June 2026*
