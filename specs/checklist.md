# Implementation Checklist: Argus Security Framework (Phases 005-014)

**Purpose**: Verify all implementation phases meet spec requirements
**Created**: 2026-06-29
**Updated**: 2026-07-24 — corrected the line below again: it went stale a second time after `025`
shipped (2026-07-23, CHK113) while this summary line still lumped it in with the untouched
021-026/028 backlog; the backlog table's own per-row status further down this file was already
correct, this summary line was not (each phase's own `specs/<phase>/tasks.md` remains the source
of truth for individual task items). See the "Backlog — Proposed Future Phases" section near the
end of this file: `019` is implemented, `020` is an experimental feature-flagged-off path, `025`
is implemented and live-verified, and `021`-`024`, `026`, and `028` remain spec-kit-only (not yet
implemented).

**Path note (added 2026-07-24)**: entries below cite test file paths as they existed at the time
each entry's work was done, not necessarily their current location - `tests/test_registry/` was
partially renamed to `tests/test_agent/` (most files moved; `test_base_tool.py`/
`test_tool_registry.py` are the only ones still actually under `test_registry/` today) and
`tests/test_memory.py` became `tests/test_memory/test_memory_service.py`, both in an unrelated
main-branch reorganization (`ac797c5`) before this checklist's later entries were written. If a
cited path 404s, check `tests/test_agent/` and `tests/test_memory/` first before assuming the
referenced test was removed.

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
- [x] **CHK052 (RESOLVED 2026-07-09)** `specs/011-gui-enhancement/tasks.md` showed 0/31
  tasks checked despite the corresponding code (`app/GUI/dashboard.py`, `agent_controller.py`,
  `blackboard.py`, etc.) existing and the fixes above being merged and live-validated. Reconciled:
  each of the 31 tasks was individually re-verified against actual code (grepped function/class
  names directly, not assumed) - all 31 confirmed done, most under a `pages/` -> `tabs/` rename
  that happened during implementation but was never reflected in the spec's task names. Full
  detail and per-task evidence in `specs/011-gui-enhancement/tasks.md`'s reconciliation note.

## Phase 012 — Spec Reconciliation

- [x] CHK053 32/33 tasks checked in `specs/012-spec-reconciliation/tasks.md`

## Phase 013 — LangGraph Workflow

- [x] CHK054 34/34 tasks checked in `specs/013-langgraph-workflow/tasks.md`

## Phase 014 — Containerized Lab

- [ ] CHK055 5/13 tasks checked in `specs/014-containerized-lab/tasks.md` — in progress
- [x] CHK056 `deploy/docker-lab/{Dockerfile,docker-compose.yml}` present, version-pinned
  (`ollama/ollama:0.3.14`, `juice-shop:v17.1.1`, gobuster 3.6.0, ffuf 2.1.0, subfinder 2.6.6 — FR-006)
- [x] CHK057 Lab is additive/optional and does not alter the WSL production path (FR-007)

## Phase 016 — Docstring Enforcement

