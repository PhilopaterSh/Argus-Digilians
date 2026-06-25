# ⚙️ Setup & Installation Pipeline

This directory contains the multi-step installation scripts that configure the complete Argus framework environment.

## Three-Step Installation Process

### ✅ Step 1: Host Environment Setup
**File**: `Step_1_Host_Setup.bat`

Configures the Windows host system:
- Validates Windows 10/11 version
- Enables WSL2 (Windows Subsystem for Linux)
- Installs/updates Ubuntu distro
- Sets up system dependencies
- Configures network settings

### ✅ Step 2: Python & AI Environment
**File**: `Step_2_Python_AI.bat`

Sets up Python virtual environment and AI packages:
- Creates `Argus_venv/` virtual environment
- Installs core Python packages (Python 3.10+)
- Configures LangChain and LLM integration
- Sets up Streamlit and dependencies
- Initializes Ollama connection
- Configures WhiteRabbitNeo model

### ✅ Step 3: Kali Linux Tools Integration
**File**: `Step_3_Kali_Tools.bat`

Integrates Kali Linux security tools:
- Establishes WSL-to-Kali bridge
- Configures SSH connectivity
- Sets up tool discovery
- Initializes specialized exploit modules
- Verifies Kali tool availability
- Tests WSL → Kali command execution

## Installation Modes

### Automatic (Recommended)
```bash
cd scripts/
powershell -NoProfile -ExecutionPolicy Bypass -File ..\INSTALL_EVERYTHING.ps1
```

### Manual (Individual Steps)
```batch
# Step by step (in order)
cd Setup/
Step_1_Host_Setup.bat
Step_2_Python_AI.bat
Step_3_Kali_Tools.bat
```

### Troubleshooting Mode
```bash
Check_Requirements.ps1  # Validate prerequisites
INSTALL_EVERYTHING.ps1  # With error logging
```

## Important Files & Locations

| Step | Script | Creates | Modifies |
|------|--------|---------|----------|
| 1 | `Step_1_Host_Setup.bat` | WSL2, Ubuntu | Windows features, PATH |
| 2 | `Step_2_Python_AI.bat` | `Argus_venv/` | `requirements.txt` deps |
| 3 | `Step_3_Kali_Tools.bat` | SSH keys, configs | WSL config, Kali tools |

## Configuration Files

- `.env` / `.env.example` - Environment variables
- `requirements.txt` - Python package dependencies
- `SSH_CONFIG` - WSL → Kali SSH connection
- `OLLAMA_CONFIG` - Model and API settings

## Path Resolution Strategy

The installer uses intelligent path resolution:

1. **Primary**: `root\Setup\Step_*.bat` ← Preferred location
2. **Secondary**: `scripts\Setup\Step_*.bat` ← Fallback
3. **Relative**: Adapts to project folder depth

This allows installation to work regardless of where scripts are copied.

## System Requirements

**Minimum**:
- Windows 10 (Build 19041+) or Windows 11
- 16GB RAM (24GB+ recommended for full tools)
- 50GB free disk space (for Kali + tools)
- Admin/elevated privileges

**Software**:
- PowerShell 5.1+ (included in Windows)
- WSL2 support (Windows 10 Build 19041+)
- Optional: Docker Desktop (for containerized Kali)

## Verification

After installation, verify each component:

### Host Setup
```batch
wsl --version          # Should show WSL version
wsl -l -v              # Should list Ubuntu as running
```

### Python Environment
```batch
Argus_venv\Scripts\activate.bat
python --version       # Should be 3.10+
pip list | findstr streamlit  # Should find Streamlit
```

### Kali Bridge
```bash
# Inside WSL/Kali
ssh kali@localhost     # Should connect without password (key auth)
```

## Troubleshooting

### WSL2 Not Available
- **Cause**: Windows version too old or WSL feature disabled
- **Solution**: Update Windows, enable WSL2 in "Turn Windows features on/off"

### Python Venv Creation Fails
- **Cause**: Python not installed or in PATH
- **Solution**: Manually install Python 3.10+ from python.org, add to PATH

### Kali Connection Fails
- **Cause**: SSH keys not generated or WSL not running
- **Solution**: Run Step 3 again, verify WSL is active

### Permission Denied Errors
- **Cause**: Scripts running without admin privileges
- **Solution**: Right-click PowerShell/CMD → "Run as administrator"

## Advanced Configuration

### Custom Python Version
Edit `Step_2_Python_AI.bat`:
```batch
set PYTHON_VERSION=3.11  # Change from default 3.10
```

### Custom Kali Distro
Edit `Step_1_Host_Setup.bat`:
```batch
set KALI_DISTRO=kali  # Default: kali-linux
```

### Offline Installation
See `docs/OFFLINE_SETUP.md` for air-gapped network setup.

## Post-Installation

Once setup completes successfully:

1. **Launch Streamlit UI**: `scripts\LAUNCH_STUDIO.bat C`
2. **Launch CLI Agent**: `scripts\LAUNCH_CLI.bat C`
3. **Run Health Check**: `scripts\Check_Requirements.ps1` (verify)
4. **Read Docs**: `Argus_Master_Documentation.md`

## Single-Source Principle

⚠️ **Important**: Only the root `Setup/` directory is the authoritative source.
- `scripts/Setup/` is **deprecated** and has been **deleted**
- All installations now use root `Setup/` only
- This prevents version mismatches and maintenance nightmares
