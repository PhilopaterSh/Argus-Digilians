# Feature Specification: Docstring Enforcement Phase

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `016-docstring-enforcement`

**Created**: 2026-07-08

**Status**: Draft

**Input**: Introduce a permanent Spec Kit phase that enforces Google-style docstrings
(Summary/Args/Returns/Raises) on every function, applied retroactively where feasible and
enforced automatically on all future code.

---

## Why this feature

`scripts/check_docstrings.py` audit (2026-07-08, AST-based, real scan not estimated):
513 functions across `app/`, `tests/`, `scripts/`, `docs/`; 427 (83.2%) have no docstring,
84 (16.4%) have a docstring but no Args/Returns/Raises sections, 2 (0.4%) are already
Google-style compliant. Undocumented internal functions were directly implicated in the
`fix/copy-setup-to-scripts` debugging sessions logged in `specs/010-langgraph-agent/tasks.md`
and `CHANGELOG.md`, where the AI agent operating this codebase had to re-derive function
contracts from source instead of reading them - the exact failure mode this phase prevents.

## Requirements

### Functional Requirements

- **FR-001**: Every function added or modified in a pull request MUST have a docstring.
- **FR-002**: A function's docstring MUST include an `Args:` section iff the function takes
  parameters beyond `self`/`cls`.
- **FR-003**: A function's docstring MUST include a `Returns:` section iff the function has a
  `return <value>` statement in its own body (not a nested function's) or a non-`None` return
  annotation.
- **FR-004**: A function's docstring MUST include a `Raises:` section iff the function contains
  a `raise` statement in its own body.
- **FR-005**: Enforcement MUST be diff-scoped in CI (stage 1): only functions touched by a PR
  are checked. The existing 511 non-compliant functions MUST NOT retroactively fail CI on
  unrelated changes - mirrors the staged rollout already used for `ruff.toml` ("conservative
  starting rule set... expand over time") and `mypy.ini` ("lenient globally... strict only for
  newly authored... modules").
- **FR-006**: Backfill of the existing 511 functions MUST proceed per-directory/per-module in
  reviewed batches, not as a single automated bulk rewrite - a docstring asserting an incorrect
  parameter, return type, or exception is worse than no docstring for both human and LLM readers.
- **FR-007**: `specs/checklist.md` MUST track backfill progress per module as a CHK series,
  same pattern as the 010-014 phase entries added 2026-07-07.

### Non-Functional Requirements

- **NFR-001**: The check script MUST run in CI with zero new runtime dependencies (stdlib
  `ast` only) - keeps it as fast/dependency-free as the existing `ruff check .` / `validate_ascii.py`
  gates.
- **NFR-002**: The check MUST NOT require semantic understanding of function behavior to
  validate structurally (docstring section presence vs. actual signature/body) - content
  *quality* (is the Summary accurate?) is a review-time concern, not a CI-gate concern.

## Success Criteria

- **SC-001**: `scripts/check_docstrings.py --diff <base>` returns 0 violations for any PR
  touching `app/`, `scripts/`, or `tests/` going forward.
- **SC-002**: Docstring coverage (Google-style, `--all` mode) is tracked per-directory in
  `specs/checklist.md` and trends upward release over release.
- **SC-003**: Zero regressions - the gate never fails on a function the PR did not touch.

## Assumptions

- "Retroactive" backfill is a scheduled, reviewed, incremental effort (FR-006), not a
  same-day bulk edit - stated explicitly since the parent request asked for full retroactive
  coverage, which is achievable but not safely automatable in one unreviewed pass at this scale.
