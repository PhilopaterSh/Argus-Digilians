# Feature Specification: Containerized Reconnaissance Lab

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `014-containerized-lab`

**Created**: 2026-07-05

**Status**: Draft - Reconstructed (restoration of a capability present on the historical
`origin/argus/SALMA` branch under `Agent_Containers/`, dropped during the `app/` + Spec-Kit refactor;
recovered via Git forensic analysis - see `docs/ARCHITECTURE_AUDIT_REPORT.md` and the reconstruction
report).

**Input**: Restore, as a modern Spec-Kit feature, the Docker Compose lab that ran the Argus agent
against a reproducible vulnerable target (OWASP Juice Shop) with a local Ollama brain. The historical
lab (`Agent_Containers/docker-compose.yml`, `Dockerfile`, `Important_info.txt`) is the source of
truth for the required behavior.

---

## Why this feature (reconstruction rationale)

The current framework is WSL-only (Constitution: WSL2/Kali required). The historical containerized
lab provided a **reproducible, disposable test environment** with a known-vulnerable target, which
is exactly the "controlled local test target" the canonical testing strategy needs
(`012-spec-reconciliation` section 6: integration and end-to-end tiers). Restoring it strengthens
CI/e2e without changing the production WSL model. The lab is **optional and additive** - it does not
replace WSL-based production runs.

---

## User Scenarios & Testing

### User Story 1 - Reproducible target for testing (Priority: P1)

As a developer, I want a one-command lab with a known-vulnerable target and a local Ollama, so that
integration and end-to-end tests run against a deterministic environment instead of a live target.

**Independent Test**: `docker compose -f deploy/docker-lab/docker-compose.yml up` brings up Ollama,
the target, and the agent on one network; the agent can reach the target by service name.

**Acceptance Scenarios**:
1. **Given** the compose stack, **When** it starts, **Then** three services join one network:
   `ollama-service` (Ollama), `juice-shop` (OWASP Juice Shop target), and `cyber-agent` (Argus agent).
2. **Given** the running stack, **When** the agent runs a recon pass against `http://juice-shop:3000`,
   **Then** it executes the tool sequence and produces a structured report (as in the historical
   `Important_info.txt` transcript).

### User Story 2 - Self-contained tool image (Priority: P1)

As a developer, I want the agent container to include the recon tools, so no host/WSL setup is
required to run the lab.

**Acceptance Scenarios**:
1. **Given** the agent image, **When** built, **Then** it contains nmap, nikto, gobuster, ffuf,
   subfinder, and whatweb (the historical Dockerfile toolset).

### User Story 3 - CI integration target (Priority: P2)

As a maintainer, I want CI integration/e2e jobs to run against the lab's Juice Shop target, so those
jobs no longer require an external host.

**Acceptance Scenarios**:
1. **Given** the lab, **When** the CI integration job runs, **Then** it starts Juice Shop and executes
   the agent against it (ties into `.github/workflows/ci.yml` `full-tests` / `ai-eval` jobs).

### Edge Cases

- Ollama model not yet pulled inside the container volume -> the entrypoint pulls `ARGUS_MODEL` on
  first run (guarded by disk, consistent with Constitution model handling).
- `lab-net` network already exists -> compose reuses it (historical `external: true` note).
- Agent needs raw sockets for some scans -> `cap_add: NET_ADMIN, NET_RAW` (historical compose).

---

## Requirements

### Functional Requirements

- **FR-001**: The lab MUST define three services on a shared network `lab-net`: `ollama-service`
  (`ollama/ollama`), `juice-shop` (`bkimminich/juice-shop`), and `cyber-agent` (built locally).
- **FR-002**: `cyber-agent` MUST receive `OLLAMA_HOST=http://ollama-service:11434` and
  `AGENT_MODEL` (default the canonical `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest`) via environment.
- **FR-003**: The `cyber-agent` image MUST install the recon toolset: nmap, nikto, gobuster, ffuf,
  subfinder, whatweb.
- **FR-004**: `cyber-agent` MUST run the **current** `app/` codebase (not the historical `main.py`),
  targeting `http://juice-shop:3000` - a modern-equivalent redesign of the agent portion.
- **FR-005**: The lab MUST be launchable with a single `docker compose up` and torn down with
  `docker compose down`.
- **FR-006**: All external images and downloaded tool binaries MUST be version-pinned (modernization
  over the historical `:latest` tags) for reproducibility.
- **FR-007**: The lab MUST NOT be required for normal (WSL) operation; it is an optional test/demo
  environment (Constitution: WSL is the production path).

### Non-Functional Requirements

- **NFR-001**: `docker compose up` reaches a ready state (all three services healthy) without manual
  steps beyond an optional first-run model pull.
- **NFR-002**: The lab is isolated on `lab-net`; the target is only reachable inside the network.
- **NFR-003**: All lab files are ASCII/English-only (Constitution VI).

### Key Entities

- `deploy/docker-lab/docker-compose.yml` - the three-service stack.
- `deploy/docker-lab/Dockerfile` - the agent image (tools + current `app/`).
- `deploy/docker-lab/README.md` - usage, pointing here.

---

## Success Criteria

- **SC-001**: One command brings up Ollama + Juice Shop + agent on `lab-net` (FR-001, FR-005).
- **SC-002**: The agent completes a recon pass against `http://juice-shop:3000` and emits a report
  (US1 AC-2).
- **SC-003**: The agent image contains all six recon tools (FR-003).
- **SC-004**: Images and tool binaries are version-pinned (FR-006).
- **SC-005**: The lab is not referenced by any WSL production path (FR-007).

---

## Assumptions

- Docker Engine + Compose v2 are available on the host (new dependency for this optional feature).
- The canonical default model is `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest`
  (`012-spec-reconciliation` section 2.6; historical compose default).
- OWASP Juice Shop (`bkimminich/juice-shop`) is the reproducible target, as in the historical lab.
