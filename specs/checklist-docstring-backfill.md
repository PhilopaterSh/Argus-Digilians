# Docstring Backfill Manifest (specs/016-docstring-enforcement, FR-006/FR-007)

Auto-generated inventory of functions this PR's diff touches that need a real, human-reviewed docstring - NOT auto-applied, per FR-006 ("a docstring asserting an incorrect parameter, return type, or exception is worse than no docstring"). Track backfill progress here per module, same pattern as specs/checklist.md's CHK series.

**Status 2026-07-24: BACKFILL COMPLETE.** `scripts/check_docstrings.py --all app scripts tests` reports **0 violations, repo-wide** (963 scanned functions as of this reconciliation pass - re-verified live, not carried over from an earlier count, since this number grows every time new functions are added and is not itself the thing being tracked). Done across the original 11 verified batches/commits (Tier 0 `scripts/`, unit-marker audits, Tier 1 `app/tools/`, Tier 2 `app/core/rag/`, Tier 3 `app/GUI/`, Tier 4 `app/core/agent/`, Tier 5 `app/modules/` incl. `experimental_agent/`, 5 previously-untracked `app/core/` files, and ~72 test-fixture functions across ~20 test files) plus a handful of later, untracked follow-up batches (`app/core/memory/memory_service.py`, `app/core/safety.py`, `app/core/config.py`, `app/core/registry/tool_registry.py`, `app/modules/__init__.py`/`argus_reasoning.py`, all of `app/modules/experimental_agent/`, and the remaining test-fixture functions below) whose checkboxes were never reconciled back into this file until now (2026-07-24 reconciliation pass) - `check_docstrings.py --all` was already returning 0 for all of them; only the tracking below was stale. Every batch was verified independently: the gate itself, `ruff`, CI's exact `mypy` file list where applicable, `validate_ascii.py`, and the full `pytest` suite.

**Real gate quirk found and worked around, not fixed**: `scripts/check_docstrings.py`'s `walk_own_body()` does not exclude a nested `def`'s own top-level position when it is a direct statement in the outer function's body - it excludes further descent into an *already-nested* FunctionDef's children, but the nested FunctionDef itself still gets its children (including its own `return`) walked once popped from the stack. Net effect: an outer function containing an inline `def helper(): return x` gets a false "needs Returns" flag for a return statement that isn't actually its own. Hit repeatedly (`tests/manual/verify_parsing_fix.py`, `tests/test_tools/test_reachability.py`, others) - worked around by documenting the outer function's *real* return behavior (often `Returns: None`) rather than fixing the checker script itself (out of scope for a docstring-content task; changing shared CI enforcement logic wasn't authorized here).

**Known gap, found 2026-07-24**: this manifest under-counts. `scripts/check_docstrings.py --all app/tools` reported 78 real violations before that directory's backfill batch, not the 28 tracked below for `app/tools/` - the manifest missed every `__init__`, property, and one-line delegator method across `command_runner.py`, `evasion.py`, `payloads.py`, `recon.py`, `self_heal.py`, `tool_registry.py` (17 of them alone), `web_search.py`, and `wsl_bridge.py` (a file this manifest doesn't mention at all). All 78 were fixed in the same batch as the 28 tracked items, verified via `check_docstrings.py --all` returning 0. This undercount pattern held for several other directories too (all now fixed regardless) - this file's per-directory line items should be read as a historical record of what was fixed, not as ground truth for what remains; `check_docstrings.py --all <path>` is now, and remains, the actual source of truth.

