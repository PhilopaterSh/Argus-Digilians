# Architecture Documentation: Argus Security Framework (arc42 & C4)

This document provides a detailed technical overview of the Argus Security Framework architecture, structured according to the **arc42** template and visualized using the **C4 Model** concepts.

---

## 1. Introduction and Goals

Argus is an autonomous AI-driven security reasoning engine that bridges the gap between high-level AI logic and low-level offensive security tools.

### 1.1 Goals
- **Autonomy:** Minimize human intervention in reconnaissance and initial vulnerability discovery.
- **Self-Healing:** Autonomously detect and resolve missing dependencies or tool failures.
- **Tactical Orchestration:** Empower the AI to manage low-level tools directly via CLI for maximum flexibility.
- **Reflective Verification:** Implement logic-based validation to eliminate false positives and WAF traps.
- **Cross-Platform Integration:** Seamlessly bridge Windows (AI/GUI) and Kali Linux (Security Tools).
- **Persistence:** Maintain a "Shared Blackboard" of intelligence across sessions.
- **RAG-Augmented Reasoning:** Retrieve relevant technical knowledge and prior findings at query time to ground AI decisions.

---

## 2. Architecture Constraints
- **Local Execution:** Must run locally (via Ollama) to ensure data privacy during pentesting.
- **WSL Dependency:** Requires Windows Subsystem for Linux (Kali) for security tool access.
- **Environment Isolation:** Python logic must reside in `Argus_venv`.
- **Vector Store**: Requires FAISS (CPU) for similarity search over embedded knowledge.
- **Embedding Model**: Requires Ollama `nomic-embed-text` or HuggingFace `all-MiniLM-L6-v2` as fallback.

---

## 3. Context and Scope (C4 Level 1: System Context)

### 3.1 High-Level System Context

```mermaid
graph TB
    User((Security Researcher))

    subgraph "Argus Framework"
        Brain[ArgusBrain<br/>app/core/agent.py]
        RAG_Engine[RAG Engine<br/>app/core/rag/]
        Blackboard[ArgusMemory / SQLite<br/>app/core/memory/]
        Modules[Tactical Modules<br/>app/modules/]
        Tools[Tool Registry<br/>app/tools/tool_registry.py]
        GUI_Frontend[GUI Frontend<br/>app/GUI/]
    end

    subgraph "RAG Knowledge Pipeline"
        KB[(knowledge_base/<br/>.md .json .csv .pdf .txt)]
        Embed_Model[nomic-embed-text<br/>Ollama Embeddings]
        VS[(FAISS Vector Store<br/>app/core/rag/store/)]
    end

    subgraph "External"
        LLM[Ollama LLM<br/>localhost:11434<br/>WhiteRabbitNeo V3 7B]
        Kali[Kali Linux WSL<br/>Subprocess / SSH]
        Target[Target Infrastructure]
    end

    %% User & UI Flow
    User -->|Launches / Interacts| GUI_Frontend
    GUI_Frontend -->|Control / Queries| Brain
    Blackboard -.->|Live Sync / Stream Findings| GUI_Frontend

    %% Brain Orchestration Loop
    Brain -->|1 - refresh blackboard| Blackboard
    Blackboard -->|blackboard insights| Brain

    Brain -->|2 - enrich with RAG| RAG_Engine
    RAG_Engine -->|combined context| Brain

    %% RAG Pipeline & Search
    RAG_Engine -->|3 - similarity search| VS
    VS -->|FAISS index from disk| RAG_Engine
    KB -->|Document Processor| Embed_Model
    Embed_Model -->|build FAISS index| VS
    RAG_Engine -->|4 - pull live state| Blackboard

    %% LLM Reasoning
    Brain -->|5 - augmented prompt| LLM
    LLM -->|reasoning + strategy decision| Brain

    %% Execution Loop (Fixed: Brain -> Modules -> Tools)
    Brain -->|6 - activate strategy| Modules
    Modules -->|7 - invoke specific tool| Tools
    Tools -->|8 - execute command| Kali
    Kali -->|9 - scan target| Target

    %% Feedback & Persistence Loop
    Target -->|10 - raw response| Kali
    Kali -->|11 - stdout + files| Tools
    Tools -->|12 - parse & structure results| Blackboard
    Blackboard -->|13 - persist state| Blackboard
```

