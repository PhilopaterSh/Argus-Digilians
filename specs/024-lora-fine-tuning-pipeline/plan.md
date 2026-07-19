# Implementation Plan: LoRA Fine-Tuning Pipeline

**Feature**: `024-lora-fine-tuning-pipeline` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

A new top-level `training/` directory, fully isolated from `app/`'s runtime dependency graph,
containing dataset curation, a LoRA training script, and a merge/GGUF-conversion step that hands
its output back to Argus's existing Ollama-based serving path with zero `app/` code changes.

## Design

### `training/requirements-training.txt` (new)
- `torch`, `transformers`, `peft`, `trl`, `bitsandbytes`, `datasets` — isolated from the main
  `requirements.txt` per FR-003, so `scripts/ARGUS_INSTALLER.ps1`'s normal install path is
  completely unaffected.

### `training/build_dataset.py` (new)
- Three source-specific fetchers (`fetch_cve_samples()`, `fetch_capec_samples()`,
  `fetch_attck_samples()`), each producing `{"instruction": ..., "response": ...}` dicts matching
  the paper's Section 3.7.1 worked-example shapes. Optionally imports `023`'s `CVEIntelligence`
  for the CVE-fetching step if that phase has shipped (soft dependency, matches `021`'s XSS-tool
  pattern of optional-not-required cross-phase reuse) — otherwise falls back to a direct NVD
  bulk-data JSON feed fetch.
- Writes `training/data/red_mirror_style_dataset.jsonl` (FR-005) plus a
  `training/data/dataset_report.md` summarizing source counts (SC-001).

### `training/train_lora.py` (new)
- Loads the chosen base model (config-driven — `--base-model` CLI arg, defaulting to a value
  set per the Assumptions section's (a)-vs-(b) decision once made) via `transformers`, applies
  `peft.LoraConfig(r=16, lora_alpha=32, target_modules="all-linear")` (matching the paper's
  config, FR-002), trains via `trl.SFTTrainer` on the FR-001 dataset, saves the adapter
  checkpoint to `training/checkpoints/`.

### `training/merge_and_convert.sh` (new)
- `peft` merge (`merge_and_unload()`) -> `llama.cpp`'s `convert_hf_to_gguf.py` -> quantize (e.g.
  Q5_K_M, matching the project's existing production-model quantization choice per this
  session's established history) -> emits a `.gguf` file plus a matching `Modelfile` referencing
  it (FR-004).

### No `app/` changes
- `llm_factory.py`, `config.yaml`'s model-name setting are the only integration point, and only
  if/when a human operator decides to switch the production `OLLAMA_MODEL` to the new
  fine-tuned tag after evaluating SC-002/SC-003 — this plan does not flip that switch
  automatically.

## Testing Strategy

`training/build_dataset.py` gets ordinary unit tests (`training/tests/test_build_dataset.py`,
kept inside `training/` rather than the main `tests/` tree since it depends on
`requirements-training.txt`, not the main test environment) — mocking each source fetcher's
HTTP calls, verifying the output JSONL shape. The training/conversion scripts themselves are
integration-tested manually (SC-002/SC-003), not via automated CI, given the GPU/VRAM
requirement (NFR-001) that CI runners are not assumed to have.

## Rollout

Nothing in the default Argus installation or runtime changes as a result of this phase landing
— it is purely an addition of new, opt-in tooling. The production model switch (if any) is a
separate, explicit, human-reviewed decision after SC-002/SC-003 are independently verified,
consistent with NFR-002's honesty requirement.
