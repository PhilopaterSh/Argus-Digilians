# Data Model: Containerized Reconnaissance Lab

**Phase**: 1 - Design | **Date**: 2026-07-05 | **Spec**: `specs/014-containerized-lab/spec.md`

---

## Purpose

The lab is infrastructure, so its "data model" is the compose topology: services, network, volumes,
and the agent container's environment contract. Derived from `origin/argus/SALMA:Agent_Containers/
docker-compose.yml` and modernized per `research.md`.

---

## Entity 1: Service

| Service | Image / build | Ports | Role |
|---------|---------------|-------|------|
| `ollama-service` | `ollama/ollama:<pinned>` | 11434 | The "brain" - serves the LLM + embeddings |
| `juice-shop` | `bkimminich/juice-shop:<pinned>` | 3000 | The reproducible vulnerable target (OWASP Juice Shop) |
| `cyber-agent` | build `deploy/docker-lab/Dockerfile` | - | The Argus agent (current `app/`) with recon tools |

**Invariants**: all three join `lab-net`; `cyber-agent` `depends_on` the other two; `cyber-agent`
adds capabilities `NET_ADMIN`, `NET_RAW` (historical compose).

---

## Entity 2: Network

| Field | Value |
|-------|-------|
| name | `lab-net` |
| scope | internal bridge; target reachable only inside the network (NFR-002) |
| external | reuse if it already exists (historical `external: true` note) |

---

## Entity 3: Volume

| Field | Value |
|-------|-------|
| name | `ollama_storage` |
| mount | `/root/.ollama` in `ollama-service` |
| purpose | persist the pulled model across restarts |

---

## Entity 4: AgentEnvironment (cyber-agent contract)

| Variable | Default | Purpose |
|----------|---------|---------|
| `OLLAMA_HOST` | `http://ollama-service:11434` | LLM endpoint (service DNS name) |
| `AGENT_MODEL` | `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest` | Canonical model (`012` section 2.6) |
| `TARGET_URL` | `http://juice-shop:3000` | The reproducible target |

**Invariant**: the agent resolves peers by service name (`ollama-service`, `juice-shop`) on `lab-net`,
never by host IP.

---

## Entity 5: ToolSet (agent image)

Installed in the `cyber-agent` image (historical Dockerfile):

| Tool | Source (pinned) |
|------|-----------------|
| nmap | apt |
| nikto | git clone sullo/nikto |
| gobuster | release v3.6.0 |
| ffuf | release v2.1.0 |
| subfinder | release v2.6.6 |
| whatweb | apt |

---

## Relationships

```text
lab-net
 +-- ollama-service  (volume: ollama_storage)   <-- OLLAMA_HOST
 +-- juice-shop                                  <-- TARGET_URL
 +-- cyber-agent (ToolSet + app/) --depends_on--> ollama-service, juice-shop
```

---

## Acceptance Criteria (data model)

- **AC-1**: Three services resolve each other by name on `lab-net` (SC-001).
- **AC-2**: `cyber-agent` env provides `OLLAMA_HOST`, `AGENT_MODEL`, `TARGET_URL` (FR-002).
- **AC-3**: The agent image contains all six tools (SC-003, FR-003).
- **AC-4**: Images and tool binaries are pinned (SC-004, FR-006).

---

## Implementation Notes

- The authoritative topology lives in `deploy/docker-lab/docker-compose.yml`; this document is the
  conceptual model and is updated if the compose file changes.
- The agent container runs the current `app/` entrypoint (e.g. `scripts/run_agent.py` /
  `run_argus_cli.py`), not the historical `main.py` (research Decision 1).
