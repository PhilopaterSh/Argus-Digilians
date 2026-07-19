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

## Addendum (2026-07-11): evaluating a multi-*model* alternative before starting T001

User proposed a heavier variant of this spec: instead of one shared model with role-scoped
prompts (FR-001 as originally written), run 4 *different* physical GGUF models per role -
Dolphin-Llama3/Mistral (uncensored, general-purpose) as Coordinator/Router, WhiteRabbitNeo-V3-7B
(unchanged) as Tactical Pentester, DeepSeek-Coder-7B/8B as Exploit/Code Analyst, and an
abliterated Llama-3-8B as the Reflective Verification agent - reasoning that specialized models
per role would be both more capable per-role and, via Ollama's model-swapping, not meaningfully
more expensive in memory than one large model. Researched this specific proposal rather than
accepting or rejecting it on priors, per the user's request to find the best-fit approach:

1. **VRAM math does not hold on this project's actual hardware.** Confirmed live via
   `nvidia-smi`: this machine has 16380 MiB (16GB) total VRAM (RTX 2000 Ada), matching the
   `~7.9GB/16GB` figure already recorded for the current single WhiteRabbitNeo Q5_K_M model
   (specs/018 CHK083). Four 7-8B GGUF models at Q4/Q5 quantization (~5-6GB each) would need
   ~20-24GB resident simultaneously - more than a single 33B model at Q4 (~20GB) would need, not
   "close to" one as the proposal assumed, and well over this machine's 16GB ceiling. The only
   way to fit within budget is Ollama swapping models in and out of VRAM per role transition,
   which trades the memory problem for an *unmeasured latency* problem - marketing benchmark
   figures found online (e.g. a claimed 112ms cold-start on an RTX 5090) are not credible for a
   genuine cold load of several GB from disk into VRAM and are not applicable to this project's
   much smaller RTX 2000 Ada anyway; the honest position is that swap latency for this specific
   hardware is currently unmeasured, not "negligible." (Source: Ollama/vLLM local-inference
   benchmark roundups surveyed for this evaluation -
   [Ollama vs vLLM: Performance Benchmark 2026](https://www.sitepoint.com/ollama-vs-vllm-performance-benchmark-2026/),
   [Performance Test: Ollama 0.5.0 vs. vLLM 0.4.0 (DEV Community)](https://dev.to/johalputt/performance-test-ollama-050-vs-vllm-040-local-llm-inference-latency-on-nvidia-rtx-5090-and-1pol) -
   both discuss `OLLAMA_KEEP_ALIVE` as the practical lever for keeping 2 (not 4) models warm
   simultaneously within a 16GB-class budget.)
2. **Abliteration specifically regresses the one capability the Verifier role most needs.**
   A 2026 comparative study on abliteration methods found MMLU/HellaSwag/IFEval move by at most
   ~1 point, but **TruthfulQA drops -7.1** - "removing the refusal direction costs some
   truthfulness" - and separately that attack-success on genuinely harmful requests rises from
   14.5% to 55.5% once over-refusal is suppressed (expected and out of scope here, but confirms
   the mechanism is real, not cosmetic). specs/019's Dual-Phase Reflection and this spec's
   Summarizer/Verifier concept both depend on a model's ability to judge a finding's truth value
   (is this a real vulnerability or a false positive) - the one documented regression from
   abliteration is a direct hit on exactly that competency. Dense architectures (Llama-3-8B
   among them) show smaller overall degradation than MoE models per the same research, so
   general reasoning would likely survive better than in an MoE - but the specific truthfulness
   cost remains and was not accounted for in the original proposal.
   (Source: [Comparative Analysis of LLM Abliteration Methods (arXiv:2512.13655)](https://arxiv.org/pdf/2512.13655),
   also surveyed [Heretic vs Abliterated LLMs: Refusal Rates & Benchmarks (2026)](https://aithinkerlab.com/heretic-ai-abliteration-benchmarks-2026/)
   and [The Cost of Abliteration in Large Language Models](https://kirill.korins.ky/articles/the-cost-of-abliteration-in-large-language-models/).)
3. **The field is independently moving toward this spec's original single-model design, not
   away from it.** A "Persona-Pruner" line of research extracts multiple lightweight agent
   personas as pruned sub-networks from *one* dense model rather than deploying several full
   separate models, "reducing the performance drop by up to 93.8% over existing pruning
   baselines" versus full separate-model deployment. This doesn't validate anything about
   Argus's specific implementation, but it does mean FR-001's original scoping decision (share
   one model, vary the prompt/tool framing per role) matches where independent research is
   heading, rather than being merely a cost-saving compromise.
   (Source: [Single Dense Model Hosts Hundreds of Agent Personas as Lightweight Masks (ai|expert)](https://aiexpert.news/en/article/persona-pruner-lightweight-models-for-multi-agent-role-playing-systems).)
4. **DeepSeek-Coder's case is the most defensible of the three proposed additions**, but doesn't
   need to be uncensored/abliterated specifically - reading leaked config files and drafting a
   `curl`/Python verification snippet is a coding task mainstream (non-abliterated) coding
   models don't typically refuse in the first place, unlike WhiteRabbitNeo's live-exploitation
   role where refusal-avoidance is the actual point. If a genuinely separate model is added
   later (per T009, only after this spec's single-model version is measured and found
   insufficient), a stock DeepSeek-Coder variant is the more defensible first thing to try, not
   an abliterated one.

**Decision**: proceed with FR-001 exactly as originally scoped (one shared model, 4 role-scoped
prompt/tool configurations, one graph) - not the multi-model variant. Revisit a second physical
model only after this version ships and `025`'s benchmark suite (once it exists) shows a
residual gap large enough to justify the added VRAM/latency/maintenance cost, and if so, prefer
a non-abliterated model for any judgment-heavy (Verifier/Summarizer) role specifically.
