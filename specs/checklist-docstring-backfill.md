# Docstring Backfill Manifest (specs/016-docstring-enforcement, FR-006/FR-007)

Auto-generated inventory of functions this PR's diff touches that need a real, human-reviewed docstring - NOT auto-applied, per FR-006 ("a docstring asserting an incorrect parameter, return type, or exception is worse than no docstring"). Track backfill progress here per module, same pattern as specs/checklist.md's CHK series.

**Known gap, found 2026-07-24**: this manifest under-counts. `scripts/check_docstrings.py --all app/tools` reported 78 real violations before that directory's backfill batch, not the 28 tracked below for `app/tools/` - the manifest missed every `__init__`, property, and one-line delegator method across `command_runner.py`, `evasion.py`, `payloads.py`, `recon.py`, `self_heal.py`, `tool_registry.py` (17 of them alone), `web_search.py`, and `wsl_bridge.py` (a file this manifest doesn't mention at all). All 78 were fixed in the same batch as the 28 tracked items, verified via `check_docstrings.py --all` returning 0. Other directories not yet backfilled may have the same undercount - re-run `check_docstrings.py --all <dir>` directly before trusting this file's per-directory counts, rather than treating the checked-off items below as the complete picture for that directory.

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

- [ ] `__init__` (line 178) - needs: Args
- [ ] `_load_rag_config` (line 239) - needs: Returns
- [ ] `_refresh_blackboard` (line 248) - needs: summary
- [ ] `_enrich_with_rag` (line 268) - needs: Args, Returns
- [ ] `ask` (line 322) - needs: Args, Returns
- [ ] `ask_deterministic` (line 338) - needs: Args, Returns
- [ ] `_to_bare_hostname` (line 415) - needs: Args, Returns
- [ ] `_invoke` (line 429) - needs: Args, Returns
- [ ] `_try_self_heal` (line 434) - needs: Args, Returns
- [ ] `_run_tool_safely` (line 465) - needs: Args, Returns
- [ ] `_parse_subdomains` (line 491) - needs: Args, Returns
- [ ] `_parse_tech` (line 511) - needs: Args, Returns
- [ ] `_clean_tech_string` (line 520) - needs: Args, Returns
- [ ] `_parse_interesting_paths` (line 556) - needs: Args, Returns
- [ ] `_build_exploit_query` (line 572) - needs: Args, Returns
- [ ] `run_deterministic_recon` (line 589) - needs: Args, Returns
- [ ] `emit` (line 606) - needs: Args, Returns
- [ ] `_extract_target` (line 666) - needs: Args, Returns
- [ ] `_looks_like_schema_echo` (line 691) - needs: Args, Returns
- [ ] `_emit_graph_step` (line 813) - needs: Args, Returns
- [ ] `_finalize_graph_output` (line 841) - needs: Args, Returns
- [ ] `_attach_rag_sources` (line 868) - needs: Args, Returns
- [ ] `_process_output` (line 885) - needs: Args, Returns
- [ ] `simple_ask` (line 907) - needs: Args, Returns
- [ ] `dispatch` (line 917) - needs: Args, Raises, Returns

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

- [ ] `_try_structured_action` (line 119) - needs: Args, Returns
- [ ] `_build_prebuilt_workflow` (line 262) - needs: Args, Returns
- [ ] `prompt_fn` (line 271) - needs: Args, Returns
- [ ] `pre_hook` (line 276) - needs: Args, Returns
- [ ] `post_hook` (line 288) - needs: Args, Returns
- [ ] `_build_custom_workflow` (line 322) - needs: Args, Returns
- [ ] `agent_node` (line 345) - needs: Args, Returns
- [ ] `_parse_react_output` (line 360) - needs: Args, Returns
- [ ] `route_after_execute` (line 644) - needs: Args, Returns
- [ ] `_build_tool_map` (line 670) - needs: Args, Returns
- [ ] `extract_target` (line 684) - needs: Args, Returns

## `app/core/config.py`

- [ ] `load` (line 83) - needs: Args, Returns

## `app/core/memory/memory_service.py`

- [ ] `__init__` (line 19) - needs: Args, Returns
- [ ] `_db_ok` (line 35) - needs: Returns
- [ ] `_reset_corrupt_db` (line 54) - needs: Returns
- [ ] `_get_conn` (line 80) - needs: Raises, Returns
- [ ] `_migrate_from_root` (line 104) - needs: Returns
- [ ] `get_detailed_findings` (line 399) - needs: Args, Returns
- [ ] `_looks_like_garbage_domain` (line 586) - needs: Args, Returns
- [ ] `purge_invalid_targets` (line 603) - needs: Returns
- [ ] `get_scan_history` (line 645) - needs: Args, Returns
- [ ] `get_priority_targets` (line 670) - needs: Args, Returns
- [ ] `clear_memory` (line 702) - needs: Returns

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

- [ ] `register` (line 13) - needs: Args, Raises, Returns

## `app/core/safety.py`

