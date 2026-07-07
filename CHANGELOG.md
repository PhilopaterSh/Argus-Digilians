# CHANGELOG

All notable changes to this project will be documented in this file.

## Fixed: GUI performance + non-functional buttons + empty results (2026-07-07)
Full root-cause writeup with before/after evidence in
`specs/011-gui-enhancement/tasks.md`'s "Post-Implementation Bug Fixes"
section. Summary: Dashboard's 4 Quick Action buttons set a session_state flag
nothing read (fixed by setting `nav_radio`, the sidebar's actual widget key);
`status_bar.py`'s Blackboard readout called `.get()` on a JSON *string*
(`ArgusMemory.get_blackboard_summary()`), always raising `AttributeError`,
silently shown as permanent "N/A" - added a real `get_blackboard_counts()`;
Knowledge Graph's `build_graph_data()` was a stub returning an always-empty
graph - now built from real `targets`/`findings` rows; Dashboard "Recent
Activity" and Reports "Generate Report" both read `session_state.jobs`, which
nothing ever appended to - now read the real `logs/agent_runs/*.json` state
files; the Agent tab's `for _ in range(60): time.sleep(1)` polling loop froze
Streamlit's entire single-threaded session (every button, every tab) for up
to 60 seconds at a stretch - replaced with `st.fragment(run_every="2s")` so
only the feed refreshes on a timer while the rest of the page stays
interactive. `pytest tests/test_gui tests/test_tools tests/test_memory.py`:
79/79 passing.

## Correction (2026-07-07)
Prior audit passes in this changelog stated live Ollama/WSL/SSH were
"unavailable in this sandboxed environment." That was incorrect - they are
genuinely installed and reachable here; the passes never actually attempted
live invocation and defaulted to a cautious assumption instead of testing it.
Corrected by direct verification: WSL boots and runs real commands, Ollama
(with `WhiteRabbitNeo-V3-7B` already pulled) answers real inference requests,
and SSH into Kali works via the project's own `paramiko`-based bridge with
the default `kali`/`kali` credentials. `LAUNCH_STUDIO.bat` was run for real
(non-interactively) and completed cleanly: Ollama check passed, SSH
self-heal (`wsl -d kali-linux -u root -- mkdir -p /run/sshd && sshd`)
started the dormant daemon, and the Streamlit dashboard came up and served
real HTTP 200 content on the configured port. No code or script change was
needed to make this work - the only "fix" was actually testing instead of
assuming. One genuine, minor, previously-undiscovered bug was found and
fixed along the way: `app/tools/self_heal.py`'s `_check_wsl()` decoded
`wsl.exe`'s UTF-16LE stdout/stderr with `text=True` (the platform default
encoding), producing an unreadable, null-byte-interleaved diagnostic message
in the failure path. This never affected the actual pass/fail result (that
was always `returncode`-based and correct) - purely cosmetic, now decoded
explicitly as `utf-16-le`.

## Fixed: dashboard stuck at "Starting reconnaissance..." (2026-07-07)
Root cause was in execution flow, not infrastructure (Ollama/SSH/WSL were all
already online). Three confirmed, independent bugs, found by reading the
actual node/runner code and reproduced live end-to-end against
`scanme.nmap.org` (Nmap Project's public scan-authorized test host):

1. **`app/tools/command_runner.py`'s `_run_ssh()` had no timeout at all** on
   `client.exec_command()`/`stdout.read()` - a hung remote command could
   block forever. `_run_direct_wsl()` had a single hardcoded 600s cap shared
   across every call, with no way for a caller to request a tighter bound.
2. **`scripts/run_agent.py`'s outer graph timeout (`DEFAULT_TIMEOUT_SECONDS
   = 120`) was shorter than a single real recon pass.** `recon_node`
   (`app/core/agent/nodes/recon.py`) runs `ReconService.recon_suite()`
   (`app/tools/recon.py`), which calls `whatweb --aggression 3`, then
   `nmap -sV -T4 --top-ports 100`, then `dig` **sequentially, synchronously**.
   Live reproduction confirmed `nmap -sV` alone routinely takes over 120
   seconds against a real, responsive host. Since `graph.invoke()` runs on a
   `daemon=True` thread joined with `worker.join(timeout_seconds)`, the
   120s outer timeout fired mid-recon on essentially every real (non-demo)
   run, before `recon_node` could ever return - so the graph never reached
   scanner/exploit, and the timeout branch never populates `final_state`,
   which is why Blackboard/Final Results showed nothing.
3. **Duplicate "Starting reconnaissance..." log**: `run_agent.py`'s `main()`
   pre-emptively called `record_state_event()` with the exact same message
   text that `recon_node()` independently writes moments later when the
   graph thread actually starts - two genuinely separate writes to the same
   state file producing the same line, not a retry/loop bug.
4. **`app/tools/evasion.py`'s `EvasionService.advanced_vuln_probe()`**
   (called from `exploit_node`) runs 6 sequential `curl` probes via
   `stealth_run()`, each with a random 1-3s stealth delay and, like the SSH
   path above, no explicit timeout - inheriting whatever generic default
   `CommandRunner.run()` had, sized for full tool scans, not single curl
   requests. Found via a second live repro that got past the (by-then-fixed)
   recon/scanner phases and still hit the outer timeout, this time during
   `exploit_node`.

Fix: added a `timeout` parameter threaded through
`CommandRunner.run()`/`_run_direct_wsl()`/`_run_ssh()` (default 180s, real
`socket.timeout` handling added to the SSH path); `recon_suite()` now passes
explicit per-tool bounds (whatweb 90s, nmap 180s, dig 20s) so recon has a
predictable ~290s worst case; raised `run_agent.py`'s
`DEFAULT_TIMEOUT_SECONDS` to 900s to give the full recon->scanner->exploit
pipeline (whose per-node worst cases stack up across three nodes' worth of
sequential external tool calls) a realistic budget; removed the redundant
pre-emptive event write. `stealth_run()` now defaults to a 20s timeout (curl
probes, not full scans) and each curl call adds `--max-time 15
--connect-timeout 5` so curl enforces its own bound rather than relying only
on the outer process being killed. Also fixed a related latent race:
`app/GUI/utils/agent_controller.py`'s `start()` wrote the run snapshot once
before spawning `run_agent.py` and once again immediately after, both
non-atomic read-modify-write cycles against the same file with no locking,
racing the child process's own writes - consolidated into a single
pre-spawn write. Separately, `app/GUI/tabs/agent.py`'s polling loop only
actively refreshed the feed for a bounded 60 seconds per script run and
never re-triggered itself, so any run taking longer looked "frozen" even
when the backend was healthy - added an `st.rerun()` when the loop's 60s
window elapses while the run is still active.

Validated live across three successive end-to-end reproductions against
`scanme.nmap.org`: run 1 (2m11s, recon timed out gracefully, scanner/exploit
still executed, exactly one recon-start event instead of two); run 2 (recon
succeeded with real open ports `[22, 80, 8008]`, scanner found 15 real
findings, exploit then hit the still-too-tight 600s outer budget - which is
what surfaced bug #4 above); run 3 (with the evasion-probe fix and 900s
budget) confirms full completion. Full `pytest` suite (`tests/test_gui`,
`tests/test_tools`, plus the graph/controller-targeted subset) passes
unchanged, 74/74.

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
