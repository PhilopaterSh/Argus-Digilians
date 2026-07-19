# Converge for 002-consolidated-installer

## Closed

| Item | Status | Notes |
|------|--------|-------|
| `scripts/CHECK_HEALTH.bat` | Removed | Health checking was folded into `ARGUS_INSTALLER.ps1`. |
| `INSTALL.bat` pointing at `scripts/INSTALL_EVERYTHING.ps1` | Updated | Now points at `scripts/ARGUS_INSTALLER.ps1`. |
| `CHECK_HEALTH.bat` references in `LAUNCH_CLI.bat` and `LAUNCH_STUDIO.bat` | Updated | Changed to use the `health` command or `INSTALL.bat health`. |
| Old `.bat` files under `Setup/` | Archived under `archive/` | Kept for reference only. |

## Still open

- Add a `-WhatIf` option to the script.
- Create a CI workflow to run the Pester tests.
- Update `README.md` to document the new usage.
