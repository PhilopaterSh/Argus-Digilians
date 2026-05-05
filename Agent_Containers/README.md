# 🤖 AI-Powered Cybersecurity Agent
### Docker-Based Lab: Ollama + LangChain + OWASP Juice Shop

> A local AI security agent that autonomously reasons about a target web application and executes security tools against it. Runs entirely inside Docker — no cloud services, no API keys, no external dependencies.

---

## Overview

The agent follows a **ReAct (Reasoning + Acting)** loop: it asks the LLM what to do next, executes the chosen tool, feeds the result back to the LLM, and repeats until it reaches a conclusion or hits the iteration limit.

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| LLM | Ollama / `dolphin-llama3` | Local AI reasoning engine |
| Agent Framework | LangChain (ReAct) | Orchestrates the think-act loop |
| Target App | OWASP Juice Shop | Intentionally vulnerable web app |
| Containerization | Docker + Compose | Isolated, reproducible environment |
| Language | Python 3 | Agent runtime |

---

## Architecture

The system is composed of three containers, all sharing a private Docker network called `lab-net`.

```
┌─────────────────────────────────────────────────────────────────────┐
│                       lab-net                                       │
│                                                                     │
│  ┌──────────────┐     prompts/decisions     ┌────────────────────┐  │
│  │  my-agent    │ ────────────────────────► │  ollama-brain      │  │
│  │  (Python)    │ ◄──────────────────────── │  :11434            │  │
│  │              │                           └────────────────────┘  │
│  │              │     HTTP scans                                    │
│  │              │ ────────────────────────► ┌────────────────────┐  │
│  │              │ ◄──────────────────────── │  juice-shop        │  │
│  └──────────────┘                           │  :3000             │  │
│                                             └────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### Container Roles

#### 🧠 `ollama-brain` — The AI Brain
- **Image:** `ollama/ollama:latest` | **Port:** `11434`
- Runs a local LLM server hosting the `dolphin-llama3` model
- Exposes an OpenAI-compatible HTTP API that the agent calls to get reasoning decisions
- Downloaded models are persisted in a named Docker volume (`ollama_storage`) so they survive container restarts

#### 🎯 `juice-shop` — The Target
- **Image:** `bkimminich/juice-shop` | **Port:** `3000`
- OWASP Juice Shop is an intentionally vulnerable Node.js web app used industry-wide for security training
- Passive target — it simply runs and waits to be scanned. Using it keeps all activity legal and contained

#### 🤖 `my-agent` — The Hands
- **Image:** Built from local `Dockerfile` | **Port:** None (outbound only)
- The Python agent that drives the ReAct loop
- Calls Ollama for decisions, executes security tools, collects observations, and feeds them back into the next reasoning cycle

---

## Networking

All containers communicate via Docker's internal DNS — service names resolve as hostnames automatically. No IP addresses are hardcoded.

| From | To | Address | Purpose |
|------|----|---------|---------|
| `my-agent` | `ollama-brain` | `http://ollama-service:11434` | Send prompts, receive tool decisions |
| `my-agent` | `juice-shop` | `http://juice-shop:3000` | Probe the target application |
| Host machine | `ollama-brain` | `http://localhost:11434` | Optional: manual Ollama API access |
| Host machine | `juice-shop` | `http://localhost:3000` | Optional: browse the target in a browser |

> **Note:** The network is declared as `external: true` in `docker-compose.yml`, so it must be created manually before running Compose:
> ```bash
> docker network create lab-net
> ```

---

## Data Flow

The agent runs a loop until it produces a `Final Answer` or hits the 5-iteration limit:

```
1. main.py        → Agent receives the security task prompt
2. LangChain      → Full prompt is sent to Ollama
3. ollama-brain   → LLM responds with: Thought / Action / Action Input
4. LangChain      → Maps Action name to a Python tool function
5. tools.py       → Tool runs (e.g. HTTP GET to juice-shop, captures headers)
6. LangChain      → Tool output appended to prompt as an Observation
7. LangChain      → Updated prompt sent back to Ollama for next step
8. (loop)         → Repeats from step 3 until LLM outputs "Final Answer"
9. main.py        → Final Answer printed to container log
```

