# Research: Human-in-the-Loop Escalation on Detected Stuck Loops

**Feature**: `027-human-in-the-loop-escalation`

## Question researched

User encountered the term "human-in-the-loop" (HITL) elsewhere and asked whether it would be a
better fix for the "agent repeats itself without reaching useful progress" problem than the
existing structural duplicate-call guard (`specs/019` CHK085-087), or a complement to it -
2026-07-13, per Constitution Principle XI this is recorded here rather than left in chat.

## Current Argus implementation reviewed

- `app/core/agent/react_workflow.py`'s `parse_node`: blocks a `(tool, input)` pair once called
  twice (`.count(call_key) >= 2`), appends a response-aware reflection note listing untried
  tools by name. Fully autonomous - zero human involvement, confirmed by reading the code
  directly (no `interrupt`/callback-to-human hook anywhere in this function).
- `app/GUI/tabs/agent.py`/`AgentController`: live-feed status vocabulary is currently
  `"running"`/`"reflecting"`/`"completed"`/`"failed"` (per `_emit_graph_step`'s existing mapping,
  confirmed by reading `brain.py`) - no "paused, needs input" state exists today.
- `docs/history/2026-06-25_react_parsing_and_simplechain_fallback_incident.md` and
  `specs/018`'s CHK088-089: this project has direct, hard-won experience with GUI polling
  mechanisms - a blocking `for _ in range(60): time.sleep(1)` loop was previously found and
  replaced with non-blocking `st.fragment(run_every="2s")` polling specifically because it froze
  the whole Streamlit session. Any new pause/resume mechanism must not reintroduce that class of
  bug - this is why `spec.md`'s FR-002 explicitly requires LangGraph's own `interrupt()`
  primitive rather than a custom polling/sleep loop.

## Web research: LangGraph's native HITL support

