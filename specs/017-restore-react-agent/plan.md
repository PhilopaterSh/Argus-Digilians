# Implementation Plan: Restore ArgusBrain as Production Driver

Retrospective documentation (2026-07-18) of the architecture actually implemented, derived from
spec.md's Requirements/Key Entities sections and specs/checklist.md's Phase 017 (CHK064-069) -
no new design, just the existing implementation record reorganized into this file.

## Summary

Reconnect `scripts/run_agent.py` (the entrypoint the canonical GUI already drives) to
`ArgusBrain.ask()` (the already-built, already-tested ReAct loop) instead of the deterministic
`build_tactical_graph()` pipeline it was actually calling. See research.md for why this was a
reconnection rather than new construction.

## Architecture

```text
app/core/agent/
├── brain.py              # ArgusBrain - unchanged, already implemented the ReAct loop
├── brain_tools.py        # NEW: build_argus_tools() - single canonical 12-tool list
├── react_callback.py     # NEW: LiveFeedCallbackHandler - bridges LangChain callbacks to the
│                          #      existing state-file event contract
├── agent_factory.py      # unchanged - build_agent_executor() ArgusBrain already used
└── graph.py               # unchanged, retained per Constitution VII (010's superseded driver)

scripts/
└── run_agent.py           # REWRITTEN: drives ArgusBrain.ask() instead of build_tactical_graph();
                            # _build_final_state() shapes the SecurityReport-typed output for
                            # persistence, timeout-bounding and demo/test fallback preserved

app/GUI/tabs/
└── agent.py                # Final Results section updated to render the real SecurityReport
                             # shape (risk score, findings, next steps, full report) instead of
                             # the old open_ports/vulnerabilities/exploit_success metrics
```

## Delivery sequence (as implemented, CHK064-069)

1. **CHK064** - `build_argus_tools()`: single canonical 12-tool list, replacing hand-copied
   per-caller duplication (Constitution IX).
2. **CHK065** - `LiveFeedCallbackHandler`: streams Thought/Action/Observation/error/finish events
   into the existing state-file contract, so the GUI needs zero polling changes.
3. **CHK066** - `run_agent.py` rewrite: drives `ArgusBrain.ask()`; preserves the existing
   timeout-bounding thread wrapper and demo/test fallback unchanged; `_build_final_state()` never
   fabricates a structured report when the LLM's output didn't parse (`parse_warning` instead,
   Constitution VIII).
4. **CHK067** - `app/GUI/tabs/agent.py` Final Results rendering updated to the real
   `SecurityReport` shape.
5. **CHK068** - `app/core/agent/graph.py` and its nodes explicitly retained unmodified
   (Constitution VII - superseded artifacts are not silently deleted); its own tests stay green.
6. **CHK069** - `specs/010-langgraph-agent/spec.md`'s status line updated to record the
   supersession; `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability matrix updated (010's row, plus
   a new 017 row).

## Constitution Check

- **VII (Traceable Reconciliation)**: this feature IS a reconciliation event by definition - see
  spec.md's "Why this feature" section for the mismatch it resolves. `010`'s graph is retained,
  not deleted.
- **VIII (Truthful Runtime)**: FR-005 - a non-parsing LLM output must produce an explicit
  `parse_warning`, never a fabricated structured report.
- **IX (No Duplication)**: FR-002 - one canonical tool-list location
  (`brain_tools.py::build_argus_tools()`), not copy-pasted per GUI file.