- [x] CHK114 (DONE 2026-07-24) `scripts/check_docstrings.py` (FR-001-005, NFR-001/002) was
  already in place from an earlier session as the diff-scoped, CI-blocking gate (stdlib `ast`
  only). This entry tracks FR-006/FR-007's retrospective backfill of the pre-existing 511+
  non-compliant functions, done per-directory in 15 reviewed batches/commits (not one bulk
  automated pass, per FR-006's explicit prohibition), tracked live in
  `specs/checklist-docstring-backfill.md`: `scripts/`, `app/tools/`, `app/core/rag/`, `app/GUI/`,
  `app/core/agent/` (3 sub-batches, done last given its documented bug history), `app/modules/`
  incl. `experimental_agent/`, 5 previously-untracked `app/core/` files found via a fresh
  full-repo scan (`config.py`, `prompts.py`, `safety.py`, `memory/memory_service.py`,
  `registry/tool_registry.py`), and ~72 test-fixture functions across ~20 test files.
  `check_docstrings.py --all app scripts tests` now reports **0 violations across all 918
  scanned functions**, repo-wide (SC-001/SC-002 fully met, not just trending).
- [x] CHK115 (DONE 2026-07-24) Real inaccuracies caught and fixed *before* committing, each via
  re-reading the actual code rather than assuming behavior (the discipline FR-006's "worse than
  no docstring" warning exists for): `RAGConfig.from_dict()`'s per-field fallback is to `cls()`'s
  own dataclass defaults, not `from_central()` as first drafted; `_tech_probe_succeeded()` returns
  False (not True) for empty input; `Verifier.verify_xss()`'s no-match fallback returns the bare
  `{url}{sep}{param}=` with no payload appended, not the last-tried payload's URL. None of these
  were pre-existing bugs in the code itself - all were docstring-drafting mistakes caught during
  this backfill, before they shipped.
- [x] CHK116 (DONE 2026-07-24) A real quirk in `check_docstrings.py`'s own AST walk was found and
  documented (not fixed - out of scope for a docstring-content task, and changing shared CI
  enforcement logic wasn't authorized here): `walk_own_body()` doesn't exclude a nested `def`'s
  own top-level position in the parent function's body before descending into its children, so an
  outer function containing an inline `def helper(): return x` gets a false "needs Returns" flag
  for a return that isn't actually its own. Hit repeatedly (`tests/manual/verify_parsing_fix.py`,
  `tests/test_tools/test_reachability.py`) - worked around by documenting each affected function's
  real return behavior (often `Returns: None`) rather than papering over it with a fabricated
  return-value claim. Recorded in `specs/checklist-docstring-backfill.md`'s header for whoever
  next touches the gate script.
- [x] CHK117 (DONE 2026-07-24) Alongside the docstring backfill, a full `pytest.mark.unit`/
  `integration` audit was completed for every collected test file (not part of spec 016 itself,
  done in the same session on explicit request): unit coverage raised from 10/339 to 279/339,
  integration from 0 to 36/339, each classification verified by reading the file for real
  external-boundary calls (not assumed from directory location) - e.g. `test_core/test_safety.py`
  is split per-class (`TestSafetyLayerPorted` unit, `TestMemoryPorted` integration) since only the
  second touches a real (if tmp-file-isolated) SQLite DB via `ArgusMemory`, matching this
  project's own `pytest.ini` wording ("integration: ... ephemeral SQLite ...") rather than
  guessing from the file's location. 4 GUI test files were deliberately left unmarked
  (`test_dashboard.py`, `test_dashboard_apptest.py`, `test_imports.py`, `test_session.py`) since
  they write to the real shared `data/argus_intelligence.db` or run a full Streamlit `AppTest` -
  confirmed by diffing the DB file's checksum before/after the unit-only run (unchanged) versus
  the full suite (changed).
- [x] CHK118 (DONE 2026-07-24) Same session, unrelated to 016/pytest-markers: a user question
  about using `graphify` for target-relationship graphing led to discovering and fixing (ADR-22,
  `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`) that `Query_Knowledge_Graph` had no live data
  behind it - see that ADR for detail. A follow-up question about a specific GitHub repo
  (`uphiago/recon-skills`, offered as a possible source of recon technique content for RAG)
  was investigated by cloning and reading it directly rather than trusting its README summary:
  `SOUL.md` describes "autonomous offensive reconnaissance at scale" selecting SMB targets
  (bakeries, churches, daycare centers, etc.) by vulnerability "yield rate," with zero mention
  of authorization/scope anywhere, and field results citing real named domains and government
  infrastructure ("Monaco government infrastructure," "Brazilian state networks"). A deeper pass
  found the contamination isn't confined to that framing layer: individual `redteam/hunt-*`
  technique files (otherwise built from legitimate public bug-bounty-report citations) embed
  real, unredacted victim domains as recurring case studies (e.g. `hunt-cors/SKILL.md`: "
  gocarwash.com (car wash...) — CRITICAL CORS", "dogtopia.com (pet grooming...) — CRITICAL
  CORS", matching `SOUL.md`'s own sector list) alongside dozens of repeated
  category-anonymized-but-likely-real domains (`retail-chain.com` x30, `mattress-retailer.com`
  x10, etc. across many files) - concluded no reliable subset could be curated without
  rewriting most files' substantive content, so nothing from that repo was imported. Instead
  authored `knowledge_base/vulnerability_class_reference.md` from scratch (public OWASP Testing
  Guide/PortSwigger Web Security Academy-class methodology only, matching
  `exploitation_techniques.md`'s existing style/provenance) covering the 4 vulnerability classes
  `benchmarks/fixtures/` exercises that weren't yet in the knowledge base (XSS, IDOR, SSTI,
  Information Disclosure) plus CORS misconfiguration. User then asked to go as deep/broad as
  possible on this same file rather than importing anything further from the rejected repo -
  extended it with the remaining 4 of `app/tools/payloads.py::PayloadSuggester`'s 8 signal-map
  categories not yet covered (Command Injection, Insecure File Upload, NoSQL Injection, GraphQL
  Injection/introspection abuse) plus 8 further OWASP Top 10/API Top 10-class sections with no
  existing Argus tool mapping yet (SSRF, XXE, CSRF, JWT/auth-token attacks, Insecure
  Deserialization, HTTP Request Smuggling, Open Redirect, Race Conditions) - 12 new sections,
  same detection/bypass-pattern/verification-pitfall structure as the first 5, same
  zero-named-real-target discipline. Request Smuggling and Race Condition sections explicitly
  flag their own testing risk to *other* real users sharing a target's connection pool/rate
  limiter and recommend cautious, bounded probing - consistent with this project's existing
  "no destructive testing" stance elsewhere. Verified it loads and structurally chunks correctly
  via the real `DocumentProcessor.process_directory()` (21 chunks from this file; 35 total
  across `knowledge_base/`, up from 14 before this session) and passes `validate_ascii.py`.
- [x] CHK119 (DONE 2026-07-25) Same session: live-benchmarked `qwen3-vl:8b-thinking` (researched
  earlier in this session as the top vision/tool-use/reasoning candidate to potentially replace
  `ArgusConfig.model_name`'s default) against the current `WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M`
  using the real `benchmarks/runner.py` harness (`--configs-json` overriding `model_name` per
  config, no code changes needed) across all 5 `benchmarks/fixtures/`. Result (full report:
  `benchmarks/results/20260725T060935Z_report.md`): **WhiteRabbitNeo strictly dominated on every
  metric** - 0/5 SR for both (neither retrieved a flag), but WhiteRabbitNeo scored 0.33 mean SCR
  on all 5 fixtures (found the vulnerable endpoint every time; never completed exploitation/
  verification) in 41-200s each, while `qwen3-vl:8b-thinking` scored 0.00 SCR on all 5 (zero
  subtask progress) and hit the harness's 280s timeout on every single fixture. Root-caused via
  a step-by-step diagnostic (`ArgusBrain` construction -> `ask()`) rather than assumed: the model
  answers a short, simple ReAct-format prompt correctly and fast (~9.5-9.8s, both plain
  `.invoke()` and `with_structured_output()`), but under Argus's actual production system prompt
  (RAG+Blackboard fusion, 17-tool descriptions, ~5100 chars) it burned all 25 ReAct iterations
  over 1646s (27+ minutes) with no further tool call ever printed after the initial recon phase -
  consistent with "thinking" mode's reasoning-chain length scaling sharply with prompt
  complexity. Documented in full, including the revised multi-model-pipeline decision this
  finding also fed into, in `specs/020-multi-agent-role-separation/research.md`'s 2026-07-25
  addendum and `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` ADR-20's addendum note. No
  `ArgusConfig.model_name` change was made - the measured result does not support one
  (Constitution VIII: a slower, less-capable-in-practice model is not an improvement regardless
  of its research-backed capability profile in isolation).

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
- [x] CHK083 (DONE 2026-07-09) Model switched from the F16
  `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest` (~15GB, ~500MB VRAM headroom - the direct
  contributing factor to CHK081's crash) to the Q5_K_M-quantized
  `hf.co/bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M` (~5.4GB, ~95% of F16 quality
  per quantization research). User-confirmed direction after comparing against a base-model swap
  (Qwen3, rejected - no mature small uncensored/pentest-tuned variant exists, and WhiteRabbitNeo's
  security-domain fine-tuning was judged more valuable than marginal tool-calling gains this
  phase's scaffolding fixes already captured). Live-verified end-to-end: valid structured tool
  calls and a correctly parsed `SecurityReport` final answer, GPU usage ~7.9GB/16GB throughout
  (vs ~15.8GB before) - no crash.
- [x] CHK084 (DONE 2026-07-09) `check_reachability()` passed a full scheme-qualified URL straight
  to `ping`, which always fails with "Name or service not known" regardless of whether the host
  is actually up - live-discovered against `https://scanme.nmap.org`, which the agent reported as
  DOWN immediately before a real nmap scan (via `Recon_Suite`) found it up with open ports 22/80.
  Fixed by reusing `app/tools/utils.py::normalize_domain_for_memory()` to strip scheme/port before
  building the ping command. New `tests/test_tools/test_reachability.py` (no prior coverage
  existed) - 5 tests. Also ran `scripts/check_docstrings.py` (specs/016) against every file
  touched this session and closed the Google-style docstring gaps it found in new/modified code
  (`check_reachability`, `_first_web_port`, `get_gui_db_connection`, `exploit_node`,
  `scanner_node`) - `app/GUI/components/session_manager.py`'s 5 functions have pre-existing
  docstring gaps unrelated to this session's one-line import change there, left as known debt.
- [x] CHK085 (DONE 2026-07-09) Live testing against `https://scanme.nmap.org` (post-CHK084)
  reproduced a real, repeating bug: the model called `Recon_Suite` with the *identical* input 4
  times in a row despite complete success on the first call - `react_prompts.py`'s own Rule 2
  ("NEVER repeat the same tool with the exact same input") is advisory text the model doesn't
  reliably follow on its own. Fixed structurally rather than trusting the prompt alone:
  `react_workflow.py`'s `execute_node` now records each successful `"{tool}::{input}"` pair into
  new state field `tool_call_history`; `parse_node` blocks a repeat of any pair already in that
  history with a "you already called this" Observation instead of re-executing (new `phase`:
  `"duplicate_call"`, routed through the same `max_iterations`-bounded loop as `format_error`).
  Also surfaced `tool_call_history` directly in the prompt (`react_prompts.py`'s new
  `TOOLS ALREADY CALLED THIS RUN` block) so the model can see what it already tried without
  relying on memory of the conversation - prevention, not just reaction. New tests:
  `test_custom_graph_blocks_identical_repeated_tool_call`,
  `test_custom_graph_duplicate_call_loop_respects_max_iterations`. Live-reverified against the
  exact scenario that exposed the bug: `Recon_Suite` now executes once, a repeat attempt is
  blocked with zero extra nmap runs, and the model produces a complete real `SecurityReport`
  immediately after. Full suite: 193 passed, 1 pre-existing unrelated failure.
- [x] CHK086 (DONE 2026-07-09) Follow-up live run with CHK085's fix active surfaced three more
  real, distinct issues, all fixed and live-reverified together:
  1. **Oscillation between two blocked tools**: once `Run_Nikto` and `Smart_Web_Search` were
     both individually blocked as duplicates, the model alternated re-proposing those same two
     for 3 more turns instead of trying a genuinely new tool (`Run_FFUF` was never attempted).
     Fixed: the duplicate-block Observation now explicitly lists every tool NOT yet tried this
     run by name, giving a concrete next step instead of vague "try something different"
     guidance.
  2. **`Run_Nikto`/`Run_FFUF` targeting the wrong closed port**: the model called `Run_Nikto`
     against `https://scanme.nmap.org` (port 443, closed per its own earlier Nmap scan) instead
     of the actually-open port 80/http, so Nikto failed to connect. Fixed at the code level, not
     the prompt: `app/tools/scanners.py`'s `run_nikto`/`run_ffuf_discovery` now auto-retry once
     with the opposite scheme (http<->https) on a connection failure/empty result, mirroring
     `app/tools/recon.py`'s existing nmap ->nmap -Pn fallback pattern - reliable regardless of
     what the model passes in. New `tests/test_tools/test_scanners.py` (no prior coverage
     existed) - 7 tests.
  3. **`overall_risk_score` inconsistent with findings' severities**: one live run produced
     `overall_risk_score: 10` (maximum) while every finding was `severity: Low` with
     "No remediation needed". Fixed: new Rule 6 in `react_prompts.py` requires the score to
     match the findings' actual severities.
  New `tests/test_registry/test_react_prompts.py` (no prior coverage existed for this module) -
  5 tests locking in the PHASE-progression, thoroughness, and risk-score-consistency guidance
  text. Live-reverified all three together against the exact target that exposed them: the
  model picked `Smart_Web_Search` then `Run_Nikto` (two genuinely different tools, zero
  oscillation) after `Recon_Suite` was blocked; `Run_Nikto`'s scheme-fallback fired
  (`"Nikto could not connect to https://... - retrying with http://..."`) and succeeded,
  producing real findings (outdated Apache 2.4.7, `mod_negotiation`/MultiViews); the final
  report had two `High`-severity findings and `overall_risk_score: 8` - consistent this time.
- [x] CHK087 (DONE 2026-07-09) A follow-up review of CHK085/086 found the duplicate-call block
  was zero-tolerance (blocked on the very first repeat), which is *stricter* than the original
  `app/core/prompts.py` design's own explicit tolerance ("do not execute the same tool with the
  same input more than **TWICE**") - leaving the model no room to retry a result it genuinely
  doubts (e.g. a transient network blip), only to abandon a call after a single attempt.
  Loosened `parse_node`'s check from "blocked if this pair has been called at all" to "blocked
  only once this pair has been called **twice** already" (`.count(call_key) >= 2`), restoring
  the original design's tolerance while still capping runaway repetition. Updated
  `react_prompts.py`'s Rule 2 and the `TOOLS ALREADY CALLED THIS RUN` framing to describe the
  one-retry allowance accurately. Renamed/updated
  `test_custom_graph_blocks_identical_repeated_tool_call` ->
  `test_custom_graph_allows_one_retry_before_blocking_third_identical_call` to assert the tool
  executes twice for real before the third identical attempt is blocked. Full suite (all of
  CHK085-087 together): 205 passed, 1 pre-existing unrelated failure.
- [x] CHK088 (DONE 2026-07-09) User asked why the GUI's Agent tab feed seemed to update only
  after the whole run finished rather than live. Verified directly rather than assumed: started a
  real run through `AgentController` (the actual GUI mechanism, not the diagnostic CLI script)
  and watched the state file's `events` array grow with real timestamps -
  `16:34:39` (Thought/Action) -> `16:34:48` (~3s later, a real ping) -> `16:34:54` (next Thought)
  -> `16:35:48` (**54s later**, real subdomain enumeration). Confirmed the live-feed mechanism
  (`LiveFeedCallbackHandler`/`append_run_event`, `st.fragment(run_every="2s")`) genuinely writes
  and polls incrementally, not in one batch - the perceived "batch" feeling is real external tool
  latency (30s-3min per tool: nmap/nikto/ffuf), not a code bug.
  While investigating, found and fixed a real, separate bug: `AgentController.start()` generates
  a `run_id` to name the state file, but `scripts/run_agent.py::main()` independently generated
  a SECOND, different `run_id` and overwrote the state file's own `run_id` field with it - the
  file's name and its content disagreed about the run's identity. Fixed: `start()` now passes
  `--run-id` to the subprocess; `main()` uses it verbatim, falling back to a fresh uuid4 only for
  standalone/manual invocations without the flag. New tests in `tests/test_modules/test_run_agent.py`:
  `test_main_uses_the_provided_run_id_verbatim`, `test_main_falls_back_to_a_generated_run_id_when_not_provided`.
  Full suite: 207 passed, 1 pre-existing unrelated failure.
- [x] CHK089 (DONE 2026-07-09) User reported the GUI itself feels heavy/slow when clicking or
  navigating tabs (a separate symptom from CHK088's live-feed question). Root cause found by
  reading `app/GUI/dashboard.py`: `render_status_bar()` is called at the top level of every page
  render, and Streamlit reruns the *entire script* on any widget interaction (any click, any tab
  switch) - so `check_ssh_status()`, which spawned a whole new `powershell.exe` process
  (`Test-NetConnection`) on every single call, ran on **every click anywhere in the app**.
  PowerShell's own cold-start overhead (hundreds of ms, often 1s+) on top of the actual check
  made the whole GUI feel heavy, exactly as reported. Also discovered live, while diagnosing this
  same report, an unrelated but real issue: a stale Streamlit process from **2 days earlier**
  (July 7) was still bound to port 12199 alongside a fresh one started today, silently serving
  some of the user's requests on pre-fix code the whole time it went unnoticed - killed.
  Fixed `check_ssh_status()`: replaced the `powershell.exe`/`Test-NetConnection` subprocess with
  the same lightweight raw socket connect `check_ollama_status()` already used for Ollama's port
  - no process spawn at all. Both functions also wrapped in `@st.cache_data(ttl=5)` as a second
  layer of protection against repeated reruns. New `tests/test_gui/test_status_bar.py` (no prior
  coverage existed for this module) - 6 tests, including one asserting no subprocess is spawned.
  Full suite: 213 passed, 1 pre-existing unrelated failure.
- [x] CHK090 (DONE 2026-07-09) User asked to "extract the greatest benefit from all existing
  files." Audited every real public method on `WSLBridgeTools` against `brain_tools.py`'s
  supposedly-canonical tool list and found real, working capabilities the agent had no way to
  invoke: `analyze_secrets` (leaked API key/credential detection - in *no* tool list anywhere),
  and `crawl_target`/`advanced_vuln_probe`/`verify_command`/`assess_difficulty` (in a *sixth*,
  independently-drifted copy, `scripts/run_argus_cli.py`, but not in the "canonical" one - the
  original consolidation had silently become incomplete relative to a list it was supposed to
  replace). Added all 5 as new tools (`Secret_Scanner`, `Crawl_Target`,
  `Advanced_Evasion_Probe`, `Reflective_Pre_Verify`, `Task_Difficulty_Assessment`) to
  `brain_tools.py` (12 -> 17 tools); `scripts/run_argus_cli.py` now imports
  `build_argus_tools()` instead of re-declaring its own drifted list. Updated
  `react_prompts.py`'s PHASE guidance to actually reference all 5 (Phase 2: Crawl_Target;
  Phase 4: Secret_Scanner; Phase 6 reframed as real exploitation - Exploit_Suggester research
  *then* Advanced_Evasion_Probe attempt, not research alone; utility tools:
  Reflective_Pre_Verify/Task_Difficulty_Assessment).
  Live-verified all 5 directly (bypassing non-deterministic LLM tool selection for a faster,
  more targeted check): found and fixed a real bug in the process -
  `crawl_target`/`analyze_secrets`'s curl calls had no `--max-time`/`--connect-timeout`, unlike
  `advanced_vuln_probe`'s existing ones, so a live check against a currently-unreachable practice
  site showed these would otherwise block on `command_runner.py`'s much longer generic default
  timeout instead of failing fast - fixed to match the existing pattern. Re-verified against
  `scanme.nmap.org`: all 5 completed correctly (`Crawl_Target` genuinely found 0 links - confirmed
  by independently checking the raw HTML, not a bug; `Secret_Scanner`/`Advanced_Evasion_Probe`
  correctly reported clean; `Reflective_Pre_Verify`/`Task_Difficulty_Assessment` both produced
  real, correct reports). New `tests/test_tools/{test_crawler,test_secrets}.py` (no prior
  coverage existed for either module) and extended `test_brain_tools.py`/`test_react_prompts.py`.
  Full suite: 222 passed, 1 pre-existing unrelated failure.
- [x] CHK109 (DONE 2026-07-10) User recalled the old `app/core/prompts.py`/`agent_factory.py`
  path (pre-specs/018, `max_iterations=50`, free-text parsing, 9-phase prompt) used to run for
  roughly an hour and asked why current runs are shorter/lighter. Investigated and explained
  honestly rather than just reverting: the old system's long runtimes were often the same
  failure-retry loop CHK070's incident proved (900s/26 retries/zero results against
  `cultbeauty.co.uk`), not necessarily extra thoroughness - but a real tradeoff does exist, since
  the current 7-phase prompt has no analogue of the old "Chaining & Escalation" phase and
  `DEFAULT_MAX_ITERATIONS=15` leaves little room for one. User approved restoring the depth on
  top of (not instead of) specs/018/019's reliability fixes, and set a standing project direction
  (see "Backlog" section below): `docs/history/2603.27127v1.pdf` is a continuing reference for
  the rest of this project's development, not a one-time gap-analysis input.
  Changes: `react_prompts.py` gained **PHASE 7 (Chaining & Escalation)** - combine confirmed
  findings (leaked creds, a working injection, an exposed config/backup file) into a further step
  via `Run_Kali_Command`/`Secret_Scanner` instead of stopping at first confirmation; deliberately
  does NOT reference `Run_Specialized_Module` (confirmed absent from `brain_tools.py`'s real tool
  list via `grep 'name="'`) unlike the old template's Phase 7/8, so the restored phase only
  points at tools that actually exist. Final Analysis renumbered PHASE 7 -> PHASE 8.
  `brain.py`'s `DEFAULT_MAX_ITERATIONS` raised 15 -> 25 to give PHASE 7 room to execute without
  reverting to the old system's unreliable 50-iteration free-text ceiling.
  `PHASE_5_6_TOOLS`/`EXPLOITATION_TOOLS` enforcement (specs/019) is keyed on tool-name sets, not
  prompt phase numbers, so the renumbering needed no changes there - verified by reading
  `react_workflow.py` before editing, not assumed.
  Updated `tests/test_registry/test_react_prompts.py` (`PHASE 7` assertion moved to `PHASE 8`;
  new `test_includes_chaining_and_escalation_phase`). Full suite: 256 passed, 1 pre-existing
  unrelated failure (`test_smart_web_search.py::test_attempt_limit`, a real-network DuckDuckGo
  call returning no results in this sandbox - unrelated to this change, matches CHK082/085's
  prior observations of the same flake). Live-reverified against `https://scanme.nmap.org`:
  5 clean steps, zero repeated/malformed output (no regression to the old failure-retry loop);
  PHASE 5/6 nudge correctly forced a `Run_Nikto` attempt before allowing a Final Answer;
  Inter-reflection majority vote fired on that result (`INCONCLUSIVE/NO FINDING`); since Nikto
  found nothing actually exploitable (only an outdated Apache version, no CVE/injection/leaked
  creds), the model correctly did NOT force PHASE 6/7 further - matching PHASE 7's own explicit
  "skip only if Phase 4-6 found nothing to chain from" instruction. This run did not exercise
  PHASE 7's chaining path itself (this target has nothing to chain), only confirmed the ceiling
  raise/renumbering causes no regression and the skip condition works as written - PHASE 7 firing
  on a target with something to actually chain (leaked creds + a login form, or a confirmed
  injection) remains unverified live and should be checked opportunistically on a future
  authorized target that has one.
- [x] CHK110 (DONE 2026-07-10) User asked whether Argus could handle a real PortSwigger Web
  Security Academy lab, then specifically recalled the project used to handle Path Traversal
  before. Investigated rather than assumed: three more live attempts to trigger CHK109's still-
  open PHASE 7 chaining path, each with a different, honestly-documented outcome -
  `https://scanme.nmap.org` (repeat) had nothing to chain; `http://testphp.vulnweb.com` was
  genuinely unreachable (confirmed independently via `curl` returning `HTTP_CODE:000` from WSL,
  not a code bug); a local mock server with a guaranteed real leaked secret hit a **WSL-to-
  Windows-host networking gap** - `Check_Reachability`/`Recon_Suite` run inside WSL, "localhost"
  from inside WSL2 resolved to WSL's own loopback (found its own sshd on port 22), never reaching
  the Windows-side mock process on port 8888 - a verification-methodology limitation, not an
  Argus bug (confirmed by the nmap output itself showing WSL's own services, not the mock
  server's).
  While investigating the Path Traversal recollection specifically, found a real, separate,
  confirmed gap: `app/tools/evasion.py::advanced_vuln_probe()` (the actual live-attack tool,
  distinct from the old node-graph pipeline's historical `path_traversal` probe referenced in the
  2026-07-07 CHANGELOG entry, which itself came back `exploit_success: false` against
  `example.com`) only ever tried Windows/IIS-style `web.config` - useless against Linux-hosted
  targets (PortSwigger's labs included, which test `/etc/passwd`) - and judged success by bare
  HTTP status (`200`/`500`) alone, which both false-negatives (wrong file entirely) and false-
  positives (any 200 "succeeds"). Separately, `app/tools/reflective_verification.py`'s
  `post_execute_verify()` already had a real, content-signature-based verifier
  (`root:x:0:0:`/`DB_PASSWORD`/`uid=` etc.) sitting unused - registered on `WSLBridgeTools` but
  never exposed as a tool `brain_tools.py`'s ReAct agent can call.
  Fixed: extracted the indicator dict into a new shared `SENSITIVE_CONTENT_INDICATORS` constant
  in `app/tools/utils.py` (Constitution IX - was duplicated only in `reflective_verification.py`
  before; now the one place either file reads from). `advanced_vuln_probe()` rewritten to fetch
  real response bodies (not `-o /dev/null` status-only) and check them against that dict; added
  Linux `/etc/passwd`-style traversal payloads (plain, URL-encoded, and dot-slash-obfuscated
  variants) alongside the original Windows ones; SQLi check extended to also look for real SQL-
  error text in the body, not just a bare `500`. New `tests/test_tools/test_evasion.py` (no prior
  coverage existed for this module) - 6 tests. Full suite: **262 passed**, 1 pre-existing
  unrelated failure (same DuckDuckGo network flake as CHK082/085/109).
  Live-verified the fix directly: stood up a mock vulnerable server *inside* WSL Kali itself
  (avoiding CHK110's own WSL-networking-gap finding above) serving real fake `/etc/passwd`
  content; `curl` confirmed reachable from within WSL first. The subsequent live agent run
  reached `Run_Nikto` (which satisfied the PHASE 5/6 nudge on its own, an inconclusive generic
  scan) and stopped at a Final Answer without calling `Advanced_Evasion_Probe` at all - an honest
  negative result, not a bug: PHASE_5_6_TOOLS enforcement requires *at least one* of
  Nikto/FFUF/Exploit_Suggester/Advanced_Evasion_Probe, not all four, so the model reasonably
  treated Nikto's attempt as sufficient. The traversal-detection fix itself remains verified only
  by the 6 new unit tests, not yet observed firing inside a live agent run - tracked as a
  follow-up, same status as CHK109's still-open PHASE 7 live-firing item.
  Separately clarified for the user: confirmed live (`ls` inside WSL Kali) that
  `/opt/payloads/PayloadsAllTheThings/` is a real, present local mirror, and that all 8 of
  `app/tools/payloads.py`'s vulnerability-type-to-directory mappings resolve to real directories
  in it - `Exploit_Suggester` genuinely works. But it is completely disconnected from
  `Advanced_Evasion_Probe`: the former only returns research text for the model to read, the
  latter's payload list is 100% hardcoded Python with no automatic pipeline pulling from
  PayloadsAllTheThings. RAG's actual content (`knowledge_base/argus_security_knowledge.md`, 58
  lines) is a general architecture/methodology summary, not a payload database - it does not
  expand attack-payload diversity at all, contrary to what the user's phrasing assumed. Connecting
  `Advanced_Evasion_Probe` to `Exploit_Suggester`/PayloadsAllTheThings automatically was proposed
  to the user as a followup, not yet implemented.
- [x] CHK111 (DONE 2026-07-10) User asked to actually test against a real PortSwigger Web
  Security Academy lab URL, and separately to implement CHK110's proposed follow-up (wire
  `Advanced_Evasion_Probe` to PayloadsAllTheThings, "make use of RAG"). Three real changes:
  1. **`check_reachability()` false-DOWN on ICMP-blocked-but-HTTP-live targets** - live-discovered
     against the actual PortSwigger lab URL: `curl` independently confirmed `HTTP_CODE:200`, but
     `Check_Reachability` (ping-only, no fallback) reported it DOWN, stopping the agent
     immediately - the same root-cause class as the 2026-07-07 CHANGELOG's Cloudflare/WAF fix for
     `recon_suite`'s nmap scan, but `check_reachability()` had never received an equivalent fix.
     Fixed: falls back to a direct `curl` HTTP(S) probe (trying the opposite scheme too, matching
     `run_nikto`/`run_ffuf`'s established scheme-retry pattern) when ping gets no reply. New
     tests added to `tests/test_tools/test_reachability.py` (3 new, 8 total). Live-reverified:
     re-running against the same PortSwigger lab now correctly reports
     `"REACHABLE (ICMP blocked, confirmed via HTTP HTTPS - status 200)"` and the run proceeds
     into real recon (Recon_Suite's tech fingerprint even captured the lab's actual page title,
     `Title[File path traversal, simple case...]` - PortSwigger literally names the vulnerability
     class in the page title). Nikto then came back inconclusive and the model produced a Final
     Answer without ever calling `Advanced_Evasion_Probe` - an honest finding, not a regression:
     the model never acted on the page-title signal sitting in its own Recon_Suite output, so the
     lab's actual traversal parameter was never attempted this run. Tracked as a new, distinct
     follow-up (nothing in the prompt currently tells the model to specifically watch for and act
     on strong signals like a page title naming the vulnerability class) - separate from CHK109's
     still-open PHASE 7 live-firing item and CHK110's still-open traversal-fix live-firing item.
  2. **`Advanced_Evasion_Probe` <-> PayloadsAllTheThings wiring**: researched first (per request)
     - confirmed PayloadsAllTheThings ships a dedicated `<Category>/Intruder/` subfolder per
     vulnerability class with plain one-payload-per-line wordlists (meant for Burp
     Intruder/ffuf), a far more reliable source to parse than scraping `README.md` prose/code-
     fences the way `suggest_payloads()` already does. Verified live in Kali WSL:
     `Directory Traversal/Intruder/dotdotpwn.txt` (21k+ real payloads, confirmed contains plain
     `../../../etc/passwd`-style entries) and `SQL Injection/Intruder/Generic_ErrorBased.txt`
     (154 lines, real ` OR 1=1`-style entries) both exist and match. New
     `app/tools/payloads.py::fetch_intruder_payloads()` samples a small (`limit=4`), bounded
     random subset via `shuf -n N` and merges it (deduplicated) into `advanced_vuln_probe()`'s
     existing static traversal/SQLi lists - fails soft (`[]`) if the mirror or file is missing, so
     a fresh install without the mirror behaves exactly as before, never worse. New
     `tests/test_tools/test_payloads.py` (6 tests) plus 2 new tests in `test_evasion.py`
     (enrichment fires; existing tests' mock runner special-cases `shuf` to return empty so their
     original deterministic payload set is preserved).
  3. **RAG "made useful"**: confirmed the only knowledge-base document
     (`argus_security_knowledge.md`) was 100% self-referential Argus architecture description -
     zero actual security/exploitation knowledge, and even that description was stale (still
     described the pre-specs/017 `AgentExecutor`/`SimpleChain` path). Corrected the stale line and
     added new `knowledge_base/exploitation_techniques.md` - real, public OWASP/PayloadsAllTheThings
     -class methodology (traversal OS-target selection and bypass encodings, SQLi WAF-evasion
     techniques, verification pitfalls/false-positive patterns, and guidance on chaining a
     confirmed finding further) - so the RAG fusion that already runs on every `ask()` call
     actually retrieves something relevant to pentesting reasoning, not just facts about Argus's
     own components.
  Full suite after all three changes: **272 passed**, 1 pre-existing unrelated failure (same
  DuckDuckGo network flake observed since CHK082).

## Constitution IX — Single Source of Truth (No Duplication)

Enforcement tool: `scripts/check_duplication.py` (built and verified 2026-07-08 -
catches exact-file and normalized-function-body duplication; `--diff` mode
confirmed to only flag newly-touched duplication, not the pre-existing backlog
below). Found via `--all` scan of `app/`, `scripts/`, `Setup/`:

- [x] CHK058 (RESOLVED 2026-07-09) `Setup/requirements.txt` was byte-identical to
  `scripts/Setup/requirements.txt`. Investigation found `scripts/Setup/` was an
  undocumented, unreferenced duplicate - nothing in `ARGUS_INSTALLER.ps1` or any
  launcher invokes paths under `scripts/Setup/`, while root `Setup/` is the one
  documented as the legacy manual fallback (`scripts/README.md`, `Setup/README.md`,
  and `ARGUS_INSTALLER.ps1`'s own `Setup/` -> `Setup_legacy/` archive step all
  reference the project-root path). `scripts/Setup/Step_1_Core_Foundation.bat` and
  `Step_2_AI_Python_Env.bat` (which existed only there, not in root `Setup/`
  despite `Setup/README.md`'s file table claiming otherwise) were moved into
  `Setup/`; the duplicate `scripts/Setup/requirements.txt` was deleted. `Setup/`
  is now the single canonical legacy-installer directory.
- [x] CHK059 (RESOLVED 2026-07-09) `_first_web_port` was identically defined in both
  `app/core/agent/nodes/exploit.py` and `app/core/agent/nodes/scanner.py` - moved to new
  `app/core/agent/nodes/_shared.py`, both nodes now import it from there. Verified no test
  imported the old per-file copies directly (only the public `*_node` functions are tested).
- [x] CHK060 (RESOLVED 2026-07-09) `_build_target_url` was identically defined in the same two
  files - moved to `app/core/agent/nodes/_shared.py` alongside CHK059 (kept the more complete
  docstring from `exploit.py`'s copy).
- [x] CHK061 (RESOLVED 2026-07-09) `_get_conn`/`_get_gui_conn` had identical DB-connection logic
  independently defined in `app/GUI/components/session_manager.py` and
  `app/GUI/utils/blackboard.py` - moved to new `app/GUI/utils/db_connection.py::get_gui_db_connection()`,
  both call sites now import it (aliased to their original private names to keep the diff
  minimal). Verified via `tests/test_gui/test_session.py`'s roundtrip tests, which exercise the
  public API these functions sit behind.
- [x] CHK062 (REVIEWED 2026-07-09, NOT CHANGED - decision, not an oversight) Re-examined the
  identical 2-line `__init__(self, runner, memory)` across the 5 tool-service classes and agreed
  with this item's own original assessment: it's idiomatic dependency-injection boilerplate, not
  accidental drift, and introducing a shared base class for 2 lines x 5 classes would be the kind
  of premature abstraction this project's own conventions warn against. Left as-is.
  Full suite re-verified after CHK059-061: 186 passed, 1 pre-existing unrelated failure.
- [x] CHK063 (RESOLVED 2026-07-09) `workspace/run_argus_cli.py` vs
  `scripts/run_argus_cli.py` reconciled. Investigation found the `workspace/`
  version's 4 "extra tools" were not a viable alternative to preserve as-is:
  `bridge.run_zero_apt_simulation` does not exist on `WSLBridgeTools` at all
  (the real class, `ZEROAPTSimulation.run_simulation()` in
  `app/tools/simulation.py`, was never wired into the tool registry - a
  separate orphaned-feature finding, not fixed here); `bridge.pre_execute_verify`/
  `post_execute_verify`/`task_difficulty_assessment` were also wrong attribute
  names (the real public methods are `verify_command`/`verify_output`/
  `assess_difficulty` - `app/tools/tool_registry.py` lines 179-186). So
  `workspace/run_argus_cli.py` and the `scripts/TEST_ARGUS.bat` menu option
  that depended on it were **already broken** (`AttributeError` on the first
  scan). Merged into `scripts/run_argus_cli.py` (config-driven model name,
  correct `PROJECT_ROOT` path handling, kept): the websocket keepalive patch,
  progress-log writer, and the two of the three verification/TDA tools that
  are actually usable as single-input `Tool`s (`verify_command`,
  `assess_difficulty` - `verify_output` needs 3 positional args and was
  dropped, not silently mis-wired). `scripts/TEST_ARGUS.bat` and
  `scripts/LAUNCH_CLI.bat` both now point at the one canonical file; verified
  by importing the merged module directly (no `AttributeError`) rather than
  assuming. `workspace/run_argus_cli.py` deleted.
- [x] CHK064 (RESOLVED 2026-07-09) The 6 ad hoc `workspace/test_*.py` scripts
  were never part of the pytest suite (`tests/` is the only path `pytest.ini`
  collects) and each was checked individually before deletion, not deleted as
  a batch assumption: `test_full_integration.py` and `test_graph_extraction.py`
  both call a `graph_ask()` method that no longer exists on `ArgusBrain` and
  both require an Ollama model (`llama3.1:latest`) that isn't installed -
  confirmed broken, not just stale; `test_custom_graph.py`,
  `test_langgraph_basic.py`, and `test_tool_errors.py` import only `langgraph`/
  `langchain_ollama` directly with no `app.*` import at all - pure library
  prototyping scratch with zero Argus-specific regression value;
  `test_custom_mode_with_mock.py` was the one genuinely real test (mock LLM,
  real `_build_custom_workflow`/`_build_tool_map` imports, no live network
  needed) but is fully superseded by `tests/test_langgraph_workflow.py::test_custom_graph_full_cycle`
  and its neighbors, which cover the identical scenario more thoroughly. All 6
  deleted.
- [x] CHK065 (RESOLVED 2026-07-09) Root `IMPLEMENTATION_GUIDE.md` had a generic
  name but narrow content (a one-off writeup of the same "Invalid Format:
  Missing 'Action:'" bug already covered by `docs/history/PARSING_ERROR_FIX.md`)
  - it was missed by Cleanup Manifest C6's original `*_FIX.*`/`*_REPORT.*` glob
  specifically because of its misleading name. Moved to
  `docs/history/IMPLEMENTATION_GUIDE_parsing_error_fix.md`
  (`docs/ARCHITECTURE_AUDIT_REPORT.md` C6 entry updated with this follow-up).
  **Superseded 2026-07-10**: this file, `PARSING_ERROR_FIX.md`, and 5 other
  writeups of the same incident were consolidated into one file and deleted -
  see `docs/history/2026-06-25_react_parsing_and_simplechain_fallback_incident.md`.

---

## Phase 019 — Shared-Memory + Dual-Phase Reflection Upgrade

First of the 8 `specs/019-026` backlog phases to move from "Proposed" to implemented, per the
user's explicit request after the Red-MIRROR gap-analysis/spec-kit-writing/web-validation passes
above. Full detail in `specs/019-shared-memory-reflection-upgrade/{spec,research,plan,tasks}.md`.

- [x] CHK091 `ArgusMemory.summarize_for_planning(k=3, max_chars=3000)` added as a new,
  additive method (`app/core/memory/memory_service.py`) - per-`(domain, tool_name)`-bounded
  aggregation, the correct real-schema analog of SRMM's `GetAggregatedContext` (the spec had
  assumed grouping by `data_type`; reading the real schema found `tool_name` is the actual
  per-writer signal). `get_blackboard_summary()` itself deliberately left untouched - its exact
  shape is asserted by existing tests and consumed as-is by `Query_Memory`/TDA/GUI callers, and
  changing it risked a real regression for no benefit the new method doesn't already provide.
  Added an `f.id DESC` query tiebreaker after finding, while writing this method's own test,
  that same-microsecond timestamps under a tight write loop made "most recent" ambiguous.
- [x] CHK092 `reflection_notes: list[str]` added to `ArgusAgentState`
  (`app/core/agent/react_state.py`)
- [x] CHK093 `_build_reflection_note()` (structured, response-aware Intra-reflection) replacing
  the previous generic "try something different" duplicate-call guidance -
  `app/core/agent/react_workflow.py`
- [x] CHK094 `_inter_reflect()` (3x self-consistency majority vote, Wang et al. ICLR 2023 -
  the same technique Red-MIRROR cites) scoped to `EXPLOITATION_TOOLS`
  (`Advanced_Evasion_Probe`, `Secret_Scanner`, `Run_Nikto`, `Run_FFUF`) via a new
  `enable_inter_reflection` config flag (default `true`) - `app/core/agent/react_workflow.py`,
  `config.yaml`, `app/core/config.py`
- [x] CHK095 `_check_early_termination()` (flag-pattern nudge, not a forced structural exit -
  `_finalize_graph_output()`'s `"Final Answer:"` requirement remains the single source of truth
  for completion, Constitution VIII) - `app/core/agent/react_workflow.py`
- [x] CHK096 Observability implemented differently than the original plan: `react_workflow.py`'s
  node functions don't receive callbacks at all (confirmed by reading `brain.py`'s actual
  `_emit_graph_step()` mechanism before implementing) - reflection notes instead flow through
  the existing per-message streaming loop as `"Reflection:"`-prefixed messages;
  `_emit_graph_step()` gained one new status branch (`"reflecting"`) - `app/core/agent/brain.py`
- [x] CHK097 18 new unit tests (13 in `tests/test_langgraph_workflow.py`, 5 in
  `tests/test_memory.py`) plus one integration smoke test combining duplicate-call reflection +
  Inter-reflection voting + early-termination in one realistic multi-step trace (7/7 assertions
  passed) - all passing
- [x] CHK098 Full regression verified: `tests/test_memory.py` + `tests/test_langgraph_workflow.py`
  + `tests/test_registry/` = 91 passed, 0 failed. Full repo suite = 239 passed, 1 failed
  (`test_smart_web_search.py::test_attempt_limit`) - confirmed via `git stash` (identical failure
  with today's changes fully reverted) as pre-existing and unrelated: a live-DuckDuckGo-network-
  dependent test in a file this phase never touched
- [x] CHK099 T013 (live wall-clock cost measurement, NFR-002) completed against the real
  production model (`hf.co/bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M` via live
  Ollama, confirmed reachable) - isolated, warm-up-controlled, 3-round interleaved comparison
  (not a full end-to-end scan, which would confound the measurement with variable tool/network
  latency the flag doesn't control): a single normal ReAct action-generation call averaged
  **10.96s**; a full `_inter_reflect()` 3x-vote call averaged **0.82s** (~8% of a single call's
  time, not the ~300% naively expected from "3x the LLM calls"). Root cause: the vote prompt
  constrains output to one word ("yes"/"no"), and autoregressive decode time is dominated by
  *output* token count, not input size or round-trip count - three short-output calls are
  cheaper than one long-output call. **Conclusion: `enable_inter_reflection=true` is confirmed
  safe as the default** - the real measured overhead is the opposite of NFR-002's original
  worry, not just "acceptable."
- [x] CHK100 (T014) This checklist section + `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability
  row updated from "Proposed" to "Implemented" + `CHANGELOG.md` entries (both the implementation
  pass and this verification pass)

---

## Phase 020 - Multi-Agent Role Separation (Experimental, 2026-07-11)

- [x] CHK112 (DONE 2026-07-11) User proposed a heavier multi-*model* variant of this phase
  (Dolphin/DeepSeek-Coder/an abliterated Llama-3-8B per role); researched it first rather than
  accepting or rejecting on priors (full findings + sources: `research.md`'s 2026-07-11
  addendum) - found the VRAM math doesn't hold on this machine's actual hardware (confirmed live
  via `nvidia-smi`: 16GB total, RTX 2000 Ada), abliteration specifically regresses TruthfulQA
  (-7.1), the wrong tradeoff for a judgment-heavy Verifier/Summarizer role, and independent
  research (Persona-Pruner) validates extracting multiple personas from one dense model over
  deploying several full models - matching this spec's own original FR-001 scope. User approved
  proceeding with FR-001 exactly as originally written (T000: GO).
  Implemented T001-T007 (see `tasks.md` for full detail per task):
  - `react_prompts.py`: 4 new role-scoped prompt builders (Collector/Exploiter/Planner/
    Summarizer). `brain_tools.py`: `build_argus_tools(role=...)` + `ROLE_TOOL_PARTITIONS` (single
    source of truth for FR-002's tool split) + `partition_tools_by_role()`.
    `react_state.py`: `current_role`/`role_history` fields (`NotRequired` - single-loop graph
    unaffected). `react_workflow.py`: new standalone `_build_multi_role_workflow()` (not a
    generalization of the production `_build_custom_workflow`'s closures, so the production path
    is provably unaffected regardless of this experimental path's behavior) - safely extracted
    `_parse_react_output` to module level first (pure function, zero behavior change, full suite
    re-verified green before building on it) so both graphs share it. `config.yaml`/`config.py`:
    `enable_multi_agent_roles` flag, default `false`. 22 new tests across
    `tests/test_agent/test_react_prompts.py`, `tests/test_agent/test_brain_tools.py`,
    `tests/test_agent/test_langgraph_workflow.py` (paths as of this feature's original
    2026-07-11 work; both directories were later renamed from `tests/test_registry/` to
    `tests/test_agent/` by an unrelated main-branch reorganization, `ac797c5`, before this code
    was actually merged onto `main` on 2026-07-19 - see `CHANGELOG.md`'s 2026-07-19 entry).
    Full suite (at merge time): **336 passed, 0 failed** - the DuckDuckGo/attempt-limit flake
    referenced in this feature's original 2026-07-11 work was itself fixed on `main` before this
    merge (`app/tools/web_search.py`'s attempt-limiting and backend-retry logic, see
    `CHANGELOG.md`), so it no longer applies.
  - **NFR-001 measurement** (`tests/manual/specs020_wallclock_comparison.py`, mocked but fixed
    per-call latency so the comparison isolates orchestration overhead from inference-time
    noise): on an equivalent-effort scenario (2 real tool calls, then a report), the multi-role
    graph took **2.00x the LLM calls** of the single-loop graph (6 vs. 3) - structural, not
    scenario-specific, since every Collector/Exploiter action pairs with one Planner routing
    decision in this topology. Converted to this project's own already-measured *real* per-call
    latency (CHK099: **10.96s** average for a real WhiteRabbitNeo-V3-7B ReAct call) rather than
    the mocked 0.05s stand-in: the same 2-tool-call scenario would cost single-loop
    3 x 10.96s ≈ 33s vs. multi-role 6 x 10.96s ≈ 66s - a real ~33s of added latency for just 2
    tool calls, compounding further over the 5-10-tool-call runs typical of `018`/`019`'s live
    testing.
  - **Honest result (Constitution VIII): borderline, lands exactly at NFR-001's own pre-agreed
    2x rollback threshold, not clearly under it.** Not promoted to default (`enable_multi_agent_
    roles` stays `false`). T008/T009 blocked pending either a design change (letting
    Collector/Exploiter run several tool calls per visit before returning to the Planner, to
    amortize the routing overhead - not implemented in this v1, flagged as a deliberate,
    documented scope decision, not an oversight) or a team decision to accept the overhead
    anyway for a measured capability gain once `025` (benchmark suite) exists.
- [x] CHK113 (DONE 2026-07-23) Implemented `025-subtask-benchmark-suite` T001-T004/T006-T008/T010
  (this session's own recommendation above - `025` was next-most-valuable since it's what lets
  `020`'s "measure before committing further" recommendation be acted on with real numbers):
  - `benchmarks/fixture_base.py` (shared 4-file fixture contract: `server.py`/`query.txt`/
    `flag.txt`/`subtasks.yaml`), `benchmarks/runner.py` (`run_fixture()`/`run_suite()`, SR/SCR/TTE
    scoring via a `TraceCaptureCallback` on `ArgusBrain.ask()`'s `on_graph_event` seam - not
    `tool_call_history`, which the return value does not expose, a real gap in `plan.md`'s
    original design found by reading `brain.py` directly before implementing).
  - 4 fixtures: `info_disclosure_env_leak` (migrated from `tests/manual/ai_benchmark.py`,
    fixing its hand-picked 2-tool-subset gap with the real 17-tool `build_argus_tools()`),
    `xss_reflected`/`idor_object_access`/`ssti_template_injection` (new, user-scoped down from
    the spec's 5-9 to 3 fixtures for this pass - real in-process vulnerable logic, genuine
    `jinja2.Template(...).render()` for SSTI, no Docker/`subprocess`).
  - `benchmarks/tests/test_runner.py`: 10 unit tests, fake-LLM-via-`ArgusBrain`'s-own-`llm=`-seam
    convention (never mocks `ArgusBrain` itself, matching `test_brain_ask.py`/
    `test_langgraph_workflow.py`), no live Ollama needed - 10/10 passing.
  - **Real bug found and fixed live, not assumed**: a bounded live sanity run (real Ollama+WSL)
    initially found `info_disclosure_env_leak` scoring SR=False/SCR=0.0 with zero tool activity.
    Root-caused via `wsl -d kali-linux -- curl 127.0.0.1:<port>/.env` -> curl exit code 7
    ("failed to connect"): fixture servers bound to `127.0.0.1` on the Windows host are
    unreachable from inside the WSL/Kali guest where Argus's tools actually execute - a latent
    bug shared with the original `ai_benchmark.py`, not a regression from this migration. Fixed
    via `fixture_base.py`'s new `_wsl_reachable_host()` (resolves WSL's own default-gateway IP
    live, cached per-process, `127.0.0.1` fallback) plus rebinding all four fixture servers to
    `0.0.0.0`. A second live run confirmed the fix: real tool execution (Nikto, subdomain
    enumeration, secrets analysis) against the resolved gateway IP, partial credit (SCR 0.33,
    found `/.env`) - a genuine baseline result, not a wiring failure (Constitution VIII).
  - `tests/manual/ai_benchmark.py` removed (T008) once the migration's wiring was confirmed
    correct end-to-end; its `tests/manual/README.md` entry removed with it.
  - **T005/T009 completed 2026-07-23 (live, real numbers, not projected)**: T005's baseline
    (`benchmarks/results/20260723T143037Z_report.md`) scored SR 0/4, mean SCR 0.33 across the
    original 4 fixtures - the agent consistently found the right endpoint but didn't complete
    extraction/reporting on any fixture, a genuine capability gap this suite now makes
    visible, not a harness defect. T009's ablation
    (`benchmarks/results/20260723T144350Z_report.md`) was the project's first real
    Table-6-shaped comparison: `baseline` (mean SCR 0.33) outperformed `no_inter_reflection`
    (mean SCR 0.25).
  - **Re-run after adding a 5th fixture (`path_traversal_download`), same day**:
    `benchmarks/results/20260723T150717Z_report.md` re-ran both configs across all 5 fixtures -
    this time `baseline` and `no_inter_reflection` scored **identically** (SR 0/5, mean SCR
    0.33 both). The earlier directional signal did NOT replicate - reported plainly rather than
    keeping only the more flattering first result (Constitution VIII). Both reports are kept on
    disk (FR-005: every run kept, not just the latest). Conclusion: at this suite's current
    scale (5 fixtures, 3 subtasks each, single run per configuration), `enable_inter_reflection`'s
    measured effect is not yet distinguishable from this local 7B model's own run-to-run ReAct
    variance - settling it needs repeated runs per configuration, not a claim either existing
    report supports alone.

---

---

## Repo Organization Pass (2026-07-10)

User asked for a full organization pass so files/folders are "مفيدة ومنظمة بشكل صحيح" (useful
and correctly organized) instead of having many discrepancies. Preceded by a dedicated audit
(Explore agent, root/`docs/`/`app/`/`scripts/`/`tests/`) whose findings were independently
verified (not taken on trust) before acting - see below for cases where verification corrected
or added nuance to the audit's own claims.

- [x] CHK101 `scripts/TEST_ARGUS.bat`'s option 6 called a `CHECK_HEALTH.bat` that never existed
  anywhere in the repo (confirmed absent) - replaced with a one-line call into the real,
  already-existing Python health-check logic (`app/tools/self_heal.py::SelfHealingService.health_check()`),
  reusing it instead of writing a second, batch-script copy of the same WSL/Ollama/Python checks.
  Verified live: returns real `{"wsl": "ok", "ollama": "ok", "python": "ok (...)"}`.
- [x] CHK102 Deleted stray untracked zip `artifacts/Argus_GUI_files_20260624_180403.zip`
  (confirmed via `git status` it was never tracked, matching `.gitignore`'s own comment that
  this exact situation has recurred before).
- [x] CHK103 Moved self-labeled-legacy `docs/ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md` into
  `docs/history/`; updated `docs/README.md` (2 references + ADR count 1-16 -> 1-19, stale since
  `019`'s ADR-19 addition) and `docs/ARCHITECTURE_AUDIT_REPORT.md`'s Section 6 accordingly.
  Left `specs/001-rag-integration/{plan,tasks}.md`'s references untouched - they're historical
  snapshots of spec 001's own timeframe, not living docs.
- [x] CHK104 **Real bug, not just clutter**: `app/tools/scanners.py::run_nikto()` built its
  Nikto `-o` output path with a `.txt` suffix already applied, but Nikto's own `-Format txt -o
  <path>` appends `.txt` itself regardless - confirmed via `reports/nikto/*.txt.txt` real files
  on disk. Fixed to pass the un-suffixed stem to `-o` (both the primary and http/https-fallback
  command); the method's own returned message now cites the correct, single-`.txt` path. New
  regression test `test_output_path_has_no_double_extension` - `tests/test_tools/test_scanners.py`
  (8/8 passing, including the 4 pre-existing tests unaffected).
- [x] CHK105 `scripts/test_agent.py` exercised `app.core.agent.graph.build_tactical_graph` (the
  superseded `010` node graph), not `ArgusBrain`'s current production ReAct loop
  (`react_workflow.py`, `017`/`018`/`019`) despite its name suggesting the opposite - not part
  of the pytest suite either way (no `test_` functions), but misleading. Renamed to
  `scripts/diagnose_legacy_tactical_graph.py` with a clarifying docstring;
  `scripts/README.md` updated (2 references).
- [x] CHK106 **Real bug, not just clutter**: `app/GUI/{app.py, argus_gui.py, gui_main.py}` were
  NOT the "deprecation shims" `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` and
  `docs/ARCHITECTURE_AUDIT_REPORT.md`'s C3 entry already claimed - each was a full,
  independently-running 90-180-line Streamlit app with `DeprecationWarning`s bolted on top but
  otherwise fully functional, each building its **own hardcoded, drifted tool list** (12, 3, and
  9 tools respectively - none matching the canonical 17-tool `brain_tools.py::build_argus_tools()`
  list, `gui_main.py` additionally hardcoding a stale model name bypassing `ArgusConfig`
  entirely). Confirmed via grep that nothing in `scripts/`/`config.yaml` launches these 3
  directly - pure dead weight with a real risk of giving anyone who ran them a materially worse,
  stale experience while believing they were using Argus normally. All 3 converted to true
  one-line `from app.GUI.dashboard import *` re-exports, matching the already-correct
  `studio.py` pattern. `desktop_gui.py` (Tkinter) deliberately left untouched - it is a
  genuinely distinct, intentional fallback GUI for non-Streamlit environments, not a duplicate
  of `dashboard.py` (different framework entirely), despite superficially resembling the other
  3 in the audit's initial framing. `tests/test_gui/` (35 tests, including the direct
  `app.GUI.app` import test) confirmed green after.
- [x] CHK107 Created `tests/manual/` and moved 6 ad hoc, non-pytest scripts into it:
  `verify_core.py` (fixed a broken pre-reorg import, `from core.tools import WSLBridgeTools` ->
  `from app.tools.tool_registry import WSLBridgeTools`, confirmed live via
  `ModuleNotFoundError` before/fixed after), `check_integration.py` (fixed its `REPO_ROOT`
  dirname-count for the new one-level-deeper location; documented 4 already-stale checks -
  referencing module-level constants that no longer exist - rather than silently fixing or
  hiding them), `ai_benchmark.py` (same one-level-deeper path fix - confirmed this one was a
  **real, newly-introduced-by-the-move bug**: `python tests/manual/ai_benchmark.py` raised
  `ModuleNotFoundError: No module named 'app'` before the fix, confirmed fixed after),
  `exploit_test.py`, `test_cd.bat`, and `docs/history/verify_parsing_fix.py` (also relocated
  here, not just the 5 originally-`tests/`-rooted ones, since a `.py` script doesn't belong in a
  docs folder either - same one-level-deeper path fix applied and verified). New
  `tests/manual/README.md` explains why each isn't part of CI and what each still needs (live
  WSL/network/Ollama). Full suite reconfirmed green after: 240 passed, 1 pre-existing unrelated
  failure (`test_smart_web_search.py`, already tracked separately).
- [x] CHK108 Consolidated 7 separate `docs/history/` writeups of the single 2026-06-25
  "Invalid Format: Missing 'Action:'" / ReAct-to-SimpleChain-fallback incident
  (`JSON_PARSING_FIX.md`, `PARSING_ERROR_FIX.md`, `IMPLEMENTATION_GUIDE_parsing_error_fix.md`,
  `REACT_FORMAT_ERROR_FIX.txt`, `RADICAL_FIX_SIMPLE_CHAIN_FALLBACK.txt`, `QUICK_START_FIX.txt`,
  `TESTING_JSON_FIX.md`) into one chronological file,
  `docs/history/2026-06-25_react_parsing_and_simplechain_fallback_incident.md`, deleting the 7
  originals. **Correction to the audit's own framing**: the audit that identified "6 overlapping
  files" also listed `STREAMLIT_JAVASCRIPT_FIX.txt` as one of them - reading it directly found
  it documents a genuinely unrelated browser-cache/JS-asset issue, not the parsing incident; left
  it alone rather than force-merging it. Conversely, `QUICK_START_FIX.txt` and
  `TESTING_JSON_FIX.md` (not in the audit's list) were found, on reading `docs/history/`
  directly, to also document the same parsing incident - the real count was 7, not 6. The
  consolidated file explicitly connects this incident's confident, tested-at-the-time claims
  ("0% -> 95%+ success rate", "4/4 tests passing") to `specs/018`'s later finding that the
  fallback mechanism it describes never actually worked - preserved as a lesson, not scrubbed.
  `docs/ARCHITECTURE_AUDIT_REPORT.md` (2 entries) and `specs/checklist.md`'s own CHK065 updated
  with pointers to the new file rather than left citing deleted paths.

---

## Backlog — Proposed Future Phases (Red-MIRROR gap analysis, 2026-07-10)

Produced from a gap analysis comparing Argus against `docs/history/2603.27127v1.pdf`
("Red-MIRROR: Agentic LLM-based Autonomous Penetration Testing with Reflective Verification and
Knowledge-augmented Interaction," arXiv:2603.27127v1), at the user's explicit request. `019` has
since been implemented (see "Phase 019" section above, CHK091-100) - the rest remain spec-kit-
only (`spec.md`/`research.md`/`plan.md`/`tasks.md` written, no implementation started). Each
phase's own `specs/<phase>/tasks.md` tracks its task list.

**Standing reference, not a one-time analysis (per explicit user direction, 2026-07-10):** this
paper stays the project's continuing foundation through the rest of development, not just the
source of this one backlog table. Changes made outside this backlog (e.g. the 2026-07-10
`react_prompts.py` PHASE 7/`brain.py` `DEFAULT_MAX_ITERATIONS` restoration, see "Phase 018
addendum" below) are still expected to be justified against it where relevant, and this table
should be revisited whenever new capability is considered, not treated as closed once written.

| Phase | Title | Status | Depends on | Risk |
|-------|-------|--------|------------|------|
| 019 | Shared-memory + Dual-Phase Reflection upgrade | **Implemented 2026-07-10** (CHK091-100) | none | Low — upgraded existing mechanisms |
| 020 | Multi-agent role separation (Planner/Collector/Exploiter/Summarizer) | **Implemented as an experimental feature-flagged-off path 2026-07-11** (CHK112) — NFR-001 measured 2.00x LLM call-count overhead, at the spec's own 2x rollback threshold; not promoted to default | 019 (done) | High — core loop architecture change (materialized: measured, not just projected) |
| 021 | Specialized exploitation toolkit (JWT/IDOR/upload/XSS-fuzzer/code-injection) | Proposed, per-tool shippable | none (XSS fuzzer soft-depends on 019, now available) | Low — new tools, established pattern |
| 022 | Browser automation via Playwright | Proposed | none | Medium — new Kali-side runtime dependency |
| 029 | Vulnerability screenshot evidence capture via Playwright | **Implemented 2026-07-25** | none (independent of 022 — different lifecycle/execution model, see spec.md "Why this feature") | Low — new host-side tool, additive `browser_manager=None` default |
| 023 | CVE intelligence & PoC retrieval | Proposed | none | Low-Medium — new external API dependency |
| 024 | LoRA fine-tuning pipeline | Proposed | none (offline pipeline) | Medium — needs training-capable hardware not guaranteed on target machines |
| 025 | Subtask-level benchmark suite (SR/SCR/TTE + ablation) | **Implemented and live-verified 2026-07-23** (CHK113) — 5 fixtures, baseline SR 0/5, mean SCR 0.33; ablation result did not replicate across two runs (0.33 vs 0.25, then 0.33 vs 0.33) - effect not yet distinguishable from run-to-run variance at this scale | none (needed to *measure* 019/020) | Low |
| 026 | Ethical safeguards (auth gate, audit log, watermarking, RAG gating) | Proposed | none | Low |
| 028 | Human-in-the-loop escalation on detected stuck loops | Proposed | 019 (done) | Low - complements, not replaces, 019's existing structural duplicate-call guard |

Recommended sequencing per each phase's own spec.md: `019` and `025` (benchmark suite) are both
done - `025`'s harness is what lets `020`'s "measure 019's residual gap before committing"
recommendation actually be acted on with real numbers instead of guesses, once T005/T009's live
runs are scheduled. `021`-`024`/`026`/`028` are independent and can proceed in any order the
team prioritizes.

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
| New files created (backlog spec kits) | +32 (019-026: 4 files each, spec/research/plan/tasks.md — no `app/` code yet) |
| **Open compliance gaps** | None as of 2026-07-24 — **CHK052** (011 task tracking) and the **CHK058-065** Constitution IX duplication/organization backlog are all resolved; **CHK055** (014 in progress) is expected, not a gap; **CHK114** closes 016's FR-006/FR-007 backfill gap (0 docstring violations repo-wide, up from 511+). `019`-`026` are an intentional, tracked backlog (not a gap) — see "Backlog — Proposed Future Phases" above |