---

## 4. Solution Strategy
- **Hybrid Language Model:** Using LangChain for reasoning (Brain) and Python Subprocess/SSH for execution (Body).
- **Containerized Tooling:** Leveraging WSL as a "Tool Container" to avoid polluting the host OS.
- **Graph-Based Memory:** Using SQLite to store not just raw text, but relationships (entities and relations).
- **RAG-Based Context Fusion:** Retrieving static technical knowledge (FAISS) and merging it with live target state (Blackboard) before each LLM query.

---

## 5. Building Block View (C4 Level 2: Containers)

### 5.1 Complete System Building Blocks

#### Core Components

| Component | Path | Responsibility |
|-----------|------|----------------|
| **ArgusBrain** | `app/core/brain.py`, `brain_v2.py` | ReAct/SimpleChain controller; triggers `_enrich_with_rag()` then `ask()` |
| **RAG Engine** | `app/core/rag/rag_engine.py` | Orchestrates retrieval + context fusion via `format_combined_context()` |
| **Embedding Factory** | `app/core/rag/embeddings.py` | Singleton: Ollama nomic-embed-text → HuggingFace → OpenAI fallback |
| **Document Processor** | `app/core/rag/document_processor.py` | Structural chunking per file type (see §5.2) |
| **Vector Store** | `app/core/rag/vector_store.py` | FAISS build/persist/load/similarity_search |
| **ArgusMemory** | `app/core/memory/memory_service.py` | SQLite Blackboard with 5 tables (targets, findings, entities, relations, global_state) |
| **Tool Registry** | `app/tools/tool_registry.py` | WSLBridgeTools facade — 12 sub-services |
| **Tactical Modules** | `app/modules/` | High-level attack workflows (deep exploit, stealth, recon) |
| **GUI** | `app/GUI/` | Streamlit (`gui_app.py`), Tkinter (`argus_gui.py`), Studio (`studio.py`) |
| **Knowledge Base** | `knowledge_base/` | Static source files ingested into FAISS |

#### Tool Services (inside `app/tools/`)

| Service | Class | Function |
|---------|-------|----------|
| Recon | `ReconService` | Subdomain enum, WAF detection, tech identification |
| Scanners | `VulnerabilityScanners` | Port scan, vuln scan via nuclei/nmap |
| Crawler | `CrawlerService` | Web crawling, endpoint discovery |
| Command Runner | `CommandRunner` | WSL / SSH command execution |
| WSL Bridge | `WSLBridge` | Low-level WSL subprocess management |
| Evasion | `EvasionService` | Payload obfuscation, WAF bypass |
| Payloads | `PayloadSuggester` | Exploit payload generation |
| Secrets | `SecretAnalyzer` | Secret/key detection in files |
| Self-Heal | `SelfHealingService` | Auto-fix missing deps (pip/apt) |
| Reflective | `ReflectiveVerificationService` | Content-level false positive elimination |
| Simulation | `ZEROAPTSimulation` | APT-style attack simulation |
| Web Search | `SmartWebSearch` | DuckDuckGo OSINT |
| Reachability | `ReachabilityService` | Target reachability validation |

### 5.2 Structural Chunking Strategy (DocumentProcessor)

