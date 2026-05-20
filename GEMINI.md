# Project Instructions: Argus Security Framework

## 🌐 Language & Documentation Standard
- **Primary Language:** All documentation, technical reports, development logs, and code comments MUST be written in **English**.
- **Tone:** Professional, technical, and concise.

## 📁 Project Structure & Naming
- **Centralized Setup:** All installation resources and sub-scripts MUST be located within the `Setup/` directory.
- **Master Documentation:** The `Argus_Master_Documentation.md` in the root is the definitive technical reference.
- **Root Utilities:** Maintain only core operational utilities (`INSTALL_EVERYTHING.bat`, `LAUNCH_STUDIO.bat`, `CHECK_HEALTH.bat`) in the root directory for a clean workspace.

## 🛠️ Development Workflow
- **Master Installer:** Keep `INSTALL_EVERYTHING.bat` updated to reflect any changes in the `Setup/` internal scripts.
- **Cross-Platform Bridge:** Maintain clear logic separation between Windows Host (Batch) and Kali Guest (Bash) within the `Setup/` environment.
