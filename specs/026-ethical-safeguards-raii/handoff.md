# Handoff: Ethical Safeguards (RBAC-lite, Audit, Watermarking, RAG Gating)

> Generated as the EGM-to-Spec-Kit adapter for `design.md` revision
> `2026-10-31-r1` (retrofit pilot). The design stays canonical; this file
> carries it into Spec Kit for `specs/026-ethical-safeguards-raii/`.

## Problem and intended outcomes

An offensive-security automation tool with no access-control layer, no
tamper-evident accountability trail, no payload attribution, and no RAG
provenance check. Success is observable: a scan cannot start without a
recorded authorization acknowledgment, an edited audit line is detected by
`verify_audit_log()`, the default watermarking flag is a byte-identical
no-op, and an un-allowlisted RAG document is refused at ingestion.

## In scope and out of scope

- In scope: authorization-acknowledgment gate (CLI + GUI), HMAC-chained
  JSONL audit log, opt-in payload watermarking, RAG trusted-source
  allowlist.
- Out of scope: full multi-user RBAC (NFR-001), PKI/HSM signing of the
  audit log, automated verification of signed scopes-of-engagement
  (RSK-01, RSK-02).

## User journeys and behavior

1. The operator starts a scan from the CLI or the GUI; the system requires
   an explicit authorization acknowledgment, records it with a timestamp,
   and only then launches (FR-001, DEC-02).
2. Every tool call and the final risk score land in an append-only audit
   log whose lines are chained with HMAC-SHA256 under a locally stored key
   (FR-002, DEC-01, NFR-002).
3. When `enable_payload_watermarking` is on, generated payloads carry a
   short run-specific marker; when off (the default), payloads are
   byte-identical to today (FR-003).
4. A document added to the RAG knowledge base is embedded only if its
   source is on the configured trusted-source allowlist (FR-004).

## Acceptance criteria

- Given no recorded acknowledgment, when a scan is requested from the CLI
  or the GUI, then the scan does not start (SC-001, FR-001).
- Given a valid audit chain, when one line's content is edited in place,
  then `verify_audit_log()` returns False (SC-002, FR-002, DEC-01).
- Given `enable_payload_watermarking=false`, when any payload is
  generated, then it is byte-identical to today's output (SC-003, FR-003).
- Given a document outside `rag_trusted_sources`, when RAG ingestion runs,
  then the document is rejected with a clear message (SC-004, FR-004).

## Approved decisions

- DEC-01: audit-line chaining uses HMAC-SHA256 with a locally stored key
  (`AUDIT_LOG_KEY`, bootstrapped via `secrets.token_hex(32)`), not a plain
  unkeyed `sha256(prev_hash + content)`.
- DEC-02: the authorization gate is unconditional in both CLI and GUI;
  watermarking is explicitly opt-in (`false` default).
- DEC-03: the audit log lives at `logs/audit/audit_<YYYY-MM-DD>.jsonl`,
  separate from the operational `logs/agent_runs/*.json`.

## Constraints and quality attributes

- None of the four safeguards may block or meaningfully slow a
  single-operator local scan; no auth servers, HSMs, or multi-tenant
  models (NFR-001).
- The audit log captures the accountability subset only, not a wholesale
  copy of the operational run state (NFR-002).

## Risks and open questions

- RSK-01: trust-based self-attestation only - accepted by the design owner.
- RSK-02: same-machine HMAC key, not HSM - accepted, gated until Argus becomes multi-user.

## Traceability Key

| Key | Meaning |
| --- | --- |
| FR-001 | explicit, recorded authorization acknowledgment required before any scan (CLI flag/prompt + GUI checkbox) |
| FR-002 | append-only HMAC-SHA256 hash-chained JSONL audit log with verify_audit_log() |
| FR-003 | opt-in payload watermarking; default off is a byte-identical no-op |
| FR-004 | RAG ingestion gated by a configured trusted-source allowlist |
| NFR-001 | no disproportionate infrastructure or meaningful scan slowdown |
| NFR-002 | audit log captures the accountability subset only, no wholesale duplication |
| DEC-01 | HMAC-SHA256 chaining with locally stored AUDIT_LOG_KEY, not unkeyed sha256 |
| DEC-02 | authorization gate unconditional; watermarking explicitly opt-in |
| DEC-03 | audit log at logs/audit/audit_<date>.jsonl, separate from agent_runs |
| RSK-01 | self-attestation only, no verified authorization (accepted) |
| RSK-02 | same-machine HMAC key, not HSM (accepted) |
