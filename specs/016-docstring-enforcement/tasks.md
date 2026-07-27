# Tasks: Docstring Enforcement Phase

**Feature**: `016-docstring-enforcement` | **Plan**: `plan.md`

**Status**: Fully implemented (T001-T010 all complete). `scripts/check_docstrings.py --all
app scripts tests` reports 0 violations, repo-wide (see
`specs/checklist-docstring-backfill.md` for the full per-function manifest and
`specs/checklist.md` CHK114-117 for the roll-up). This tasks.md was written retrospectively
(2026-07-24, spec-kit accuracy review) documenting work that had already landed across an
earlier session (the gate script) and this session (the backfill) - not a forward-looking
plan.

- [x] T001 `scripts/check_docstrings.py`: AST-based Google-style docstring gate
  (FR-001-004, NFR-001/002), `--diff <base_ref>` (CI-blocking) and `--all` (informational
  coverage) modes. Predates this tasks.md; already wired into
  `.github/workflows/ci.yml`'s stage-1 as a blocking step before the backfill began.
- [x] T002 Tier 0 backfill: `scripts/` (FR-006). Verified via the gate, ruff,
  `validate_ascii.py`, full pytest.
- [x] T003 Tier 1 backfill: `app/tools/` - manifest originally tracked 28 functions;
  `check_docstrings.py --all app/tools` found 78 real violations before this batch (every
  `__init__`, property, and one-line delegator the manifest had missed, including
  `wsl_bridge.py` which the manifest didn't mention at all). All 78 fixed in this batch,
  not just the tracked 28.
- [x] T004 Tier 2 backfill: `app/core/rag/`. Caught and corrected one drafting mistake
  before commit: `RAGConfig.from_dict()`'s missing-key fallback is `cls()`'s own dataclass
  defaults, not `from_central()` as first written (CHK115).
- [x] T005 Tier 3 backfill: `app/GUI/`.
- [x] T006 Tier 4 backfill: `app/core/agent/` (highest-risk tier - `brain.py`/
  `react_workflow.py`'s documented bug history), done in 3 smaller sub-batches with a
  syntax-parse + fresh gate scan after each. Caught and corrected two more drafting
  mistakes before commit: `_tech_probe_succeeded()` returns `False` (not `True`) for empty
  input; `Verifier.verify_xss()`'s no-match fallback returns the bare `{url}{sep}{param}=`
  with no payload appended, not the last-tried payload's URL (CHK115). Also caught and
  reverted a stray placeholder line accidentally inserted during one edit, before it was
  ever committed.
- [x] T007 Tier 5 backfill: `app/modules/` including `experimental_agent/` (docstrings
  only - module otherwise stays unregistered/untested per its own README).
- [x] T008 Backfill 5 previously-untracked `app/core/` files found via a fresh full-repo
  `--all` scan: `config.py`, `prompts.py`, `safety.py`, `memory/memory_service.py`,
  `registry/tool_registry.py`.
- [x] T009 Backfill ~72 test-fixture functions across ~20 test files.
- [x] T010 Reconciliation pass (2026-07-24): re-verified every remaining item in
  `specs/checklist-docstring-backfill.md` against a live `check_docstrings.py --all` run
  and closed out ~135 checkboxes that had gone stale (the underlying fix had already
  landed in an earlier, untracked batch; only the manifest's tracking was behind).
  Corrected two section headers pointing at pre-rename paths
  (`tests/test_langgraph_workflow.py` -> `tests/test_agent/test_langgraph_workflow.py`,
  `tests/test_memory.py` -> `tests/test_memory/test_memory_service.py`) and removed one
  verbatim-duplicate paragraph. This `research.md`/`plan.md`/`tasks.md` set was authored
  in the same pass, upgrading this feature's own `spec.md` **Status** from `Draft` to
  `Implemented` to match reality.

## Explicitly out of scope for this feature

- **`check_docstrings.py`'s own two AST-walk quirks** (research.md) - documented, not
  fixed; changing shared CI enforcement logic wasn't authorized as part of a
  docstring-*content* backfill.
- **The `pytest.mark.unit`/`integration` marker audit** (`specs/checklist.md` CHK117) -
  done in the same working session on a separate, explicit request; not an FR-001-007
  requirement of this spec and deliberately not folded into these tasks.
