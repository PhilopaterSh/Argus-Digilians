# Implementation Plan: Containerized Reconnaissance Lab

**Feature ID**: `014-containerized-lab` | **Date**: 2026-07-05 | **Spec**: `specs/014-containerized-lab/spec.md`

**Status**: Draft - Reconstructed

---

## Summary

Restore the historical `Agent_Containers/` lab as a modern `deploy/docker-lab/` feature: a Docker
Compose stack (Ollama + OWASP Juice Shop + Argus agent) where the agent runs the current `app/`
codebase against a reproducible target. Infrastructure is restored and version-pinned; the agent
layer is redesigned onto `app/`.

---

## Technical Context

**Language/Version**: Python 3.12 (`app/`) inside a container; base image `python:3.11-slim` may be
bumped to 3.12-slim during implementation.

**Primary Dependencies**: Docker Engine + Compose v2 (new, optional); `Setup/requirements.txt` for the
agent; recon tools installed in the image (nmap, nikto, gobuster, ffuf, subfinder, whatweb).

**Storage**: named volume `ollama_storage` for the model; no host DB required (the Blackboard lives
in the agent container).

**Target Platform**: any Docker host (Linux/Windows/macOS). Distinct from the WSL production path.

**Project Type**: optional deployment/test environment.

## Constitution Check

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Admin-First Elevation | Not Applicable | No host OS mutation; containers only |
| II. Single-Source Installer | Compliant | Lab does not alter the installer; separate `deploy/` tree |
| III. Idempotent & Test-Gated | Compliant | `compose up`/`down` are idempotent; used by CI |
| IV. Platform-Boundary Clarity | Compliant | Containers are isolated on `lab-net`; not the WSL bridge |
| V. Observability & Logging | Compliant | Container logs; agent writes structured events |
| VI. English-Only Documentation | Compliant | All lab files ASCII/English |

**Gate Decision**: PASS - no violations.

## Project Structure

```text
specs/014-containerized-lab/
+-- spec.md
+-- research.md
+-- plan.md
+-- data-model.md
+-- quickstart.md
+-- tasks.md

deploy/docker-lab/
+-- docker-compose.yml   # 3 services on lab-net (restored + pinned)
+-- Dockerfile           # agent image: recon tools + current app/
+-- README.md            # usage; points to this spec
```

## Key Design Decisions

1. **Split restore**: infrastructure restored from `origin/argus/SALMA:Agent_Containers/*`; agent code
   redesigned onto `app/` (research Decision 1).
2. **Version pinning** for reproducible CI (research Decision 2).
3. **Optional/additive**: never on the WSL production path (research Decision 3; spec FR-007).
4. **CI target**: Juice Shop becomes the deterministic target for integration/e2e (research Decision 5).

## Restoration source commands (evidence recovery)

```bash
# Inspect the historical lab (already fetched; no network needed)
git show origin/argus/SALMA:Agent_Containers/docker-compose.yml
git show origin/argus/SALMA:Agent_Containers/Dockerfile
git show origin/argus/SALMA:Agent_Containers/Important_info.txt
```

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 0 | Recover + read historical `Agent_Containers/*` from Git | Done (research.md) |
| 1 | Author `deploy/docker-lab/docker-compose.yml` (pinned) | This feature |
| 2 | Author `deploy/docker-lab/Dockerfile` (tools + current app/) | This feature |
| 3 | Author `deploy/docker-lab/README.md` | This feature |
| 4 | Wire CI integration/e2e job to the lab target | Follow-up (ci.yml) |
| 5 | Validate: `compose up`, agent recon vs juice-shop, `compose down` | Requires Docker host |

## Complexity Tracking

| Item | Why needed | Simpler alternative rejected |
|------|------------|------------------------------|
| New `deploy/` tree + Docker dependency | Reproducible target + isolated test env | Testing against live/WSL targets is non-deterministic and not CI-friendly |
