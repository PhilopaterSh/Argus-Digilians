# Merge notes: Argus-Digilians + Editing_Salma _Branch

This folder is a merge of two local copies:

- **Base**: `HABIBA/Argus-Digilians` (main working copy, commit `9cb999f`)
- **Compared against**: `HABIBA/Editing_Salma _Branch/Argus-Digilians` (Salma's branch, commit `250b092`)

## How the merge was done

1. **Files identical in both** (312 files) - kept once, at their normal path. No duplication.
2. **Files that exist only in Salma's branch** (12 files) - copied in as-is, normal path. These are Salma's new, unmerged tools:
   - `Payloads/` (payload database + loader: `build_payload_db.py`, `payload_store.py`, wordlists)
   - `app/tools/path_traversal.py`
   - `app/tools/encoding_ladder.py`
   - `tests/manual/ai_benchmark.py`
   - `tests/test_agent/test_deterministic_report.py`
   - `tests/test_tools/test_path_traversal.py`
3. **Files that exist in both but differ** (128 files) - the base version stays at its normal path; Salma's differing version is added alongside it with a `.SALMA` suffix inserted before the extension, e.g.:
   - `app/tools/evasion.py` (base) sits next to `app/tools/evasion.SALMA.py` (Salma's version)
   - `app/core/agent/brain.py` next to `app/core/agent/brain.SALMA.py`

   128 files differ mainly because `main` has moved forward significantly since Salma's branch was last synced (new benchmark suite, phase12/zero-tool-call agent fixes, browser screenshot feature, etc.) - most `.SALMA.*` files are simply an **older** version of the same file, not necessarily a meaningful alternative. Diff each pair individually before assuming Salma's side has something worth pulling in.

## Excluded from this copy

`.git`, `Argus_venv`, `__pycache__`, `.mypy_cache`, `.pytest_cache`, `.ruff_cache`, `.coverage`, `.streamlit`, `.claude`, `.opencode` (local caches/tooling, not project source).

## Not yet done

Salma's `path_traversal.py` / `encoding_ladder.py` are not registered in `tool_registry.py` / `brain_tools.py`, so the agent cannot invoke them yet - this is a follow-up decision, not done automatically here.
