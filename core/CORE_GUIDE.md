# Argus Core Module: Technical Documentation

This directory represents the "heart" of the **Argus Security Framework**. It contains the AI decision-making logic and the technical bridge between the Windows host and the Kali Linux (WSL) environment.

---

## 1. Argus AI Agent (`agent.py`)

This file contains the `ArgusBrain` class, which is responsible for managing the system's intelligence and decision-making processes.

### Key Components:
- **LLM Integration:** Utilizes the `langchain_ollama` library to interface with Large Language Models (e.g., Llama 3) as the primary security analyst.
- **ReAct Agent:** Implements the "Reasoning & Acting" methodology. The AI thinks about the next logical step, invokes the appropriate tool, and analyzes the observation.
- **Operational Rules:** Follows strict penetration testing protocols:
  1. **Connectivity:** Verify target status.
  2. **Attack Surface Mapping:** Subdomain enumeration.
  3. **Deep Discovery:** Full recon suite execution.
  4. **Analysis:** Synthesis of findings into a final security report.

---

## 2. WSL Bridge & Security Engines (`tools.py`)

This file acts as the "Technical Bridge." The `WSLBridgeTools` class is responsible for translating AI decisions into real actions inside the Kali Linux environment.

### Key Components:
- **WSL Native Execution:** Executes commands directly within WSL using `bash -c` for maximum performance.
- **SSH Fallback & Self-Healing:** Includes a redundant SSH communication system with the ability to automatically start the service if it's inactive.
- **Native Recon Engine Integration:** Calls the high-performance `argus_recon` engine located at `/usr/local/bin/argus_recon` inside Kali.

### Core Functional Engines:
- **`enumerate_subdomains`:** A high-speed discovery engine that orchestrates the 5-phase pipeline (Passive, Active, Permutation, Validation, Introspection).
- **`recon_suite`:** Executes parallel tasks for WAF detection, technology fingerprinting, and port scanning.
- **`_clean_ansi_codes`:** A critical utility that strips terminal escape codes and formatting from Linux output to ensure clean presentation in the GUI.

---

## 3. Module Integration

The two files work in harmony: `agent.py` determines **what** to do (Strategy), while `tools.py` determines **how** to do it (Execution).

### Data Workflow:
1. **Agent** receives the user query.
2. **Agent** identifies the need for target information.
3. **Agent** requests **Tools** to execute a specific scan (e.g., Subdomain Enumeration).
4. **Tools** executes the command inside Kali natively and returns cleaned text.
5. **Agent** analyzes the results and synthesizes the final comprehensive security report.
