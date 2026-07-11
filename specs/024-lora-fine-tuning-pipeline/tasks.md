# Tasks: LoRA Fine-Tuning Pipeline

**Feature**: `024-lora-fine-tuning-pipeline`

**Status**: Proposed — no tasks started.

- [ ] T000 (gate) Decide base model: replicate paper (Qwen2.5-14B) vs. fine-tune on top of
  Argus's own production model (WhiteRabbitNeo-V3-7B) — see research.md's open question;
  record the decision here before T001
- [ ] T001 `training/requirements-training.txt` (isolated from main `requirements.txt`)
- [ ] T002 `training/build_dataset.py` (CVE + CAPEC + ATT&CK fetchers, JSONL output,
  dataset report) — reuse `023`'s `CVEIntelligence` if available, else direct NVD feed
- [ ] T003 Tests for `build_dataset.py` (mocked HTTP) — `training/tests/test_build_dataset.py`
- [ ] T004 `training/train_lora.py` (LoRA r=16/alpha=32, `trl.SFTTrainer`)
- [ ] T005 `training/merge_and_convert.sh` (PEFT merge -> llama.cpp GGUF convert -> quantize ->
  Modelfile)
- [ ] T006 SC-001: dataset composition report matches paper's 3-source shape
- [ ] T007 SC-002: before/after held-out comparison shows measurable improvement over base
- [ ] T008 SC-003: converted GGUF loads via `ollama create` and responds through
  `build_chat_llm()` with zero `app/` code changes
- [ ] T009 Document minimum VRAM requirements (NFR-001) prominently in `training/README.md`
- [ ] T010 `CHANGELOG.md` entry + `specs/checklist.md` CHK series +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row, once implemented

## Explicitly out of scope (see spec.md)

- Full RQ1-style commercial-API-model head-to-head comparison (depends on `025`)
- Automated/continuous online fine-tuning from production agent runs
