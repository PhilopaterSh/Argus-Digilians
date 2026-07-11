# Research: LoRA Fine-Tuning Pipeline

**Feature**: `024-lora-fine-tuning-pipeline`

## Primary source

`docs/history/2603.27127v1.pdf`, Section 3.7 (LLM Fine-tuning with LoRA) and Section 4.2.4
(LoRA Configuration): `r=16`, `alpha=32`, LoRA+ optimizer with differentiated learning rates
(`eta_B = lambda_ratio * eta_A`), applied to "all linear modules," cosine-annealed learning
rate, gradient accumulation. Dataset composition (Section 3.7.1): 500 CVE + 239 CAPEC + 905
ATT&CK = 1,644 pairs. RQ2 results (Section 4.5.2, Table 4/5): base Qwen2.5-14B 2%/0%
(XBOW/Vulhub) -> fine-tuned 12%/0%, SCR 43.34%->52.97%, versus DeepSeek-V3.2's 86%/93.99% — the
paper's own honest conclusion: "a substantial performance gap persists... mid-scale open-source
models remain limited... even after fine-tuning."

## Current Argus implementation reviewed (confirmed absent)

`requirements.txt` has no `torch`/`transformers`/`peft`/`trl` entries (checked directly).
`app/core/llm_factory.py::build_llm()`/`build_chat_llm()` only ever call into `langchain_ollama`
against an already-pulled GGUF model — confirmed by reading the file directly, including its
own extensive comments about `num_ctx`/VRAM headroom tuning for the *current* 7.6B-at-F16 model,
which already documents this project runs close to its target hardware's VRAM ceiling even at
inference time, before any training workload is added.

## Base-model choice: why this is flagged as an open question, not settled

The paper picked Qwen2.5-14B specifically as a **general-purpose** base model to test whether
domain fine-tuning alone (without starting from an already-pentest-tuned model) can close the
gap to a large commercial model. Argus's actual production model, WhiteRabbitNeo-V3-7B, is
**already** a security/pentest-domain fine-tune (of Llama/Qwen lineage, per its HuggingFace
model card, distributed via `bartowski`'s GGUF quantizations per this project's Ollama model
tag). Two genuinely different experiments are possible: (a) replicate the paper exactly
(Qwen2.5-14B base + this dataset), for direct comparability with the paper's own numbers; (b)
apply this dataset's LoRA on top of WhiteRabbitNeo-V3-7B itself, testing whether further
domain-narrowing (CVE/CAPEC/ATT&CK specifically, vs. WhiteRabbitNeo's broader security-adjacent
training) helps a model that's already ahead of a generic base. `research.md` flags (b) as the
more practically interesting experiment for Argus specifically, since it's the model already in
production, but (a) is more scientifically comparable to the paper's own published numbers.
This choice should be made explicitly before `training/` work starts, not defaulted silently.

## GGUF conversion path (grounds FR-004)

`llama.cpp`'s `convert_hf_to_gguf.py` (or the PEFT-merge-then-convert two-step: `peft`'s
`merge_and_unload()` to bake the LoRA adapter into the base model's weights, then
`llama.cpp`'s converter, then `ollama create -f Modelfile` pointing at the resulting `.gguf` —
this is the exact same mechanism already used to obtain the current production model
(`bartowski`'s community GGUF quantizations of WhiteRabbitNeo follow this identical pipeline
upstream). This is well-trodden, documented tooling, not a novel integration risk.

## Why this is scoped honestly against RQ2's modest result (NFR-002)

The paper is explicit and quantified that fine-tuning a mid-scale model narrows but does not
close the gap to a frontier commercial model. Any Argus proposal to replicate this work should
carry the same honesty — the value case here is not "make Argus's model as good as DeepSeek-V3.2,"
it's "measurably improve Argus's existing model's structured-output/domain-reasoning behavior
within the constraints of what's locally hostable," a much narrower and more defensible claim.
