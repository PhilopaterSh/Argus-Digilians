# Scripts & Automation

This directory contains launch scripts, the unified master installer, and CLI
entry points for the Argus framework.

---

## Master Installer

### `ARGUS_INSTALLER.ps1` (Recommended — Single Source of Truth)

A fully self-contained PowerShell script that embeds all dependencies
(requirements.txt, check_and_install.sh) internally as here-strings.
It has ZERO external file dependencies — copy this ONE file and run it.
This is the **only** supported installer; the previous `INSTALL_EVERYTHING.ps1`
was removed (it depended on the now-archived `Setup/` directory).

After a successful first run, the legacy `Setup/` directory is automatically
archived to `Setup_legacy/`.

**Execution (from project root):**

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ARGUS_INSTALLER.ps1
```

**Parameters:**

| Parameter | Description |
|-----------|-------------|
| `-Offline` | Skip all network downloads |
| `-Interactive` | Prompt before each critical step |
| `-DryRun` | Simulate without making system changes |
| `-SkipHealthCheck` | Skip the embedded final health check |
| `-RetryCount N` | Retry failed steps N times (default: 2) |
| `-OnlyHealthCheck` | Run **only** the embedded health check, no install steps, no elevation |

**Embedded Steps (in order):**

1. Self-Elevation (Admin-first)
2. System Readiness (OS, RAM, Disk, Internet)
3. Python 3.12 bootstrap
4. Host Foundation (WSL2, Kali distro, `wsl --update`, Ollama)
5. AI Environment (Argus_venv, pip, model pull + response verification)
6. Kali Security Tools (embedded check_and_install.sh inside WSL)
7. SSH Bridge (sshd + port 22 test)
8. Embedded Health Check (venv, Ollama, Kali, SSH)
9. Cleanup (archive Setup/ to Setup_legacy/)

---

## Launch Scripts

### `LAUNCH_STUDIO.bat`

Starts the Streamlit web UI (Argus Studio).

```batch
LAUNCH_STUDIO.bat        # Default mode (GPU)
LAUNCH_STUDIO.bat C      # Force CPU mode
LAUNCH_STUDIO.bat R      # Clean restart Ollama
LAUNCH_STUDIO.bat G      # Standard GPU mode
```

**Port:** 12199

### `LAUNCH_CLI.bat`

Starts the autonomous CLI agent.

```batch
LAUNCH_CLI.bat           # Standard CLI mode
LAUNCH_CLI.bat C         # Enhanced mode
```

**Entry Point:** `scripts/run_argus_cli.py`

---

## Directory Structure

```text
scripts/
+-- ARGUS_INSTALLER.ps1        # Self-contained installer (single source of truth)
+-- LAUNCH_STUDIO.bat          # Streamlit web UI launcher
+-- LAUNCH_CLI.bat             # CLI agent launcher
+-- run_argus_cli.py           # CLI Python entry point
+-- README.md                  # This file
```

---

## Important Notes

- **Single-Click:** Run `scripts\ARGUS_INSTALLER.ps1` for a one-command install
  with auto-elevation.
- **Elevation Required:** The installer handles Admin elevation internally.
  No need to "Run as Administrator" manually.
- **Self-Contained:** `ARGUS_INSTALLER.ps1` embeds all dependencies internally.
  Copy ONE file and run it anywhere — no Setup/ directory needed.
- **Post-Install:** After a successful run, `Setup/` is archived to `Setup_legacy/`.
  The legacy files remain as a debugging fallback.
- **Idempotent:** Re-running the installer is safe; completed steps are skipped.
- **Log File:** Every run writes to `logs/argus_install_<timestamp>.log`.

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Not running as Administrator" | Accept the UAC prompt when it appears |
| WSL2 not available after features | Reboot the system, then re-run |
| Python 3.12 not found | Install from python.org, then re-run |
| Ollama not starting | Check `LAUNCH_STUDIO.bat R` for a clean restart |
| SSH bridge (port 22) down | Re-run installer; it auto-starts sshd in Kali |

---

*Maintained by: Argus Security Framework Team | June 2026*