- [ ] `__init__` (line 32) - needs: Args
- [ ] `sanitize_input` (line 37) - needs: Args, Returns
- [ ] `is_destructive_payload` (line 47) - needs: Args, Returns
- [ ] `validate_target` (line 56) - needs: Args, Returns
- [ ] `guard_command` (line 88) - needs: Args, Returns
- [ ] `_log_block` (line 97) - needs: Args

## `app/modules/__init__.py`

- [ ] `register` (line 11) - needs: Args, Returns
- [ ] `run_module` (line 16) - needs: Args, Raises, Returns
- [ ] `run_all` (line 22) - needs: Args, Returns

## `app/modules/argus_reasoning.py`

- [ ] `run_autonomous_reasoning` (line 7) - needs: summary

## `app/modules/experimental_agent/agent.py`

- [ ] `__init__` (line 124) - needs: Args
- [ ] `_log` (line 193) - needs: Args
- [ ] `_safe_step` (line 197) - needs: Args, Returns
- [ ] `_load_subdomain_wordlist` (line 219) - needs: Returns
- [ ] `_crtsh_subdomains` (line 240) - needs: Args, Returns
- [ ] `_wsl_subfinder` (line 264) - needs: Args, Returns
- [ ] `_httpx_probe` (line 290) - needs: Args, Raises, Returns
- [ ] `_probe_subdomain` (line 378) - needs: Args, Returns
- [ ] `_scan_subdomain` (line 459) - needs: Args
- [ ] `_load_dir_wordlist` (line 490) - needs: Returns
- [ ] `_probe_path` (line 512) - needs: Args, Returns
- [ ] `_enumerate_level` (line 530) - needs: Args, Returns
- [ ] `_step_reachability` (line 646) - needs: Returns
- [ ] `_step_fingerprint` (line 666) - needs: summary
- [ ] `_step_fuzz_files` (line 804) - needs: summary
- [ ] `_step_secrets` (line 839) - needs: summary
- [ ] `_step_sqli` (line 858) - needs: summary
- [ ] `_collect_xss_targets` (line 903) - needs: Args, Returns
- [ ] `add` (line 916) - needs: Args
- [ ] `_step_xss` (line 957) - needs: summary
- [ ] `_build_decider_context` (line 1226) - needs: Args, Returns
- [ ] `_adaptive_xss` (line 1345) - needs: Args
- [ ] `_adaptive_sqli_blind` (line 1383) - needs: Args
- [ ] `_adaptive_file_fuzz` (line 1416) - needs: Args
- [ ] `_step_llm_analysis` (line 1449) - needs: Returns
- [ ] `run` (line 1471) - needs: Returns
- [ ] `_build_result` (line 1561) - needs: Args, Returns

## `app/modules/experimental_agent/agent_payload_decider.py`

- [ ] `__init__` (line 105) - needs: Args, Returns
- [ ] `select_payloads` (line 116) - needs: Args, Returns
- [ ] `_build_prompt` (line 220) - needs: Args, Returns
- [ ] `_validate` (line 340) - needs: Args, Returns
- [ ] `_build_prepend_list` (line 464) - needs: Args, Returns
- [ ] `_fallback` (line 489) - needs: Args, Returns

## `app/modules/experimental_agent/llm_engine.py`

- [ ] `_load_seclists_file` (line 159) - needs: Args, Returns
- [ ] `_get_reference_payloads` (line 188) - needs: Args, Returns
- [ ] `__init__` (line 209) - needs: Args
- [ ] `ensure_ready` (line 234) - needs: Returns
- [ ] `_pull_model` (line 261) - needs: Returns
- [ ] `generate` (line 292) - needs: Args, Returns
- [ ] `_simplify_prompt` (line 373) - needs: Args, Returns
- [ ] `analyze_findings` (line 385) - needs: Args, Returns
- [ ] `quick_classify` (line 533) - needs: Args, Returns

## `app/modules/experimental_agent/payload_encoder.py`

- [ ] `encode` (line 101) - needs: Args, Returns
- [ ] `get_waf_tips` (line 143) - needs: Args, Returns
- [ ] `apply_random_evasion` (line 151) - needs: Args, Returns
- [ ] `_double_url_encode` (line 169) - needs: Args, Returns
- [ ] `_triple_url_encode` (line 175) - needs: Args, Returns
- [ ] `_hex_encode` (line 185) - needs: Args, Returns
- [ ] `_char_encode` (line 191) - needs: Args, Returns
- [ ] `_concat_bypass` (line 199) - needs: Args, Returns
- [ ] `_mysql_version_comment` (line 206) - needs: Args, Returns
- [ ] `_sql_comment_obfuscation` (line 227) - needs: Args, Returns
- [ ] `_unicode_encode` (line 286) - needs: Args, Returns
- [ ] `_html_entity_encode` (line 298) - needs: Args, Returns
- [ ] `_null_byte_insertion` (line 314) - needs: Args, Returns
- [ ] `_base64_wrapper` (line 325) - needs: Args, Returns

