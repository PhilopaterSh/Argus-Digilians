# Research: Docstring Enforcement Phase

**Feature**: `016-docstring-enforcement`

## Why AST-based, stdlib-only (NFR-001)

`scripts/check_docstrings.py` parses each file with `ast.parse()` and inspects
`FunctionDef`/`AsyncFunctionDef` nodes directly - no third-party docstring linter
(pydocstyle, darglint, etc.) was pulled in. This mirrors the existing `ruff check .` /
`validate_ascii.py` gates: zero new runtime dependency, fast enough to run on every PR,
and easy to reason about exactly (no opaque third-party rule engine to audit).

## Why diff-scoped rollout, modeled on existing precedent (FR-005)

At the time this gate was written, a full-repo enforcement pass would have failed CI on
511+ pre-existing functions with no docstring or an incomplete one - the same shape of
problem `ruff.toml` and `mypy.ini` already solved for this project:

- `ruff.toml`: "Conservative starting rule set... Expand `select` over time."
- `mypy.ini`: lenient globally, strict only for a curated "typed modules" file list.

`check_docstrings.py --diff <base_ref>` reuses that same staged-rollout shape: only
functions whose lines were touched by the current diff are checked, so new code is held
to the standard immediately (SC-001) without retroactively blocking unrelated PRs on the
pre-existing backlog (FR-005). `--all` (no `--diff`) is the separate, informational-only
full-repo coverage report used to track backfill progress (SC-002).

## Design decision: `TRIVIAL_BODY_MAX_STATEMENTS = 1`

A function whose body is a single statement (e.g. `def __repr__(self): return self.name`)
doesn't need a full Args/Returns/Raises breakdown - demanding one is ceremony, not
documentation value. `check_function()` skips section-presence checks (but still requires
*a* docstring exists) whenever `body_len <= TRIVIAL_BODY_MAX_STATEMENTS`. This is what
keeps one-line delegator methods and trivial properties from needing inflated docstrings
during the backfill (FR-006).

## Two real quirks in the gate itself, found during backfill (not fixed - see CHK116)

1. **`walk_own_body()`'s nested-`def` boundary**: it excludes further descent into an
   *already-nested* `FunctionDef`'s children, but the nested `FunctionDef` node itself is
   still popped from the stack and its own top-level children (including its own
   `return`) get walked once that happens. Net effect: an outer function containing an
   inline `def helper(): return x` gets a false "needs Returns" flag for a return that
   isn't actually the outer function's own. Hit repeatedly in
   `tests/manual/verify_parsing_fix.py` and `tests/test_tools/test_reachability.py`.
2. **Explicit `-> None` is an `ast.Constant`, not `ast.Name`**: `has_return_annotation`'s
   check (`getattr(func.returns, "id", None) != "None"`) only recognizes a bare `None`
   annotation via `ast.Name.id`; an explicit `-> None` return annotation is parsed as
   `ast.Constant(value=None)`, which has no `.id` attribute, so `getattr(..., None)`
   silently returns `None` and the comparison `None != "None"` is `True` - the function
   is (correctly, if for the wrong structural reason) still flagged as needing a
   `Returns:` section. Confirmed harmless in practice (the fix is always just writing
   `Returns: None`), but the *reason* it's flagged is not the one a reader would expect
   from the code.

Both were worked around at the docstring-content level (documenting the real behavior,
in one case adding an explicit `Returns: None`) rather than by patching the gate script -
changing shared CI enforcement logic was out of scope for a docstring-content backfill
task, and wasn't authorized as part of this effort.

## Backfill batching strategy (FR-006)

A single automated bulk rewrite was explicitly rejected (FR-006: "a docstring asserting
an incorrect parameter, return type, or exception is worse than no docstring"). Every
batch was scoped to one directory/tier, backfilled by reading the actual function body
(not inferring from its name/signature alone), and verified independently before commit:
`check_docstrings.py` itself, `ruff`, CI's exact `mypy` file list where applicable,
`validate_ascii.py`, and the full `pytest` suite. Three real docstring-drafting mistakes
were caught this way *before* they shipped (see CHK115 in `specs/checklist.md`) - direct
evidence the batching discipline, not just the gate's existence, is what FR-006 is for.
