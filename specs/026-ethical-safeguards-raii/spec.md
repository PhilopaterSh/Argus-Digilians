# Feature Specification: Ethical Safeguards (RBAC, Audit Logging, Payload Watermarking, RAG Gating)

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `026-ethical-safeguards-raii`

**Created**: 2026-07-10

**Status**: Proposed — spec kit only, not yet implemented.

**Input**: Gap analysis of `docs/history/2603.27127v1.pdf` against Argus's current codebase,
requested by the user 2026-07-10.

---

## Why this feature

Argus today has no access-control layer at all (confirmed by grep — no RBAC/role/access-control
code found anywhere in `app/`). Anyone who can start `LAUNCH_STUDIO.bat`/reach the Streamlit
dashboard can launch a scan against any target string the tool accepts, with no authentication,
no per-user audit trail, and no record of who ran what beyond `logs/agent_runs/*.json` — which
are **operational** state files (run status, findings, for the GUI to poll), not accountability
records: they are not tamper-evident, not attributed to an identity, and are overwritten/reused
by run ID rather than append-only per actor.

Red-MIRROR's Section 5.4 (Ethical Considerations) proposes exactly this gap, framed as necessary
"foundational design principles rather than auxiliary features" for any offensive-security
automation tool: role-based access control, verifiable activity auditing, cryptographic
watermarking of generated payloads, and RAG knowledge-source gating. This spec scopes a
proportionate, Argus-appropriate version of each — proportionate because Argus is currently a
single-operator local tool (run from one machine against targets the operator has already
chosen to point it at), not a multi-tenant SaaS platform; the paper's safeguards were designed
for a research system the authors explicitly flag as dual-use-risky, and Argus should take that
warning seriously without over-building infrastructure a single-operator local tool doesn't need.

## Requirements

### Functional Requirements

- **FR-001 (Authorization gate, not full RBAC)**: Before any scan starts, the system MUST
  require an explicit, recorded acknowledgment that the operator is authorized to test the
  target (a simple "I confirm I am authorized to test this target" checkbox/prompt in the GUI
  and CLI, logged with a timestamp) — this is deliberately lighter than the paper's full RBAC
  (multi-user roles/permissions), which is disproportionate for a single-operator local tool,
  but it closes the real gap: today nothing stops (or even records) a scan against an
  unauthorized target.
- **FR-002 (Tamper-evident audit log)**: A new, append-only audit log (`logs/audit/
  audit_<date>.jsonl`, distinct from the existing operational `logs/agent_runs/*.json`) MUST
  record, per run: timestamp, target, FR-001's authorization acknowledgment, every tool call
  made (name + truncated args, not full payload text — avoid logging secrets the tools
  themselves might retrieve), and the final report's risk score. Each line MUST include a
  hash chained to the previous line's hash. **Refined from 2026-07-10 web-research validation**:
  use **HMAC-SHA256 with a locally-stored key** (`hmac.new(key, prev_hash + line_content,
  sha256)`), not plain unkeyed `sha256(prev_hash + line_content)` — with a plain hash chain,
  anyone with filesystem access to edit one entry can also read the (public, keyless) hash
  function and regenerate every subsequent hash consistently, defeating the whole point; a
  locally-stored HMAC key that isn't itself editable through the same access path raises the bar
  from "detects careless/accidental edits" to "detects tampering by anyone who doesn't also have
  the key" — still not a full PKI/HSM signature scheme (see Explicitly out of scope), but a
  materially stronger, still-lightweight guarantee for the same implementation cost.
