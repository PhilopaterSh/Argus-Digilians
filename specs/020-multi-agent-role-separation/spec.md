# Feature Specification: Multi-Agent Role Separation (Planner/Collector/Exploiter/Summarizer)

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `020-multi-agent-role-separation`

**Created**: 2026-07-10

**Status**: Proposed — spec kit only, not yet implemented. **Explicitly flagged high-risk /
optional** — this is the largest architectural bet identified in the Red-MIRROR gap analysis
and should be decided on its own merits, independent of `019` (which delivers most of the
paper's measured benefit without this change).

**Input**: Gap analysis of `docs/history/2603.27127v1.pdf` against Argus's current codebase,
requested by the user 2026-07-10.

---

## Why this feature (and why it is flagged high-risk)

Red-MIRROR's architecture (Section 3.3) splits penetration testing into four role-scoped
agents — Planner (strategy, DAG path planning, inter-agent reflection), Collector (all recon,
consolidated to avoid fragmentation), Exploiter (payload generation/execution, intra-reflection),
Summarizer (knowledge synthesis, final report) — coordinated through SRMM and Dual-Phase
Reflection. Argus today is architecturally a **single agent**: one `ArgusBrain`, one LLM call
site per loop iteration (`app/core/agent/react_workflow.py`'s `_build_custom_workflow`), 17
tools in one flat action space, one system prompt (`react_prompts.py`).

This is a real, load-bearing difference, not a naming mismatch — and the case for closing it is
weaker than for `019`:
- The paper's own ablation (Table 6/7/8) attributes its gains to **SRMM and Dual-Phase
  Reflection specifically**, not to the 4-way role split per se; there is no ablation row in the
  paper isolating "multi-agent split alone, no SRMM, no reflection" to know how much the role
  split itself contributes versus the memory/reflection mechanisms riding on top of it.
- Argus's current single-loop design was a **deliberate, hard-won stability choice**: `017`
  restored a working ReAct loop after prior multi-node graph attempts (`010`, superseded);
  `018` then fixed a live 900s-timeout production failure by making the loop *more* structured
  and predictable, not more distributed. Introducing 3-4 separate LLM-driven decision points
  reintroduces the class of coordination failure `018` was written to eliminate (context
  fragmentation between agents is exactly VulnBot's failure mode the paper itself diagnoses in
  Section 2.1 — and VulnBot is multi-agent already, so multi-agent alone is not sufficient
  without the memory/reflection discipline `019` proposes).
- Real cost: 4 separate LLM decision points instead of 1 means proportionally more local GGUF
  inference wall-clock time on the same consumer-grade hardware profile Argus targets — the
  paper's own Table 1 shows even their large-context, commercial-API `DeepSeek-V3.2` config
  averaging ~$0.20/challenge in the 4-agent config vs ~$0.10 for 2-agent baselines; Argus has no
  API metering but pays the equivalent in latency.

This spec exists so the option is scoped and costed, **not** as a recommendation to build it
immediately. The recommended sequencing is: ship `019` first, measure whether its memory/
reflection upgrade alone closes enough of the gap (per the paper's own finding that SRMM-alone
and Reflection-alone each already recover ~85-86% SCR vs. the 94% full config — a 8-9 point gap,
not the 44-point gap versus the zero-mechanism baseline), and revisit this spec only if that
residual gap is judged worth the added complexity and latency.

## Requirements

### Functional Requirements

- **FR-001**: IF this phase is approved, the system MUST introduce four role-scoped prompt/tool
  configurations sharing the existing `react_workflow.py` graph machinery — NOT four separate
  LangGraph graphs, four separate Ollama model loads, or four separate processes. Each "agent"
  is a `(system_prompt, tool_subset)` pair invoked at a specific point in one still-single
  running graph, to avoid the operational cost of loading `WhiteRabbitNeo-V3-7B` multiple times
  concurrently on the project's documented consumer-GPU target hardware.
- **FR-002**: Tool space MUST be partitioned per FR-001's roles, mirroring Section 3.6's
  `A_recon`/`A_exploit` disjoint split: Collector gets `Recon_Suite`, `Subdomain_Enumeration`,
  `Check_Reachability`, `Crawl_Target`, `Secret_Scanner`, plus any `021`-toolkit recon-side
  additions; Exploiter gets `Run_Nikto`, `Run_FFUF`, `Advanced_Evasion_Probe`,
  `Exploit_Suggester`, `Run_Kali_Command`, plus any `021`-toolkit exploit-side additions;
  Planner and Summarizer get no direct execution tools — only `Query_Memory`/
  `Query_Knowledge_Graph` (read-only), matching SRMM's unidirectional-flow property this time
  as an actual architectural constraint (not just a coding convention as in `019`, since a real
  role boundary exists to enforce it against).
- **FR-003**: The Planner role MUST own the phase transition (`Trecon -> Texploit`) decision,
  replacing `react_prompts.py`'s current static "RECOMMENDED PHASE PROGRESSION" text guidance
  with an explicit routing decision made by a dedicated graph node.
- **FR-004**: The Summarizer role MUST be the only path that produces the final
  `SecurityReport` (reusing `018`'s `_try_structured_final_answer`) — Collector/Exploiter nodes
  return raw findings to shared memory only, never a final answer directly.
- **FR-005**: This phase depends on `019` being implemented first — the Planner's read-only
  access (FR-002) and the Collector/Exploiter's write access are exactly the `source`-partitioned
  memory model `019` builds; without `019`, this phase would need to build that partitioning
  itself, duplicating work.

### Non-Functional Requirements

- **NFR-001**: End-to-end wall-clock time for a representative scan target MUST be measured
  against the current single-loop baseline before this phase is considered successful — a
  regression beyond an agreed threshold (proposed: 2x current p50 run time) is a valid reason to
  roll back to the single-loop design, not a bug to "fix" by cutting corners elsewhere.
  Constitution VIII applies: no fabricated improvement claims if the measured result is worse.
  Exact multiplier subject to team review before this phase starts.
- **NFR-002**: `ArgusBrain.ask()`'s external contract MUST still not change (same constraint as
  `018`/`019`) — the GUI and `run_agent.py` should be unaware of whether one or four role
  configurations ran underneath.

## Success Criteria

- **SC-001**: A benchmark run (ideally via `025-subtask-benchmark-suite`, once it exists) shows
  a measurable SCR/SR improvement over `019`-only on at least one held-out scenario class the
  paper identifies as benefiting most from role separation (stateful IDOR/Auth scenarios,
  Table 3) — without this, the phase should not be considered validated even if it "works."
- **SC-002**: NFR-001's wall-clock threshold is met or the team explicitly accepts the tradeoff.

## Assumptions

- This phase is **not** scheduled. It is documented so its cost/benefit is legible if and when
  the team decides to revisit it, per this spec's own recommendation to ship `019` first and
  measure the residual gap.

## Explicitly out of scope

- Four independently-scaled model deployments (e.g., a smaller/faster model for Collector, a
  larger one for Exploiter) — interesting per the paper's own RQ2 finding that model scale
  matters a lot (Qwen2.5-14B vs DeepSeek-V3.2), but a separate, larger infrastructure question
  than this spec covers.
- Full DAG-based path planning with branch pruning (Section 3.3.2) — a plausible FR-003 follow-
  up once the Planner role exists, not required for the initial split.

## Artifact applicability

- data-model.md: N/A — spec-kit-only, not yet implemented (per specs/checklist.md); no
  persistent schema or data contract exists yet to document.
- quickstart.md: N/A — spec-kit-only, not yet implemented; no runnable user/operator workflow
  exists yet to document.
