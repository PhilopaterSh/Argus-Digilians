# Research: Ethical Safeguards

**Feature**: `026-ethical-safeguards-raii`

## Primary source

`docs/history/2603.27127v1.pdf`, Section 5.4 (Ethical Considerations): "future iterations should
incorporate formal access control mechanisms... verifiable activity auditing and cryptographic
watermarking of generated payloads... constraining knowledge retrieval to trusted and curated
repositories." Also Section 3.2 (Threat Model, STRIDE): "(i) Tampering & Information Disclosure
countered by SRMM's immutable write-once semantic and gated RAG" — the paper ties its own RAG
gating claim directly to SRMM's write-once property, which Argus's `019` spec already addresses
on the memory side; this spec's FR-004 is the RAG-specific half of that same STRIDE mitigation.

## Current Argus implementation reviewed (confirmed absent/present by direct check)

- `grep -rli "rbac\|role.based\|access.control\|auth"` across `app/` found no access-control
  code (the one incidental match, `app/tools/secrets.py`, is its `Environment Variable` secret-
  detection regex matching on the literal string `DB_PASSWORD`, unrelated to authorization).
- `logs/agent_runs/*.json` — confirmed these are per-run-ID operational state files (status,
  findings, for `AgentController`/the GUI to poll), not append-only, not hash-chained, not
  attributed to an operator identity — genuinely different in purpose from an audit log, not
  just a naming difference.
- `app/core/rag/` — no gating found at the ingestion path; whatever is placed in `knowledge_base/`
  is embedded and retrievable, confirmed by this session's own prior observation that the
  knowledge base currently holds only "1 document (~8 chunks)" (from earlier RAG-loading log
  lines referenced elsewhere in this project's history) — a small, presumably-trusted set
  today, which is exactly why gating should be added *before* the knowledge base grows to a
  size where every entry isn't individually eyeballed by the operator.

## Why this is scoped down from the paper's full proposal (NFR-001)

The paper's own system is explicitly a multi-agent, potentially multi-operator research
artifact evaluated against third-party benchmark infrastructure (XBOW, Vulhub) — a context
where formal RBAC and cryptographic audit trails are proportionate. Argus, as it exists today,
is a local, single-operator tool: one person runs `LAUNCH_STUDIO.bat` on their own machine
against a target they've already decided to test. Building a full login/permission system for
that deployment shape would be exactly the kind of over-engineering this project's own operating
principles (avoid speculative complexity, don't build for hypothetical future requirements)
argue against. This spec's FR-001-FR-004 are each the proportionate version of the paper's
corresponding safeguard — real, checkable, but sized to the actual deployment, with NFR-001
stating explicitly that a future multi-user/hosted deployment would need to revisit and likely
strengthen every one of these.

## Hash-chaining as a lightweight tamper-evidence mechanism (FR-002)

A chain where each log line's hash depends on the previous line's hash (Merkle-chain-style but
linear, not tree-shaped) is a well-established, minimal-dependency pattern for making silent
post-hoc edits to a log detectable without needing a signing key, timestamping authority, or
blockchain — appropriate for FR-002's stated goal ("detectable," not "provably unforgeable
against a filesystem-level attacker," which NFR-001/Explicitly-out-of-scope both say plainly is
not this spec's target threat model).

### Correction (2026-07-10 web-research validation)

The original design used a **plain, unkeyed** `sha256(prev_hash + line)` chain. Checking this
against current guidance on tamper-evident logging found a real weakness worth fixing at zero
extra cost: with a plain hash chain, the hash function itself is public knowledge, so anyone
with filesystem access sufficient to edit one log entry can also recompute every subsequent
entry's hash correctly and produce an internally-consistent, edited chain — the tamper-evidence
guarantee silently degrades to "detects careless edits" rather than "detects tampering." The
standard fix, confirmed via multiple current tamper-evident-audit-log implementation guides
(e.g. HMAC-SHA256 hash-chain writeups), is to use a **keyed** MAC (HMAC-SHA256) instead of a
plain hash — an attacker without the key cannot regenerate a valid chain even with full
filesystem access to the log file itself, only to the key too. This raises the practical bar
meaningfully (an attacker now needs the key file/`.env` entry, not just the log file) for
identical implementation complexity — `hmac.new(key, data, sha256)` vs. `hashlib.sha256(data)`
is the same number of lines of code. Applied to `spec.md`/`plan.md`.

This is still explicitly *not* equivalent to a signed audit trail with a remotely-held or
HSM-backed key (an attacker with full access to the same machine can read the key file too) —
that stronger guarantee remains Explicitly out of scope, proportionate to NFR-001's
single-operator-local-tool framing, not because it wasn't considered.
