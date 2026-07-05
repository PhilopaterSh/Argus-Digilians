# Feature Specification: Consolidated Single-File Installer

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-06-27

**Status**: Draft

**Input**: Replace the multi-file installation system (INSTALL_EVERYTHING.ps1 + Setup/*.bat + Setup/*.sh + Setup/requirements.txt) with a single, self-contained PowerShell script that handles all steps: admin elevation, environment verification, Python/WSL/Kali/Ollama setup, venv creation, model pull, Kali tools, SSH bridge, and health check.

---

## User Scenarios & Testing

### User Story 1 - Single-Command Installation (Priority: P1)

As a user, I want to run ONE file to install and configure the entire Argus environment, so I don't need to manually execute multiple steps in order.

**Why this priority**: Core value — every new user needs to install the system.

**Independent Test**: Run the installer on a clean Windows machine. Verify all components are functional at the end.

**Acceptance Scenarios**:

1. **Given** a clean Windows machine, **When** the installer runs, **Then** it should self-elevate to Administrator and proceed without manual intervention.
2. **Given** the installer completes successfully, **When** I run the health check, **Then** all components should report "OK" or "ONLINE".
3. **Given** the installer encounters an error, **When** it fails, **Then** it should report which step failed and exit with a meaningful error code.

---

### User Story 2 - Self-Contained Script (Priority: P1)

As a user, I want the installer to have NO external file dependencies, so I can copy just one `.ps1` file to any machine and run it.

**Why this priority**: Eliminates "file not found" errors from missing Setup/ files.

**Independent Test**: Move only the single `.ps1` file to a new location — run it and verify it works without any companion files.

**Acceptance Scenarios**:

1. **Given** only the single installer `.ps1` file exists, **When** it runs, **Then** it should embed requirements.txt and check_and_install.sh content internally.
2. **Given** the old `Setup/` directory exists, **When** the installer completes, **Then** it should archive or remove the old multi-file setup to prevent confusion.

---

### User Story 3 - Idempotent Re-Runs (Priority: P2)

As a user, I want to re-run the installer without duplicate installations or errors, so I can recover from partial failures.

**Why this priority**: Practical for debugging and CI/CD pipelines.

**Independent Test**: Run the installer twice. Verify component count and state are the same after both runs.

**Acceptance Scenarios**:

1. **Given** a fully installed system, **When** the installer runs again, **Then** it should detect existing components (Python, venv, Kali, Ollama, model) and skip them.
2. **Given** a partially installed system, **When** the installer runs again, **Then** it should resume from the failed step.

---

### Edge Cases

- What happens when the user declines admin elevation? — Script exits with clear message.
- What happens when WSL2 requires a reboot? — Script prompts for reboot and offers auto-restart command.
- What happens when disk space is insufficient for the AI model? — Script warns and skips model pull, suggesting a smaller model.
- What happens in an offline/air-gapped environment? — Script supports `-Offline` flag, skips network installs.
- What happens when Ollama is already running? — Script detects and reuses existing instance.

---

## Requirements

### Functional Requirements

- **FR-001**: Installer MUST self-elevate to Administrator at the very start before any changes.
- **FR-002**: Installer MUST embed all dependencies (requirements.txt content, check_and_install.sh content) internally.
- **FR-003**: Installer MUST support `-Offline` flag to skip all network downloads.
- **FR-004**: Installer MUST support `-Interactive` flag for step-by-step confirmation.
- **FR-005**: Installer MUST support `-DryRun` flag to simulate without system changes.
- **FR-006**: Installer MUST detect and skip already-installed components (idempotent).
- **FR-007**: Installer MUST log all steps to a timestamped file in `logs/`.
- **FR-008**: Installer MUST report a per-step summary table at the end.
- **FR-009**: Installer MUST archive the old `Setup/` directory after successful consolidation.
- **FR-010**: Installer MUST write `check_and_install.sh` and `requirements.txt` temporarily inside WSL, not rely on them being on the Windows side.
- **FR-011**: Installer MUST be identical in both `Argus` and `remote_Argus_PhilopaterSh` branches.

### Key Entities

- **ARGUS_INSTALLER.ps1**: The single self-contained PowerShell script at `scripts/ARGUS_INSTALLER.ps1`.
- **Embedded YAML/Here-String Block**: requirements.txt content stored as a PowerShell here-string.
- **Embedded Script Block**: check_and_install.sh content stored as a PowerShell here-string, written to /tmp inside WSL.
- **Step Sequence**: Self-elevate → System Readiness → Python → WSL/Kali/Ollama → venv+Model → Kali Tools → SSH Bridge → Health Check → Cleanup.

---

## Success Criteria

### Measurable Outcomes

- **SC-001**: Single `.ps1` file — zero external dependencies.
- **SC-002**: Full installation completes in under 30 minutes on a 100Mbps connection.
- **SC-003**: Re-running the installer takes under 2 minutes (all detection-only).
- **SC-004**: Health check reports 5/5 components as OK (venv, Ollama, Kali, SSH, Python).
- **SC-005**: Old `Setup/` directory is renamed to `Setup_legacy/` after first successful run.

---

## Assumptions

- User has Windows 10 (build 19041+) or Windows 11.
- Winget is available on the system (for Python installation).
- User has internet access (unless `-Offline` is specified).
- WSL2 requires a reboot if Windows features are newly enabled.
- The installer is run from the project root (where `scripts/` and `Setup/` exist).
