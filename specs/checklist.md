# Implementation Checklist: Argus Security Framework (Phases 005-014)

**Purpose**: Verify all implementation phases meet spec requirements
**Created**: 2026-06-29
**Updated**: 2026-07-07 — extended to cover Phases 010-014 (previously untracked here; each
phase's own `specs/<phase>/tasks.md` remains the source of truth for individual task items).

---

## Phase 005 — Tool Registry

- [x] CHK001 BaseToolService ABC created in `app/core/registry/base_tool.py`
- [x] CHK002 ToolRegistry class with register/unregister/get_tool/list_tools in `app/core/registry/tool_registry.py`
- [x] CHK003 WSLBridgeTools refactored to use ToolRegistry internally (`app/tools/tool_registry.py`)
- [x] CHK004 14 tools registered via `_register_defaults()` (recon, subdomains, reachability, nikto, ffuf, payloads, secrets, web_search, archive_search, crawler, evasion, self_heal, intelligence, knowledge_graph)
- [x] CHK005 SelfHealingService adapted to implement BaseToolService (`app/tools/self_heal.py`)
- [x] CHK006 ArgusBrainV2 created with dispatch/get_available_tools in `app/core/agent/brain_v2.py`
- [x] CHK007 agent_factory_v2.py with create_default_registry/create_brain/register_all_tools
- [x] CHK008 All 42 legacy WSLBridgeTools methods remain backward-compatible
- [x] CHK009 23 unit tests passing in `tests/test_registry/`

## Phase 006 — Tactical Modules

- [x] CHK010 Import paths fixed in argus_reasoning.py (`core.agent` → `app.core.brain`, `core.tools` → `app.tools.tool_registry`)
- [x] CHK011 Import paths fixed in argus_deep_exploit.py
- [x] CHK012 Import paths fixed in run_recon.py
- [x] CHK013 Import paths fixed in run_full_recon.py
- [x] CHK014 Import paths fixed in map_target.py
- [x] CHK015 Import paths fixed in crawler.py
- [x] CHK016 BaseTacticalModule ABC in `app/modules/base.py`
- [x] CHK017 `__init__.py` refactored with register/run_all/run_module/list_modules
- [x] CHK018 12 import tests passing in `tests/test_modules/`

## Phase 007 — Reflective Verification

- [x] CHK019 In-memory command history tracking in `ReflectiveVerificationService`
- [x] CHK020 Infinite-loop detection: 3+ identical consecutive commands blocked
- [x] CHK021 History limited to last 10 entries (MAX_HISTORY = 10)
- [x] CHK022 Delegation methods in WSLBridgeTools: verify_command, verify_output, assess_difficulty
- [x] CHK023 3 new tools registered: verify_command, verify_output, assess_difficulty
- [x] CHK024 20 unit tests passing in `tests/test_tools/test_reflective_verification.py`

## Phase 008 — Self-Healing

- [x] CHK025 health_check() method with WSL/Ollama/Python checks
- [x] CHK026 `_check_wsl()` via subprocess (wsl --status)
- [x] CHK027 `_check_ollama()` via HTTP GET localhost:11434/api/tags
- [x] CHK028 `_check_python()` verifying sys.version and venv
- [x] CHK029 restart_service(name) for ollama and wsl
- [x] CHK030 `_restart_ollama()` (taskkill + ollama serve)
- [x] CHK031 `_restart_wsl()` (wsl --terminate + verify)
- [x] CHK032 system_self_heal unchanged (backward-compatible)
- [x] CHK033 10 unit tests passing in `tests/test_tools/test_self_heal.py`

## Phase 009 — GUI

- [x] CHK034 Imports fixed in argus_gui.py (`core.*` → `app.*`)
- [x] CHK035 desktop_gui.py created (Tkinter desktop with target input, run button, output area)
- [x] CHK036 Graceful Tkinter fallback: clear error if Tkinter not installed
- [x] CHK037 studio.py created as alias re-exporting app.py
- [x] CHK038 3 import validation tests passing in `tests/test_gui/`

## Cross-Cutting

- [x] CHK039 All 88 tests pass (pytest tests/ -v)
- [x] CHK040 All Phase 005-009 tasks committed with descriptive messages
- [x] CHK041 Commit strategy followed (commit per completed phase)
- [x] CHK042 Architecture v2 alignment maintained across all phases

---

## Phase 010 — LangGraph Agent

- [x] CHK043 `build_tactical_graph()` implements recon → scanner → exploit → reflective →
  self_heal/post_exploit as a LangGraph `StateGraph` (`app/core/agent/graph.py`)
- [x] CHK044 Conditional `reflective → {exploit, END}` edge added so an exhausted retry
  budget ends the run instead of guaranteeing one more failed exploit attempt
  (`app/core/agent/graph.py::_route_after_reflective`)
- [x] CHK045 Recon degrades explicitly (never silently) when nmap can't confirm a port:
  `-Pn` retry tagged `ports_scan_degraded`, whatweb-confirmed scheme-port inference tagged
  `ports_inferred` (`app/tools/recon.py`, `app/core/agent/nodes/recon.py`)
- [x] CHK046 Scanner falls back to the target's own URL scheme when `open_ports` is empty
  and persists it back into state so exploit doesn't redundantly fail
  (`app/core/agent/nodes/scanner.py`)
- [x] CHK047 30/33 tasks checked in `specs/010-langgraph-agent/tasks.md`; remaining 3
  (T027/T029/T031-T033-range) are explicitly tracked as out-of-scope, not silent gaps
- [x] CHK048 163/163 pytest passing per CHANGELOG.md validation entry (2026-07-07),
  excluding one pre-existing unrelated network-dependent test

## Phase 011 — GUI Enhancement

- [x] CHK049 Non-functional Blackboard status, Knowledge Graph, and dashboard buttons wired
  to real backend data (commit `179e979`)
- [x] CHK050 Blocking sleep-loop polling replaced with non-blocking `st.fragment` (commit `1186adb`)
- [x] CHK051 Agent state-file write race between parent/child process removed (commit `194dbc5`)
- [ ] **CHK052 (OPEN — tracking gap)** `specs/011-gui-enhancement/tasks.md` still shows 0/31
  tasks checked (`[ ]` on every line) despite the corresponding code (`app/GUI/dashboard.py`,
  `agent_controller.py`, `blackboard.py`, etc.) existing and the fixes above being merged and
  live-validated. The work is done; the tracking file was never updated to reflect it. **Action
  owner must reconcile `specs/011-gui-enhancement/tasks.md` against actual code before this
  phase can be marked compliant** — not fixed in this pass, since marking 31 individual items
  done requires per-item code verification, not a blanket check.

## Phase 012 — Spec Reconciliation

- [x] CHK053 32/33 tasks checked in `specs/012-spec-reconciliation/tasks.md`

## Phase 013 — LangGraph Workflow

- [x] CHK054 34/34 tasks checked in `specs/013-langgraph-workflow/tasks.md`

## Phase 014 — Containerized Lab

- [ ] CHK055 5/13 tasks checked in `specs/014-containerized-lab/tasks.md` — in progress
- [x] CHK056 `deploy/docker-lab/{Dockerfile,docker-compose.yml}` present, version-pinned
  (`ollama/ollama:0.3.14`, `juice-shop:v17.1.1`, gobuster 3.6.0, ffuf 2.1.0, subfinder 2.6.6 — FR-006)
- [x] CHK057 Lab is additive/optional and does not alter the WSL production path (FR-007)

## Phase 017 — Restore ReAct Agent (Canonical Reconciliation)

- [x] CHK064 `app/core/agent/brain_tools.py::build_argus_tools()` — one canonical 12-tool
  list for `ArgusBrain`, replacing the pattern of hand-copying it into every GUI file
  (verified: `tests/test_registry/test_brain_tools.py`, 3/3 passing)
- [x] CHK065 `app/core/agent/react_callback.py::LiveFeedCallbackHandler` — streams
  Thought/Action/Observation/error/finish into the existing state-file event contract
  (verified: `tests/test_registry/test_react_callback.py`, 6/6 passing)
- [x] CHK066 `scripts/run_agent.py` rewritten to drive `ArgusBrain.ask()` instead of
  `build_tactical_graph()`; timeout-bounding thread wrapper and demo/test fallback preserved
  unchanged; `_build_final_state()` never fabricates a structured report when the LLM's
  output didn't parse (`parse_warning` instead) — verified end-to-end with an injected
  `FakeListLLM` (no live Ollama/WSL needed), and unit-tested:
  `tests/test_modules/test_run_agent.py`, 4/4 passing
- [x] CHK067 `app/GUI/tabs/agent.py` Final Results section renders the real
  `SecurityReport` shape (risk score, findings, next steps, full report) instead of the old
  open_ports/vulnerabilities/exploit_success metrics — verified with a real Streamlit
  `AppTest` run against a completed-run state file, zero exceptions, findings content
  confirmed present in rendered output
- [x] CHK068 `app/core/agent/graph.py` and its nodes retained unmodified (Constitution VII);
  `tests/test_modules/test_tactical_graph_termination.py` still passes
- [x] CHK069 `specs/010-langgraph-agent/spec.md` status line updated to record the
  supersession; `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability matrix row 010 updated,
  new row 017 added

## Phase 018 — Structured Agent Reliability

First real production run of 017 (against `https://www.cultbeauty.co.uk/`) timed out after
900s with zero results - full incident + fix in `specs/018-structured-agent-reliability/`.

- [x] CHK070 Root cause confirmed from the real run log: WhiteRabbitNeo-V3-7B repeated
  identical malformed non-ReAct output on every retry; `ArgusBrain`'s claimed
  ReAct->SimpleChain fallback never actually existed (`_get_react_agent`/`_get_simple_chain`
  built the identical `AgentExecutor`, differing only in `verbose`)
- [x] CHK071 Web research conducted (Ollama structured-outputs docs, LangChain/LangGraph
  reliability patterns) confirming schema-constrained decoding as the standard fix -
  `specs/018-structured-agent-reliability/research.md`
- [x] CHK072 `app/core/agent/react_workflow.py::_try_structured_final_answer()` added,
  applying the same structured-decoding fix already used for tool selection to the final
  report shape (verified: `tests/test_langgraph_workflow.py`, 3 new tests passing)
- [x] CHK073 Independent bug fixed: `route_after_parse()`'s format-error branch previously
  had no `max_iterations` check at all (unlike the tool-execute path) - unbounded except by
  LangGraph's default `recursion_limit` (25), via an ungraceful `GraphRecursionError`.
  Regression test: `test_custom_graph_format_error_loop_respects_max_iterations`
- [x] CHK074 `ArgusBrain` rewired to `react_workflow.build_workflow().stream()` instead of
  `agent_factory.py`'s classic `AgentExecutor`; `ask()`'s external contract unchanged (017's
  `scripts/run_agent.py`/`brain_tools.py`/`app/GUI/tabs/agent.py` needed zero changes)
- [x] CHK075 Live incident directly reproduced with a mock LLM replaying the exact failure
  behavior, proving the fix terminates within `max_iterations` (15) with an honest error
  instead of hanging - `test_ask_terminates_within_max_iterations_on_repeated_malformed_output`
- [x] CHK076 Happy path (real structured report + live-feed events via new `on_graph_event`)
  verified unaffected; zero regressions across `tests/test_registry/`,
  `tests/test_langgraph_workflow.py`, and all `017` tests

### Phase 018 addendum — live re-run against a real target (2026-07-09)

T011's live-run follow-up was performed and found four more real bugs plus one
infrastructure-level crash, none reachable by the mock-LLM suite above.

- [x] CHK077 `OllamaLLM.with_structured_output()` confirmed live to raise `NotImplementedError`
  (silently degrading to regex fallback); `llm_factory.py::build_chat_llm()` added, returns a
  `ChatOllama` verified live to support `with_structured_output`; `build_llm()` left untouched
  for its other callers
- [x] CHK078 `get_blackboard_summary()` confirmed to pull every finding across every target ever
  scanned (56 findings / 3 targets, 6123-char fused prompt) - bounded to `max_chars=3000` by
  default, priority/recency-ordered, never truncated mid-entry; regression test updated in
  `tests/test_memory.py::test_large_insert_performance`
- [x] CHK079 `ChatOllama.bind_tools()` succeeding (unlike `OllamaLLM`'s) confirmed to silently
  route `build_workflow()` to the untested prebuilt tool-calling graph instead of this phase's
  custom graph; `ArgusBrain` now calls `_build_custom_workflow()` directly
- [x] CHK080 `extract_target()` confirmed live to read a corrupted target (a Blackboard JSON key)
  from the RAG-enriched query instead of the real target; `ArgusBrain.ask()` now extracts the
  target from the raw pre-enrichment query and passes it explicitly into the graph -
  regression test: `test_ask_extracts_target_before_blackboard_enrichment_not_after`
- [x] CHK081 Intermittent Ollama/CUDA/Windows `llama-server` crash reproduced twice, independent
  of context size, matching upstream `ollama/ollama` issue #16650 - confirmed not fixable from
  application code; mitigated with a scoped one-time retry keyed on the exact error signature
  (`_TRANSIENT_INFRA_ERROR_MARKERS`) plus `OLLAMA_KV_CACHE_TYPE=q8_0`/`OLLAMA_FLASH_ATTENTION=1`
  in `scripts/LAUNCH_STUDIO.bat` to reduce VRAM pressure. Regression tests:
  `test_ask_retries_once_on_transient_ollama_cuda_crash`,
  `test_ask_does_not_retry_non_infra_errors` (non-matching errors are never masked by a retry)
- [x] CHK082 Full suite re-verified green after all five fixes: 186 passed, 1 pre-existing
  unrelated network-dependent failure (`test_smart_web_search.py::test_attempt_limit`)

## Constitution IX — Single Source of Truth (No Duplication)

Enforcement tool: `scripts/check_duplication.py` (built and verified 2026-07-08 -
catches exact-file and normalized-function-body duplication; `--diff` mode
confirmed to only flag newly-touched duplication, not the pre-existing backlog
below). Found via `--all` scan of `app/`, `scripts/`, `Setup/`:

- [ ] CHK058 (OPEN) `Setup/requirements.txt` byte-identical to
  `scripts/Setup/requirements.txt` — pick one canonical file; the other must
  either be deleted or become a generated copy, not hand-maintained twice.
- [ ] CHK059 (OPEN) `_first_web_port` identically defined in both
  `app/core/agent/nodes/exploit.py:11` and `app/core/agent/nodes/scanner.py:11`
  — consolidate into one shared helper (e.g. `app/core/agent/nodes/_shared.py`
  or similar).
- [ ] CHK060 (OPEN) `_build_target_url` identically defined in both
  `app/core/agent/nodes/exploit.py:17` and `app/core/agent/nodes/scanner.py:18`
  — same consolidation as CHK059.
- [ ] CHK061 (OPEN) `_get_conn`/`_get_gui_conn` identical DB-connection logic
  independently defined in `app/GUI/components/session_manager.py:9` and
  `app/GUI/utils/blackboard.py:12` — consolidate into one shared connection
  helper.
- [ ] CHK062 (OPEN, low severity) Identical 2-line `__init__(self, runner,
  memory)` constructor body independently repeated across 5 tool-service
  classes (`app/tools/{crawler,reachability,scanners,secrets,simulation}.py`)
  — candidate for a shared base class, but low urgency since it's idiomatic
  dependency-injection boilerplate rather than accidental drift.
- [ ] CHK063 (OPEN, tracked but NOT simple duplication) `workspace/run_argus_cli.py`
  vs `scripts/run_argus_cli.py` — these started as the same file and have
  since diverged (workspace/ has 4 extra tools); `scripts/TEST_ARGUS.bat`
  depends on the `workspace/` version. Requires a decision on which tool set
  is current before reconciling, not a mechanical delete.

---

## Summary

| Metric | Value |
|--------|-------|
| Phases completed | 5 (005-009) fully; 010 (superseded as production driver, code retained)/012/013/014/017/018 substantially; 011 code-complete but tracking-stale |
| Tasks completed | 60+ (005-009) + 30/33 (010) + 0/31-tracked-but-code-complete (011) + 32/33 (012) + 34/34 (013) + 5/13 (014) + 6/6 (017) + 11/11 (018) |
| Tests written | 68 (new, 005-009) + 13 (new, 017) + 8 (new, 018: 3 in test_brain_ask.py, 1 in test_react_callback.py, 4 in test_langgraph_workflow.py) |
| Total tests passing | 163/163 per CHANGELOG.md 2026-07-07 validation + 13/13 (017) + full test_registry/test_langgraph_workflow suites green (018, 2026-07-08) |
| Commits | 16+ (005-009) + ongoing |
| New files created | 20+ (005-009) + 5 (017) + 4 (018: spec/research/plan/tasks.md) |
| Files refactored | 10+ (005-009) |
| **Open compliance gaps** | **CHK052** (011 task tracking vs. code mismatch); **CHK055** (014 in progress, not a gap — expected); **CHK058-063** (Constitution IX duplication backlog, found 2026-07-08) |
