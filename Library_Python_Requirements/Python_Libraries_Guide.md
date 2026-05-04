# Argus Security Framework: AI Environment Technical Guide

This document details the Python libraries and intelligence models used in the Argus Security Framework, along with the automated setup procedures.

---

## 1. Tactical Intelligence Core (LLMs)

The framework supports multiple specialized models through Ollama. During setup, you can choose the engine best suited for your current operation:

### WhiteRabbitNeo
- **Focus:** Offensive Security and Penetration Testing (Uncensored).
- **Ollama Path:** `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B`
- **Usage:** Ideal for vulnerability analysis, payload generation, and exploit research. This model is explicitly fine-tuned for cybersecurity tasks and lacks standard AI safety guardrails.

### Dolphin-Llama3
- **Focus:** General Purpose and Uncensored Reasoning.
- **Ollama Path:** `dolphin-llama3`
- **Usage:** Ideal for broad data analysis, coding assistance, and creative problem-solving without strict safety filters.

---

## 2. Advanced Deployment & External Sources

For operations requiring specific quantizations or versions not available in the primary Ollama library, the following sources are recommended:

### Hugging Face (GGUF Format)
If Ollama's automated pull fails or a specific version is needed:
*   **7B (V3 - Latest):** `bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF`
*   **70B (High Reasoning):** `bartowski/Llama-3.1-WhiteRabbitNeo-2-70B-GGUF`
*   **13B (Classic):** `TheBloke/WhiteRabbitNeo-13B-GGUF`

### LM Studio Integration
The framework can be directed to an LM Studio local server for enhanced monitoring:
1. Load the GGUF model in LM Studio.
2. Start the Local Server on port `1234`.
3. Update framework configurations to point to `http://localhost:1234/v1`.

---

## 3. Core Frameworks & Libraries

### LangChain Ecosystem
- **langchain-ollama:** The primary bridge for communication between Python and the Ollama engine.
- **langchain-community:** Provides integration with external tools like search engines and vector databases.
- **langchain-huggingface:** Powers the semantic memory and embedding generation.

### Performance & Storage
- **FAISS-CPU:** High-performance local vector storage for document intelligence.
- **Sentence-Transformers:** Converts security findings into mathematical vectors for semantic search.
- **Streamlit:** Powers the graphical user interface for the AI Multi-Agent Studio.

---

## 3. Automated Setup Procedure (Universal_AI_Setup.bat)

The setup script is designed for zero-touch configuration and high reliability:

### Interactive Selection
Upon execution, the script prompts for a choice between WhiteRabbitNeo and Dolphin-Llama3. This allows you to tailor the environment to your specific mission needs.

### Automated Retry Mechanism (Persistent Download)
To ensure reliability on unstable networks:
- The script checks if the selected model is fully present.
- If the download fails or is interrupted, the script enters a **Retry Loop**, attempting the download again every 5 seconds until success is achieved.

### Environment Isolation
The script automatically manages a Python virtual environment (`.venv`), ensuring that Argus intelligence libraries do not conflict with other system software.

---

## Quick Start Command

To initialize or update your environment, run the following from the root directory:

```powershell
# From Library_Python_Requirements folder
.\Universal_AI_Setup.bat
```

*Note: Ensure Ollama is installed on the host. The script will attempt to start the Ollama engine automatically if it is not running.*

---
Maintained by: Argus Security Framework Team
Last Documentation Update: May 2026