- **FR-003 (Payload watermarking)**: Any payload string a tool generates and sends to a target
  (via `021`'s toolkit, `Advanced_Evasion_Probe`, etc.) MAY optionally include a distinguishing,
  non-functional marker (e.g., a comment/parameter fragment containing a short run-specific
  token) when a new `enable_payload_watermarking` config flag is set — enabling a target
  operator or downstream log review to attribute observed traffic back to a specific Argus run.
  Default **off**, because watermarking is only useful/appropriate when the target operator has
  agreed to look for it (a coordinated red-team engagement), and a marker that changes traffic
  shape could itself interfere with certain test cases (e.g., exact-length-sensitive payloads) —
  this MUST be an explicit opt-in, not a default behavior.
- **FR-004 (RAG source gating)**: `app/core/rag/`'s knowledge base ingestion MUST validate that
  any new document added comes from an explicitly configured trusted-source allowlist (a
  simple path/URL-pattern allowlist in `config.yaml`, e.g. local `knowledge_base/` files
  reviewed by the operator, or specific documented external sources) before it's embedded and
  made retrievable — today, confirmed by reading `app/core/rag/`'s structure, there is no
  gating at all: whatever file exists in `knowledge_base/` gets embedded, no provenance check.
  This is the lowest-effort of the four safeguards, since it only needs a check at one ingestion
  entry point.

### Non-Functional Requirements

- **NFR-001**: None of FR-001 through FR-004 MUST block or meaningfully slow down a scan for a
  single-operator local run — this spec explicitly rejects building infrastructure (a real
  auth server, a signing HSM, a multi-tenant permission model) disproportionate to Argus's
  actual deployment shape today. If Argus later becomes a multi-user/hosted service, these
  safeguards should be revisited and very likely need to become more rigorous — this spec is
  scoped to Argus as it exists now, not a hypothetical future deployment.
- **NFR-002**: FR-002's audit log MUST NOT duplicate `logs/agent_runs/*.json`'s existing
  operational data wholesale (Constitution IX) — it captures the subset relevant to
  accountability (who/what/when/authorized-by-whom), not a second copy of the full run state.

## Success Criteria

- **SC-001**: A test confirms a scan cannot start without FR-001's acknowledgment being present
  (CLI: a required flag/prompt; GUI: a required checkbox) — both interfaces enforce it, not
  just one.
- **SC-002**: A test appends several audit-log entries, then modifies one entry's content
  in-place, and confirms a verification pass (`verify_audit_log(path)`) detects the broken hash
  chain — proving FR-002's tamper-evidence actually works, not just that hashes are written.
- **SC-003**: A test confirms `enable_payload_watermarking=false` (the default) produces
  byte-identical payloads to today's behavior — proving FR-003 is a true no-op when disabled,
  not a hidden behavior change.
- **SC-004**: A test confirms a document outside the configured allowlist is rejected at RAG
  ingestion with a clear message, and one inside the allowlist is accepted unchanged.

## Assumptions

- FR-001's "authorization acknowledgment" is a trust-based control (the operator self-attests),
  not a verified one (Argus cannot itself confirm the operator's claim is true) — this is stated
  explicitly rather than implied to be stronger than it is, per Constitution VIII. Real
  authorization verification (e.g., checking a signed scope-of-engagement document) is a
  substantially larger feature explicitly out of scope here.
- FR-002's HMAC key is assumed stored locally (e.g., a file under restrictive OS permissions, or
  `.env`) on the same machine as the log — this protects against casual/opportunistic tampering
  by someone with file access but not against someone with full access to that same machine
  (who could read the key too). A remote/HSM-held key would close that gap but is explicitly a
  heavier control than this single-operator-local-tool spec targets (NFR-001).

## Explicitly out of scope

- Full multi-user RBAC (roles, permissions, user management, login system) — disproportionate
  to a single-operator local tool per NFR-001; FR-001's lightweight acknowledgment gate is the
  scoped substitute.
- Cryptographic signing with a real PKI/HSM for the audit log — FR-002's hash-chaining is
  tamper-*evident* (detects post-hoc edits), not tamper-*proof* (cannot prevent a determined
  attacker with full filesystem access from regenerating the whole chain) — a proportionate,
  not maximal, control.
- Automated verification that a target is actually within an authorized scope (e.g., checking
  against a signed rules-of-engagement document) — FR-001 is a self-attestation gate only.

## Artifact applicability

- data-model.md: N/A — spec-kit-only, not yet implemented (per specs/checklist.md); no
  persistent schema or data contract exists yet to document.
- quickstart.md: N/A — spec-kit-only, not yet implemented; no runnable user/operator workflow
  exists yet to document.