**Reconciliation note, 2026-07-24**: this file also went stale in the opposite direction - real batches were done (`app/core/memory/`, `app/core/safety.py`, `app/core/config.py`, `app/core/registry/tool_registry.py`, `app/modules/__init__.py`/`argus_reasoning.py`, `app/modules/experimental_agent/`, remaining test fixtures) without their checkboxes ever being ticked here, so the file looked incomplete while the actual gate was already clean. All remaining `[ ]` items below have been re-verified via a live `check_docstrings.py --all` run and marked `[x]` accordingly. Two section headers also pointed at paths that no longer exist (`tests/test_langgraph_workflow.py` -> `tests/test_agent/test_langgraph_workflow.py`, `tests/test_memory.py` -> `tests/test_memory/test_memory_service.py`, both renamed in an unrelated earlier restructuring) - corrected below.

## `app/GUI/components/export.py`

- [x] `generate_html_report` (line 6) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `generate_markdown_report` (line 70) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `generate_json_report` (line 109) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `get_available_templates` (line 124) - needs: Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/components/session_manager.py`

- [x] `save_session` (line 8) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `load_session` (line 34) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `list_sessions` (line 52) - needs: Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `delete_session` (line 63) - needs: Args. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `update_session` (line 72) - needs: Args. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/components/status_bar.py`

- [x] `render_status_bar` (line 57) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/desktop_gui.py`

- [x] `__init__` (line 26) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `_build_ui` (line 40) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `_log` (line 80) - needs: Args. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `_run_analysis` (line 87) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `main` (line 121) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/tabs/agent.py`

- [x] `_reconcile_agent_running_state` (line 4) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `_render_events` (line 24) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `render_agent` (line 42) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `_live_section` (line 95) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/tabs/knowledge_graph.py`

- [x] `render_knowledge_graph` (line 7) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/tabs/overview.py`

- [x] `_load_recent_runs` (line 10) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `render_dashboard` (line 29) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/tabs/reports.py`

- [x] `_latest_run_for_target` (line 11) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `render_reports` (line 33) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/tabs/settings.py`

- [x] `render_settings` (line 7) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/tabs/targets.py`

- [x] `render_targets` (line 6) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/utils/agent_controller.py`

