# Tasks: Ethical Safeguards

**Feature**: `026-ethical-safeguards-raii`

**Status**: Proposed — no tasks started.

- [ ] T001 `AuditLog` class (`append`, HMAC-SHA256 hash-chaining — corrected 2026-07-10 from a
  plain unkeyed hash, see research.md) + `verify_audit_log()` + `AUDIT_LOG_KEY` `.env`
  bootstrap — `app/core/audit.py`
- [ ] T002 Wire `scan_start`/`scan_end` audit events into `scripts/run_agent.py`
- [ ] T003 CLI `--confirm-authorized` flag / interactive prompt gate (FR-001)
- [ ] T004 GUI "authorized" checkbox gating the Start Agent button —
  `app/GUI/tabs/agent.py` (or current equivalent at implementation time)
- [ ] T005 `maybe_watermark_payload()` helper + `enable_payload_watermarking` config flag —
  `app/tools/utils.py`, `config.yaml`, `app/core/config.py`
- [ ] T006 Wire the watermarking helper into `021`'s toolkit + `evasion.py`'s payload
  construction call sites (once `021` exists; `evasion.py` alone if it doesn't yet)
- [ ] T007 `is_source_allowed()` RAG ingestion gate + `rag_trusted_sources` config —
  `app/core/rag/` (confirm exact ingestion entry point at implementation time)
- [ ] T008 Test SC-001 (both CLI and GUI gate enforcement) — `tests/test_audit.py`
- [ ] T009 Test SC-002 (tamper-detection via mutated log line) — `tests/test_audit.py`
- [ ] T010 Test SC-003 (watermarking default-off no-op) —
  `tests/test_tools/test_watermarking.py`
- [ ] T011 Test SC-004 (RAG allowlist accept/reject) — `tests/test_rag/test_gating.py`
- [ ] T012 `CHANGELOG.md` entry + `specs/checklist.md` CHK series +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row, once implemented

## Explicitly out of scope (see spec.md)

- Full multi-user RBAC (roles/permissions/login system)
- PKI/HSM-backed cryptographic signing of the audit log
- Automated rules-of-engagement/scope verification
