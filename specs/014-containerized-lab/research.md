# Research: Containerized Reconnaissance Lab

**Phase**: 0 - Technical Research | **Date**: 2026-07-05 | **Spec**: `specs/014-containerized-lab/spec.md`

---

## Purpose

Records the evidence and decisions for reconstructing the historical containerized lab. All evidence
is drawn from Git (`origin/argus/SALMA:Agent_Containers/*`); no external sources are used.

---

## Evidence (historical source of truth)

| Artifact (SALMA branch) | Content |
|-------------------------|---------|
| `Agent_Containers/docker-compose.yml` | 3 services on `lab-net`: `ollama-service` (ollama/ollama, 11434), `juice-shop` (bkimminich/juice-shop, 3000), `cyber-agent` (build ., NET_ADMIN/NET_RAW, `OLLAMA_HOST`, `AGENT_MODEL=WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest`) |
| `Agent_Containers/Dockerfile` | `python:3.11-slim` + nmap, nikto (git), gobuster v3.6.0, ffuf v2.1.0, subfinder v2.6.6, whatweb, nodejs/npm |
| `Agent_Containers/Important_info.txt` | Transcript of the agent running against `http://juice-shop:3000`: check_web_headers -> run_nmap -> run_nikto -> run_whatweb -> run_ffuf_discovery -> run_gobuster -> run_subfinder -> Final Answer report; plus an n8n-vs-LangChain comparison note |
| `Agent_Containers/main.py`, `tools.py` | The historical (pre-refactor) agent entrypoint and tools |

---

## Decision 1: Restore vs redesign - split by layer

| Layer | Decision | Reason |
|-------|----------|--------|
| Infrastructure (compose + Dockerfile) | **Restore + modernize** | The 3-service topology and toolset are directly reusable and valuable |
| Agent code (`main.py` / `tools.py`) | **Redesign to current `app/`** | The historical agent predates the `app/` + Spec-Kit refactor; reusing it would reintroduce legacy modules and drift |

**Traceability**: `spec.md` FR-004; Constitution "Single-Source" (avoid two agent implementations).

---

## Decision 2: Version pinning

| Option | Pros | Cons |
|--------|------|------|
| A. Pin all images + tool binaries | Reproducible, deterministic CI | Requires periodic bumps |
| B. Keep `:latest` (historical) | No maintenance | Non-reproducible; breaks CI silently |

**Decision**: Option A - pin `ollama/ollama`, `bkimminich/juice-shop`, and the tool binary versions
already pinned in the historical Dockerfile (gobuster 3.6.0, ffuf 2.1.0, subfinder 2.6.6).
*Traceability*: `spec.md` FR-006, SC-004.

---

## Decision 3: Relationship to the WSL production model

**Decision**: the lab is **optional and additive**; it is a test/demo environment, not a replacement
for the WSL/Kali production path (Constitution). This avoids two competing production architectures.
*Traceability*: `spec.md` FR-007, SC-005.

---

## Decision 4: Model provisioning inside the container

**Decision**: the Ollama model is pulled on first run into a named volume (`ollama_storage`), using
`AGENT_MODEL` (default canonical WhiteRabbitNeo). Guarded so a missing model does not crash the stack.
*Traceability*: `spec.md` Edge Cases; `012-spec-reconciliation` section 2.6 (canonical model).

---

## Decision 5: Use as the canonical CI test target

**Decision**: wire the lab's Juice Shop as the deterministic target for CI integration/e2e jobs, which
currently require an external host (`.github/workflows/ci.yml` `full-tests` / `ai-eval`).
*Traceability*: `012-spec-reconciliation` section 6 (integration/e2e tiers), section 7 (CI/CD).

---

## Alternatives rejected

- **n8n visual workflow** (mentioned in historical `Important_info.txt`) - rejected; it loses the
  dynamic LLM tool-selection the LangGraph agent provides (architecture ADR-12). Kept for reference
  only.
- **Restore the legacy `main.py` agent** - rejected per Decision 1 (drift).

---

## Decision Traceability Summary

| Decision | Spec ref | Source |
|----------|----------|--------|
| 1 Restore infra / redesign agent | FR-001..004 | SALMA compose + Dockerfile |
| 2 Version pinning | FR-006, SC-004 | Dockerfile pins |
| 3 Optional/additive to WSL | FR-007, SC-005 | Constitution |
| 4 Model provisioning | Edge Cases | compose env + 012 s2.6 |
| 5 CI target | US3 | 012 s6-7, ci.yml |

---

## Open Questions

None blocking. Docker availability is a new host dependency (documented in `spec.md` Assumptions),
not an unknown.
