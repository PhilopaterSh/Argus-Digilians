# Project Instructions: Argus Security Framework

## 🌐 Language & Documentation Standard
- **Primary Language:** All documentation, technical reports, development logs, and code comments MUST be written in **English**.
- **Tone:** Professional, technical, and concise.

## 📁 Project Structure & Naming
- **Application Logic (`app/`):** All core application code, including `core/` (brain, memory, schemas) and `tools/` (modularized tool services).
- **Specialized Modules (`app/modules/`):** Advanced exploit and reasoning scripts.
- **Centralized Setup:** All installation resources and sub-scripts MUST be located within the `Setup/` directory.
- **Master Documentation:** The `Argus_Master_Documentation.md` in the root is the definitive technical reference.
- **Operational Scripts:** Maintain core utilities (`scripts/CHECK_HEALTH.bat`, `scripts/LAUNCH_STUDIO.bat`, etc.) in the `scripts/` directory for a clean workspace.

## 🛠️ Development Workflow
- **Master Installer:** Keep `INSTALL_EVERYTHING.bat` updated to reflect any changes in the `Setup/` internal scripts.
- **Cross-Platform Bridge:** Maintain clear logic separation between Windows Host (Batch) and Kali Guest (Bash) within the `Setup/` environment.
