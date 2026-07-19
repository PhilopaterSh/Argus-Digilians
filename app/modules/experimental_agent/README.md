# experimental_agent — opt-in, unregistered, undertested

This module is **not part of the production tool set**. It is not registered in
`app/core/registry/tool_registry.py` and is not reachable through any normal
agent/tool entry point (verified repeatedly via grep during
`specs/001-merge-branches` - zero references outside this directory besides
explanatory comments elsewhere). Nothing in the normal application flow
imports or calls into this package.

## Why it exists

Ported from the `momen` contributor branch during branch-unification
(`specs/001-merge-branches` T014) as a 13-step, LLM-driven scanning pipeline,
kept opt-in per that feature's Constitution Principle I rather than wired into
the live agent.

## Known state - read before enabling this for real use

- **Two confirmed blocking bugs were found and fixed after the port** (see
  `specs/001-merge-branches/tasks.md`'s Methodology Notes for commit
  `1309e5b` and `3361d89`): a missing-argument `TypeError` that made the
  entire LLM-driven adaptive-retry path for XSS/blind-SQLi silently produce
  zero findings, and an `AttributeError` from a `self._session` that was
  never initialized, which made SSRF/open-redirect/XXE detection silently
  produce zero findings too. Both were only found because someone traced an
  actual call path by hand - neither pytest, ruff, nor mypy catch this class
  of bug.
- **This module has zero automated test coverage.** Every step is wrapped in
  `_safe_step()`, which catches all exceptions and returns `None`/continues -
  by design, so one broken step doesn't abort a whole scan, but the same
  property means further undiscovered bugs of the same shape (a step that
  always raises and is always silently caught) are plausible and would not
  be visible from the outside without deliberately exercising each step.
- Given the above, **treat every capability in this module as unverified
  until it has a real test** exercising it end-to-end (mocked LLM/HTTP
  boundaries, real assertions on the actual finding/output produced) - the
  two bugs already found are graduation-worthy candidates for exactly that
  kind of test, not yet written.

## Before promoting this out of opt-in status

1. Write real tests for each of the 13 steps - at minimum, one that proves
   the step can actually record a finding without raising, not just that it
   doesn't crash on import.
2. Only then consider registering it in `tool_registry.py`.
3. Revisit `ArgusMemory`'s missing `severity` semantics if a second real
   caller needs them beyond what `app/core/memory/memory_service.py`
   already added for this module (see that file's `get_detailed_findings()`
   docstring).