- [x] `__init__` (line 19) - needs: Args. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `stop` (line 103) - needs: Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `get_log_tail` (line 122) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `get_status` (line 133) - needs: Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `get_feed` (line 142) - needs: Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `is_running` (line 146) - needs: Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `_write_state` (line 154) - needs: Args. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/GUI/utils/blackboard.py`

- [x] `_get_memory` (line 13) - needs: Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `load_targets` (line 20) - needs: Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `save_target` (line 25) - needs: Args, Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/) - docstring also notes `target_type`/`status`/`tags` are accepted but unused (verified: `ArgusMemory.upsert_target` takes no such params) and the real return value is always `None`, not the `int` a casual read of `return memory.upsert_target(url)` might suggest.
- [x] `build_graph_data` (line 50) - needs: Returns. **Done 2026-07-24**: Tier 3 batch (app/GUI/).
- [x] `init_gui_tables` (line 78) - needs: summary. **Done 2026-07-24**: Tier 3 batch (app/GUI/).

## `app/core/agent/agent_factory.py` (not previously tracked by this manifest)

- [x] `build_agent_executor` (line 9) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1 of 3 - smaller/lower-risk files first).

## `app/core/agent/blackboard.py`

- [x] `get_connection` (line 11) - needs: Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `init_schema` (line 21) - needs: summary. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `save_entry` (line 55) - needs: Args. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).

## `app/core/agent/brain.py`

Riskiest single file in the whole backlog (this project's own history: 2 mypy errors and 2 silent-TypeError bugs found here across 2 earlier sessions) - backfilled in 3 smaller sub-batches with a syntax parse + fresh gate scan after each, not as one pass.

- [x] `__init__` (line 178) - needs: Args. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 3, group A - init/setup/ask path).
- [x] `_load_rag_config` (line 239) - needs: Returns. **Done 2026-07-24**: sub-batch 3, group A.
- [x] `_refresh_blackboard` (line 248) - needs: summary. **Done 2026-07-24**: sub-batch 3, group A.
- [x] `_enrich_with_rag` (line 268) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group A.
- [x] `ask` (line 322) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group A.
- [x] `ask_deterministic` (line 338) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group A - noted `callbacks` param is accepted but never referenced in this method's own body (verified by grep).
- [x] `_to_bare_hostname` (line 415) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group B (tool-execution/parsing helpers).
- [x] `_invoke` (line 429) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group B.
- [x] `_try_self_heal` (line 434) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group B.
- [x] `_run_tool_safely` (line 465) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group B.
- [x] `_parse_subdomains` (line 491) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group B.
- [x] `_parse_tech` (line 511) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group B.
- [x] `_clean_tech_string` (line 520) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group B.
- [x] `_parse_interesting_paths` (line 556) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group B.
- [x] `_build_exploit_query` (line 572) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group B.
- [x] `run_deterministic_recon` (line 589) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group C (orchestration/output path).
- [x] `emit` (line 606) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group C - nested function inside `run_deterministic_recon`.
- [x] `_extract_target` (line 666) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group C.
- [x] `_looks_like_schema_echo` (line 691) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group C.
- [x] `_emit_graph_step` (line 813) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group C.
- [x] `_finalize_graph_output` (line 841) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group C.
- [x] `_attach_rag_sources` (line 868) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group C.
- [x] `_process_output` (line 885) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group C - noted `raw_output` param is accepted but never referenced in this method's own body (verified by re-reading the code).
- [x] `simple_ask` (line 907) - needs: Args, Returns. **Done 2026-07-24**: sub-batch 3, group C.
- [x] `dispatch` (line 917) - needs: Args, Raises, Returns. **Done 2026-07-24**: sub-batch 3, group C.

**Tier 4 complete**: `check_docstrings.py --all app/core/agent` now reports 0 violations across all 112 scanned functions in the directory. Full verification after every sub-batch: syntax parse, the gate itself, ruff, CI's exact mypy file list (brain.py/react_workflow.py are both in it), validate_ascii.py, full pytest (339/339) - never just the last one.

## `app/core/agent/contracts.py`

- [x] `normalize_run_mode` (line 48) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `build_run_event` (line 57) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `build_run_snapshot` (line 68) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `build_initial_agent_state` (line 85) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `load_json_file` (line 113) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `write_json_file` (line 123) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `append_run_event` (line 129) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `record_state_event` (line 146) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).

## `app/core/agent/graph.py`

- [x] `self_heal_node` (line 25) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `should_continue` (line 54) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `_route_after_reflective` (line 73) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1) - caught and corrected a slipped edit (a stray placeholder line accidentally inserted after `should_continue` instead of a real docstring on this function) before verifying; re-checked with a syntax parse and a fresh gate scan afterward.
- [x] `build_tactical_graph` (line 88) - needs: Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).

## `app/core/agent/nodes/post_exploit.py`

- [x] `post_exploit_node` (line 10) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).

## `app/core/agent/nodes/recon.py`

- [x] `parse_nmap_ports` (line 13) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `_tech_probe_succeeded` (line 23) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1) - caught and fixed an inaccurate first draft claiming empty input returns True; it actually returns False (verified against the real `if not tech_output...: return False` body) before committing.
- [x] `_infer_web_port_from_scheme` (line 36) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `recon_node` (line 41) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).

## `app/core/agent/nodes/reflective.py`

- [x] `reflective_node` (line 13) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).

## `app/core/agent/react_callback.py`

- [x] `_emit` (line 43) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1).
- [x] `on_agent_action` (line 50) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 1) - note: the gate's own AST logic treats an explicit `-> None` annotation as requiring a Returns section (a `None` annotation is an `ast.Constant`, not an `ast.Name`, so the gate's `getattr(func.returns, "id", None) != "None"` check doesn't recognize it) - documented as `Returns: None` to satisfy this, same quirk hit again on 3 functions in contracts.py/react_callback.py.

## `app/core/agent/react_workflow.py`

- [x] `_try_structured_action` (line 119) - needs: Args, Returns. **Already compliant 2026-07-24** - fixed in an earlier, unrelated session round (see this file's own Methodology Notes on the specs/020 merge and CI-fix rounds); confirmed via a fresh `check_docstrings.py --all` scan, not re-touched.
- [x] `_build_prebuilt_workflow` (line 262) - needs: Args, Returns. **Already compliant 2026-07-24**, same as above.
- [x] `prompt_fn` (line 271) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 2 - react_workflow.py).
- [x] `pre_hook` (line 276) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 2).
- [x] `post_hook` (line 288) - needs: Args, Returns. **Already compliant 2026-07-24**, same as `_try_structured_action` above.
- [x] `_build_custom_workflow` (line 322) - needs: Args, Returns. **Already compliant 2026-07-24**, same.
- [x] `agent_node` (line 345) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 2).
- [x] `_parse_react_output` (line 360) - needs: Args, Returns. **Already compliant 2026-07-24**, same.
- [x] `route_after_execute` (line 644) - needs: Args, Returns. **Already compliant 2026-07-24**, same.
- [x] `_build_tool_map` (line 670) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 2).
- [x] `extract_target` (line 684) - needs: Args, Returns. **Done 2026-07-24**: Tier 4 batch (app/core/agent/, sub-batch 2).

## `app/core/config.py`

- [x] `load` (line 83) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/core/memory/memory_service.py`