```mermaid
flowchart LR
    KB[(knowledge_base/)]

    KB -->|md| MD[MarkdownHeaderTextSplitter<br/>headers: H1 H2 H3]
    KB -->|json list| JSON_L[Each array item = 1 doc]
    KB -->|json object| JSON_O[RecursiveJsonSplitter]
    KB -->|csv| CSV[DictReader row by row]
    KB -->|pdf| PDF[PyPDFLoader page by page]
    KB -->|txt yaml| TXT[RecursiveCharacterSplitter<br/>chunk=600 overlap=100]

    MD & JSON_L & JSON_O & CSV & PDF & TXT --> Chunks[Unified Chunk List]
    Chunks --> Emb[EmbeddingFactory]
    Emb --> VS[(FAISS Index)]
```

### 5.3 Component Diagram (Full Accuracy)

```mermaid
graph TB
    subgraph "GUI Layer [app/GUI/]"
        Streamlit[gui_app.py<br/>Streamlit Web UI]
        Tkinter[argus_gui.py<br/>Tkinter Desktop]
        Studio[studio.py<br/>Argus Studio]
    end

    subgraph "Core Engine [app/core/]"
        Brain[ArgusBrain / ArgusBrainV2<br/>brain.py / brain_v2.py]
        LLM_Factory[build_llm()<br/>NonStreamingOllamaLLM<br/>CPU forced, stream=False]
        Agent_Factory[agent_factory.py<br/>build_agent_executor()]
        Agent_Factory_V2[agent_factory_v2.py<br/>SimpleChain Executor]
        Prompts[prompts.py<br/>ReAct Prompt Template]
        Schemas[schemas.py<br/>SecurityReport Pydantic]
    end

    subgraph "RAG Subsystem [app/core/rag/]"
        RAG_Engine[rag_engine.py<br/>RAGEngine]
        Emb_Factory[embeddings.py<br/>EmbeddingFactory]
        Doc_Proc[document_processor.py<br/>DocumentProcessor]
        VStore[vector_store.py<br/>VectorStore]
    end

    subgraph "Memory [app/core/memory/]"
        Mem_Service[memory_service.py<br/>ArgusMemory]
        DB[(argus_intelligence.db<br/>SQLite)]
        Mem_Service --> DB
        DB -->|5 tables| Targets[targets]
        DB --> Findings[findings]
        DB --> Entities[entities]
        DB --> Relations[relations]
        DB --> Global[global_state]
    end

    subgraph "Knowledge Base Files"
        KB_Files[(knowledge_base/<br/>.md .json .csv .pdf .txt)]
    end

    subgraph "Tool Services [app/tools/]"
        Registry[WSLBridgeTools<br/>tool_registry.py]
        Recon[ReconService]
        Scanners[VulnerabilityScanners]
        Crawler[CrawlerService]
        Evasion[EvasionService]
        Payloads[PayloadSuggester]
        Secrets[SecretAnalyzer]
        SelfHeal[SelfHealingService]
        Reflective[ReflectiveVerificationService]
        Simulation[ZEROAPTSimulation]
        WebSearch[SmartWebSearch]
        Reachability[ReachabilityService]
        CmdRunner[CommandRunner]
        WSL[WSLBridge]
    end

    subgraph "Tactical Modules [app/modules/]"
        Reasoning[argus_reasoning.py]
        DeepExploit[argus_deep_exploit.py]
        Stealth[stealth_exploit.py]
        RunRecon[run_recon.py]
        FullRecon[run_full_recon.py]
        MapTarget[map_target.py]
        SeedMem[seed_memory.py]
        DDGS[ddgs.py]
    end

    subgraph "External Systems"
        Ollama[(Ollama Server<br/>localhost:11434)]
        Kali[Kali Linux WSL<br/>wsl.exe / SSH]
        Target[Target Infrastructure]
    end

    Streamlit --> Brain
    Tkinter --> Brain
    Studio --> Brain

    KB_Files -->|load from dir| Doc_Proc
    Doc_Proc -->|structural chunking| Emb_Factory
    Emb_Factory -->|nomic-embed-text| VStore
    VStore -->|build and persist| VStore

    Brain -->|refresh blackboard| Mem_Service
    Brain -->|enrich with RAG| RAG_Engine
    RAG_Engine -->|combined context| VStore
    RAG_Engine -->|blackboard summary| Mem_Service

    Brain -->|build LLM| LLM_Factory
    LLM_Factory -->|invoke model| Ollama

    Brain -->|use ReAct| Agent_Factory
    Brain -->|fallback| Agent_Factory_V2
    Agent_Factory -->|ReAct agent| Prompts
    Agent_Factory_V2 -->|simple chain| Prompts

    Brain -->|tool dispatch| Registry
    Registry --> Recon
    Registry --> Scanners
    Registry --> Crawler
    Registry --> Evasion
    Registry --> Payloads
    Registry --> Secrets
    Registry --> SelfHeal
    Registry --> Reflective
    Registry --> Simulation
    Registry --> WebSearch
    Registry --> Reachability
    Registry --> CmdRunner
    CmdRunner --> WSL

    WSL -->|subprocess or SSH| Kali
    Kali -->|scan with tools| Target

    Target -->|scan results| Kali
    Kali -->|stdout and files| CmdRunner
    CmdRunner -->|parsed data| Registry
    Registry -->|persist to DB| Mem_Service
    Mem_Service -->|state change| Brain
```

