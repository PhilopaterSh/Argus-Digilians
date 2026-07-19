# Argus Containerized Reconnaissance Lab

Optional, disposable test environment for Argus. It brings up a local Ollama brain, a reproducible
vulnerable target (OWASP Juice Shop), and the Argus agent (current `app/`) on one isolated network.

- **Specification**: [`../../specs/014-containerized-lab/`](../../specs/014-containerized-lab/)
- **Not** part of the WSL production path - this is for testing, CI, and demos only.

## Reconstruction note

This lab was recovered from the historical `origin/argus/SALMA:Agent_Containers/` tree (dropped during
the `app/` + Spec-Kit refactor) and modernized: images and tool binaries are version-pinned, the base
image is Python 3.12, and the agent container runs the current `app/` instead of the legacy `main.py`.
See `specs/014-containerized-lab/research.md` for the evidence and decisions.

## Quick start

```bash
docker compose -f deploy/docker-lab/docker-compose.yml up -d
docker exec ollama-brain ollama pull "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"   # first run
docker exec my-agent python scripts/run_agent.py --target http://juice-shop:3000
docker compose -f deploy/docker-lab/docker-compose.yml down
```

Full steps and validation checklist: [`../../specs/014-containerized-lab/quickstart.md`](../../specs/014-containerized-lab/quickstart.md).

## Services

| Service | Image / build | Port | Role |
|---------|---------------|------|------|
| `ollama-service` | `ollama/ollama:0.3.14` | 11434 | LLM + embeddings ("brain") |
| `juice-shop` | `bkimminich/juice-shop:v17.1.1` | 3000 | Reproducible target |
| `cyber-agent` | built from `Dockerfile` | - | Argus agent + recon tools |

Tools baked into the agent image: nmap, nikto, gobuster, ffuf, subfinder, whatweb.
