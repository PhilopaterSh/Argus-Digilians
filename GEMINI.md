# Project Instructions: Argus Security Framework

## 🌐 Language & Documentation Standard
- **Primary Language:** All documentation, technical reports, development logs, and code comments MUST be written in **English**.
- **Tone:** Professional, technical, and concise.

## 📁 Project Structure & Naming
- Use descriptive, numbered prefixes for installation steps (e.g., `01_Infrastructure_Setup`).
- Maintain a clear separation between Host (Windows) and Guest (WSL/Kali) logic.

## 🛠️ Development Workflow
- **Master Installer:** Always ensure `INSTALL_EVERYTHING.bat` is kept up to date with any changes to sub-scripts.
- **Silent Installation:** Sub-scripts should respect the `ARGUS_AUTO_INSTALL` environment variable to skip manual prompts when called from the master installer.
