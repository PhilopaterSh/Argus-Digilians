# Research: Restore ArgusBrain as Production Driver

Retrospective documentation (2026-07-18) of research already recorded in spec.md's "Why this
feature (reconciliation rationale)" section, reorganized into this file - no new investigation,
just the existing record moved to its expected location.

## Investigation

Direct code inspection (2026-07-08) found a mismatch between the project's original design intent
and what was actually running in production:

- `app/core/prompts.py::ARGUS_AGENT_TEMPLATE` defines a classic ReAct
  (Thought/Action/Observation) prompt with 9 operational phases and a structured JSON final
  answer format - this already existed, fully built.
- `app/core/agent/brain.py::ArgusBrain` already used this prompt via
  `app/core/agent/agent_factory.py::build_agent_executor()`, constructing a real LangChain
  `create_react_agent` + `AgentExecutor` with free tool choice (not a fixed sequence).
- `ArgusBrain(...)` was instantiated **only** by the already-deprecated GUI shims
  (`app/GUI/{app,argus_gui,gui_main}.py`) and the Tkinter fallback (`desktop_gui.py`) - never by
  the canonical `app/GUI/dashboard.py`, which instead drove `scripts/run_agent.py` ->
  `app/core/agent/graph.py::build_tactical_graph()` (a deterministic recon -> scanner -> exploit
  -> reflective pipeline with only one narrow single-token LLM call).

## Conclusion

The user's own description of the intended design ("the AI follows instructions and a predefined
path in `app/core/prompts.py`, runs the tool it's directed to, sees the result, and decides the
best next path based on it") matched `ArgusBrain`'s ReAct loop exactly, not the deterministic
graph the canonical GUI was actually driving. This is the situation Constitution VII (Traceable
Reconciliation) exists for: production ran a different design than the one the project's own
prompt/brain infrastructure was built for and still fully supported. The fix is reconnection, not
new construction - see plan.md.