---

## File Reference

### `docker-compose.yml`
Defines and wires all three services. Key decisions:
- **`depends_on`** — Ensures Ollama and Juice Shop start before the agent. Does not wait for readiness (no healthcheck configured).
- **`OLLAMA_HOST` env var** — Injected into the agent container so it knows the Ollama address without hardcoding.
- **`external: true` on `lab-net`** — Compose won't create or destroy this network; you manage it manually.
- **`ollama_storage` volume** — Named volume that persists downloaded models across restarts.

---

### `main.py`
The agent's orchestration layer. Responsible for:
1. Connecting to Ollama via LangChain's `Ollama` wrapper
2. Registering tools so the LLM knows what actions it can take
3. Defining the ReAct prompt template (`Thought → Action → Observation → Final Answer`)
4. Running the agent with a `max_iterations=5` hard cap to prevent infinite loops

The `IMPORTANT RULES` block inside the prompt is deliberate prompt engineering — it prevents the LLM from retrying tools that already returned empty results, which would otherwise waste all 5 iterations.

---

### `tools.py`
Contains the two executable tools the LLM can invoke. The `@tool` decorator makes them visible to LangChain — it reads the docstring as the tool description, which the LLM uses to decide when to call each one.

#### `check_web_headers(url)`
Makes an HTTP GET to the target and filters response headers for security-relevant fields:
`Server`, `X-Powered-By`, `Content-Security-Policy`. Returns a dict string or a "not found" message.
> `verify=False` skips SSL validation — fine for a local lab, not for production.

#### `run_subfinder(domain)`
Runs the `subfinder` CLI binary for subdomain enumeration. Currently **stubbed** — logic is incomplete. Guards against running if the binary isn't installed.
> ⚠️ Only works on bare domains (e.g. `example.com`), not URLs with ports like `:3000`.

---

### `requirements.txt`

| Package | Version | Purpose |
|---------|---------|---------|
| `langchain` | 0.1.0 | Core agent framework |
| `langchain-community` | 0.0.12 | Ollama integration and community tools |
| `langchainhub` | 0.1.14 | Prompt template hub (partially used) |
| `requests` | 2.31.0 | HTTP client for `check_web_headers` |
| `pydantic` | 2.5.3 | Data validation (LangChain dependency) |

> ⚠️ `langchain==0.1.0` is an early 2024 release. The API has changed significantly — upgrade carefully.

---

### `Dockerfile`
Builds the `my-agent` container from the project root. Installs Python requirements and sets `main.py` as the entrypoint. Referenced by `docker-compose.yml` via `build: .`

---

## Setup & Running

### Prerequisites
- Docker and Docker Compose installed
- `dolphin-llama3` model available in Ollama

### Steps

**1. Create the shared network**
```bash
docker network create lab-net
```

**2. Start all services**
```bash
docker compose up --build
```

**3. Pull the LLM model (first time only)**
```bash
docker exec ollama-brain ollama pull dolphin-llama3
```

**4. Watch the agent reason in real time**
```bash
docker logs -f my-agent
```

---

## Known Limitations

| Issue | Detail |
|-------|--------|
| No healthcheck on `depends_on` | If Ollama takes time to load the model, the agent may fail on first run. Add a retry or sleep if needed. |
| `run_subfinder` is incomplete | Tool logic is stubbed. `subfinder` also needs to be installed inside the `Dockerfile`. |
| Old LangChain version | `v0.1.0` is pinned for stability but is far behind current. Upgrade carefully. |
| `verify=False` in headers tool | Disables SSL verification. Fine for local lab, not for production. |
| `max_iterations=5` | Hard safety cap. Increase it if you add more tools or complex multi-step tasks. |

---

*Internal use — security lab environment only.*
