# Feature Specification: Human-in-the-Loop Escalation on Detected Stuck Loops

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `028-human-in-the-loop-escalation`

**Created**: 2026-07-13

**Status**: Proposed - spec kit only, not yet implemented.

**Input**: User asked whether "human-in-the-loop" (a term encountered in unrelated reading)
could help with the "agent repeats itself without reaching useful progress" failure class, and
requested research into whether it's a better fix than the existing structural duplicate-call
guard, or a complement to it - 2026-07-13.

---

## Why this feature

`specs/019` (CHK085-087) already added a **fully autonomous** structural fix for literal
repetition: `parse_node` blocks a `(tool, input)` pair once it has been called twice, and
response-aware reflection notes redirect the model toward untried tools. This closed the exact
failure `specs/018`'s original incident exposed (WhiteRabbitNeo repeating an identical malformed
action forever) and a follow-up live-discovered oscillation bug (bouncing between two *already-
blocked* tools instead of trying a genuinely new one).

What that fix does **not** cover: a run that keeps trying *different* tools, each individually
legal (no literal repeat), but never converges on a real finding - e.g. alternating recon tools
against a target that's clearly WAF-blocked, without ever surfacing "this looks blocked" to
anyone until `max_iterations` is exhausted and the run ends with an honest-but-unhelpful "no
Final Answer" error. A human operator watching the live feed could very plausibly recognize the
pattern (a WAF challenge page recurring in every Observation, say) long before the iteration
budget runs out - but today the GUI has no mechanism to pause and ask, and the agent has no
mechanism to request it.

Web research (documented in `research.md`) confirms this is a distinct, well-established
capability class - "Human-in-the-Loop" (HITL) escalation - not a replacement for the existing
autonomous guard, but the layer above it: autonomous mechanisms should keep handling everything
they can, and escalate to a human specifically when *structurally* (not self-reported) detected
as stuck. Anthropic's own agent-building guidance frames this exactly as "pause for human
feedback... when encountering blockers," and 2026 industry practice increasingly treats the
escalation checkpoint as a designed system property, not a fallback bolted on after failures.

