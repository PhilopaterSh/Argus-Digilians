# Argus Security Framework

Argus is a professional-grade security analysis system and autonomous AI agent
studio, bridging Windows accessibility with Kali Linux's offensive power.

> **ABSTRACT** — Argus is a single-agent AI system for automated discovery and
> verification of web application vulnerabilities, organized around the OWASP
> Top 10 and designed to replace signature-based scanning with evidence-driven
> reasoning. The agent couples a locally hosted large language model (via
> Ollama — no cloud dependency) with a LangGraph/ReAct control loop that plans,
> executes, and interprets a modular tool suite: reconnaissance and subdomain
> enumeration; a breadth-first crawler that harvests concrete
> `(endpoint, parameter)` injection points rather than raw URL lists; a
> dedicated path-traversal scanner sweeping a depth × encoding matrix drawn
> from a curated payload database of 4,400+ entries; SQL-injection, XSS, and
> WAF-evasion probes; and sensitive-file fuzzing. Findings are accepted only
> when confirmed by response *content* — such as the actual bytes of
> `/etc/passwd` or `win.ini` — never by HTTP status alone, suppressing false
> positives at the architectural level; every confirmation is captured as
> repeatable Proof-of-Concept evidence, including headless-browser screenshots.
> A persistent blackboard memory isolates concurrent scans and grounds
> decisions in prior evidence, while a retrieval-augmented layer — a FAISS
> vector index over a 1,040-scenario exploitation playbook — injects curated
> attack knowledge into reasoning. Reflective command verification,
> self-healing recovery, and deterministic safety guardrails bound agent
> behavior end-to-end. The system is validated by benchmark fixtures modeled
> on PortSwigger's training labs, 550+ automated tests, and seven enforced
> code-quality gates, offering a reproducible, on-premises foundation for
> trustworthy AI-driven penetration testing.

```mermaid
graph TB
    User((Security Researcher))

    subgraph Argus["Argus Security Framework"]
        GUI[GUI Layer<br/>Streamlit / Tkinter / Studio]
        Brain[ArgusBrain<br/>ReAct / SimpleChain]
        RAG[RAG Engine<br/>FAISS + nomic-embed-text]
        KB[(Knowledge Base<br/>.md .json .csv .pdf)]
        Mem[ArgusMemory<br/>SQLite Blackboard]
        Modules[Tactical Modules<br/>apps/modules/]
        Tools[Tool Registry<br/>17 Services]
    end

    subgraph External["External Systems"]
        LLM[Ollama LLM<br/>WhiteRabbitNeo V3 7B]
        Kali[Kali Linux WSL<br/>SSH / Subprocess]
        Target[Target Infrastructure]
    end

    User -->|Launches| GUI
    GUI -->|Queries| Brain

    Brain -->|1 - Refresh| Mem
    Brain -->|2 - Enrich| RAG
    RAG -->|3 - Similarity| KB
    RAG -->|4 - Pull State| Mem

    Brain -->|5 - Prompt| LLM
    LLM -->|Reasoning| Brain

    Brain -->|6 - Strategy| Modules
    Modules -->|7 - Invoke| Tools
    Tools -->|8 - Execute| Kali
    Kali -->|9 - Scan| Target

    Target -->|Results| Kali
    Kali -->|stdout| Tools
    Tools -->|Persist| Mem
    Mem -->|Update| Brain
```

---

## Quick Start

### 1. Install (First Time Only)

Run the **Single-Click Installer** to set up WSL2, Kali Linux, Python, Ollama,
AI models, and all security tools in one go.

**File:** `INSTALL.bat` (at the project root)

The installer will auto-elevate to Administrator and write a log to
`logs\argus_install_<timestamp>.log`.

A system reboot may be required after WSL2 features are enabled.

### 2. Launch the Studio (Daily Use)

**File:** `scripts\LAUNCH_STUDIO.bat`

Starts the AI engine, activates the SSH bridge, and opens your browser at
`http://localhost:12199`.

---

## System Diagnostics

The installer runs an embedded health check automatically at the end of every
install. To verify the system manually at any time:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts\ARGUS_INSTALLER.ps1 -SkipHealthCheck:$false
```

The health check verifies: Argus_venv, Ollama, Kali (WSL), and SSH bridge (port 22).

---

## Project Structure

```text
Argus-Digilians/
+-- INSTALL.bat                     # Single-click master installer (launcher)
+-- scripts/
|   +-- ARGUS_INSTALLER.ps1         # Unified self-elevating installer (single source of truth)
|   +-- LAUNCH_STUDIO.bat            # Streamlit web UI launcher
|   +-- LAUNCH_CLI.bat               # CLI agent launcher
|   +-- run_argus_cli.py             # CLI entry point
|   +-- README.md                   # Scripts usage guide
|
+-- config/                         # config.yaml, requirements.txt, requirements-dev.txt, requirements-graphify.txt (optional)
+-- app/                            # Main application
|   +-- GUI/                        # Streamlit web UI
|   +-- core/                       # AI brain, config, agent, memory, RAG
|   +-- tools/                      # Security tool modules
|   +-- modules/                    # Specialized exploit scripts
|
+-- specs/                          # Spec-kit feature specs (spec/plan/tasks per feature)
+-- docs/                           # Technical documentation
+-- tests/                          # Test suites
+-- data/                           # Data & databases
+-- logs/                           # Installer & runtime logs
```

---

## Key Features

- **Parallel Reconnaissance:** Executes multiple tools (WhatWeb, Wafw00f, Nikto, etc.)
  simultaneously for maximum speed.
- **AI Intelligence:** Integrated with WhiteRabbitNeo for advanced security reasoning.
- **WSL Bridge:** Securely executes offensive tools inside a native Linux environment
  via SSH (port 22).
- **Report Export:** Download comprehensive security reports in Markdown format.

---

## Installation Modes

The master installer (`scripts\ARGUS_INSTALLER.ps1`) supports `-DryRun`, `-Offline`,
`-Interactive`, and `-SkipHealthCheck` (also reachable via `INSTALL.bat dryrun`/`offline`/etc.) -
see [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) for the full mode reference and parameters.

---

## Documentation

This README is a quick start, not the full picture. For anything beyond it:

| Need | Start here |
|------|------------|
| Full documentation index, canonical/governance docs, audience-specific reading paths | [docs/README.md](docs/README.md) |
| Detailed installation reference (all modes, prerequisites, troubleshooting) | [INSTALLATION_GUIDE.md](INSTALLATION_GUIDE.md) |
| "Which script do I run?" - every script in `scripts/`, what it's for | [scripts/README.md](scripts/README.md) |
| Feature/spec implementation status across all phases | [specs/checklist.md](specs/checklist.md) |
| Manual/offline setup reference (what the installer automates, step by step) | [docs/Argus_Master_Documentation.md](docs/Argus_Master_Documentation.md) |
| Contributing (fork/branch/test/PR workflow) | [CONTRIBUTING.md](CONTRIBUTING.md) |

---

*Maintained by: Argus Security Framework Team | June 2026*

## License

Distributed under the [Apache License 2.0](LICENSE). Vulnerability-scanning tooling is provided for authorized security testing and education only.