- [x] `__init__` (line 19) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_db_ok` (line 35) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_reset_corrupt_db` (line 54) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_get_conn` (line 80) - needs: Raises, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_migrate_from_root` (line 104) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `get_detailed_findings` (line 399) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_looks_like_garbage_domain` (line 586) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `purge_invalid_targets` (line 603) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `get_scan_history` (line 645) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `get_priority_targets` (line 670) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `clear_memory` (line 702) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/core/rag/config.py`

- [x] `from_central` (line 25) - needs: Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `from_dict` (line 41) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/) - caught and fixed an inaccurate first draft (claimed missing-key fallback was to `from_central()`; it's actually `cls()`'s own dataclass defaults) before committing.

## `app/core/rag/document_processor.py`

- [x] `load_from_directory` (line 16) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `load_file` (line 38) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `_load_csv` (line 58) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `_load_json` (line 72) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `_load_pdf` (line 100) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `split_documents` (line 107) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `process_directory` (line 154) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).

## `app/core/rag/embeddings.py`

- [x] `__new__` (line 11) - needs: Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `get_embeddings` (line 17) - needs: Args, Raises, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `reset` (line 101) - needs: summary. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).

## `app/core/rag/local_kb.py`

- [x] `get_tech_context` (line 148) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `analyze_timeout_pattern` (line 169) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `_load_scenario_engine` (line 192) - needs: Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `retrieve_scenario_context` (line 246) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).

## `app/core/rag/manifest.py`

- [x] `compute_kb_hash` (line 56) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `write_manifest` (line 89) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `read_manifest` (line 106) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `needs_rebuild` (line 118) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).

## `app/core/rag/rag_engine.py`

- [x] `__init__` (line 61) - needs: Args. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `initialize` (line 69) - needs: Args. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `retrieve` (line 83) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `retrieve_with_scores` (line 95) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `augment` (line 99) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `query` (line 107) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `query_relevant` (line 144) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `add_document` (line 148) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `rebuild_index` (line 174) - needs: summary. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `format_context` (line 179) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `format_combined_context` (line 189) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).

## `app/core/rag/vector_store.py`

- [x] `__init__` (line 19) - needs: Args. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `build_index` (line 32) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `rebuild_from_directory` (line 51) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `load_index` (line 56) - needs: Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `_persist` (line 92) - needs: summary. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `similarity_search` (line 98) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `similarity_search_with_score` (line 105) - needs: Args, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `get_retriever` (line 112) - needs: Args, Raises, Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).
- [x] `index_size` (line 123) - needs: Returns. **Done 2026-07-24**: Tier 2 batch (app/core/rag/).

