# Tasks: Containerized Reconnaissance Lab

**Input**: `specs/014-containerized-lab/spec.md`, `plan.md`

**Note**: reconstructed feature. Historical infrastructure is restored + modernized; the agent layer
is redesigned onto the current `app/`.

---

## Phase 0: Evidence recovery

- [x] T001 Recover historical `Agent_Containers/*` from `origin/argus/SALMA` via Git (documented in `research.md`).
- [x] T002 Classify restore-vs-redesign per layer (infra = restore; agent = redesign onto `app/`).

## Phase 1: Compose stack

- [x] T003 Author `deploy/docker-lab/docker-compose.yml` - 3 services (`ollama-service`, `juice-shop`, `cyber-agent`) on `lab-net`, pinned images, agent env (`OLLAMA_HOST`, `AGENT_MODEL`, `TARGET_URL`).
- [x] T004 Author `deploy/docker-lab/Dockerfile` - recon toolset (nmap, nikto, gobuster, ffuf, subfinder, whatweb) + current `app/`.
- [x] T005 Author `deploy/docker-lab/README.md` pointing to this spec.

## Phase 2: Agent entrypoint (redesign onto app/)

- [ ] T006 Confirm/author a container entrypoint that runs the current agent against `TARGET_URL` (e.g. `scripts/run_agent.py --target $TARGET_URL`). Requires the runtime.
- [ ] T007 Ensure the Blackboard (`data/argus_intelligence.db`) initializes inside the container.

## Phase 3: CI integration

- [ ] T008 Wire `.github/workflows/ci.yml` `full-tests` / `ai-eval` to start the lab, run the agent against Juice Shop, then tear down (self-hosted or Docker-enabled runner).

## Phase 4: Validation (requires a Docker host)

- [ ] T009 `docker compose up`; verify 3 services on `lab-net` (SC-001).
- [ ] T010 Verify agent -> `http://juice-shop:3000` returns 200 (data-model AC-1).
- [ ] T011 Run a recon pass; verify structured report (SC-002).
- [ ] T012 Verify all six tools present in the image (SC-003).
- [ ] T013 `docker compose down`; verify clean teardown and volume persistence.

## Dependencies & Execution Order

1. T001 -> T002 (evidence)
2. T003 -> T004 -> T005 (compose stack)
3. T006 -> T007 (agent entrypoint; needs runtime)
4. T008 (CI; needs Docker runner)
5. T009 -> T013 (validation; needs Docker host)

## Blockers

- T006-T013 require a Docker host (external infrastructure) and are validation/runtime tasks; they
  cannot be completed without Docker + Ollama. Specs and infrastructure files (T001-T005) are complete.