---

## 6. Runtime View (C4 Level 3: Components)

### 6.1 Complete Query Lifecycle (Exact Code Path)

```mermaid
sequenceDiagram
    participant User as Security Researcher
    participant GUI as GUI Layer<br/>gui_app.py / studio.py
    participant Brain as ArgusBrain<br/>ask()
    participant RAG as RAG Engine<br/>app/core/rag/
    participant FAISS as FAISS Vector Store
    participant Blackboard as SQLite Blackboard<br/>ArgusMemory
    participant LLM as Ollama LLM<br/>NonStreamingOllamaLLM
    participant Registry as Tool Registry<br/>WSLBridgeTools
    participant Tool as Tool Service<br/>e.g. ReconService
    participant Kali as Kali Linux WSL
    participant Target as Target System

    User->>GUI: Enter target URL
    GUI->>Brain: brain.ask(query)

    Note over Brain,Blackboard: === PHASE 1: CONTEXT ASSEMBLY ===

    Brain->>Brain: _refresh_blackboard()

    Brain->>Blackboard: get_blackboard_summary()
    Blackboard-->>Brain: current findings JSON

    Brain->>Blackboard: get_graph_insights()
    Blackboard-->>Brain: entity→relation→entity triples

    Brain->>RAG: _enrich_with_rag(query)
    RAG->>FAISS: similarity_search(query, k=4)
    FAISS-->>RAG: top 4 chunks + scores
    RAG->>RAG: format_combined_context(rag, blackboard)
    RAG-->>Brain: fused prompt string

    Note over Brain,LLM: === PHASE 2: REASONING ===

    Brain->>Brain: augmented_query = fused string
    Brain->>LLM: invoke(augmented_query)<br/>[num_predict=4096, temp=0.2, CPU]

    LLM-->>Brain: ReAct thought → Action → Observation

    Note over Brain,Kali: === PHASE 3: TOOL EXECUTION ===

    alt use_react=True (brain_v2.py)
        Brain->>Brain: _get_react_agent()
        Brain->>Registry: tool_map[name].func(args)
    else use_react=False (brain.py default)
        Brain->>Brain: _get_simple_chain()
        Brain->>Registry: sequential tool calls
    end

    alt Invalid Format error
        Brain->>Brain: self.use_react = False
        Brain->>Brain: _ask_simple_chain(…)
        Brain->>Registry: retry with SimpleChain
    end

    Registry->>Tool: delegate(target, options)
    Tool->>Kali: runner.run("nmap -A target")
    Kali->>Target: scan / probe
    Target-->>Kali: open ports / services / headers

    Kali-->>Tool: stdout / stderr / file output
    Tool->>Tool: parse results (JSON, grep, regex)
    Tool-->>Registry: structured findings

    Note over Brain,Blackboard: === PHASE 4: PERSISTENCE ===

    Registry->>Blackboard: upsert_target(domain)
    Registry->>Blackboard: add_finding(domain, tool, type, raw, summary)
    Registry->>Blackboard: upsert_entity(ip/tech/vuln)
    Registry->>Blackboard: add_relation(entity1, entity2, "HOSTS")

    Blackboard-->>Registry: OK
    Registry-->>Brain: result dict

    Note over Brain,User: === PHASE 5: OUTPUT ===

    Brain->>Brain: _process_output(output)
    alt Pydantic parse OK
        Brain->>Brain: SecurityReport.dict()
    else JSON extraction OK
        Brain->>Brain: json.loads(match)
    else fallback
        Brain->>Brain: {"output": raw_string}
    end

    Brain-->>GUI: {"output": SecurityReport, "raw": "..."}
    GUI-->>User: Report / Dashboard update
```

