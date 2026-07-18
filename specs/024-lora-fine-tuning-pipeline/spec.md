# Feature Specification: LoRA Fine-Tuning Pipeline

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `024-lora-fine-tuning-pipeline`

**Created**: 2026-07-10

**Status**: Proposed — spec kit only, not yet implemented. Different in kind from every other
phase in this gap analysis: an **offline training pipeline**, not runtime application code.

**Input**: Gap analysis of `docs/history/2603.27127v1.pdf` against Argus's current codebase,
requested by the user 2026-07-10.

---

## Why this feature

Argus's entire model-serving stack (confirmed by reading `app/core/llm_factory.py`,
`requirements.txt`) is Ollama-only: `build_llm()`/`build_chat_llm()` wrap `OllamaLLM`/`ChatOllama`
against a locally-pulled GGUF model (`WhiteRabbitNeo/WhiteRabbitNeo-V3-7B`, per this session's
established project history). `requirements.txt` has **no** `torch`, `transformers`, `peft`, or
`trl` — there is no training capability anywhere in this codebase today; Argus consumes an
already-fine-tuned model produced by a third party (WhiteRabbitNeo's own team), it does not
fine-tune anything itself.

Red-MIRROR's second stated contribution (Section 3.7, Abstract) is a **curated 1,644-sample
fine-tuning dataset** (500 CVE descriptions, 239 CAPEC patterns, 905 MITRE ATT&CK techniques)
applied via LoRA to Qwen2.5-14B, improving that model's XBOW score from 2% to 12% (RQ2,
Table 4) — a real, measured, but modest improvement, and still far below the 86% their
large-scale API model achieves. This spec proposes building the equivalent **capability**
(dataset + training pipeline), scoped honestly against that same modest-improvement finding —
this is a research/experimentation investment, not a guaranteed large capability jump.

## Requirements

### Functional Requirements

- **FR-001**: A new, separate directory `training/` (outside `app/`, since none of this runs at
  Argus's application runtime) MUST house a dataset-curation pipeline that builds
  instruction-response pairs from three sources, mirroring the paper's exact composition: CVE
  descriptions (from NVD, reusing `023`'s NVD query capability if it exists, else a direct NVD
  bulk-data feed), CAPEC attack patterns (from MITRE's public CAPEC XML/JSON export), and MITRE
  ATT&CK techniques (from the public ATT&CK STIX data). Each entry follows the paper's own
  demonstrated format (Section 3.7.1's three worked examples): an instruction ("Analyze the
  vulnerability and identify the related CWEs and CAPECs") paired with a structured response.
- **FR-002**: A training script MUST apply LoRA (rank `r=16`, `alpha=32`, matching the paper's
  own configuration — a reasonable starting point to replicate before tuning further) to a
  locally-hostable base model. Given Argus already standardizes on Ollama/GGUF for serving
  (not a reason to change the paper's choice of base model family, but a reason to plan the
  path from "trained checkpoint" to "servable in Argus's existing stack" explicitly — see
  FR-004) using the HuggingFace `peft`/`transformers` stack (industry-standard for LoRA,
  matching the paper's own tooling implication).
- **FR-003**: The training pipeline MUST run **outside** the main Argus runtime environment —
  in a separate `training/requirements-training.txt` (torch/transformers/peft/trl/bitsandbytes),
  not added to the main `requirements.txt` that `scripts/ARGUS_INSTALLER.ps1` installs for every
  user. Every existing Argus user should not be forced to install a multi-GB CUDA/PyTorch stack
  to run the pentest agent — training is an opt-in, separate activity, matching how the paper
  itself used a completely separate hardware/software environment (Kaggle T4 notebooks) from
  its Windows-host+Kali-VM pentest execution environment (Section 4.2.1).
- **FR-004**: After training, the resulting LoRA adapter MUST be merged into the base model and
  converted to GGUF (via `llama.cpp`'s conversion scripts — the standard, documented path from a
  HuggingFace/PEFT checkpoint to an Ollama-servable format) so the output of this pipeline is
  directly usable by Argus's existing `ollama create -f Modelfile` workflow — closing the loop
  back into the application runtime without requiring any change to `llm_factory.py`.
- **FR-005**: The dataset (FR-001's output) MUST be versioned and checked into the repository
  (or a documented external location if too large for git) so the fine-tuning is reproducible
  and reviewable — this is a research artifact, not a secret, and matches the paper's own
  framing of the dataset as one of its citable contributions.

### Non-Functional Requirements

- **NFR-001**: This phase's hardware requirement (a training-capable GPU, even for a small base
  model + LoRA) is **not** guaranteed to be available on Argus's documented target user
  hardware profile (the project's own installer/docs target consumer machines, similar in class
  to this session's referenced GTX1650-class hardware) — the pipeline MUST document minimum
  VRAM requirements up front and MUST NOT be silently assumed runnable on the same machine that
  runs the Argus agent day-to-day.
- **NFR-002**: Given RQ2's own finding (2%→12% XBOW, still far below the 86% large-model
  baseline), this phase's success criteria MUST be scoped to "produces a working, measurably-
  improved-over-base checkpoint," not "closes the gap to commercial-API-model performance" —
  overclaiming here would violate Constitution VIII before a single token of training even runs.

## Success Criteria

- **SC-001**: `training/build_dataset.py` produces a dataset file with the same three-source
  composition and instruction/response shape as the paper's worked examples, with a
  reproducible source-count report (X CVE, Y CAPEC, Z ATT&CK entries).
- **SC-002**: A training run (on whatever base model is chosen — see Assumptions) completes and
  produces a LoRA adapter checkpoint; a before/after comparison on a small held-out subset of
  the dataset itself (not a full XBOW-style benchmark, which depends on `025`) shows the
  fine-tuned model's responses are measurably more aligned with the expected structured format
  than the base model's.
- **SC-003**: The merged, GGUF-converted checkpoint loads successfully via `ollama create` and
  responds to a basic prompt through Argus's existing `build_chat_llm()` path with no code
  changes required — proving FR-004's "closes the loop" claim concretely, not just in theory.

## Assumptions

- Base model choice is deliberately left open in this spec rather than committing to
  Qwen2.5-14B specifically — the paper chose it for a specific reason (deployable on
  consumer-grade T4/3090-class hardware); Argus's own current runtime model
  (WhiteRabbitNeo-V3-7B) is already pentest-domain-tuned by a third party, so fine-tuning
  further on top of it, rather than starting from a general-purpose base like Qwen2.5, is a
  legitimate alternative worth evaluating in `research.md`'s follow-up before committing.
- This phase does not depend on any other proposed phase — it is fully independent (a separate
  offline pipeline), though its dataset-curation step (FR-001) can optionally reuse `023`'s NVD
  query tool if that has already shipped, purely as a convenience, not a hard dependency.

## Explicitly out of scope

- Full RQ1-style commercial-API-model comparison — this phase produces and validates a
  fine-tuned checkpoint; comparing it head-to-head against a hosted API model on the full
  benchmark is `025`'s job once both exist.
- Automated, continuous/online fine-tuning from live agent runs — this is a one-shot, offline,
  manually-triggered pipeline; building a feedback loop that retrains from production usage is
  a substantially larger, separate proposal with real data-quality and safety implications not
  addressed here.

## Artifact applicability

- data-model.md: N/A — spec-kit-only, not yet implemented (per specs/checklist.md); no
  persistent schema or data contract exists yet to document.
- quickstart.md: N/A — spec-kit-only, not yet implemented; no runnable user/operator workflow
  exists yet to document.