## `app/core/registry/tool_registry.py`

- [x] `register` (line 13) - needs: Args, Raises, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/core/safety.py`

- [x] `__init__` (line 32) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `sanitize_input` (line 37) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `is_destructive_payload` (line 47) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `validate_target` (line 56) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `guard_command` (line 88) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_log_block` (line 97) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/modules/__init__.py`

- [x] `register` (line 11) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `run_module` (line 16) - needs: Args, Raises, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `run_all` (line 22) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/modules/argus_reasoning.py`

- [x] `run_autonomous_reasoning` (line 7) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/modules/experimental_agent/agent.py`

- [x] `__init__` (line 124) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_log` (line 193) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_safe_step` (line 197) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_load_subdomain_wordlist` (line 219) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_crtsh_subdomains` (line 240) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_wsl_subfinder` (line 264) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_httpx_probe` (line 290) - needs: Args, Raises, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_probe_subdomain` (line 378) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_scan_subdomain` (line 459) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_load_dir_wordlist` (line 490) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_probe_path` (line 512) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_enumerate_level` (line 530) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_step_reachability` (line 646) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_step_fingerprint` (line 666) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_step_fuzz_files` (line 804) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_step_secrets` (line 839) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_step_sqli` (line 858) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_collect_xss_targets` (line 903) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `add` (line 916) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_step_xss` (line 957) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_build_decider_context` (line 1226) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_adaptive_xss` (line 1345) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_adaptive_sqli_blind` (line 1383) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_adaptive_file_fuzz` (line 1416) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_step_llm_analysis` (line 1449) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `run` (line 1471) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_build_result` (line 1561) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/modules/experimental_agent/agent_payload_decider.py`

- [x] `__init__` (line 105) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `select_payloads` (line 116) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_build_prompt` (line 220) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_validate` (line 340) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_build_prepend_list` (line 464) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_fallback` (line 489) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/modules/experimental_agent/llm_engine.py`

- [x] `_load_seclists_file` (line 159) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_get_reference_payloads` (line 188) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `__init__` (line 209) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `ensure_ready` (line 234) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_pull_model` (line 261) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `generate` (line 292) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_simplify_prompt` (line 373) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `analyze_findings` (line 385) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `quick_classify` (line 533) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/modules/experimental_agent/payload_encoder.py`

- [x] `encode` (line 101) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `get_waf_tips` (line 143) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `apply_random_evasion` (line 151) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_double_url_encode` (line 169) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_triple_url_encode` (line 175) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_hex_encode` (line 185) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_char_encode` (line 191) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_concat_bypass` (line 199) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_mysql_version_comment` (line 206) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_sql_comment_obfuscation` (line 227) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_unicode_encode` (line 286) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_html_entity_encode` (line 298) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_null_byte_insertion` (line 314) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_base64_wrapper` (line 325) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/modules/experimental_agent/verifier.py`

- [x] `__init__` (line 100) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_soft_404_size` (line 117) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `verify_file` (line 130) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `verify_sqli` (line 187) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `verify_xss` (line 224) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `filter_nikto` (line 289) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `filter_secrets` (line 307) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `app/tools/command_runner.py`

- [x] `run` (line 47) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/); also fixed `__init__`, `config`, `_is_waf_blocked`, `_with_safe_path`, `_run_ssh` (undercounted by this manifest, see note above).

## `app/tools/evasion.py`

- [x] `stealth_run` (line 24) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/); also fixed `__init__`, `_get_stealth_headers`, `advanced_vuln_probe` (undercounted by this manifest).

## `app/tools/payloads.py`

- [x] `suggest_payloads` (line 55) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/); also fixed `PayloadSuggester.__init__` (undercounted by this manifest).

## `app/tools/recon.py`

