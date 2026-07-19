# Argus Security Framework

Argus is a professional-grade security analysis system and autonomous AI agent
studio, bridging Windows accessibility with Kali Linux's offensive power.

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
+-- config/                         # config.yaml, requirements.txt, requirements-dev.txt
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
