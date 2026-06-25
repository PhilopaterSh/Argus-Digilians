# 🛠️ Scripts & Automation

This directory contains all launch scripts, installers, and automation tools for the Argus framework.

## Launch Scripts

### `LAUNCH_STUDIO.bat`
- **Purpose**: Start the Streamlit web UI (Argus Studio)
- **Syntax**: `LAUNCH_STUDIO.bat [option]`
- **Options**:
  - `A`: Run with default Streamlit settings
  - `B`: Run with performance optimizations
  - `C`: Run with GPU support (if available) / CPU-only fallback
- **Default Port**: 12199

**Example**:
```batch
LAUNCH_STUDIO.bat C
```

### `LAUNCH_CLI.bat`
- **Purpose**: Start the autonomous CLI agent
- **Syntax**: `LAUNCH_CLI.bat [option]`
- **Options**:
  - `A`: Standard CLI mode
  - `B`: Debug mode (verbose output)
  - `C`: Enhanced mode (full features)
- **Entry Point**: `run_argus_cli.py` (in project root)

**Example**:
```batch
LAUNCH_CLI.bat C
```

## Installation Scripts

### `INSTALL_EVERYTHING.ps1`
- **Purpose**: Master installer orchestrating all setup steps
- **Execution**:
  ```powershell
  .\INSTALL_EVERYTHING.ps1
  ```
- **Steps Performed**:
  1. **Step 1**: Host environment setup (Windows, WSL2, dependencies)
  2. **Step 2**: Python virtual environment and AI dependencies
  3. **Step 3**: Kali Linux tools installation and configuration

**Path Resolution**:
- Searches: `root\Setup\` → `scripts\Setup\` → relative paths
- Automatically adapts to different installation scenarios

### Individual Setup Steps
Located in `Setup/` directory (root level):
- `Step_1_Host_Setup.bat` - Environment and system dependencies
- `Step_2_Python_AI.bat` - Python venv and AI packages
- `Step_3_Kali_Tools.bat` - Kali Linux integration

## Helper Scripts

### `Check_Requirements.ps1`
- Validates system requirements before installation
- Checks for: Python, WSL2, Kali, Ollama, SSH bridge

### `Initialize_Folders.bat`
- Creates required directory structure
- Sets up proper folder permissions

## Directory Structure

```
scripts/
├── LAUNCH_CLI.bat              # CLI launcher
├── LAUNCH_STUDIO.bat           # Streamlit launcher
├── INSTALL_EVERYTHING.ps1      # Master installer
├── Check_Requirements.ps1      # Pre-flight checks
├── Initialize_Folders.bat      # Folder setup
├── Setup/                       # (Deleted - now in root Setup/ only)
└── README.md                    # This file
```

## Important Notes

- **Working Directory**: Scripts should be run from `scripts/` directory
- **Elevation**: Installation scripts require admin/elevated privileges
- **Path Resolution**: All scripts use relative paths that adapt to project structure
- **Deduplication**: `scripts/Setup/` has been removed - use `root/Setup/` as single source

## Troubleshooting

### Script Not Found
- **Cause**: Script executed from wrong directory
- **Solution**: Run from `scripts/` directory or use full path

### Permission Denied
- **Cause**: Script requires admin privileges
- **Solution**: Right-click → "Run as administrator" or use `powershell -NoProfile -ExecutionPolicy Bypass`

### ModuleNotFoundError in CLI
- **Cause**: Python path not set correctly
- **Solution**: Ensure `run_argus_cli.py` is in project root, scripts are in project root/scripts/

## Performance Tips

- Use `LAUNCH_STUDIO.bat C` for optimal performance (auto-selects GPU or CPU mode)
- Run `Check_Requirements.ps1` before first launch to identify issues early
- Keep `Argus_venv/` in project root only (no duplication)
