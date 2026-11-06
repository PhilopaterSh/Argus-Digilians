# Handoff: Recon-Assist Integration (spec 030)

> Generated from `specs/030-recon-assist-integration/spec.md` revision
> `2026-10-31`. This file is an adapter between the approved spec and
> goldfish-gate, not a second specification.

## Problem and intended outcomes

Recon-Assist produces a weekly differential recon brief but Argus cannot
read it. Success is observable: ArgusMemory contains ingested leads from the
brief, and the tool registry exposes three read-side tools.

## In scope and out of scope

- In scope: brief loading, memory ingestion, registry adapters, RAG chunks.
- Out of scope: pipeline execution (Phase 2), report drafting, RAG re-index.

## User journeys and behavior

Primary flows match `spec.md` sections FR-01 (load+ingest), FR-02
(priority queue), FR-03 (new hosts), FR-04 (guidance).

## Acceptance criteria

- Given a valid argus_brief.json, when `load_brief` is called, then targets
  are upserted and findings are created with lifecycle tags.
- Given a missing or malformed brief, then a clear error string is returned
  (R2) without raising to the agent loop.
- Given the same brief loaded twice, then no duplicate targets or findings
  are created (R1).

## Functional requirements

- FR-01: Load and ingest
- FR-02: Priority queue rendering
- FR-03: New host diff listing
- FR-04: Manual-testing guidance

## Non-functional requirements

- NFR-01: Host-side, stdlib-only
- NFR-02: Idempotent ingestion

## Security requirements

- SEC-01: Domain validation before any command
- SEC-02: No credentials in briefs
- SEC-03: Scope guard in the pipeline is the authorization boundary

## Decisions

- DEC-01: Loose coupling via files
- DEC-02: Deterministic scoring first, LLM refines

## Risks

- RSK-01: Unattended cron runs (mitigated: scope.txt is the boundary)
- RSK-02: JS secrets are candidates until verified (documented in spec)