- [x] `_nmap_needs_fallback` (line 65) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/); also fixed `__init__`, `enumerate_subdomains`, `prioritize_targets`, `recon_suite` (undercounted by this manifest).

## `app/tools/reflective_verification.py`

- [x] `__init__` (line 17) - needs: Args. **Done 2026-07-24**: Tier 1 batch (app/tools/).
- [x] `pre_execute_verify` (line 22) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/).
- [x] `post_execute_verify` (line 66) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/).
- [x] `task_difficulty_assessment` (line 112) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/).

## `app/tools/self_heal.py`

- [x] `execute` (line 37) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/); also fixed `__init__` (undercounted by this manifest).
- [x] `system_self_heal` (line 41) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/).
- [x] `restart_service` (line 113) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/).
- [x] `_restart_ollama` (line 122) - needs: Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/).

## `app/tools/simulation.py`

- [x] `__init__` (line 15) - needs: Args. **Done 2026-07-24**: Tier 1 batch (app/tools/).
- [x] `run_simulation` (line 19) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/).

## `app/tools/tool_registry.py`

- [x] `__init__` (line 26) - needs: Args. **Done 2026-07-24**: Tier 1 batch (app/tools/) - `_ToolServiceAdapter.__init__`.
- [x] `execute` (line 35) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/) - `_ToolServiceAdapter.execute`.
- [x] `__init__` (line 47) - needs: summary. **Done 2026-07-24**: Tier 1 batch (app/tools/) - `WSLBridgeTools.__init__`; also fixed `_register_defaults`, `host`/`distro`/`user`/`last_recon_results` properties, and 14 one-line delegator methods (`run`, `check_reachability`, `recon_suite`, `enumerate_subdomains`, `prioritize_targets`, `run_nikto`, `run_ffuf_discovery`, `suggest_payloads`, `analyze_secrets`, `smart_web_search`, `archive_research_subagent`, `crawl_target`, `advanced_vuln_probe`, `system_self_heal`, `get_intelligence_summary`, `query_knowledge_graph`, `run_kali_command`) - all undercounted by this manifest.
- [x] `_register_defaults` (line 72) - needs: summary. **Done 2026-07-24**: Tier 1 batch (app/tools/).

## `app/tools/utils.py`

- [x] `normalize_domain_for_memory` (line 9) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/); also fixed `clean_ansi_codes` (undercounted by this manifest).

## `app/tools/web_search.py`

- [x] `__init__` (line 13) - needs: Args. **Done 2026-07-24**: Tier 1 batch (app/tools/). Note: `smart_web_search`/`archive_research_subagent` were already fully compliant (fixed in an earlier, unrelated commit) - only `__init__` was a real violation.

## `app/tools/xss_classifier.py`

- [x] `_snippet` (line 17) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/).
- [x] `classify_xss_reflection` (line 24) - needs: Args, Returns. **Done 2026-07-24**: Tier 1 batch (app/tools/).

## `app/tools/wsl_bridge.py` (not previously tracked by this manifest - found via `check_docstrings.py --all`)

- [x] `__init__` (line 21) - needs: Args. **Done 2026-07-24**: Tier 1 batch (app/tools/).

## `scripts/_diagnostic_cli_verbose.py`

- [x] `main` (line 23) - needs: summary. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).

## `scripts/check_docstrings.py`

- [x] `main` (line 160) - needs: Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).

## `scripts/check_duplication.py`

- [x] `main` (line 174) - needs: Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).

## `scripts/diagnose_legacy_tactical_graph.py`

- [x] `main` (line 14) - needs: summary. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).

## `scripts/get_port.py`

- [x] `get_port` (line 13) - needs: Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).

## `scripts/run_argus_cli.py`

- [x] `_patched_ws_init` (line 30) - needs: Args, Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `run_analysis` (line 63) - needs: Args. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).

## `scripts/test_rag.py`

- [x] `_write_sample_doc` (line 22) - needs: Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `main` (line 29) - needs: Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).

## `scripts/validate_ascii.py`

