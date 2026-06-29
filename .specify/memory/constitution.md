<!--
Sync Impact Report
==================
Version change: 0.0.0 (empty template) -> 1.0.0 (initial ratified set)

Modified principles:
- [PRINCIPLE_1_NAME] -> I. Admin-First Elevation (NON-NEGOTIABLE)
- [PRINCIPLE_2_NAME] -> II. Single-Source Installer
- [PRINCIPLE_3_NAME] -> III. Idempotent & Test-Gated (NON-NEGOTIABLE)
- [PRINCIPLE_4_NAME] -> IV. Platform-Boundary Clarity
- [PRINCIPLE_5_NAME] -> V. Observability & Logging
- [PRINCIPLE_6_NAME] -> VI. English-Only Documentation

Added sections:
- "Security & Operational Constraints" (former [SECTION_2_NAME])
- "Development Workflow & Quality Gates" (former [SECTION_3_NAME])

Removed sections: none

Templates requiring updates:
- .specify/templates/plan-template.md        -> no change (already has Constitution Check gate)
- .specify/templates/spec-template.md        -> no change (generic; principles enforced at review)
- .specify/templates/tasks-template.md       -> no change (generic phase scaffolding)
- .opencode/commands/speckit.constitution.md -> no change (agent-neutral)

Follow-up TODOs: none. All placeholders resolved.
-->

# Argus Security Framework Constitution

## Core Principles

### I. Admin-First Elevation (NON-NEGOTIABLE)

Any script that modifies the host operating system, Windows features, WSL, or the
network configuration MUST self-elevate to Administrator before performing a single
mutating action. Warning the user and continuing without elevation is forbidden.

Rules:
- The installer MUST detect non-admin execution and re-launch itself elevated,
  preserving all original arguments.
- If elevation is declined, the script MUST abort with a clear, actionable message
  and a non-zero exit code. It MUST NOT degrade into a partial run.
- Re-elevation is allowed exactly once, at the very start of execution.

Rationale: a mid-way failure because a privileged step hit a permission wall leaves
the environment half-configured and is the primary source of broken Argus installs.

### II. Single-Source Installer

There MUST be exactly one authoritative entry point that installs, configures, and
validates the full Argus environment. Fragmented multi-file orchestration that
duplicates prerequisite checks across steps is forbidden.

Rules:
- `scripts/INSTALL_EVERYTHING.ps1` is the single source of truth for installation.
- A root-level `INSTALL.bat` exists only as a convenience launcher; it MUST NOT
  contain installation logic of its own.
- Each prerequisite (Python, Ollama, WSL, Kali) MUST be checked exactly once and
  its result reused by every downstream step. Duplicate checks across files are a
  defect.

Rationale: distributed, duplicated logic (the legacy `Setup/Step_*.bat` chain)
causes version drift, path-resolution fragility, and inconsistent behavior.

### III. Idempotent & Test-Gated (NON-NEGOTIABLE)

Every installation step MUST be safe to re-run, and the pipeline MUST be gated so a
failed critical step halts before it cascades.

Rules:
- Every step MUST check whether its target is already satisfied before acting, and
  skip cleanly if it is. Re-running the installer on a healthy system MUST produce
  no errors and no redundant work.
- Steps are ordered by the critical dependency chain (Python -> Ollama -> WSL2 ->
  Kali -> venv -> tools -> SSH). A CRITICAL step that fails MUST abort the run; a
  NON-CRITICAL step that fails MUST be recorded as a warning and must not block the
  final health check.
- The pipeline MUST end with a health check that verifies all key components, and
  this health check MUST be embedded in the installer (no separate manual script
  required).

Rationale: operators re-run installers constantly (after reboots, after fixes).
A non-idempotent installer forces a full clean-up before every retry.

### IV. Platform-Boundary Clarity

Windows-host logic and Kali-guest logic MUST stay strictly separated, with the WSL
bridge as the only permitted crossing point.

Rules:
- Windows-side operations (PowerShell / Batch) MUST NOT assume a Linux tool is
  available on the host, and vice versa.
