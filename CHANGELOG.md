# CHANGELOG

All notable changes to this project will be documented in this file.

## [Unreleased]
- Initial structure proposals applied.
- Closed the last two documented test gaps in `specs/010-langgraph-agent/tasks.md`
  (T027, T029), evaluated as the one safe, purely-additive improvement available
  after a conservative options review. `tests/test_modules/test_tactical_graph_termination.py`
  (7 tests) exercises `app/core/agent/graph.py`'s `should_continue()` directly:
  exploit-success termination, dependency-error retry routing, retry-budget
  exhaustion, missing-payload termination, and a config-driven retry bound.
  Extracted the stale-running reconciliation check in `app/GUI/tabs/agent.py`
  into a pure `_reconcile_agent_running_state()` function (behavior-preserving)
  and added `tests/test_gui/test_agent_tab_status.py` (5 tests) proving a
  failed/completed run is never displayed as still running.
- Full install-to-runtime audit pass: re-verified installer PowerShell syntax,
  project compilation, and the import-time-execution sweep (no new issues
  found beyond what earlier passes already fixed). Added genuinely new
  verification depth: `tests/test_gui/test_dashboard_apptest.py` uses
  Streamlit's `AppTest` harness to actually *run* `dashboard.py` and all 6
  tabs in a simulated session (not just import), catching runtime errors an
  import check cannot - zero exceptions found. This also satisfies Cleanup
  Manifest C3's "Streamlit smoke test of dashboard passes" precondition for
  the first time with real evidence. Confirmed `scripts/run_argus_cli.py --help`
  runs cleanly. Explicitly documented what remains unverifiable in this
  sandboxed environment (live WSL/Kali provisioning, live Ollama inference,
  live SSH bridge, full end-to-end recon->exploit runs) rather than assumed
  away - see `docs/ARCHITECTURE_AUDIT_REPORT.md` section 12.
- Completed the pending merge of `fix/setup-script-update` (all conflicts had been
  resolved in the working tree but never committed); fixed a missing `langgraph`
  dependency in `scripts/Setup/requirements.txt` surfaced during review.
- Consolidated Brain/Factory/Workflow per specs/012-spec-reconciliation T025-T030:
  removed dead RAG forwarder shims (`engine.py`/`processor.py`/`vectorstore.py`);
  merged `ArgusBrainV2`/`agent_factory_v2` into `app/core/agent/{brain,agent_factory}.py`
  and deleted the `_v2` shadow files; migrated `app/core/workflow/` into
  `app/core/agent/{react_workflow,react_state,react_prompts}.py` (dropping the
  already-dead `hooks.py`); wired `EmbeddingManifest` into `VectorStore`/`RAGEngine`
  so a stale or provider-mismatched FAISS index is never silently queried; added
  Ollama `format=json` structured Action decoding as the primary parse path, with
  the existing regex parser retained as fallback.
- Fixed two latent bugs found via mypy/testing: `RAGEngine.retrieve()` (and thus
  `format_context()`/`format_combined_context()`, used on every live RAG-enriched
  query) never applied the configured similarity threshold; `llm_factory.build_llm()`
  passed `timeout=3600` as a bare `OllamaLLM` kwarg, which that class silently drops
  (moved to `client_kwargs`, the correct channel).
- Added a `llm=` injection seam to `ArgusBrain.__init__` and new unit tests
  (brain dispatch/ask, agent factory, RAG threshold/manifest wiring) that run
  against `langchain_core`'s `FakeListLLM` and mocked FAISS/embeddings, with no
  live Ollama/FAISS server required.
- Translated the 8 Arabic `specs/*/converge.md` files to English (constitution VI).
- Expanded CI mypy coverage to the consolidated agent/RAG modules; hardened
  `installer.yml`'s Pester job (pinned checkout, explicit Pester module install,
  soft-skip when the test file is absent instead of hard-failing).
