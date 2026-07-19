# Research: Multi-Agent Role Separation

**Feature**: `020-multi-agent-role-separation`

## Primary source

`docs/history/2603.27127v1.pdf`, Section 3.3 (Overall System Architecture) and 3.6 (Specialized
Toolsets). Also Section 2.1/2.3's diagnosis of *why* naive multi-agent designs fail (context
fragmentation via unstructured message-passing) — the paper is explicit that role separation
alone is not the contribution; SRMM + Dual-Phase Reflection riding on top of it is (see the
paper's own framing: "In contrast to prior systems that primarily introduce reflection as a
local heuristic... Red-MIRROR operationalizes reflection as a system-level control mechanism
tightly coupled with persistent shared memory and planning").

## Current Argus implementation reviewed

- `app/core/agent/react_workflow.py::_build_custom_workflow` — one graph, one `agent` node
  calling one LLM per iteration; `app/core/agent/brain_tools.py::build_argus_tools()` returns a
  single flat list of 17 tools, no per-role partition exists anywhere in the tool-wiring code.
- `app/core/agent/react_prompts.py` — one system prompt with a static, textual
  "RECOMMENDED PHASE PROGRESSION" section guiding the model through recon-then-exploit phases —
  this is Argus's only current analog to Planner-driven phase transition, and it is a
  suggestion baked into the prompt, not a decision made by dedicated logic.
- Git history context (from this session's prior work): `010-langgraph-agent`'s original
  multi-node tactical graph (`app/core/agent/graph.py`, `nodes/`) was **superseded as the
  production driver by `017`** specifically because a single ReAct loop proved more reliable in
  practice against this project's actual model (`WhiteRabbitNeo-V3-7B` via Ollama) — this is
  documented in `docs/ARCHITECTURE_AUDIT_REPORT.md`'s traceability matrix row for `010`. This is
  directly relevant prior art: Argus already tried a more distributed design and moved away from
  it for reliability reasons before this gap analysis existed. Any multi-agent proposal must
  reckon with that history, not ignore it.

## Why this is scoped as "flagged high-risk," not just another phase

Every other phase in this gap analysis (`019`, `021`-`026`) is additive: new tool, new memory
behavior, new offline pipeline, new benchmark harness, none of which risk the stability of the
already-working single-loop production path. This phase is the one exception — it changes
*how the core loop is driven*, in the same code area `017` and `018` both had to fix live
production failures in. The research conclusion is: propose it, cost it honestly (this
document + spec.md's NFR-001), and make ship-`019`-first-and-measure the explicit
recommendation rather than defaulting to "more architecture = more paper-fidelity = better."

## Key adaptation decisions (and why)

1. **Shared graph, role-scoped prompts/tools — not 4 separate processes** (FR-001). Running
   four independent LLM contexts against one locally-hosted 7B GGUF model on consumer hardware
   (per `docs/ARCHITECTURE_AUDIT_REPORT.md`'s documented hardware assumptions, echoing the
   paper's own GTX1650-class target) would either serialize behind one model anyway (no
   parallelism benefit) or require loading multiple model instances (memory cost this project's
   target hardware profile can't obviously absorb). One graph with role-scoped configuration
   nodes gets the *reasoning* separation the paper argues for without the *infrastructure* cost
   Red-MIRROR's own setup (Kaggle T4s / DeepSeek API) didn't have to worry about.
2. **Hard dependency on `019`** (FR-005) — building per-role memory partitioning twice (once
   ad hoc for this phase, once properly in `019`) would violate Constitution IX (Single Source
   of Truth), the exact anti-pattern this session's tool-list consolidation work
   (`brain_tools.py` CHK090) already had to clean up once this session.
