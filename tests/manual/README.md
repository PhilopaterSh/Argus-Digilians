# Manual / Ad Hoc Scripts (not part of the pytest suite)

Everything in this folder is a standalone diagnostic script, not a pytest test. None of it is
collected by `pytest tests/` (per `pytest.ini`'s `python_files = test_*.py`, and separately
because these need live infrastructure - a real WSL/Kali bridge, a real network, or a real
target site - that a CI run shouldn't depend on). They were previously loose files directly
under `tests/`, which made them easy to mistake for real, CI-relevant tests; moved here
2026-07-10 as part of a repo-wide organization pass to make that distinction obvious from the
path alone.

Run each directly with the project's venv Python from the repo root, e.g.:
```
Argus_venv\Scripts\python.exe tests\manual\check_integration.py
```

## Files

- **`check_integration.py`** - Quick sanity check that core config/import wiring hasn't
  drifted (10 checks: `config.yaml` loads, key modules import, a couple of module-level
  constants exist). No live network/WSL needed.
  **Known stale as of 2026-07-10**: checks 7-10 (`command_runner._CMD_TIMEOUT`,
  `web_search._WEB_TIMEOUT`, `recon._TRUNCATE`, `scanners._PROJECT_ROOT`) fail with
  `AttributeError` - a since-refactored module-level-constant pattern that no longer exists on
  these modules. Left failing rather than silently fixed or removed, since diagnosing what (if
  anything) should replace them is a separate task from this reorganization pass.

- **`verify_core.py`** - Manual live check of `WSLBridgeTools.crawl_target()` /
  `.advanced_vuln_probe()` against a real target (`testasp.vulnweb.com`). Needs live WSL/Kali
  and network access. Its import (`from core.tools import WSLBridgeTools`, a pre-reorg path)
  was broken (`ModuleNotFoundError: No module named 'core'`) - fixed 2026-07-10 to
  `from app.tools.tool_registry import WSLBridgeTools`.

- **`ai_benchmark.py`** - Starts a local mock HTTP server (true/false-positive info-disclosure
  scenario) and runs a real `ArgusBrain.ask()` against it, scoring precision/recall/hallucination
  rate. No external network needed (mock server is `localhost`-only), but does need live
  Ollama. **Known limitation**: calls `ArgusBrain` with a hand-picked 2-tool list
  (`Run_FFUF`, `Run_Kali_Command`), not production's real `build_argus_tools()` 17-tool list -
  `specs/025-subtask-benchmark-suite/tasks.md` T001 plans to migrate this exact scenario into a
  proper fixture that fixes that gap; this file is superseded once that lands, not before.

- **`exploit_test.py`** - Manual SQLi/path-traversal probe against a real external site
  (`testasp.vulnweb.com`, a known intentionally-vulnerable test target). Needs live network. No
  Argus imports at all - pure `requests`-based scratch script.

- **`test_cd.bat`** - Trivial one-off diagnostic (prints cwd, checks `Argus_venv\Scripts\activate.bat`
  exists). Despite the `test_` name it is not a pytest artifact (it's a `.bat` file; `pytest.ini`
  only collects `.py`).

- **`verify_parsing_fix.py`** - Moved here 2026-07-10 from `docs/history/` (it was a loose
  executable script sitting in a docs folder). Historical verification script for the
  2026-06-25 ReAct-format-parsing incident - see
  `docs/history/2026-06-25_react_parsing_and_simplechain_fallback_incident.md`. Named to avoid
  pytest's `test_*.py` discovery on purpose; exercises a `use_react`/SimpleChain fallback
  mechanism that no longer exists in the current codebase (superseded by `specs/018`'s
  structured-output graph) - kept for historical reference only, not a meaningful regression
  check today.

## Why these weren't just deleted

Each still has some diagnostic value (per-file notes above) and none is actively harmful sitting
here - the goal of this move was making their non-CI, ad-hoc nature obvious from their location,
not removing working diagnostics. If a file's value drops to zero (e.g. once `ai_benchmark.py`
is fully superseded by `specs/025`'s benchmark suite), delete it then, with that specific
justification - not as part of a blanket cleanup.
