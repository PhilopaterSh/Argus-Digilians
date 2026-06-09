# Architecture Documentation: Argus Security Framework (arc42 & C4)

This document provides a detailed technical overview of the Argus Security Framework architecture, structured according to the **arc42** template and visualized using the **C4 Model** concepts.

---

## 1. Introduction and Goals

Argus is an autonomous AI-driven security reasoning engine that bridges the gap between high-level AI logic and low-level offensive security tools.

### 1.1 Goals
*   **Autonomy:** Minimize human intervention in reconnaissance and initial vulnerability discovery.
*   **Cross-Platform Integration:** Seamlessly bridge Windows (AI/GUI) and Kali Linux (Security Tools).
*   **Extensibility:** Allow easy addition of new tools and AI models.
*   **Persistence:** Maintain a "Shared Blackboard" of intelligence across sessions.

---

## 2. Architecture Constraints
*   **Local Execution:** Must run locally (via Ollama) to ensure data privacy during pentesting.
*   **WSL Dependency:** Requires Windows Subsystem for Linux (Kali) for security tool access.
*   **Environment Isolation:** Python logic must reside in `Argus_venv`.

---

## 3. Context and Scope (C4 Level 1: System Context)

```mermaid
graph TD
    User((Security Researcher)) -->|Interacts with| Argus[Argus Framework]
    Argus -->|Queries| Ollama[Ollama LLM Engine]
    Argus -->|Executes Commands| Kali[Kali Linux WSL]
    Kali -->|Scans| Target[Target Infrastructure]
    Argus -->|Stores Data| SQLite[(Argus Memory DB)]
```

---

## 4. Solution Strategy
*   **Hybrid Language Model:** Using LangChain for reasoning (Brain) and Python Subprocess/SSH for execution (Body).
*   **Containerized Tooling:** Leveraging WSL as a "Tool Container" to avoid polluting the host OS.
*   **Graph-Based Memory:** Using SQLite to store not just raw text, but relationships (entities and relations).

---

## 5. Building Block View (C4 Level 2: Containers)

### 5.1 System Building Blocks
*   **Argus GUI (Streamlit):** The frontend providing a real-time view of the agent's "Thought" process.
*   **Argus Brain (core/agent.py):** The ReAct (Reasoning and Acting) controller.
*   **WSL Bridge (core/tools.py):** The execution layer that handles WSL/SSH communication.
*   **Argus Memory (core/memory.py):** The persistence layer (SQLite).

---

## 6. Runtime View (C4 Level 3: Components)

### 6.1 Reconnaissance Workflow
1.  **Input:** User provides a URL.
2.  **Reasoning:** `ArgusBrain` analyzes the task and selects `Check_Reachability`.
3.  **Bridge:** `WSLBridgeTools` sends a ping/curl command to Kali.
4.  **Action:** Kali executes the command and returns output.
5.  **Perception:** `ArgusBrain` reads the output, updates `ArgusMemory`, and decides on the next step (e.g., `Subdomain_Enumeration`).

---

## 7. Deployment View (C4 Level 4: Code/Infrastructure)

*   **Host OS:** Windows 10/11.
*   **AI Engine:** Ollama (Localhost:11434).
*   **Environment:** `Argus_venv` (Python 3.12).
*   **Virtualization:** WSL 2 (Distro: kali-linux).
*   **Bridge:** Local SSH (Port 22) or `wsl.exe` direct execution.

---

## 8. Cross-Cutting Concepts
*   **Security:** API keys and credentials managed via `.env`.
*   **Error Handling:** "Guided Reflection" - the system detects missing tools and suggests installation commands.
*   **Persistence:** SQLite database (`argus_intelligence.db`) with relational mapping for Knowledge Graph visualization.

---

## 9. Architecture Decisions (ADR)
*   **ADR 1: Why SQLite?** Chosen for simplicity and zero-configuration, while supporting relational data needed for the Knowledge Graph.
*   **ADR 2: Why WSL?** Provides a native Linux environment for industry-standard security tools while remaining accessible from Windows.
*   **ADR 3: Why LangChain ReAct?** Standardizes how the AI interacts with tools, allowing for complex multi-step reasoning.

---
*Created by Argus Security Framework Team - June 2026*
