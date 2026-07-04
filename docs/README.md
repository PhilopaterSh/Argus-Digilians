# 📚 Documentation & Architecture

This directory contains comprehensive documentation, architecture diagrams, and technical references for the Argus security framework.

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

### `arc42.md`
**Architecture Documentation**: Formal system architecture
- System overview and context
- Solution strategy
- Building block view
- Runtime view
- Deployment view
- Cross-cutting concepts

## Project Standards

### `GEMINI.md`
**Project Standards & Guidelines**:
- Code style requirements
- File organization standards
- Directory naming conventions
- Documentation requirements
- Git workflow and commit messages
- Performance benchmarks
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
| **Language** | Python | 3.10+ |
| **UI Framework** | Streamlit | Latest |
| **AI/LLM** | WhiteRabbitNeo | V3-7B |
| **Tool Orchestration** | LangChain | 0.1+ |
| **Security Tools** | Kali Linux | Rolling |
| **Virtualization** | WSL2 | Windows Subsystem for Linux |
| **Bridge/SSH** | Paramiko | 3.x |

## Documentation Structure

```
docs/
├── README.md                              # This file
├── Argus_Master_Documentation.md          # Main technical reference
├── arc42.md                               # Architecture view (ISO/IEC/IEEE 42010)
├── GEMINI.md                              # Project standards & guidelines
├── OFFLINE_SETUP.md                       # Air-gapped installation (if exists)
├── ARCHITECTURE_DIAGRAMS.md               # Visual system design (if exists)
└── API_REFERENCE.md                       # Tool & API documentation (if exists)
```

## How to Use This Documentation

### For New Users
1. Start: `Argus_Master_Documentation.md` (Sections 1-4)
2. Setup: Follow installation steps (Section 5)
3. Quick Start: `README.md` in project root
4. Launch: Use `LAUNCH_STUDIO.bat C` to test

### For Developers
1. Review: `GEMINI.md` (coding standards)
2. Understand: `arc42.md` (system design)
3. Deep Dive: Relevant section in `Argus_Master_Documentation.md`
4. Code: Use `app/README.md` for component details

### For System Administrators
1. Infrastructure: `Argus_Master_Documentation.md` (Section 5)
2. Deployment: `arc42.md` (Deployment View)
3. Troubleshooting: `Argus_Master_Documentation.md` (Section 7)
4. Scaling: See performance optimization tips

## Key Concepts

### WSL Bridge Architecture
- **Purpose**: Execute Kali/Linux tools from Windows Streamlit UI
- **Mechanism**: SSH tunnel over localhost
- **Security**: Key-based authentication (no passwords over network)
- **Performance**: Local network (WSL2 on same machine = fast)

### ArgusBrain Integration
- **Model**: WhiteRabbitNeo (7B parameter, specialized for penetration testing)
- **Interface**: LangChain Tool use
- **Context**: Receives target info, tool results, historical context
- **Output**: Formatted analysis and recommendations

### Tool Registry Pattern
- **Purpose**: Centralized facade for all security tools
- **Implementation**: `WSLBridgeTools` class in `app/tools/tool_registry.py`
- **Extensibility**: Add new tools without modifying core UI
- **Integration**: Tools can be local (Windows) or remote (Kali/WSL)

## Contributing Documentation

When adding new features or capabilities:

1. **Code Documentation**
   - Add inline comments for complex logic
   - Update docstrings with parameters and return values
   - Link to relevant sections in master docs

2. **Technical Documentation**
   - Update `Argus_Master_Documentation.md` with new sections
   - Add diagrams to `arc42.md` if architectural changes
   - Update `GEMINI.md` if adding new standards

3. **User Documentation**
   - Add usage examples to relevant README.md
   - Document new launch options in `scripts/README.md`
   - Update quick-start guides if adding new features

## Standards & Best Practices

Refer to `GEMINI.md` for:
- Code style (PEP 8 for Python)
- Git commit message format
- Branch naming conventions
- Pull request requirements
- Documentation requirements
- Testing requirements

## Version Control

- **Main Branch**: Production-ready code
- **fix/** branches**: Bug fixes and improvements
- **feature/** branches: New capabilities
- **docs/** branches: Documentation updates
- See `GEMINI.md` for complete git workflow

## Support & Troubleshooting

- **Installation Issues**: See `Argus_Master_Documentation.md` Section 7
- **Architecture Questions**: See `arc42.md`
- **Development Standards**: See `GEMINI.md`
- **Tool-Specific Issues**: See component README files (`app/`, `scripts/`)

## Related Documentation

- `README.md` - Project overview and quick start
- `Argus_Master_Documentation.md` - Complete technical reference
- `GEMINI.md` - Development standards and guidelines
- `arc42.md` - System architecture (ISO/IEC standard format)
