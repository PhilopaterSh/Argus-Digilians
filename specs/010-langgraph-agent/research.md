# Research: Argus Architectural Framework (LangChain vs LangGraph)

## Topic: Optimal Framework Selection for RAG vs Tactical Agents

### 1. Retrieval-Augmented Generation (RAG) Architecture
- **Decision**: Use LangChain directly (without LangGraph) for all RAG operations in `app/core/rag/`.
- **Rationale**: The RAG workflow is inherently deterministic and linear. The process (load -> split -> embed -> index -> retrieve -> prompt LLM) does not require cyclical logic or back-tracking. Using LangChain's built-in chains (`FAISS`, `RecursiveCharacterTextSplitter`, `OllamaEmbeddings`) avoids the unnecessary overhead of state machine management and prevents complexity bloat.
- **Alternatives considered**: Using LangGraph for RAG. Rejected because it introduces unnecessary boilerplate (nodes and edges) for a workflow that has no feedback loops.

### 2. Tactical PenTest Agent Architecture
- **Decision**: Use LangGraph for the PenTest Agent in `app/core/agent/`.
- **Rationale**: Tactical pentesting is highly interactive, stateful, and relies heavily on feedback loops (e.g., detecting a WAF block, modifying a payload, and retrying). A standard LangChain implementation would require complex "spaghetti code" (nested while-loops and manual state passing) to manage this. LangGraph models each step as a distinct `Node` (Recon, Scanner, Exploit, Reflective, Post-Exploit) and automatically persists the global state (the attack context) across these cyclical transitions.
- **Alternatives considered**: Standard LangChain Agents (e.g., ReAct). Rejected because they struggle with rigid, multi-step tactical workflows where specific tools (like a reflective evasion node) must be forcibly routed to upon specific failure conditions. LangGraph provides the explicit state machine required for reliable tactical routing.

### Conclusion
This strict bifurcation—LangChain for linear knowledge retrieval, LangGraph for stateful cyclical execution—represents a robust, 100% reliable architectural standard for the Argus framework.