### 6.2 RAG Index Build Workflow (Exact Code Path)

```mermaid
flowchart TB
    START([RAG Engine start])

    START --> CHECK{FAISS index exists?}

    CHECK -->|Yes, skip rebuild| DONE([Ready])
    CHECK -->|No or auto rebuild| BUILD

    subgraph BUILD[Full Index Build]
        WALK[Document Processor<br/>walks knowledge_base/]

        WALK --> CLASSIFY{File type}

        CLASSIFY -->|markdown| MD[Split by headers]
        CLASSIFY -->|json list| JSONL[Each item = doc]
        CLASSIFY -->|json object| JSONO[Recursive split]
        CLASSIFY -->|csv| CSV[Row by row]
        CLASSIFY -->|pdf| PDF[Page by page]
        CLASSIFY -->|text/yaml| TXT[Fixed size chunks]

        MD & JSONL & JSONO & CSV & PDF & TXT --> MERGE[Chunk List]

        MERGE --> EMBED[Embedding Factory]
        EMBED --> TRY{Ollama ready?}
        TRY -->|Yes| OLLAMA[nomic-embed-text]
        TRY -->|No| HF[all-MiniLM-L6-v2]
        HF -->|No| OPENAI[text-embedding-3-small]

        OLLAMA --> STORE[Build FAISS index]
        HF --> STORE
        OPENAI --> STORE

        STORE --> PERSIST[Save to disk<br/>app/core/rag/store/]
    end

    BUILD --> DONE
```

### 6.3 Context Fusion: Prompt Assembly in enrich_with_rag

```mermaid
flowchart LR
    Q[User Query] --> Brain

    subgraph "Refresh Blackboard"
        BLACK[Blackboard Summary<br/>targets + findings]
        GRAPH[Graph Insights<br/>entities + relations]
        BLACK --> MERGE_BB[Live State]
        GRAPH --> MERGE_BB
    end

    subgraph "RAG Retrieval"
        RAG[RAG Engine]
        VS[FAISS search]
        VS --> CHUNKS[Top K chunks]
        CHUNKS --> MERGE_RAG[Static Knowledge]
    end

    Brain --> BLACK
    Brain --> Q
    Q --> RAG
    MERGE_BB --> RAG
    RAG --> MERGE[Fused Prompt]
    MERGE_BB --> MERGE

    MERGE --> PROMPT["===== STATIC KNOWLEDGE =====
    chunk 1 ...
    ===== LIVE TARGET STATE =====
    blackboard JSON
    graph triples
    Question: query
    Priority: live > static
    Flag contradictions"]

    PROMPT --> LLM[Ollama LLM]
```

---

## 7. Deployment View (C4 Level 4: Code/Infrastructure)

