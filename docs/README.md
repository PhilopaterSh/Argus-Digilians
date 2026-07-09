# Documentation & Architecture

This directory contains comprehensive documentation, architecture diagrams, and technical references for the Argus security framework.

## Canonical & Governance Documents (start here)

These are the authoritative sources of truth. When any other document disagrees, these win.

| Document | Role |
|----------|------|
| [`ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`](ARGUS_FRAMEWORK_ARCHITECTURE_v2.md) | Canonical architecture (arc42 + C4) and all ADRs (1-16) |
| [`../specs/012-spec-reconciliation/`](../specs/012-spec-reconciliation/) | Canonical cross-cutting decisions (naming, ports, RAG embedding, agent design, testing, CI/CD) |
| [`ARCHITECTURE_AUDIT_REPORT.md`](ARCHITECTURE_AUDIT_REPORT.md) | Repository audit, duplication analysis, and the Cleanup Manifest (C1-C7) |
| [`ARGUS_SPECKIT_ARCHITECTURE_REVIEW.md`](ARGUS_SPECKIT_ARCHITECTURE_REVIEW.md) | Point-in-time architecture review (pre-consolidation baseline) |
| [`../.specify/memory/constitution.md`](../.specify/memory/constitution.md) | Project governance and coding/process principles (supersedes the removed `GEMINI.md`) |
| [`../scripts/README.md`](../scripts/README.md) | Repository structure and script/entry-point overview |
| [`ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md`](ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md) | Archived pre-RAG architecture (historical) |

Automation and validation: `scripts/validate_specs.py`, `scripts/validate_ascii.py`,
`scripts/consolidate_canonical.sh`, and the CI pipeline `.github/workflows/ci.yml`.

## Documentation Files

### `Argus_Master_Documentation.md`
**Main Reference**: Complete technical documentation
- System architecture and design
- Hardware requirements and optimization
- WSL2 and Kali setup procedures
- Python environment configuration
- Ollama AI model setup
- SSH bridge configuration
- Troubleshooting guide

### `ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`
**Architecture Documentation**: Formal system architecture (arc42 + C4 format)
- System overview and context
- Solution strategy
- Building block view
- Runtime view
- Deployment view
- Cross-cutting concepts (ADRs 1-16)

## Project Standards

### `.specify/memory/constitution.md`
**Project Standards & Guidelines** (governance document, amendment-tracked):
- Code style and duplication requirements
- Testing and truthful-runtime requirements
- Documentation requirements
- Git commit discipline
- Security considerations

## Quick References

### System Architecture
```
┌─────────────────────────────────────────┐
│   Windows Host (AI_PenTest_Project)     │
├─────────────────────────────────────────┤
│  ├─ Streamlit Studio (Port 12199)       │
│  ├─ CLI Agent (run_argus_cli.py)        │
│  ├─ ArgusBrain (LLM: WhiteRabbitNeo)    │
│  ├─ Tool Registry (Local Tools)         │
│  └─ SSH Bridge to WSL Kali              │
├─────────────────────────────────────────┤
│   WSL2 (Ubuntu)                         │
│  ├─ SSH Server (Port 22)                │
│  └─ Kali Container/Distro               │
├─────────────────────────────────────────┤
│   Kali Linux (WSL / Docker)             │
│  ├─ Reconnaissance Tools (nmap, etc.)   │
│  ├─ Scanners (Burp, ZAP, etc.)         │
│  ├─ Exploit Framework (Metasploit)      │
│  └─ Web Tools (sqlmap, nikto, etc.)     │
└─────────────────────────────────────────┘
```

### Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Language** | Python | 3.12 |
| **UI Framework** | Streamlit | Latest |
| **AI/LLM** | WhiteRabbitNeo | V3-7B |
| **Tool Orchestration** | LangChain | 0.1+ |
| **Security Tools** | Kali Linux | Rolling |
| **Virtualization** | WSL2 | Windows Subsystem for Linux |
| **Bridge/SSH** | Paramiko | 3.x |

## Documentation Structure

```
docs/
├── README.md                                   # This file (documentation index)
├── ARGUS_FRAMEWORK_ARCHITECTURE_v2.md          # Canonical architecture (arc42 + C4) + ADRs 1-16
├── ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md # Archived pre-RAG architecture
├── ARCHITECTURE_AUDIT_REPORT.md                # Repository audit + Cleanup Manifest
├── ARGUS_SPECKIT_ARCHITECTURE_REVIEW.md        # Pre-consolidation review baseline
├── Argus_Master_Documentation.md               # Main technical reference
├── Multi_Agent_Pentest_Architectures.md        # Background research
├── Information_Disclosure_Notes.md             # Findings notes
└── history/                                    # Superseded docs, retained not deleted (Constitution VII)
```

> Canonical cross-cutting decisions live in [`../specs/012-spec-reconciliation/`](../specs/012-spec-reconciliation/), not in this directory.
> Project governance and coding standards live in [`../.specify/memory/constitution.md`](../.specify/memory/constitution.md).

## How to Use This Documentation

### For New Users
1. Start: `../README.md` in the project root (quick start)
2. Setup: `../INSTALLATION_GUIDE.md`, then `Argus_Master_Documentation.md` for the manual steps it automates
3. Launch: `scripts\LAUNCH_STUDIO.bat`

### For Developers
1. Review: `../.specify/memory/constitution.md` (coding/process standards)
2. Understand: `ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` (system design, arc42 + C4)
3. Code: `../scripts/README.md` for entry points, `../app/README.md` for component details

### For System Administrators
1. Infrastructure: `Argus_Master_Documentation.md`
2. Troubleshooting: `Argus_Master_Documentation.md` (Operation and Troubleshooting section)

## Key Concepts

### WSL Bridge Architecture
- **Purpose**: Execute Kali/Linux tools from Windows Streamlit UI
- **Mechanism**: SSH tunnel over localhost
- **Security**: Key-based authentication (no passwords over network)
- **Performance**: Local network (WSL2 on same machine = fast)

### ArgusBrain Integration
- **Model**: config-driven (`config.yaml`'s `model_name`; currently a WhiteRabbitNeo-V3-7B build), not hardcoded
- **Interface**: LangChain Tool use via a structured-output-first ReAct graph (`app/core/agent/react_workflow.py`)
- **Context**: Receives target info, tool results, historical (Blackboard) context
- **Output**: Formatted analysis and recommendations (`app.core.schemas.SecurityReport`)

### Tool Registry Pattern
- **Purpose**: Centralized facade for all security tools
- **Implementation**: `WSLBridgeTools` class in `app/tools/tool_registry.py`
- **Extensibility**: Add new tools without modifying core UI
- **Integration**: Tools can be local (Windows) or remote (Kali/WSL)