- [x] `scan_file` (line 22) - needs: Args, Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `iter_files` (line 28) - needs: Args. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `main` (line 44) - needs: Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).

## `scripts/validate_specs.py`

- [x] `feature_dirs` (line 39) - needs: Args, Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `check_duplicate_numbers` (line 48) - needs: Args, Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `_read_spec_text` (line 60) - needs: Args, Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `_status_tier` (line 68) - needs: Args, Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `check_required_artifacts` (line 84) - needs: Args, Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `check_supersession_targets` (line 104) - needs: Args, Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).
- [x] `main` (line 120) - needs: Returns. **Done 2026-07-24**: Tier 0 docstring backfill batch (scripts/).

## `tests/manual/ai_benchmark.py`

- [x] `run_benchmark` (line 63) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/manual/verify_parsing_fix.py`

- [x] `test_brain_initialization` (line 33) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `test_output_format` (line 59) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `test_gui_output_handling` (line 156) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `main` (line 207) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_gui/test_agent_tab_status.py`

- [x] `_make_controller` (line 12) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_gui/test_session.py`

- [x] `setup_gui_tables` (line 9) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_agent/test_langgraph_workflow.py` (renamed from `tests/test_langgraph_workflow.py` in an unrelated later restructuring)

- [x] `__init__` (line 34) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `invoke` (line 38) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `__init__` (line 61) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `with_structured_output` (line 65) - needs: Args, Raises, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `__init__` (line 87) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `invoke` (line 93) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_memory/test_memory_service.py` (renamed from `tests/test_memory.py` in an unrelated later restructuring)

- [x] `db_path` (line 9) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `mem` (line 17) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_modules/test_tactical_graph_termination.py`

- [x] `_make_state` (line 13) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_ported_safety.py`

- [x] `db_path` (line 90) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `mem` (line 97) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_rag/test_add_document.py`

- [x] `_reset_embedding_factory` (line 23) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `build_index` (line 35) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_make_engine` (line 40) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_rag/test_manifest.py`

- [x] `_make_kb` (line 27) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_rag/test_rag_engine_threshold.py`

- [x] `_reset_embedding_factory` (line 17) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_make_engine` (line 37) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_rag/test_vector_store_manifest.py`

- [x] `_reset_embedding_factory` (line 18) - needs: summary **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_make_config` (line 24) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_registry/test_brain.py`

- [x] `_make_brain` (line 12) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_registry/test_brain_ask.py`

- [x] `__init__` (line 36) - needs: Args **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `invoke` (line 40) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `invoke` (line 86) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `_make_brain_with_fake_rag` (line 123) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `test_ask_extracts_target_before_blackboard_enrichment_not_after` (line 241) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `fake_tool` (line 255) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `invoke` (line 287) - needs: Args, Raises, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `invoke` (line 314) - needs: Args, Raises **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_registry/test_react_prompts.py`

- [x] `_make_state` (line 4) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_registry/test_tool_registry.py`

- [x] `_make_registry` (line 24) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_tools/test_evasion.py`

- [x] `_make_runner` (line 6) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `run` (line 17) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_tools/test_reachability.py`

- [x] `service` (line 8) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `test_falls_back_to_http_when_icmp_is_blocked` (line 63) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `run` (line 73) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `test_tries_opposite_scheme_before_giving_up` (line 88) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `run` (line 91) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `test_still_reports_down_when_both_ping_and_http_fail` (line 107) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.
- [x] `run` (line 110) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_tools/test_reflective_verification.py`

- [x] `verifier` (line 7) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_tools/test_scanners.py`

- [x] `service` (line 8) - needs: Args, Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

## `tests/test_tools/test_self_heal.py`

- [x] `healer` (line 7) - needs: Returns **Done (verified 2026-07-24 reconciliation pass)**: `check_docstrings.py --all` confirms 0 violations for this file; the checkbox was simply never ticked when the actual fix landed in an untracked follow-up batch.

