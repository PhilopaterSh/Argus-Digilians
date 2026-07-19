# Tasks: Multi-Agent Role Separation

**Feature**: `020-multi-agent-role-separation`

**Status**: **In progress** (started 2026-07-11). `019` shipped first as planned (2026-07-10).
User separately proposed a heavier multi-*model* variant (Dolphin-Llama3 as Coordinator,
DeepSeek-Coder as Exploit Analyst, an abliterated Llama-3-8B as Verifier) — evaluated and
explicitly rejected in favor of this spec's original FR-001 scope (single model, role-scoped
prompts/tools, one graph) after research found: (a) this machine's 16GB VRAM (confirmed via
`nvidia-smi`: RTX 2000 Ada, 16380 MiB total) can't hold more than ~2 of those 7-8B models
resident at once, making 4-model swapping a real, unmeasured latency risk; (b) abliteration
measurably regresses TruthfulQA specifically (-7.1, other benchmarks near-unchanged) — the
wrong tradeoff for a role whose entire job is judging true vs. false findings; (c) recent
research (Persona-Pruner) shows the field moving toward extracting multiple personas from one
dense model rather than deploying separate full models, validating this spec's original FR-001
design rather than the heavier alternative. Full findings in `research.md`'s 2026-07-11 addendum.

- [x] T000 (gate) Team decision: **GO** — proceed with FR-001's original single-model,
  role-scoped-prompts/tools design (2026-07-11, user-approved). Explicitly NOT the multi-model
  variant evaluated and rejected above.
- [x] T001 (DONE 2026-07-11) Split `react_prompts.py`'s single system prompt into 4 role-scoped
  prompts: `build_collector_prompt`, `build_exploiter_prompt`, `build_planner_prompt`,
  `build_summarizer_prompt`. 5 new tests in `tests/test_registry/test_react_prompts.py`.
- [x] T002 (DONE 2026-07-11) Added `role` parameter to `build_argus_tools()` — new
  `ROLE_TOOL_PARTITIONS` dict is the single source of truth for which of the 17 tools belong to
  which role (Collector: recon/discovery, Exploiter: scanning/exploitation, Planner/Summarizer:
  read-only `Query_Memory`/`Query_Knowledge_Graph` only, per FR-002). Also added
  `partition_tools_by_role()` so `ArgusBrain` (which only holds the flat tool list, not a
  `WSLBridgeTools` reference) can get the same split without rebuilding tools from a bridge.
  9 new tests in `tests/test_registry/test_brain_tools.py`.
- [x] T003 (DONE 2026-07-11) Added `current_role`/`role_history` fields to `ArgusAgentState` —
  `NotRequired`, so the single-loop graph (which never sets them) is unaffected.
- [x] T004 (DONE 2026-07-11) Implemented `_build_multi_role_workflow()` — a standalone graph
  (not a generalization of `_build_custom_workflow`'s closures, to keep the production path
  provably unaffected per NFR-002): `planner` node makes a structured routing decision
  (`_PlannerDecision`/`_try_planner_decision`, mirroring `_try_structured_action`'s exact
  pattern) -> `collector`/`exploiter` each execute exactly ONE tool call per visit (reusing
  `_parse_react_output`, `_try_structured_action`, `_check_early_termination`,
  `_extract_vulnerability_hints`, `_inter_reflect` - extracted `_parse_react_output` to module
  level from `_build_custom_workflow`'s `parse_node` closure to share it safely, verified with
  the full existing suite green before building on top) -> back to `planner` -> .... ->
  `summarizer` (terminal, produces the Final Answer). Known, documented scope reduction v1: does
  not replicate the single-loop's "block a call repeated 3+ times" duplicate-call guard - flagged
  in the function's own docstring, not silently missing. 8 new tests in
  `tests/test_langgraph_workflow.py` (full happy-path cycle, one-tool-call-per-visit, shared
  `max_iterations` budget enforcement, inconclusive-decision-defaults-to-summarizer, Exploiter-
  scoped Inter-reflection).
- [x] T005 (DONE 2026-07-11) Added `enable_multi_agent_roles` config flag (default `false`) —
  `config.yaml`, `app/core/config.py`; wired into `brain.py::_run_structured_graph` (branches to
  `_build_multi_role_workflow` + `partition_tools_by_role(self.tools)` only when the flag is
  true; default path is byte-for-byte the pre-existing `_build_custom_workflow` call).
  Full suite after T001-T005: **296 passed**, 1 pre-existing unrelated failure (same DuckDuckGo
  network flake observed since CHK082).
- [x] T006 (DONE 2026-07-11) Built `tests/manual/specs020_wallclock_comparison.py` - measures
  LLM call-count and wall-clock ratio (mocked, fixed per-call latency, so the comparison isolates
  each topology's own orchestration overhead from unrelated inference-time noise) between the
  two graphs on an equivalent-effort scenario (exactly 2 real tool calls: one recon-class, one
  exploit-class, then a final report).
- [x] T007 (DONE 2026-07-11) Ran the measurement. Result, reported honestly regardless of
  outcome (Constitution VIII):
  ```
  Single-loop graph:  0.2048s wall-clock, 3 LLM calls
  Multi-role graph:   0.3533s wall-clock, 6 LLM calls
  LLM call-count ratio (multi-role / single-loop): 2.00x
  Wall-clock ratio (mocked latency):                1.72x
  ```
  The call-count ratio (**2.00x**) is the structurally meaningful number - it's
  latency-independent and scales directly to real inference time, unlike the mocked wall-clock
  number above (which used a 0.05s/call stand-in, not WhiteRabbitNeo-V3-7B's actual real-seconds-
  per-call latency on this project's hardware). This is not scenario-specific: every
  Collector/Exploiter tool call structurally pairs with one Planner routing decision in this
  topology, so 2.00x is close to the steady-state overhead ratio regardless of run length, not
  an artifact of this short 2-tool-call scenario.
  **This lands exactly at NFR-001's own pre-agreed 2x rollback threshold, not clearly under it.**
  Per Constitution VIII, this is reported as a borderline/inconclusive-leaning-negative result,
  not a pass - the honest read is that the Planner's per-step routing overhead (one full extra
  LLM decision for every single specialist action) is the direct, structural cause, not
  something a config tweak fixes. A follow-up worth considering before any live-target
  measurement (SC-001) or default-flipping (T009): let Collector/Exploiter each execute several
  tool calls per visit before returning to the Planner (amortizing the routing overhead across
  multiple actions instead of paying it every single action) - not implemented in this v1, since
  it changes FR-003's "Planner owns every phase transition" framing and deserves its own
  decision, not a silent scope change inside T004.
- [ ] T008 Per T007's borderline result: **not clearly passing NFR-001** as currently designed.
  Feature flag stays `false`. Live-target end-to-end measurement (real WhiteRabbitNeo-V3-7B
  latency, not mocked) not yet attempted - the mocked call-count ratio alone is judged sufficient
  to withhold a "pass" without spending a live run to confirm what the structural analysis above
  already shows. Revisit only if the Collector/Exploiter multi-action-per-visit change proposed
  in T007 is implemented and re-measured.
- [ ] T009 Blocked on T008 - SC-001 benchmark comparison (depends on `025`, which doesn't exist
  yet either) not started.
- [x] T010 (DONE 2026-07-11) This file's T001-T007 entries are the record; `CHANGELOG.md` entry
  added; `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row pending (tracked as a quick
  follow-up, not a code change).

## Explicitly out of scope (see spec.md)

- Independently-scaled per-role model deployments
- Full DAG-based path planning with branch pruning
