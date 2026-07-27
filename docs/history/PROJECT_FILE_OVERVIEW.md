Project File Overview — Argus Security Framework

Purpose
-------
This document maps the repository layout, explains the role of each important file and directory, and provides a recommended, professional reorganization plan and checklist to improve readability and maintainability.

Guidelines
----------
- Documentation and master design documents are written in English (project standard).
- Keep the code structure logical: app/ (application), Setup/ (installers), scripts/ (helper scripts), docs/ (documentation), tests/ (tests), reports/ (artifacts).
- Avoid committing generated files: .pyc, __pycache__, desktop.ini, and local databases — .gitignore already covers many of these.

Top-level layout (current) and purpose
-------------------------------------
- app/
  - core/
    - brain.py — Agent orchestration (ArgusBrain). Builds the agent executor and parses LLM output into Pydantic SecurityReport. Contains fallback JSON extraction.
    - llm_factory.py — Ollama LLM factory. Provides NonStreamingOllamaLLM wrapper with safe defaults.
    - agent_factory.py — Builds LangChain AgentExecutor (ReAct) with config-driven settings.
    - prompts.py — The Argus agent prompt template (operational rules, required JSON output schema).
    - schemas.py — Pydantic models: Finding, SecurityReport (structured AI output schema).
    - memory/ — SQLite-based local memory & knowledge graph (argus_intelligence.db). Manages targets, findings, entities, relations.
  - tools/
    - tool_registry.py — WSLBridgeTools facade: public API aggregating focused services.
    - command_runner.py — Executes commands via WSL or SSH, normalizes output, WAF detection, error hints.
    - recon.py — ReconService: subdomain enumeration, recon_suite, prioritization (integrates with memory).
    - scanners.py — VulnerabilityScanners: nikto, ffuf wrappers and report saving.
    - payloads.py — PayloadSuggester: local mirror lookup of PayloadsAllTheThings.
    - crawler.py, evasion.py, reflective_verification.py, self_heal.py, simulation.py, etc. — focused services.
  - GUI/ — Streamlit UI and launcher scripts for the Argus Studio.
  - modules/ — Standalone exploit / reasoning modules (argus_deep_exploit.py, argus_reasoning.py, run_full_recon.py). Executable as scripts.

- Setup/ — Installer scripts to setup host, WSL/Kali, Python environment and Kali tools. Contains requirements.txt and helper shell scripts.
- scripts/ — Windows/PowerShell and batch wrapper installers, health checks, Launch scripts, and test helpers.
- docs/ — existing architecture docs, master documentation, and technical notes. (This file will live here.)
- README.md, CHANGELOG.md, CONTRIBUTING.md — project meta-files.
- __pycache__/, *.pyc, desktop.ini — generated or OS metadata files (should be ignored; .gitignore covers them).
- argus_intelligence.db — local SQLite knowledge base. Consider keeping a seed DB but avoid committing sensitive data.

Recommended reorganization (safe, non-destructive)
--------------------------------------------------
1. Consolidate documentation: Ensure all high-level docs live under docs/ with a clear TOC. Keep Argus_Master_Documentation.md as the canonical reference and add a short README per major subfolder (app/README.md, Setup/README.md, scripts/README.md).

2. Code packaging and naming:
   - Make app a proper package (app/__init__.py exists). Ensure subpackages (core, tools, modules, GUI) have minimal README.md explaining purpose.
   - Group related service classes in app/tools by feature and expose a minimal public API in app/tools/__init__.py (already exists but verify).

3. Tests and examples:
   - Move any ad-hoc tests under tests/ and add a small test matrix or instructions for running them.

4. Artifacts and reports:
   - Place generated reports under reports/ and add this path to .gitignore if not required in repo.

5. Secrets and DBs:
   - Remove/rotate any committed secrets and add argus_intelligence.db to .gitignore unless it is a safe seed DB. Consider storing a seed schema/fixture instead of live DB.

6. Clean repository:
   - Remove unnecessary desktop.ini files from subfolders (these are OS artifacts). Do not delete .pyc if they are generated locally; instead ensure .gitignore prevents them from being committed. Provide a cleanup script for contributors: scripts/clean_repo.bat (safe: deletes __pycache__, *.pyc, desktop.ini, wsl_output.txt).

7. Installer and Setup hygiene:
   - Keep Setup/ scripts focused. Add a short INSTALL.md describing the recommended order: INSTALL_EVERYTHING.ps1 → Setup steps → verify with CHECK_HEALTH.bat.

Suggested next steps (I can implement any or all):
- Create per-folder README files (app/README.md, app/core/README.md, app/tools/README.md).
- Add scripts/clean_repo.bat to remove generated artifacts locally.
- Create docs/PROJECT_FILE_OVERVIEW.md (this file) and docs/TOC.md linking the master docs.
- Offer to run a non-destructive cleanup (create a cleanup script and optionally run it) and stage changes for commit.

Minimal immediate actions to improve readability (recommended first pass)
------------------------------------------------------------------------
- Add: app/README.md (short purpose + how to run GUI and modules)
- Add: scripts/clean_repo.bat (safe cleanup of __pycache__ and desktop.ini)
- Update: docs/TOC.md to reference Argus_Master_Documentation.md and this overview

Do you want the assistant to:
A) Create the README files and the cleanup script now (non-destructive), or
B) Only generate a downloadable Markdown report of the plan and leave code untouched, or
C) Proceed to perform the cleanup (delete __pycache__, desktop.ini) locally in the repo? 

(Reply with A, B, or C or ask for a modified option.)