- Repository hygiene pass (Cleanup Manifest C2/C3/C4/C6/C7 from
  `docs/ARCHITECTURE_AUDIT_REPORT.md`): untracked generated/runtime artifacts
  (`logs/agent_runs/*.json`, `artifacts/*.zip`). Root-caused *why* they were
  tracked despite looking gitignored: 3 `.gitignore` rules used inline trailing
  comments (`pattern  # comment`) - git does not strip these, so the whole
  comment was part of the literal pattern and the rules matched nothing. Fixed
  by moving all 3 comments onto their own line; verified with `git check-ignore`.
  Moved 13 root-level incident notes into
  `docs/history/`, relocated the misnamed `Plan md/` folder, and retired the
  superseded `INSTALL_EVERYTHING.bat`/`.ps1` installer path (the `scripts/README.md`
  had already documented it as removed). Cleaned 9 pure-scratch files out of
  `workspace/`.
- GUI consolidation (C3): renamed `app/GUI/argus_studio.py` to `app/GUI/dashboard.py`
  per specs/011's naming. Along the way, found and fixed a real misconfiguration:
  `config.yaml`'s `gui_entry` and `app/core/config.py`'s `PathSettings` default were
  both pointing at `gui_app.py` (a crude single-target demo script), not the actual
  modular dashboard - `app/core/agent/contracts.py`'s own
  `STREAMLIT_DASHBOARD_ENTRYPOINT` constant already correctly named `argus_studio.py`
  as canonical. Fixed both config paths plus the two launcher scripts that each
  pointed at a different (and different from each other) GUI file. Added
  deprecation banners to the remaining legacy GUI entrypoints, matching the pattern
  already used by `app.py`.
- Reconciled `specs/010-langgraph-agent/tasks.md` (previously showed 0/33 complete
  despite the tactical agent graph being fully built) and updated
  `specs/013-langgraph-workflow`'s status from "Partially Superseded" to "Fully
  Superseded" now that its migration into `app/core/agent/` is complete. Confirmed
  Manifest C5 (missing `002`/`003-sqlite` spec artifacts) was already done.
- Deleted `app/GUI/gui_app.py` and `app/GUI/gui_root.py`: both executed
  `brain.ask()` unconditionally at import time (no button gate), crashing with
  `'NoneType' object has no attribute 'update'` when Ollama/WSL aren't reachable
  and Streamlit runs in bare mode. Verified 98% identical to each other and fully
  superseded by `app/GUI/dashboard.py`'s `AgentController`-based Agent tab.
  Updated `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`, `IMPLEMENTATION_GUIDE.md`,
  and `specs/012-spec-reconciliation/tasks.md` (T033) to match.
- Fixed a misleading status claim in `app/GUI/argus_gui.py`: it displayed
  "WSL Bridge: ACTIVE" unconditionally regardless of actual reachability; now
  reuses `status_bar.py`'s existing `check_ssh_status()` instead of duplicating
  the check.
- Repo-wide sweep for import-time side effects beyond the GUI package (per
  specs/012's "deterministic imports" principle) found two real, if low-severity,
  cases: `app/core/agent/blackboard.py` created the SQLite schema unconditionally
  on import (moved to lazy init on first `get_connection()` call); `app/core/agent/graph.py`
  read `config.yaml` via `ArgusConfig.load()` at import to set `MAX_RETRIES`
  (moved into a `_get_max_retries()` function called from `should_continue()`).
  Neither depended on Ollama/WSL, so neither could crash in a bare environment -
  both were hygiene fixes, not crash fixes. `app/tools/wsl_bridge.py`'s
  `load_dotenv()` at import and `scripts/run_argus_cli.py`'s pre-`__main__`
  `load_dotenv()`/`ArgusConfig.load()` were reviewed and left as-is: standard,
  low-risk bootstrap patterns for a `.env`-driven module and a CLI entrypoint
  script respectively, not accidental side effects.

## [0.1.0] - 2026-06-22
- Added CONTRIBUTING guidelines.
- Added CI workflow for linting and testing.
- Added pre-commit configuration.
- Added security notes directory and sample note.
- Added logging configuration.
- Added requirements.txt and env.example.
- Added plugins directory with PluginBase stub.
- Updated .gitignore for additional patterns.
