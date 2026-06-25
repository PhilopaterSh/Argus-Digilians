# 🔧 Argus Application Core

This directory contains the main application logic and components for the Argus security framework.

## Directory Structure

### `GUI/`
- **Purpose**: Streamlit web interface for the Argus Studio
- **Entry Point**: `app/GUI/app.py`
- **Port**: 12199 (HTTP) / 12200 (HTTPS)
- **Key Features**:
  - WSL Bridge configuration panel
  - Target URL analysis interface
  - Real-time vulnerability scanning
  - Exploit execution dashboard

### `tools/`
- **Purpose**: Security tools and utilities
- **Main Module**: `tool_registry.py`
- **Facade**: `WSLBridgeTools` class
- **Integrated Services**:
  - Reconnaissance tools (recon/)
  - Port/service scanners (scanners/)
  - Web search and OSINT (web_search/)
  - Exploit modules (exploits/)

### `core/`
- **Purpose**: Core framework functionality
- **Components**:
  - Argus Brain (AI/LLM integration)
  - Tool orchestration
  - Configuration management
  - Logging and reporting

### `modules/`
- **Purpose**: Specialized security modules and plugins
- **Includes**:
  - Deep exploitation scripts
  - WAF bypass techniques
  - Stealth modules
  - Payload generators

## Quick Start

### Launch Streamlit UI
```bash
cd path\to\remote_Argus_PhilopaterSh
LAUNCH_STUDIO.bat C
```

### Launch CLI Agent
```bash
cd path\to\remote_Argus_PhilopaterSh
LAUNCH_CLI.bat C
```

## Architecture Notes

- **Package Structure**: All subdirectories have `__init__.py` to function as proper Python packages
- **Import Precedence**: Main project root is inserted at position 0 in `sys.path` for correct relative imports
- **Dependencies**: See `Argus_Master_Documentation.md` for full dependency list

## Important Files

| File | Purpose |
|------|---------|
| `app.py` | Streamlit UI entry point |
| `tool_registry.py` | Central tool facade and orchestration |
| `__init__.py` | Package initialization (all subdirs) |

## Troubleshooting

### ModuleNotFoundError: 'app' is not a package
- **Cause**: Missing `__init__.py` files
- **Solution**: Ensure all subdirectories contain `__init__.py`

### Import path resolution issues
- **Cause**: Incorrect `sys.path` configuration
- **Solution**: Check that main project root is inserted at position 0

### AttributeError: WSLBridgeTools has no attribute...
- **Cause**: Tool method doesn't exist in registry
- **Solution**: Verify method exists in `tool_registry.py` before calling
