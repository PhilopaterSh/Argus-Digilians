# Quickstart: Containerized Reconnaissance Lab

**Phase**: 1 - Validation | **Date**: 2026-07-05 | **Spec**: `specs/014-containerized-lab/spec.md`

---

## Purpose

How to run and validate the Docker Compose lab. Derived from `spec.md` (Success Criteria) and the
historical `Agent_Containers/Important_info.txt` transcript.

## Prerequisites

- Docker Engine + Docker Compose v2 on the host.
- Disk for the Ollama model volume (canonical WhiteRabbitNeo is several GB).
- Run from the repository root. The lab is optional and does not require WSL.

---

## Step 1: Bring up the lab

```bash
docker compose -f deploy/docker-lab/docker-compose.yml up -d
```

**Expected**: three services start on `lab-net`: `ollama-brain`, `juice-shop`, `my-agent`
(`spec.md` SC-001).

---

## Step 2: Pull the model (first run only)

```bash
docker exec ollama-brain ollama pull "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"
```

**Expected**: the model is stored in the `ollama_storage` volume and reused on later runs
(`spec.md` Edge Cases).

---

## Step 3: Verify the target is reachable

```bash
docker exec my-agent curl -s -o /dev/null -w "%{http_code}\n" http://juice-shop:3000
```

**Expected**: `200` - the agent resolves the target by service name on `lab-net`
(`data-model.md` AC-1).

---

## Step 4: Run a recon pass

```bash
docker exec my-agent python scripts/run_agent.py --target http://juice-shop:3000
```

**Expected**: the agent executes the recon tool sequence (headers -> nmap -> nikto -> whatweb ->
ffuf -> gobuster -> subfinder) and emits a structured report, as in the historical transcript
(`spec.md` US1 AC-2, SC-002).

---

## Step 5: Confirm the toolset

```bash
docker exec my-agent bash -lc "for t in nmap nikto gobuster ffuf subfinder whatweb; do command -v \$t >/dev/null && echo \"\$t OK\" || echo \"\$t MISSING\"; done"
```

**Expected**: all six report `OK` (`spec.md` SC-003).

---

## Step 6: Tear down

```bash
docker compose -f deploy/docker-lab/docker-compose.yml down
```

**Expected**: all services stop; the `ollama_storage` volume persists for the next run.

---

## Validation checklist

| Check | Expected | Source |
|-------|----------|--------|
| Stack up | 3 services on `lab-net` | SC-001 |
| Target reachable | HTTP 200 from agent | data-model AC-1 |
| Recon pass | structured report | SC-002 |
| Toolset | 6 tools present | SC-003 |
| Pinned images | no `:latest` in compose/Dockerfile | SC-004 |
| Not on WSL path | no production script references the lab | SC-005 |

---

## Troubleshooting

- **`lab-net` missing**: create it once with `docker network create lab-net`, or remove
  `external: true` from the compose network to let Compose create it (historical note).
- **Model pull fails / no disk**: free space and re-run Step 2; the stack still starts without the
  model (Edge Cases).
- **Agent cannot reach Ollama**: confirm `OLLAMA_HOST=http://ollama-service:11434` and that
  `ollama-service` is healthy (`data-model.md` Entity 4).

---

## CI usage

The same stack is the deterministic target for CI integration/e2e (`012-spec-reconciliation`
section 6; `.github/workflows/ci.yml` `full-tests` / `ai-eval`): start Juice Shop, run the agent
against it, then tear down.
