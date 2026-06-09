# Argus Core: The Definitive & Ultra-Detailed Technical Manual

This document is the absolute, most comprehensive technical reference for the Argus Core. It covers every line of code, every import, and every architectural decision in extreme detail.

---

## 1. core/agent.py - The Cognitive Orchestrator

This file contains the high-level logic that drives the AI's decision-making process.

### 1.1 Detailed Import Analysis
```python
from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.schemas import SecurityReport
import os
import json
```
- **`from langchain_ollama import OllamaLLM`**: This library is the specific wrapper for the Ollama inference server. It handles the serialization of prompts into HTTP requests and manages the streaming of responses. It is chosen for its native support for local LLMs.
- **`from langchain_classic.agents import AgentExecutor, create_react_agent`**: These are the core orchestration components. `create_react_agent` implements the "Reasoning and Acting" paper's logic, allowing the AI to cycle between thought and action. `AgentExecutor` is the runtime that manages the loop, history, and error handling.
- **`from langchain_core.tools import Tool`**: A wrapper class that standardizes the interface for any function the AI can call. It requires a name and a description, which the AI uses to understand when to use the tool.
- **`from langchain_core.prompts import PromptTemplate`**: A system for managing complex multi-line strings with placeholders. This allows us to inject things like `target` or `format_instructions` dynamically.
- **`from langchain_core.output_parsers import PydanticOutputParser`**: A crucial component that uses Python's reflection capabilities to generate a schema definition for the LLM. It then takes the LLM's raw text response and attempts to parse it into a structured Python object.
- **`from core.schemas import SecurityReport`**: The custom data model that defines what a final security report looks like.
- **`import os, json`**: Standard libraries used for environment variable access (like `OLLAMA_HOST`) and data manipulation.

### 1.2 Class: `ArgusBrain` - The AI Management Hub

#### 1.2.1 Initialization (`__init__`)
```python
class ArgusBrain:
    def __init__(self, model_name, tools_list):
        self.llm = OllamaLLM(
            model=model_name, 
            timeout=3600, 
            temperature=0.1,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
        self.tools = tools_list
        self.output_parser = PydanticOutputParser(pydantic_object=SecurityReport)
        self.agent_executor = self._setup_agent()
```
- **`model_name`**: Passed from the UI/CLI, this determines which model (e.g., WhiteRabbitNeo) is loaded.
- **`timeout=3600`**: This 1-hour timeout is critical. Security tasks like brute-forcing or deep port scanning can take significant time; this prevents the connection from dropping mid-task.
- **`temperature=0.1`**: This low value minimizes "creativity." In security, we need exact, factual reporting. Higher values could lead the AI to invent (hallucinate) vulnerabilities that don't exist.
- **`base_url`**: Fetches the Ollama address from the environment, defaulting to the local machine's port 11434.

#### 1.2.2 Agent Setup (`_setup_agent`)
This method constructs the complex internal logic of the AI.

**The Prompt Template:**
The `template` string is the "Instruction Manual" for the AI. It contains:
- **Persona**: Defines Argus as a "Senior Security Researcher."
- **Operational Rules**: A 6-phase mandatory methodology that enforces professional standards (Connectivity -> Subdomains -> Discovery -> Memory -> Exploitation -> Analysis).
- **Format Instructions**: Dynamically injected instructions telling the AI how to produce the final JSON.
- **ReAct Format**: Defines the `Thought`, `Action`, `Action Input`, `Observation` cycle.

**The Executor Configuration:**
```python
return AgentExecutor(
    agent=agent, 
    tools=self.tools, 
    verbose=True, 
    handle_parsing_errors=True,
    max_iterations=50,
    early_stopping_method="generate"
)
```
- **`verbose=True`**: This causes the AI's internal "Thought" process to be printed to the console, allowing the user to see exactly why it is making certain decisions.
- **`max_iterations=50`**: A safety limit. If the AI gets stuck in a loop calling tools, it will stop after 50 attempts to save resources.
- **`handle_parsing_errors=True`**: If the LLM makes a mistake in its tool-calling format, the executor will send the error message back to the LLM to try and fix it.

#### 1.2.3 Communication Methods
- **`ask(query)`**: The primary entry point. It runs the agent and then uses the `output_parser` to validate the final answer. If validation fails, it provides a raw fallback result.
- **`simple_ask(prompt)`**: A direct line to the LLM. Used for quick analysis tasks where the full agent/tool loop isn't needed (e.g., summarizing a short text).

---

## 2. core/tools.py - The Technical Execution Layer

This file bridges the gap between AI reasoning and real-world security tool execution in Kali Linux.

### 2.1 Detailed Class Analysis: `WSLBridgeTools`

#### 2.1.1 Configuration and Setup
- **`.env` Integration**: Uses `os.getenv` to pull `WSL_HOST`, `WSL_USER`, `WSL_PASS`, and `WSL_DISTRO`. This makes the code portable across different machines.
- **`threading.Lock()`**: This is vital for the multi-agent system. It ensures that if two tools are trying to initialize the environment (like starting SSH) at once, they won't conflict and crash the system.
- **`self.memory = ArgusMemory()`**: Every tool has a direct link to the database, ensuring all discoveries are saved instantly.

