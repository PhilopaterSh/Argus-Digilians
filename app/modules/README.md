# app/modules/ — standalone CLI utilities, not wired into the live agent

Found during a `main`-organization review (2026-07-19, orchestrator + opencode-delegate;
codex-delegate unavailable, hard usage-limit wall until 2026-08-17 - disclosed, not silently
skipped) that this directory's status was undocumented, unlike `app/modules/experimental_agent/`
which has its own README. This file fills that gap.

## What these are

Every file below except `base.py` and `ddgs.py` is a real standalone script - each has its own
`if __name__ == "__main__":` entry point and is meant to be run directly
(`python -m app.modules.<name>` or `python app/modules/<name>.py`), not imported by the live
agent/GUI pipeline. Confirmed by grep: none of them are referenced anywhere in `app/tools/`,
`app/core/`, or `app/GUI/` - only `tests/test_modules/test_imports.py` touches them, and only to
assert the import doesn't raise.

- `argus_deep_exploit.py`, `argus_reasoning.py`, `stealth_exploit.py` - standalone exploitation/
  reasoning CLI entry points.
- `crawler.py` - a standalone crawler script (`requests.get` + regex href extraction) with a
  hardcoded demo target (`http://testasp.vulnweb.com`), not a parameterized tool - confirmed
  2026-07-19, along with an unused import (`WSLBridgeTools`, removed same date). Distinct
  from `app/tools/crawler.py`'s `CrawlerService`, which is the production crawler actually
  registered in `app/tools/tool_registry.py`'s `WSLBridgeTools`. Same basename, unrelated code -
  if grepping for "crawler", check which file a result is actually in.
- `map_target.py`, `run_full_recon.py`, `run_recon.py` - standalone recon CLI entry points, each a
  thin wrapper around `WSLBridgeTools`.
- `seed_memory.py` - manually seeds `ArgusMemory`'s knowledge-graph tables
  (`upsert_entity`/`add_relation`) with example data for local testing/demos.

## `base.py` and `ddgs.py` - different from the above

- `base.py` **is** live: `app/modules/__init__.py` imports `BaseTacticalModule` from it and
  exposes `register()`/`run_module()`/`run_all()`/`list_modules()` as this package's own
  lightweight plugin registry. None of the 8 scripts above actually register through it, though -
  that registry currently has no real callers either.
- `ddgs.py` is a single-line, no-op re-export (`from duckduckgo_search import DDGS`) with no
  `__main__` guard and no function - not a CLI utility like the others, and not used anywhere.
  Confirmed pointless during this same review; left in place (not deleted) rather than acted on
  unilaterally, per this project's standing three-way-review practice.

## Before treating any of this as production-critical

None of the 8 standalone scripts are covered by CI, and several call `WSLBridgeTools()` directly
(a real, heavyweight WSL/Kali bridge) - running them requires the same environment the main agent
needs. Treat them as developer utilities, not supported entry points, until someone adds real
tests and wires them through `app/modules/__init__.py`'s registry (or removes that registry if it
stays unused).
