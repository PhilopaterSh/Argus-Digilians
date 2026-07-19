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
was removed (it depended on a `Setup/` directory that no longer exists in this
repository - see STEP 9 below).

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
9. Cleanup (archives a `Setup/` directory to `Setup_legacy/` if one is present -
   a leftover from older checkouts; a fresh clone of this repository no longer
   has a `Setup/` directory, so this step is a no-op on it)

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

## Which Script Do I Run?

| I want to... | Run this |
|---|---|
| Install everything from scratch | `INSTALL.bat` (repo root) or `scripts\ARGUS_INSTALLER.ps1` directly |
| Start the Streamlit web UI (Argus Studio) | `scripts\LAUNCH_STUDIO.bat` |
| Start the autonomous agent from the CLI, no GUI | `scripts\LAUNCH_CLI.bat` (runs `run_argus_cli.py`) |
| Debug/watch an agent run step-by-step in a terminal | `python scripts\_diagnostic_cli_verbose.py <target-url>` (prints every graph step live; not a production entry point) |
| Run the full automated test suite | `pytest` from the project root (uses `tests/`, not anything in `scripts/`) |
| Manually smoke-test the RAG pipeline during development | `scripts\test_rag.py` (ad hoc dev script, not part of the pytest suite) |
| Manually smoke-test the *superseded* `010` tactical graph (not current production - that's `react_workflow.py`) | `scripts\diagnose_legacy_tactical_graph.py` (renamed 2026-07-10 from the misleading `test_agent.py`; ad hoc, not part of the pytest suite) |
| Check for duplicate code before committing | `scripts\check_duplication.py` |
| Check for missing/inconsistent docstrings | `scripts\check_docstrings.py` |
| Validate Spec Kit artifacts (`specs/`) | `scripts\validate_specs.py` |
| Check a file only uses ASCII (Windows console safety) | `scripts\validate_ascii.py` |
| Find a free local port | `scripts\get_port.py` |

---

## Directory Structure

```text
scripts/
+-- ARGUS_INSTALLER.ps1          # Self-contained installer (single source of truth)
+-- LAUNCH_STUDIO.bat            # Streamlit web UI launcher
+-- LAUNCH_CLI.bat               # CLI agent launcher
+-- TEST_ARGUS.bat               # Quick manual smoke-test launcher
+-- run_agent.py                 # ArgusBrain entry point used by the GUI's "Start Agent" button
+-- run_argus_cli.py             # CLI Python entry point (used by LAUNCH_CLI.bat)
+-- _diagnostic_cli_verbose.py   # Verbose step-by-step live debugging CLI (not production)
+-- diagnose_legacy_tactical_graph.py  # Ad hoc smoke-test for the superseded 010 graph only (renamed from test_agent.py)
+-- test_rag.py                  # Ad hoc manual dev smoke-test (not part of the pytest suite)
+-- check_docstrings.py          # Spec Kit / Constitution compliance check
+-- check_duplication.py         # Constitution IX duplication scanner
+-- validate_specs.py            # Spec Kit artifact validator
+-- validate_ascii.py            # ASCII-only file checker
+-- get_port.py                  # Free local port finder
+-- clean_repo.bat                # Repo cleanup helper
+-- README.md                    # This file
```

---

## Important Notes

- **Single-Click:** Run `scripts\ARGUS_INSTALLER.ps1` for a one-command install
  with auto-elevation.
- **Elevation Required:** The installer handles Admin elevation internally.
  No need to "Run as Administrator" manually.
- **Self-Contained:** `ARGUS_INSTALLER.ps1` embeds all dependencies internally.
  Copy ONE file and run it anywhere — no `Setup/` directory needed (removed
  2026-07-19; it had no remaining use beyond what this installer already covers).
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