## `app/modules/experimental_agent/verifier.py`

- [ ] `__init__` (line 100) - needs: summary
- [ ] `_soft_404_size` (line 117) - needs: Args, Returns
- [ ] `verify_file` (line 130) - needs: Args, Returns
- [ ] `verify_sqli` (line 187) - needs: Args, Returns
- [ ] `verify_xss` (line 224) - needs: Args, Returns
- [ ] `filter_nikto` (line 289) - needs: Args, Returns
- [ ] `filter_secrets` (line 307) - needs: Args, Returns

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

- [ ] `run_benchmark` (line 63) - needs: summary

## `tests/manual/verify_parsing_fix.py`

- [ ] `test_brain_initialization` (line 33) - needs: Returns
- [ ] `test_output_format` (line 59) - needs: Returns
- [ ] `test_gui_output_handling` (line 156) - needs: Returns
- [ ] `main` (line 207) - needs: Returns

## `tests/test_gui/test_agent_tab_status.py`

- [ ] `_make_controller` (line 12) - needs: Args, Returns

## `tests/test_gui/test_session.py`

- [ ] `setup_gui_tables` (line 9) - needs: summary

## `tests/test_langgraph_workflow.py`

- [ ] `__init__` (line 34) - needs: Args
- [ ] `invoke` (line 38) - needs: Args, Returns
- [ ] `__init__` (line 61) - needs: Args
- [ ] `with_structured_output` (line 65) - needs: Args, Raises, Returns
- [ ] `__init__` (line 87) - needs: Args
- [ ] `invoke` (line 93) - needs: Args, Returns

## `tests/test_memory.py`

- [ ] `db_path` (line 9) - needs: summary
- [ ] `mem` (line 17) - needs: Args

## `tests/test_modules/test_tactical_graph_termination.py`

- [ ] `_make_state` (line 13) - needs: Args, Returns

## `tests/test_ported_safety.py`

- [ ] `db_path` (line 90) - needs: summary
- [ ] `mem` (line 97) - needs: Args

## `tests/test_rag/test_add_document.py`

- [ ] `_reset_embedding_factory` (line 23) - needs: summary
- [ ] `build_index` (line 35) - needs: Args, Returns
- [ ] `_make_engine` (line 40) - needs: Args, Returns

## `tests/test_rag/test_manifest.py`

- [ ] `_make_kb` (line 27) - needs: Args, Returns

## `tests/test_rag/test_rag_engine_threshold.py`

- [ ] `_reset_embedding_factory` (line 17) - needs: summary
- [ ] `_make_engine` (line 37) - needs: Args, Returns

## `tests/test_rag/test_vector_store_manifest.py`

- [ ] `_reset_embedding_factory` (line 18) - needs: summary
- [ ] `_make_config` (line 24) - needs: Args, Returns

## `tests/test_registry/test_brain.py`

- [ ] `_make_brain` (line 12) - needs: Returns

## `tests/test_registry/test_brain_ask.py`

- [ ] `__init__` (line 36) - needs: Args
- [ ] `invoke` (line 40) - needs: Args, Returns
- [ ] `invoke` (line 86) - needs: Args, Returns
- [ ] `_make_brain_with_fake_rag` (line 123) - needs: Args, Returns
- [ ] `test_ask_extracts_target_before_blackboard_enrichment_not_after` (line 241) - needs: Returns
- [ ] `fake_tool` (line 255) - needs: Args, Returns
- [ ] `invoke` (line 287) - needs: Args, Raises, Returns
- [ ] `invoke` (line 314) - needs: Args, Raises

## `tests/test_registry/test_react_prompts.py`

- [ ] `_make_state` (line 4) - needs: Args, Returns

## `tests/test_registry/test_tool_registry.py`

- [ ] `_make_registry` (line 24) - needs: Returns

## `tests/test_tools/test_evasion.py`

- [ ] `_make_runner` (line 6) - needs: Args, Returns
- [ ] `run` (line 17) - needs: Args, Returns

## `tests/test_tools/test_reachability.py`

- [ ] `service` (line 8) - needs: Returns
- [ ] `test_falls_back_to_http_when_icmp_is_blocked` (line 63) - needs: Args, Returns
- [ ] `run` (line 73) - needs: Args, Returns
- [ ] `test_tries_opposite_scheme_before_giving_up` (line 88) - needs: Args, Returns
- [ ] `run` (line 91) - needs: Args, Returns
- [ ] `test_still_reports_down_when_both_ping_and_http_fail` (line 107) - needs: Args, Returns
- [ ] `run` (line 110) - needs: Args, Returns

## `tests/test_tools/test_reflective_verification.py`

- [ ] `verifier` (line 7) - needs: Returns

## `tests/test_tools/test_scanners.py`

- [ ] `service` (line 8) - needs: Args, Returns

## `tests/test_tools/test_self_heal.py`

- [ ] `healer` (line 7) - needs: Returns