- Kali-side logic lives in shell scripts run via WSL (e.g. `check_and_install.sh`);
  it MUST be invoked as root inside the target distro and MUST receive only a
  translated WSL path (`/mnt/...`), never a raw Windows path.
- SSH (port 22) is the designated application-level bridge into Kali; tools and
  launchers MUST rely on it rather than ad-hoc command plumbing.

Rationale: confusing the two execution domains causes silent path errors and
permission failures that are extremely hard to diagnose.

### V. Observability & Logging

Installation and launch flows MUST produce an auditable record of every action and
its outcome.

Rules:
- The installer MUST write a timestamped log file under `logs/` for every run, in
  addition to console output.
- Every step MUST record a structured result (step id, name, status, detail) that
  feeds a final summary table.
- Launch scripts MUST report which engine mode (GPU/CPU) and which bridge state
  they are starting in, so a failed boot can be traced.

Rationale: when an install "mostly works", the log is the only artifact that lets
an operator see which component is the holdout.

### VI. English-Only Documentation

All documentation, comments, log messages, and user-facing strings MUST be written
in professional, technical English.

Rules:
- Code comments, README files, and Spec-Kit artifacts MUST be in English.
- Console output and log lines MUST be ASCII-safe English.
- No mixed-language files; no placeholder or template tokens left in committed
  documentation.

Rationale: mixed-language and placeholder-laden docs are unreadable to most
contributors and tools, and signal an unfinished artifact.

## Security & Operational Constraints

- **Target platform:** Windows 10 (build 19041+) or Windows 11, with WSL2 and a
  `kali-linux` distribution. The framework is authorized for defensive security
  testing, CTF, and educational use cases only.
- **Hardware floor:** 8 GB RAM minimum (16 GB+ recommended for AI models), 20 GB+
  free disk on the project drive. The installer MUST warn (not abort) when below
  these thresholds, except for model pulls which MUST be guarded by disk space.
- **AI engine:** Ollama, default model `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest`.
  The model name and pull-retry count MUST be overridable via environment variables
  (`ARGUS_MODEL`, `ARGUS_MODEL_PULL_RETRIES`, `ARGUS_MODEL_MIN_GB`).
- **Offline mode:** The installer MUST support an `-Offline` mode that skips every
  network download and clearly reports what the operator must provision manually.
- **Virtual environment:** Python dependencies MUST live in the isolated
  `Argus_venv/` at the project root; the system Python MUST NOT be polluted.

## Development Workflow & Quality Gates

- **Spec-Kit workflow:** Feature work follows `constitution -> specify -> clarify ->
  plan -> tasks -> implement -> analyze`. No implementation step may begin without
  an approved spec and plan.
- **Syntax gate:** Any PowerShell change MUST pass parser validation
  (`[System.Management.Automation.Language.Parser]::ParseFile`) with zero errors
  before it is considered done.
- **Dry-run gate:** The installer MUST expose a `-DryRun` mode that exercises the
  full control flow and path resolution without mutating the system; it is used to
  validate changes safely.
- **Legacy retention:** Deprecated `Setup/Step_*.bat` scripts are retained as a
  manual debugging fallback but are no longer the supported path. New logic goes
  into the single installer.
- **Review gate:** All PRs/reviews MUST verify compliance with these principles;
  any deviation MUST be justified and documented in the plan's Complexity Tracking.

## Governance

This Constitution is the highest-authority artifact for Argus development decisions
and supersedes any conflicting guidance in README files or older documentation when
a conflict exists.

Amendment procedure:
- Amendments require a documented rationale, a version bump per semantic versioning
  (MAJOR for principle removal/redefinition, MINOR for additions/expansions, PATCH
  for clarifications), and an updated Sync Impact Report at the top of this file.
- A ratified amendment MUST be propagated through the dependent templates listed in
  the Sync Impact Report.

Compliance review: every `/speckit.plan` invocation runs a Constitution Check gate;
violations MUST be either resolved or explicitly justified in the plan's Complexity
Tracking table before implementation begins.

**Version**: 1.0.0 | **Ratified**: 2026-06-27 | **Last Amended**: 2026-06-27
