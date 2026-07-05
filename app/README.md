app/ — Application code for Argus Security Framework

Structure
- core/: Agent orchestration, LLM factory, prompts, schemas, and memory service (SQLite KG).
- tools/: Focused service classes (recon, scanners, payloads, command runner, etc.).
- GUI/: Streamlit UI and launchers.
- modules/: Standalone exploit/reasoning scripts (executable via Python).

How to use
- See root README.md and docs/Argus_Master_Documentation.md for installation and high-level instructions.
- To run GUI: run app\GUI\Run_Argus_Studio.bat (requires Python environment).

Notes
- Keep app/ as a package. Add per-module README files when adding new modules.