This is explicitly an **additive, opt-in-by-monitoring** feature: a CLI/headless run (no GUI
watching) must behave exactly as it does today - this spec must never introduce a hang or a
requirement for human input to complete a run. Argus's core autonomy goal (`docs/
ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` §1.1: "Minimize human intervention in reconnaissance and
initial vulnerability discovery") is not being walked back; this is a safety-net upgrade for the
*monitored* case, not a new requirement for the *unmonitored* case.

## Requirements

### Functional Requirements

- **FR-001**: A new, structural (not model-self-reported) "stuck" detector MUST run inside
  `execute_node` (or the equivalent node in `020`'s multi-role graph, if that path is ever
  promoted), evaluated after each tool result. Proposed trigger conditions (either satisfies):
  (a) 3 or more `reflection_notes` in the current run contain an "INCONCLUSIVE"/"blocked"/
  "duplicate" signal with no intervening confirmed finding added to the Blackboard; or
  (b) `iteration_count` has reached 80% of `max_iterations` with zero findings recorded via
  `memory.add_finding()` this run. Exact thresholds are tunable (see `NFR-001`), not hardcoded
  magic numbers buried in the check itself.
- **FR-002**: On trigger, the graph MUST call LangGraph's native `interrupt()` (not a custom
  polling/sleep mechanism - `019`/`018` already replaced a blocking sleep-loop with
  `st.fragment`-based polling once, per `docs/history/2026-06-25_react_parsing_and_simplechain_
  fallback_incident.md`'s lesson; this must not reintroduce that class of problem), passing a
  structured payload: the stuck-pattern reason, the current Blackboard summary, and the last N
  reflection notes.
- **FR-003**: The GUI's Agent tab (`app/GUI/tabs/agent.py`, `AgentController`) MUST render a
  distinct "Needs Input" state (separate from `"running"`/`"reflecting"`/`"completed"`/
  `"failed"` - reuses `_emit_graph_step`'s existing status vocabulary, extended by one value,
  not a parallel status system) showing FR-002's payload and a text field for the operator to
  supply a redirect hint.
- **FR-004**: Submitting a hint MUST resume the graph via LangGraph's `Command(resume=...)`
  (the documented pairing with `interrupt()`), injecting the hint as a new `reflection_notes`
  entry (reusing the exact mechanism `_build_reflection_note()` already populates that field
  with - no new state-shape) before the next `agent_node`/`planner_node` call.
- **FR-005** (the non-negotiable safety property): IF no human responds within a bounded timeout
  (proposed default: 5 minutes, configurable), the run MUST auto-resume on its own - treating the
  timeout itself as an empty hint - rather than hang. This is what makes the feature safe for
  unattended/CLI use: `scripts/run_argus_cli.py`/`scripts/run_agent.py` invocations never have a
  human to respond, so every stuck-detection in those contexts immediately auto-resumes with no
  observable behavior change from today (mirrors the "timeout mechanisms... proceed with the AI's
  recommendation" pattern found in this spec's research).
- **FR-006**: Every interrupt (whether resolved by a human hint or by FR-005's timeout) MUST be
  logged to the run's audit trail (the existing `logs/agent_runs/*.json` state file) - Constitution
  V (Observability & Logging) applies to this new decision point exactly as it does to every other
  step.

### Non-Functional Requirements

- **NFR-001**: FR-001's exact thresholds MUST be configurable via `config.yaml`
  (`hitl_escalation.stuck_reflection_count`, `hitl_escalation.stuck_iteration_fraction`), not
  hardcoded - this is a new heuristic with no live-tuning history yet, unlike `019`'s
  already-validated duplicate-call counts.
- **NFR-002**: This feature MUST be behind a config flag (`enable_hitl_escalation`, default
  `false` initially - same rollout stance `020` took for a genuinely new, unmeasured behavior),
  promoted to default only after live GUI-monitored runs confirm FR-005's timeout path never
  fires unexpectedly during normal (non-CLI) operation and doesn't introduce perceptible latency
  when no interrupt occurs.
- **NFR-003**: `interrupt()`/`Command(resume=...)` requires a LangGraph checkpointer (state
  persistence across the pause) - MUST reuse whatever checkpointing mechanism, if any, `020`'s
  experimental graph or the production single-loop graph already has, or add the minimum
  (`MemorySaver` for a single-process run) rather than a new persistence layer; this needs
  verifying against the actual installed LangGraph version at implementation time (T001 in
  `tasks.md`), not assumed from generic documentation.

## Success Criteria

- **SC-001**: A mock-LLM test reproducing the "different tools, no convergence" pattern (3+
  distinct tools, each individually legal, all INCONCLUSIVE, no Blackboard finding) confirms the
  graph reaches `interrupt()` before exhausting `max_iterations`, not after.
- **SC-002**: A test simulating a human-supplied hint confirms the graph resumes and the hint
  appears in the next prompt's reflection-notes block.
- **SC-003**: A test simulating FR-005's timeout (no hint supplied) confirms the graph auto-
  resumes on its own within the configured window - proving the safety property holds, not just
  the happy path.
- **SC-004**: A full CLI run (`enable_hitl_escalation` at its default) triggers the exact same
  stuck pattern as SC-001 and completes with **zero observable difference** from today's
  behavior (still ends via `max_iterations` if genuinely stuck) - proving this is additive for
  unmonitored runs, not a behavior change.

## Assumptions

- The GUI's existing live-feed polling (`st.fragment(run_every="2s")`) is the delivery mechanism
  for surfacing FR-003's "Needs Input" state - no new polling/websocket infrastructure assumed.
- Only single-operator, single-run escalation is in scope (one human, one pending question at a
  time) - a multi-operator approval-routing system (mentioned in some research sources as an
  "identity-aware orchestration layer") is out of scope for Argus's single-operator deployment
  shape, consistent with `026`'s own scoping-down rationale for ethical safeguards.

## Explicitly out of scope

- Asking for human approval *before* every action (a permission gate, not an escalation safety
  net) - this would directly conflict with Argus's autonomy goal and is not what this spec
  proposes; FR-001's trigger is specifically a detected-stuck condition, not a default check-in.
- Trusting the model's own self-report of being "stuck" as the trigger signal - research
  explicitly warns RLHF-trained models are miscalibrated about their own confidence/correctness;
  FR-001 is deliberately structural (counting real signals: reflection-note patterns, iteration
  fraction, Blackboard finding count), not "ask the model if it thinks it's stuck."
- Multi-operator approval routing / audit-signed sign-off workflows - single-operator only (see
  Assumptions).

## Artifact applicability

- data-model.md: N/A — spec-kit-only, not yet implemented (per specs/checklist.md); no
  persistent schema or data contract exists yet to document.
- quickstart.md: N/A — spec-kit-only, not yet implemented; no runnable user/operator workflow
  exists yet to document.