#### 2.1.2 Utility: `_clean_ansi_codes`
```python
def _clean_ansi_codes(self, text):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    return ansi_escape.sub('', text)
```
- This regex removes terminal color and bolding codes (e.g., `[31m`). These codes look like gibberish to an AI and would break its ability to understand the text output of tools like Nmap.

#### 2.1.3 The Execution Core (`run`)
- **Direct WSL Path**: Uses `subprocess.run` to call `wsl.exe`. It uses `bash -c` to ensure that any Linux-specific logic or aliases inside the Kali container are correctly handled.
- **SSH Fallback**: If WSL direct fails, it uses `paramiko` to SSH into the Kali environment. This provides a robust "double-layered" connection strategy.
- **Guided Reflection**: If a tool isn't installed, the code identifies the "command not found" error and provides a suggestion like `apt install`. This allows the AI to learn how to fix the environment itself.

#### 2.1.4 Advanced Security Modules
- **`check_reachability`**: A two-tier check using `ping` and then `curl`. It links the domain and IP in the knowledge graph.
- **`fuzz_sensitive_files`**: Uses a `ThreadPoolExecutor` with 5 workers to check for 16 high-value paths (like `.env`, `.git/config`) simultaneously. It uses `curl -I` (Head requests) to check for existence without downloading the whole file, which is much faster.
- **`analyze_secrets`**: A regex-based scanner that looks for:
    - **Emails**: PII discovery.
    - **API Keys**: Generic keys and specific ones like Google, AWS Access Keys, and Firebase URLs.
    - **Knowledge Graph Linkage**: Automatically creates `EXPOSES` relations in the database.
- **`recon_suite`**: The "Master Orchestrator" for tools. It runs `wafw00f`, `whatweb`, and `nmap` in parallel (3 workers) to build a massive intelligence profile of a target in seconds.
- **`suggest_payloads`**: A directory-mapping tool that looks through `/opt/payloads/PayloadsAllTheThings` on the Kali machine. It reads README files to give the AI actual code snippets it can use for testing.

---

## 3. core/memory.py - The Persistence and Graph Layer

This file manages the "State" of the engagement and the Knowledge Graph.

### 3.1 Database Schema Breakdown (`_init_db`)
- **`targets`**: Stores the attack surface (domains, status, priority).
- **`findings`**: The "Blackboard." Stores tool results, summaries, and timestamps.
- **`entities`**: The nodes of the Knowledge Graph (e.g., an IP address, a technology like "Apache").
- **`relations`**: The edges (connections) between nodes (e.g., `Domain A` -> `USES_TECH` -> `Apache`).

### 3.2 Key Logic Methods
- **`upsert_entity`**: Uses a `UNIQUE` constraint on the `value` column. If an entity like `127.0.0.1` is added twice, it updates the metadata instead of creating a duplicate.
- **`add_relation`**: Creates a link between two IDs. It uses `strength` (default 1.0) which can be used to weight how certain we are about a relationship.
- **`get_graph_insights`**: A complex SQL query that joins relations and entities to return a human-readable string like `(example.com) --[PROTECTED_BY]--> (Cloudflare)`. This allows the AI to "see" relationships.
- **`get_blackboard_summary`**: This is the "Context Compressor." It takes every tool output for every target and creates a clean JSON summary. This prevents the AI from becoming overwhelmed by raw data.

---

## 4. core/schemas.py - The Data Structure Layer

This file defines the "language" used between the AI and the system.

### 4.1 `Finding` Class
Each vulnerability must follow this structure:
- **`target`**: The specific domain or IP.
- **`issue`**: The name of the vulnerability (e.g., "SQL Injection").
- **`severity`**: Low, Medium, High, or Critical.
- **`description`**: A deep technical explanation.
- **`suggested_payload`**: A practical example of how to test it.
- **`remediation`**: Exact steps to fix the problem.

### 4.2 `SecurityReport` Class
This is the final product. It includes:
- **`summary`**: An executive overview.
- **`attack_surface_stats`**: Numbers of discovered subdomains/services.
- **`findings`**: A list of the `Finding` objects defined above.
- **`overall_risk_score`**: A number from 1 to 10 (enforced by `ge=1, le=10`).
- **`next_steps`**: A list of recommended future actions.

---

## Logic Interaction Summary

1. **Input**: User asks "Scan target.com" in `agent.py`.
2. **Decision**: `agent.py` decides to use the `Recon_Suite` tool in `tools.py`.
3. **Execution**: `tools.py` starts a multi-threaded scan in Kali Linux via WSL.
4. **Storage**: As `tools.py` gets results, it calls `memory.py` to save them in SQLite and link them in the Knowledge Graph.
5. **Synthesis**: `agent.py` calls `memory.py` to get a summary of all findings.
6. **Output**: `agent.py` uses the structure in `schemas.py` to create a final, validated report.
