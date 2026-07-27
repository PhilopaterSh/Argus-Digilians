# Implementation Plan: Ethical Safeguards

**Feature**: `026-ethical-safeguards-raii` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

Four small, independent additions: a CLI/GUI authorization-acknowledgment gate, a new
hash-chained JSONL audit log distinct from existing operational logs, an opt-in payload
watermarking flag, and a RAG ingestion allowlist check. No new subsystem-scale infrastructure,
per NFR-001.

## Design

### `app/core/audit.py` (new)
- `AuditLog` class: `append(event: dict)` — computes `hmac.new(self._key, (prev_hash_hex +
  json.dumps(event, sort_keys=True)).encode(), hashlib.sha256).hexdigest()` (HMAC-SHA256, per
  spec.md's 2026-07-10 correction — not a plain unkeyed hash), writes `{**event, "hash":
  new_hash, "prev_hash": prev_hash_hex}` as one JSONL line to `logs/audit/
  audit_<YYYY-MM-DD>.jsonl`, keeps `prev_hash` in memory for the current process (re-reads the
  last line's hash on startup if the day's file already exists, so multiple runs on the same day
  chain correctly). `self._key` is loaded from a new `AUDIT_LOG_KEY` `.env` entry (generated
  once, e.g. via `secrets.token_hex(32)`, on first run if absent — matching how the project's
  other `.env`-driven secrets are already bootstrapped) rather than hardcoded or derived from
  anything guessable.
- `verify_audit_log(path, key) -> bool`: re-walks the file, recomputing each line's HMAC from
  its content + the previous line's stored hash + the same key, returns `False` on the first
  mismatch (SC-002) — verification requires the key, same as generation.

### `app/core/agent/brain.py` / `scripts/run_agent.py` / GUI entrypoint
- Before `ArgusBrain.ask()` is called, require and pass through an `authorized: bool`
  acknowledgment (FR-001): CLI gains a required `--confirm-authorized` flag (or an interactive
  prompt if omitted and running in a TTY); GUI's "Start Agent" button is disabled until a new
  checkbox is checked. Both paths call `AuditLog.append({"event": "scan_start", "target":...,
  "authorized_ack": True, "timestamp": ...})` before the graph starts, and
  `{"event": "scan_end", "risk_score": ..., "tool_calls": [...]}"` after (FR-002).

### `app/tools/*.py` (payload-emitting tools, `021`'s toolkit + `evasion.py`)
- A small shared helper `app/tools/utils.py::maybe_watermark_payload(payload: str) -> str`:
  when `ArgusConfig.enable_payload_watermarking` is `True` (default `False`, FR-003), appends a
  short, position-appropriate, non-functional marker (e.g. a URL comment fragment or an extra
  harmless query param carrying a short run-ID token) to a payload string before it's sent;
  when `False`, returns the input unchanged (byte-identical, SC-003). Existing/new tools call
  this helper at their one or two payload-construction call sites rather than each
  reimplementing marker logic (Constitution IX).

### `app/core/rag/` (ingestion entry point — exact function name to confirm against the current
`app/core/rag/` module layout at implementation time)
- New `is_source_allowed(path_or_url: str) -> bool` checked before embedding, against a new
  `rag_trusted_sources` allowlist in `config.yaml` (glob patterns for local paths, domain list
  for URLs). A rejected source raises/logs a clear, specific message (FR-004, SC-004) rather
  than silently skipping or silently embedding anyway.

### `config.yaml` / `app/core/config.py`
- New fields: `enable_payload_watermarking: false`, `rag_trusted_sources: ["knowledge_base/**"]`
  (default covers today's existing local-only knowledge base without behavior change until the
  operator adds an external source).

## Testing Strategy

`tests/test_audit.py` — SC-001 (gate enforcement, both CLI and GUI paths, GUI test via
Streamlit's testing utilities if already used elsewhere in `tests/test_gui/`, else a direct
function-level test of the gating logic) and SC-002 (tamper-detection: build a valid chain,
mutate one line, assert `verify_audit_log` returns `False`). `tests/test_tools/
test_watermarking.py` — SC-003 (default-off no-op proof). `tests/test_rag/test_gating.py` —
SC-004 (allowed vs. rejected source).

## Rollout

`enable_payload_watermarking` defaults `false` (explicit opt-in, FR-003). FR-001's
authorization gate and FR-004's RAG gating are **not** optional/flagged — they are a hard
requirement to start a scan / ingest a document respectively, since their entire value is in
being unconditional (an optional authorization gate would defeat its own purpose).
