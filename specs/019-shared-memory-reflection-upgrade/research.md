# Research: Partitioned Bounded Memory + Dual-Phase Reflection

**Feature**: `019-shared-memory-reflection-upgrade`

## Primary source

Tran Vy Khang et al., "Red-MIRROR: Agentic LLM-based Autonomous Penetration Testing with
Reflective Verification and Knowledge-augmented Interaction," arXiv:2603.27127v1, 28 Mar 2026
(`docs/history/2603.27127v1.pdf`). Sections used directly:

- **3.4 (SRMM)**: formal write/read operators (Eq. 2-4), the five formal properties, Algorithm 1
  (`WriteObservation`) and Algorithm 2 (`GetAggregatedContext`).
- **3.5 (Dual-phase Reflection)**: Algorithm 3 (`IntraReflection`) and Algorithm 4
  (`UpdatePlan`), especially Step 1's 3x self-consistency majority vote (Eq. 10) and Step 2's
  flag-prefix early termination.
- **3.1 (Motivating example)**: the filtered-XSS scenario used as this spec's SC-001 test target.
- **4.5.3 (RQ3 ablation) + Table 8**: the quantitative evidence that SRMM and Dual-Phase
  Reflection are synergistic (not additive), strongest under adaptive/replacement-based
  filtering (Type 5: 0% solved without both components combined, 100% with).

## Current Argus implementation reviewed

- `app/core/memory/memory_service.py::ArgusMemory` — `add_finding(target, source, category,
  title, detail)` already tags a `source` per write (confirmed by reading the method signature
  directly, not assumed); `get_blackboard_summary(max_chars=3000)` bounds by total character
  count via truncation, added in `018`'s addendum (CHK-tracked) after an unbounded-context GPU
  crash. It orders by recency/priority but does not group or bound per-source.
- `app/core/agent/react_workflow.py` — `tool_call_history` (a list on `ArgusAgentState`) records
  every `(tool, input)` pair; the third identical repeat is blocked with a generic "try
  something different" instruction appended to the next prompt. No structured capture of *why*
  a call failed (HTTP status, error string) is fed back — the model sees only that its own
  prior action text is now disallowed.
- `app/core/agent/react_callback.py::LiveFeedCallbackHandler` — has `on_graph_event(status,
  detail)` (added in `018`) that can carry a new `"reflecting"` status without any new plumbing.
- `max_iterations=15` (set in `018`) already bounds the whole loop; this phase's FR-006 adds
  LLM calls inside that same bound rather than a separate budget, per NFR-002.

## Why this phase is prioritized first among the paper's gaps

Of the 8 proposed phases from this gap analysis, this is the only one that upgrades **existing**
Argus mechanisms rather than adding a new subsystem (new tool, new agent role, new training
pipeline, new benchmark harness). It carries the paper's own strongest empirical signal (the
Type-5-filtering 0%-vs-100% result) and requires no new runtime dependency (no Playwright
binary, no NVD API key, no GPU training run) — it is pure logic/prompt-engineering work inside
files Argus already owns and tests without live infrastructure.

## Key adaptation decisions (and why)

1. **No separate Planner process** — Argus is single-loop by design (`018`'s explicit choice to
   keep `ArgusBrain.ask()`'s contract stable). SRMM's "planner cannot write" guarantee (Property
   2) is reframed as a *coding convention* (only the action-generation step reads the
   aggregated summary; only tool-execution results write) rather than a process-boundary
   enforcement. This is weaker than the paper's guarantee and the spec says so explicitly
   (Constitution VIII — no overclaiming what was actually built).
2. **Per-source, not per-agent, partitioning** — since there is one agent, "per execution agent"
   (the paper's partition key) is reinterpreted as "per tool/source" (`Check_Reachability` vs.
   `Advanced_Evasion_Probe` vs. `Secret_Scanner`, etc.), which is the finest-grained partition
   Argus's current write call sites naturally support without new plumbing.
3. **Majority voting scoped, not blanket** — applying Algorithm 4 Step 1 to every single tool
   call (including deterministic ones like `Check_Reachability`, whose success is a plain
   boolean from the transport layer) would triple LLM calls for zero benefit. FR-006 scopes it
   to tools whose result text requires judgment to interpret as success/failure — the same
   class of tools the paper's own Exploiter Agent (not its Collector Agent) owns.
