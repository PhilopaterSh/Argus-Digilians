# Implementation Plan: Docstring Enforcement Phase

**Feature**: `016-docstring-enforcement` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

One new CI gate script (`scripts/check_docstrings.py`, already in place before this
tasks.md was written retrospectively - see `tasks.md` T001) plus a per-directory
retroactive backfill of the pre-existing 511+ non-compliant functions it found, tracked
live in `specs/checklist-docstring-backfill.md` and rolled up per-phase in
`specs/checklist.md`'s CHK114-117.

## Design

### `scripts/check_docstrings.py` (existing, documented in research.md)

- `required_sections(func)`: derives the exact set of `{Args, Returns, Raises}` a
  function's docstring must contain from its real signature (`args`/`vararg`/`kwarg`/
  `kwonlyargs`) and body (`walk_own_body()`-scoped `Return`/`Raise` nodes, plus explicit
  non-`None` return annotations) - never from a fixed template.
- `check_function(func, filename)`: missing docstring is always a violation; missing
  section is a violation unless `TRIVIAL_BODY_MAX_STATEMENTS` exempts it.
- `main()`: `--diff <base_ref>` (CI-blocking, stage 1) restricts scanning to lines the
  current diff actually touched (`changed_line_ranges()` via `git diff --unified=0`);
  `--all` (informational) scans everything and prints a `Scanned N functions.` coverage
  line, used to track FR-006/SC-002 backfill progress over time.

### Backfill execution (FR-006/FR-007)

Batches, in order, each independently verified (gate, ruff, CI's exact mypy file list
where applicable, `validate_ascii.py`, full pytest) before commit - see
`specs/checklist-docstring-backfill.md` for the per-function manifest and
`specs/checklist.md` CHK114 for the roll-up:

1. Tier 0 - `scripts/` (lowest blast radius, run first to validate the batching process
   itself).
2. Tier 1 - `app/tools/`.
3. Tier 2 - `app/core/rag/`.
4. Tier 3 - `app/GUI/`.
5. Tier 4 - `app/core/agent/` (highest blast radius - `brain.py`/`react_workflow.py` are
   this project's most historically bug-prone files - done last, in 3 smaller
   sub-batches with a syntax-parse + fresh gate scan after each rather than one pass).
6. Tier 5 - `app/modules/` including `experimental_agent/` (docstrings only - this module
   stays otherwise untouched/unregistered/untested per its own README and this project's
   risk-aware-exclusion convention).
7. 5 previously-untracked `app/core/` files found via a fresh full-repo `--all` scan
   (`config.py`, `prompts.py`, `safety.py`, `memory/memory_service.py`,
   `registry/tool_registry.py`) - the original per-tier plan undercounted these; caught
   before declaring the backfill complete, not after.
8. ~72 test-fixture functions across ~20 test files, plus a later reconciliation pass
   (2026-07-24) that caught the remaining functions `specs/checklist-docstring-backfill.md`
   itself had gone stale on tracking (checkboxes never ticked despite the underlying fix
   already landing).

## Testing Strategy

No new test suite - `check_docstrings.py` is itself the verification mechanism
(structural AST check, not behavioral), run in both `--all` (full coverage) and
`--diff origin/<base>` (CI's real blocking invocation) modes after every batch, alongside
the project's existing full gate suite (ruff, mypy, validate_ascii, pytest) to catch any
accidental behavior change slipped in alongside a docstring edit.

## Rollout

CI (`.github/workflows/ci.yml`) already runs `check_docstrings.py --diff
"origin/${{ github.base_ref || 'main' }}" app scripts tests` as a blocking stage-1 step
(FR-005) - no separate rollout step was needed since the diff-scoped gate was already
live before the backfill started; backfilling only closes the pre-existing `--all`-mode
gap, it doesn't change what CI blocks on.