- **Host OS:** Windows 10/11.
- **AI Engine:** Ollama (Localhost:11434) with models: `WhiteRabbitNeo-V3-7B`, `nomic-embed-text`.
- **Vector Store:** FAISS (CPU) persisted to `app/core/rag/store/`.
- **Environment:** `Argus_venv` (Python 3.12).
- **Directory Structure:**
  - `/app`: Core logic (core, tools, modules, GUI).
  - `/app/core/rag`: RAG subsystem (embeddings, vector store, document processor, engine).
  - `/knowledge_base`: Static source documents for RAG ingestion.
  - `/docs`: Documentation and workflows.
  - `/scripts`: Root-level operational utilities.
  - `/setup`: Environment installation resources.
- **Virtualization:** WSL 2 (Distro: kali-linux).
- **Bridge:** Local SSH (Port 22) or `wsl.exe` direct execution.

---

## 8. Cross-Cutting Concepts
- **Modular Tooling:** Tools are in category-specific services, improving testability.
- **Security:** API keys and credentials managed via `.env`.
- **Error Handling:** "Guided Reflection" with WAF detection and autonomous repair suggestions.
- **Reflective Verification:** Mandatory multi-step validation (Content-Length/Header checks) for all discoveries.
- **RAG Context Fusion:** Every LLM query is enriched with:
  - **Static Knowledge (FAISS):** General pentest techniques, cheatsheets, reference material from `knowledge_base/`.
  - **Live Target State (Blackboard):** Current findings, entities, relations discovered during active reconnaissance.
  - The prompt explicitly separates both sources with priority rules.
- **Structural Chunking:** Documents are split by structure (not just character count):
  - Markdown by headers, JSON by logical blocks, CSV row-by-row.
- **Persistence:** SQLite database (`argus_intelligence.db`) with relational mapping for Knowledge Graph visualization.
- **Automated Organization:** Centralized storage of tool-specific reports (e.g., `reports/nikto/`) with semantic, timestamped naming conventions.

---

## 9. Architecture Decisions (ADR)
- **ADR 1: Why SQLite?** Chosen for simplicity and zero-configuration, while supporting relational data needed for the Knowledge Graph.
- **ADR 2: Why WSL?** Provides a native Linux environment for industry-standard security tools while remaining accessible from Windows.
- **ADR 3: Why LangChain ReAct?** Standardizes how the AI interacts with tools, allowing for complex multi-step reasoning.
- **ADR 4: Autonomous Orchestration vs Static Scripts:** Shifted toward `Run_Kali_Command` to allow the AI to troubleshoot and pivot in real-time.
- **ADR 5: Self-Healing Logic:** Implemented `system_self_heal` to reduce "agent downtime".
- **ADR 6: Reflective Verification over Status-Only Discovery:** Mandated content-level validation because modern WAFs use deceptive "200 OK" redirects.
- **ADR 7: Autonomous Syntax Learning:** Empowered the agent to run `--help` commands on-the-fly.
- **ADR 8: Intelligent Rate-Limiting & IP Protection:** Automated halt-on-block logic to protect IP reputation.
- **ADR 9: Why nomic-embed-text?** Chosen as the primary embedding model because it runs locally via Ollama (no API key, no data leakage), provides 768-dim embeddings with strong retrieval accuracy, and falls back gracefully to HuggingFace/OpenAI.
- **ADR 10: Why RAG + Blackboard Fusion?** Separating static knowledge (techniques, cheatsheets) from live target state (active findings) prevents the LLM from confusing general knowledge with current reconnaissance data, reducing hallucination and improving decision accuracy.
- **ADR 11: Why Structural Chunking?** Different file formats carry meaning in their structure. JSON lists, CSV rows, and Markdown headers each require format-specific splitting to preserve semantic coherence during retrieval.
- **ADR 12: Why LangChain vs LangGraph?** LangChain is utilized for the linear, deterministic RAG indexing and query flow (docs, embeddings, FAISS) due to its specialized retrieval modules. LangGraph is selected for the autonomous Penetration Testing Agent to handle non-linear execution, cycles (e.g. feedback loops during failed exploits), multi-agent orchestration, and native state management without spaghetti code.

---

*Created by Argus Security Framework Team - June 2026*
