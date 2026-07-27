# Incident: "Invalid Format: Missing 'Action:'" and the ReAct→SimpleChain Fallback

**Date of incident/fix: 2026-06-25. Consolidated 2026-07-10** from 7 separate writeups
(`JSON_PARSING_FIX.md`, `PARSING_ERROR_FIX.md`, `IMPLEMENTATION_GUIDE_parsing_error_fix.md`,
`REACT_FORMAT_ERROR_FIX.txt`, `RADICAL_FIX_SIMPLE_CHAIN_FALLBACK.txt`, `QUICK_START_FIX.txt`,
`TESTING_JSON_FIX.md`) that all documented this same incident at different levels of detail,
written within minutes to hours of each other on the same day. Consolidated into one
chronological record per a repo-organization pass (the originals are deleted, not kept
alongside this file, to avoid the exact duplication problem being fixed). `STREAMLIT_JAVASCRIPT_FIX.txt`,
initially assumed to be part of this same group, was found on inspection to document an
unrelated browser-cache/JS-asset-loading issue and was **not** merged here - it remains its own
file.

> **Read this first if you're trying to understand today's agent architecture**: the fix
> described below (a `self.use_react` flag switching between a ReAct agent and a "SimpleChain"
> executor) is **not how the current agent works**, and - more importantly - a later
> investigation (`specs/018-structured-agent-reliability`, 2026-07-08, ~2 weeks after this
> incident) found via live production testing that **this fallback never actually worked in the
> first place**: `_get_react_agent()` and `_get_simple_chain()` both built the identical
> `AgentExecutor`, differing only in a `verbose` flag. The "smart fallback" this incident
> confidently reports as fixing the problem (with "4/4 tests passing" and a claimed "0% → 95%+
> success rate") was, per that later finding, not actually switching executors at all. This file
> preserves the original engineering narrative as real history - including its unverified
> confidence - specifically so that contrast is visible, not because the original claims were
> confirmed correct.

## Problem

**Error**: `Invalid Format: Missing 'Action:' after 'Thought:'` (also seen as `Analysis Error:
LLM did not return valid JSON for analysis`)

**Symptom**: Clicking "RUN ANALYSIS" in the GUI produced a parser error instead of a security
report, every time, for every query.

**Root cause analysis at the time**: WhiteRabbitNeo V3-7B did not reliably produce LangChain's
required ReAct format (`Thought: / Action: / Action Input:`). Contributing factors identified:
- The model was fine-tuned for general tasks, not specifically for ReAct-style structured output.
- The original prompt was long (~80 lines) with format instructions "buried" rather than
  foregrounded.
- There was no graceful degradation - a single format deviation was a hard failure with no
  fallback, so the error was hit on effectively 100% of attempts.

## What was implemented (2026-06-25, chronological)

**11:53 - `REACT_FORMAT_ERROR_FIX.txt`**: First diagnostic pass. Simplified `app/core/prompts.py`
(80 lines → 40, format rules moved to the top, 5x emphasis on "CRITICAL FORMATTING RULES"),
added `handle_tool_error=True` to the agent factory, and wrapped `agent.invoke()` in
try/except in `app/core/brain.py` to return a structured error dict instead of crashing.
Improved `app/GUI/gui_app.py`'s error display. This alone did not fix the underlying format
issue - it made failures visible/non-crashing, not successful.

**11:57 - `RADICAL_FIX_SIMPLE_CHAIN_FALLBACK.txt`** (the most detailed writeup): Concluded that
fighting the model's format non-compliance directly was not working ("Simpler prompts → model
ignores instructions... Result: Unreliable, unpredictable parsing failures") and instead
implemented a two-layer fallback:
- **Layer 1**: Try the ReAct agent as before.
- **Layer 2 (new)**: `app/core/agent_factory_v2.py`'s new `SimpleChainExecutor` - no ReAct format
  requirement at all. Three-phase flow: (1) ask the LLM to return intent/tool/tool_input as
  loosely-structured text, (2) execute that tool directly, (3) ask the LLM to summarize the
  tool's result into a professional response. `app/core/brain.py` was changed to set
  `self.use_react = False if "whiterabbit" in model_name.lower() else True` at init, and to
  detect `"Invalid Format"`/`"Missing 'Action:'"` in a caught error and fall through to
  `self._ask_simple_chain(query, callbacks)`, additionally flipping `self.use_react = False` so
  subsequent calls in the same session skip straight to SimpleChain. Also created (per this
  writeup) `app/core/brain_v2.py`, described as "reference only... kept for reference, not
  actively used" - both `brain_v2.py` and `agent_factory_v2.py` were deleted well before this
  consolidation (confirmed absent repo-wide as of 2026-07-10).

**Same day - `JSON_PARSING_FIX.md`**: Documents `agent_factory_v2.py`'s parsing logic in more
detail - a three-method fallback chain for interpreting the LLM's SimpleChain-phase response:
(1) a key-value regex parser (`tool: X`, `intent: Y`, ...), (2) a JSON-object regex extractor,
(3) a keyword-based "smart default tool" heuristic (if the query contains `http`/a domain-like
token, default to `Check_Reachability`; otherwise default to `Recon_Suite`) as a last resort
that "never returns error to user."

**Same day - `PARSING_ERROR_FIX.md`** and **`IMPLEMENTATION_GUIDE_parsing_error_fix.md`**: Two
overlapping summaries of the same brain.py/agent_factory_v2.py/GUI changes above, framed as a
"complete solution" and an "implementation guide" respectively - both claim a 4-test suite
(`test_parsing_fix.py`, later renamed `verify_parsing_fix.py`, moved to `tests/manual/` in this
same 2026-07-10 reorganization) passed 4/4.

**Same day - `QUICK_START_FIX.txt`**: A one-page TL;DR of the same fix for quick reference.

**Same day - `TESTING_JSON_FIX.md`**: A manual test plan/checklist (specific target URLs to try,
expected console log lines, a before/after example transcript, a "known limitations" list noting
WhiteRabbitNeo's CPU inference speed and WSL/network dependencies for some tools).

## Claimed outcome (as of 2026-06-25, unverified against later findings)

- "0% success rate (format errors every time)" → "95%+ success rate"
- 4/4 tests passing in `test_parsing_fix.py`
- Users see markdown-formatted reports instead of parser error text

## What we now know (specs/018, 2026-07-08)

A real production run against `https://www.cultbeauty.co.uk/` timed out after 900 seconds with
zero results. Investigation of the live run log found WhiteRabbitNeo repeating the exact same
malformed, non-ReAct output on every one of ~26 retries over 15 minutes - the same class of
failure this 2026-06-25 incident was supposed to have already fixed via automatic fallback.
Code inspection at that point found `_get_react_agent()` and `_get_simple_chain()` (by then
already refactored/renamed from this incident's original `_ask_simple_chain`/`use_react` shape,
but carrying the same intent forward) both constructed the identical `AgentExecutor` object -
the "fallback" was structurally incapable of ever behaving differently, regardless of which
branch executed. specs/018 replaced this entire dual-path with `app/core/agent/react_workflow.py`'s
structured-output-first graph (Ollama schema-constrained decoding, not regex/keyword parsing of
free text) - see `specs/018-structured-agent-reliability/spec.md` for that fix, and
`docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`'s ADR-17/18 for how it fits into the architecture's
history.

**Lesson**: a fallback path that is never truly exercised under adversarial/live conditions
(here: never tested against a model that fails in exactly the way it's meant to catch) can look
complete - passing its own test suite, backed by confident documentation - while not actually
providing the guarantee it claims. The fix that actually worked (`018`) was found via live
reproduction of the failure with a mock LLM replaying the exact malformed behavior, not via a
new round of documentation.

## Files referenced in the original incident (current status, 2026-07-10)

| Path (as referenced in 2026-06-25 docs) | Status |
|---|---|
| `app/core/brain.py` | Still exists, substantially rewritten since (see `018`/`019`) |
| `app/core/agent_factory_v2.py` | Deleted |
| `app/core/brain_v2.py` | Deleted |
| `app/GUI/gui_app.py` | Deleted 2026-07-06 (unsafe import-time `brain.ask()` execution) |
| `app/GUI/gui_root.py` | Deleted 2026-07-06 (same reason, 98% duplicate of `gui_app.py`) |
| `app/GUI/gui_main.py` | Converted to a re-export shim 2026-07-10 (this same reorganization pass) |
| `test_parsing_fix.py` | Renamed `verify_parsing_fix.py`, moved to `tests/manual/` |
