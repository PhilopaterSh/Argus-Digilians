# Feature Specification: Partitioned Bounded Memory + Dual-Phase Reflection

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `019-shared-memory-reflection-upgrade`

**Created**: 2026-07-10

**Status**: Proposed — spec kit only, not yet implemented. Awaiting prioritization.

**Input**: Gap analysis of `docs/history/2603.27127v1.pdf` ("Red-MIRROR: Agentic LLM-based
Autonomous Penetration Testing with Reflective Verification and Knowledge-augmented
Interaction") against Argus's current codebase, requested by the user 2026-07-10. This is the
highest-value, lowest-risk phase identified in that analysis: it upgrades mechanisms Argus
already has (`ArgusMemory`, `tool_call_history` duplicate-blocking) rather than requiring a new
architecture, and the paper's own ablation study (Section 4.5.3, Table 8) is the strongest
evidence in the source material that this pairing matters.

---

## Why this feature

Red-MIRROR's ablation study isolates two components — the Shared Recurrent Memory Mechanism
(SRMM) and Dual-Phase Reflection — and shows they are **synergistic, not additive**: under
Type-5 filtering (replacement-based/dynamic sanitization, the hardest defensive setting tested),
the fully-ablated baseline and *both* single-component variants solve **zero** challenges, while
the combined configuration solves 100% with an average of 14.5 agent steps (Table 8). The
paper's own motivating example (Section 3.1) is a concrete illustration: an agent probing a
filtered reflected-XSS endpoint needs to accumulate transformation evidence across ~20-30
attempts (which characters get stripped, which survive) to infer the filter's rule — a
conversational-history-only agent instead "revisit[s] previously invalidated tag-based
strategies" because early evidence gets diluted.

Argus's current state has weak, uncoupled analogs of both halves:
- **Memory**: `ArgusMemory` (`app/core/memory/memory_service.py`) is a single shared SQLite
  table, not partitioned by writer/role; `get_blackboard_summary(max_chars=3000)` bounds prompt
  size but has no per-source recency guarantee (a flood of one finding type can crowd out an
  older, still-relevant one) and no formal read/write access separation.
- **Reflection**: `app/core/agent/react_workflow.py`'s `tool_call_history` blocks a literal
  third repeat of an identical tool call, forcing the model to "try something different" — but
  there is no structured mechanism that captures *why* the last attempt failed and feeds that
  reasoning back in, and no equivalent of Inter-reflection's majority-vote success check at all
  (a single LLM pass currently decides whether an exploitation step "succeeded").

This phase proposes closing that gap using the paper's own formal model (Section 3.4-3.5) as the
design target, adapted to Argus's actual single-loop architecture (see `020-multi-agent-role-
separation` for the separate, higher-risk question of whether to also split Argus into distinct
agents — this phase does **not** require that split).

## Requirements

### Functional Requirements — Memory (SRMM-adapted)

- **FR-001**: `ArgusMemory` MUST expose a write path that tags every finding with a `source`
  (already present as the `tool_name`/`agent` column per `add_finding()`'s existing signature)
  and an `append_seq` (monotonic per-source counter), so no write ever overwrites an older
  one — matching SRMM's Property 1 (monotonic growth/traceability).
- **FR-002**: `get_blackboard_summary()` MUST support a `k`-per-source bounded read — the last
  `k` findings per distinct `source`, not just the last N rows overall — so one noisy tool
  cannot crowd out another's findings (SRMM Property 3, bounded context window:
  `|Filter_k| <= k * |sources|`). Default `k` MUST remain small enough that
  `max_chars=3000`'s existing cap is rarely hit in practice, not just capped after the fact.
- **FR-003**: The existing `max_chars` truncation MUST become a last-resort safety net, not the
  primary bounding mechanism — `k`-per-source filtering (FR-002) is what keeps output bounded
  under normal operation; `max_chars` only protects against pathological cases (e.g., one
  finding's text being unexpectedly huge).
- **FR-004**: A new `summarize_for_planning(k)` MUST format the `k`-per-source result with an
  explicit `[source] ...` prefix per entry (mirroring Algorithm 2's `Format` step), making the
  provenance of each fact visible to the LLM instead of an undifferentiated blob.

### Functional Requirements — Reflection (Dual-Phase-adapted)

- **FR-005**: The existing duplicate-call block in `react_workflow.py` MUST be upgraded from
  "block on 3rd identical call" to a structured **Intra-reflection** step: when a tool call
  fails or repeats, the graph MUST inject a explicit reflection prompt containing the specific
  prior action, the prior response/error, and an instruction to change one concrete dimension
  (encoding, HTTP method, injection point, etc.) — not just "try something different." This is
  the direct analog of Algorithm 3's `ReflectAndUpdate(state, o, resp, T)` step.
- **FR-006**: A new **Inter-reflection** check MUST run before the graph accepts a tool result
  as a confirmed finding for the final report: invoke the LLM 3 times with a fixed low-variance
  prompt asking "did this step succeed at its stated goal, yes or no" and take the majority
  (>=2/3) — mirroring Algorithm 4 Step 1 and Eq. 10. This MUST be scoped to exploitation-style
  tool calls (e.g., `Advanced_Evasion_Probe`, `Secret_Scanner`) where success is ambiguous from
  raw output; it MUST NOT wrap purely informational calls (`Query_Memory`, `Check_Reachability`)
  where a single deterministic check already suffices, to avoid tripling LLM calls with no
  benefit.
- **FR-007**: The graph MUST check the final-answer/tool-output text for a `flag{...}`-shaped
  string (or a configurable success-pattern) as an early-termination signal, independent of
  `max_iterations` — mirroring Algorithm 4 Step 2. This is a straightforward addition since
  `react_workflow.py` already inspects message text for `Final Answer:`.
- **FR-008**: All reflection-related LLM calls (FR-005, FR-006) MUST count toward
  `max_iterations`/token budgets and MUST be visible in the live-feed stream
  (`on_graph_event`) as a distinct step type (e.g., `"reflecting"`), so the added LLM calls are
  observable, not hidden overhead. Constitution VIII (Truthful Runtime) applies: a reflection
  step's outcome must be reported honestly, including when majority voting is inconclusive.

### Non-Functional Requirements

- **NFR-001**: This phase MUST NOT change `ArgusBrain.ask()`'s external contract — same
  constraint `018` held itself to. `scripts/run_agent.py`, `brain_tools.py`, and
  `app/GUI/tabs/agent.py` require zero changes.
- **NFR-002**: FR-006's 3x self-consistency check triples LLM cost/latency for the tool calls it
  wraps. Given Argus's local GGUF inference has no per-token API cost but real wall-clock cost,
  this MUST be measured (not assumed) against `max_iterations=15`'s existing time budget before
  being enabled by default — a config flag (e.g., `enable_inter_reflection: bool`, default
  `true`, in `config.yaml`) MUST allow disabling it if it makes runs time out in practice.
  **Measured 2026-07-10 (tasks.md T013), against the real production model**: the "triples
  cost" framing above turned out to be the wrong intuition. 3 interleaved, warm-up-controlled
  rounds comparing one normal ReAct action-generation call vs. one full `_inter_reflect()` call
  gave averages of **10.96s** and **0.82s** respectively — the vote is ~8% of a normal call's
  cost, not ~300%, because its prompt constrains the model to a single word ("yes"/"no") and
  decode time is output-token-bound, not call-count-bound. The `enable_inter_reflection` escape
  hatch (FR-006/config flag) is kept regardless, since this measurement isolates the vote's own
  cost and doesn't cover every possible target/model combination — but the default is confirmed
  safe by real measurement, not left as an open assumption.
- **NFR-003**: Fully unit-testable without live Ollama/WSL, matching this repo's established
  fake/mock-LLM convention (`tests/test_registry/test_brain_ask.py`,
  `tests/test_langgraph_workflow.py`).

## Success Criteria

- **SC-001**: A test reproducing the paper's motivating XSS-filter scenario (a mock tool that
  returns a different "stripped" pattern on each call) shows the agent's Nth attempt correctly
  avoiding a previously-invalidated pattern class, provable by asserting the reflection prompt
  fed into the Nth `GenerateAction` call contains a summary of the N-1 prior failures — not
  just that the run eventually terminates.
- **SC-002**: A test with a mock LLM that answers "yes" twice and "no" once to the 3x
  self-consistency check confirms the majority-vote result (`True`) is what the graph acts on,
  and a 1-yes/2-no case confirms `False` is used — both paths exercised, not just the trivial
  unanimous case.
- **SC-003**: `get_blackboard_summary(k=3)` with 5 findings each from 3 different sources
  returns exactly the last 3 per source (9 total formatted entries), not the last 9 overall —
  proving per-source bounding, not global truncation, is what's under test.
- **SC-004**: All existing `tests/test_memory.py`, `tests/test_registry/`,
  `tests/test_langgraph_workflow.py` suites stay green.

## Assumptions

- Argus stays single-loop (one `ArgusBrain`, one LLM call site per iteration) for this phase.
  Formalizing SRMM's "planner cannot write" unidirectional guarantee (Property 2) in a
  single-agent system means: tool-execution results write to memory; only the step that
  synthesizes the next action reads the aggregated summary. There is no separate planner
  process to enforce this against, so it is a coding convention (which functions call
  `add_finding` vs. `summarize_for_planning`) rather than an architectural firewall — a real,
  if weaker, guarantee than the paper's, and one this spec is explicit about not overclaiming.
- This phase's design is intentionally decoupled from `020-multi-agent-role-separation`. If 020
  is later approved, its Planner/Collector/Exploiter roles become the natural writer/reader
  partition SRMM was originally designed for, and FR-001's `source` tagging becomes a straight
  per-agent partition instead of a per-tool one — no rework of the memory schema needed.

## Explicitly out of scope

- Splitting `ArgusBrain` into multiple agents — see `020-multi-agent-role-separation`.
- DAG-based penetration-path planning with branch pruning — that is part of the Planner Agent's
  role in the paper (Section 3.3.2) and depends on 020 existing first.
- Cryptographic/formal proofs of SRMM's five properties — Argus's adaptation is a best-effort
  engineering analog, not a verified implementation of the paper's formalism.