LangGraph ships a first-class `interrupt()` function specifically for this pattern - it halts
graph execution at a chosen point, persists state via a checkpointer, and resumes later from
that exact point via `Command(resume=...)` once a human (or, per this spec's FR-005, a timeout)
supplies input. This is not something to build from scratch on top of LangGraph; it's the
documented, intended mechanism for exactly this use case - directly lowering this feature's
integration cost since Argus already runs on LangGraph (`_build_custom_workflow`/
`_build_multi_role_workflow`).
(Sources: [Human-in-the-loop - Docs by LangChain](https://docs.langchain.com/oss/python/langchain/human-in-the-loop),
[Making it easier to build human-in-the-loop agents with interrupt (LangChain blog)](https://www.langchain.com/blog/making-it-easier-to-build-human-in-the-loop-agents-with-interrupt),
[Interrupts and Commands in LangGraph (DEV Community)](https://dev.to/jamesbmour/interrupts-and-commands-in-langgraph-building-human-in-the-loop-workflows-4ngl).)

## Web research: escalation-after-N-failures is an established pattern, not a novel idea

"Limiting how many times an agent can revise its output before requiring escalation" is
described as a common, recognized pattern specifically to prevent the failure mode this spec
targets - an agent repeatedly failing/retrying without human intervention. Separately, timeout-
based auto-resolution ("if a human doesn't respond within X minutes, the workflow proceeds with
the AI's recommendation... or escalates further") is the documented basis for this spec's FR-005
safety property - not an ad hoc invention, a recognized production pattern for making HITL safe
for unattended operation.
(Sources: [How to Build Human in the Loop AI Agent with LangGraph (Elite AI Advantage)](https://eliteaiadvantage.com/blog/build-human-loop-ai-agent-langgraph),
[LangGraph Human-in-the-Loop: Pausing, Reviewing, and Rewinding Your Agent (Towards AI)](https://pub.towardsai.net/langgraph-human-in-the-loop-pausing-reviewing-and-rewinding-your-agent-4028bd05b049).)

## Web research: is HITL appropriate for an *autonomous pentesting* agent specifically?

This is the question that most directly shaped this spec's scoping. Findings:

1. **Division of labor, not a contradiction of autonomy**: 2026 industry framing is
   "autonomous agents own breadth and continuous coverage; human experts own validation,
   judgment, and regulatory sign-off" - i.e. HITL for pentesting agents is about *when to
   escalate*, not a return to manual operation. Autonomous pentesting is explicitly described as
   "configurable for human-in-the-loop oversight at any stage," not an either/or choice.
2. **The checkpoint should be a designed property, not a bolted-on fallback**: "Escalation
   design is the enforcement layer that stops [an] action before it executes... a designed
   property of the system, not a fallback." This directly informed `spec.md`'s stance that
   FR-001's trigger conditions must be specified up front (not "add HITL vaguely and figure out
   thresholds later").
3. **Anthropic's own agent-building guidance** recommends agents "can pause for human feedback
   at checkpoints or when encountering blockers" - the "blocker" framing matches this spec's
   target failure mode (a stuck, non-converging run) almost exactly.
4. **Important caution guiding FR-001's design**: models trained with RLHF are "systematically
   miscalibrated - their highest verbal confidence often correlates with incorrect outputs." This
   is the direct reason `spec.md`'s "Explicitly out of scope" section rules out asking the model
   itself whether it feels stuck - the trigger must be a structural count (reflection-note
   pattern, iteration fraction, Blackboard finding count), never the model's self-report.
   (Sources: [Human-in-the-Loop Escalation Design for AI Agents 2026 (Digital Applied)](https://www.digitalapplied.com/blog/human-in-the-loop-escalation-design-ai-agents-2026),
   [What Is Autonomous Pentesting? (Picus Security)](https://www.picussecurity.com/resource/blog/what-is-autonomous-pentesting),
   [Human-in-the-Loop: A 2026 Guide to AI Oversight (Strata)](https://www.strata.io/blog/agentic-identity/practicing-the-human-in-the-loop/),
   [Autonomous AI Agents for Penetration Testing: A Complete Guide (Astra)](https://www.getastra.com/blog/penetration-testing/autonomous-ai-agents-for-penetration-testing/).)

## Conclusion: complement, not a replacement

`019`'s existing structural duplicate-call guard stays exactly as-is - it correctly and fully
autonomously handles literal repetition, the failure mode it was built for. HITL escalation
(this spec) targets a *different, currently uncovered* failure mode: non-repetitive but
non-converging behavior across several distinct tools. The two are complementary layers, not
competing solutions to the same problem - this spec does not propose removing or weakening
anything `019` built.

## Why this warrants its own spec, not a quick patch to `019`

Unlike `019`'s addition (a counter and a text-formatting change inside an existing node),
`interrupt()`/`Command(resume=...)` requires: a LangGraph checkpointer (state persistence across
a real pause, not just a Python-object lifetime - `NFR-003` flags this as needing verification
against the actual installed LangGraph version, not assumed), a new GUI status state and input
widget (`app/GUI/tabs/agent.py`), and a non-negotiable timeout/auto-resume safety property
(`FR-005`) that must be proven, not just implemented, before this could ever be promoted beyond
`enable_hitl_escalation: false`. That is a materially larger and more infrastructure-sensitive
change than a duplicate-call counter, warranting its own spec/plan/tasks review rather than being
folded into `019`'s already-closed scope.

## Follow-up question researched (2026-07-13): is RLHF a better/complementary fix than either of the above?

User separately asked (after this spec's HITL research was already recorded above) whether
RLHF - a term encountered elsewhere - would be a more effective technique for the same "agent
repeats itself without reaching useful progress" failure class than what Argus currently uses,
and asked for a web search before trusting the idea (per this project's standing rule to measure
rather than assume a plausible-sounding technique is actually the right fit).

**What "RLHF fixes this" would actually require, checked against Argus's real capabilities**:
`requirements.txt` has no `torch`/`trl`/`peft` (confirmed in `024`'s research), and the only
training capability even proposed anywhere in this project (`specs/024`) is a **supervised**
LoRA fine-tune (instruction/response pairs, no reward model, no policy-gradient loop). RLHF, and
the newer agentic-RL techniques purpose-built for this exact symptom (OTC-PO's tool-productivity
reward, β-GRPO's confidence thresholds, HiPRAG's hierarchical process rewards, step-level rubric
rewards reducing measured looping rate to 26.5%), all require a full reinforcement-learning loop
- a reward signal plus GRPO/PPO-style policy optimization - which is a materially larger,
different-in-kind infrastructure investment than `024`'s already-scoped SFT pipeline, let alone
`019`'s shipped counter or this spec's proposed `interrupt()` reuse.
(Sources: [Step-wise Rubric Rewards for LLM Reasoning](https://arxiv.org/pdf/2605.17291),
[Efficient Agentic Reinforcement Learning with On-Policy Intrinsic Knowledge Boundary Enhancement](https://arxiv.org/pdf/2605.26952),
[Learning When Not to Act: Mitigating Tool Abuse in Agentic Reinforcement Learning](https://arxiv.org/pdf/2606.02132),
[The Landscape of Agentic Reinforcement Learning for LLMs: A Survey](https://arxiv.org/pdf/2509.02547).)

**A caution that cuts against RLHF specifically, not just "RL is expensive"**: models trained
with RLHF are documented as **action-biased** - rewarded for producing output rather than for
correctly recognizing that no further action is needed. Applied to an agentic loop, that is the
same failure direction this spec targets (excess, non-converging action-taking), not its cure -
classic RLHF alignment training is not obviously pointed the right way for this specific problem
without the specialized anti-redundancy reward shaping the papers above had to add on top of it.
(Source: [Step-wise Rubric Rewards for LLM Reasoning](https://arxiv.org/pdf/2605.17291).)

**Practical industry guidance found**: try the lightest fix first (prompt/tool-level changes),
escalate to supervised fine-tuning only for a persistent format/domain behavior, and treat RL
training as the last, heaviest tier - not the first thing to reach for. `019`'s structural guard
is already the lightest tier and is shipped; this spec's HITL escalation is the layer above it
for the case `019` doesn't cover. RL/RLHF-based fixes act at the training layer (reshaping the
model's policy) rather than the runtime-orchestration layer these two mechanisms operate at.

**Conclusion**: RLHF is not a better fix than what Argus already has or than this spec's proposed
HITL escalation - it targets the same symptom from a different, heavier layer (retraining the
model's policy) that Argus has no infrastructure for today, and its "action bias" property may
work against rather than for this specific problem unless purpose-built anti-redundancy reward
terms (as in the OTC-PO/HiPRAG/SRaR work above) are added, which is a substantially larger,
separate research investment than anything proposed in `019`, `024`, or this spec. It is not
being adopted as a fix here. If Argus ever builds real RL training infrastructure beyond `024`'s
SFT-only LoRA pipeline, revisit this as a `024` follow-up, not a patch to `019`/`027`.
