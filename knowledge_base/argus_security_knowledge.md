# Argus AI Penetration Testing Knowledge Base

## Architecture Overview
Argus is a multi-agent AI penetration testing system.
- **Brain**: Core reasoning engine using LangChain AgentExecutor (ReAct or SimpleChain fallback)
- **Agent Factory**: Builds tool-enabled agents from available tools
- **Memory**: SQLite-backed knowledge graph (entities, relations, targets, findings)
- **LLM**: Ollama-hosted models (default: WhiteRabbitNeo V3 7B)
- **GUI**: Streamlit web interface for interactive pentesting

## Core Tools Available
- **Recon Tools**: Subdomain enumeration, WAF detection, port scanning, technology identification, web crawling
- **Exploitation**: Deep exploitation module, stealth exploitation, reflective verification
- **Analysis**: Reachability analysis, secrets detection, self-healing, simulation engine
- **Web Search**: DuckDuckGo search for OSINT gathering
- **WSL Bridge**: Execute Linux/Kali tools via WSL integration
- **Evasion**: Payload generation with evasion techniques

## Pentesting Methodology
### Phase 1: Reconnaissance
1. Target mapping with subdomain enumeration
2. WAF detection
3. Technology stack identification
4. Port and service scanning
5. Web crawling for endpoint discovery

### Phase 2: Analysis & Intelligence
1. Blackboard intelligence gathering and correlation
2. Knowledge graph construction (entities and relations)
3. Vulnerability assessment
4. Attack surface mapping

### Phase 3: Exploitation
1. Payload generation with evasion
2. Controlled exploitation testing
3. Reflective verification of findings
4. Simulation of attack scenarios

### Phase 4: Reporting
1. Automated report generation in STIX/JSON format
2. Technical findings documentation
3. Remediation recommendations

## SQLite Memory Schema
- **targets**: Domain, parent_domain, status, priority, last_seen
- **findings**: Target reference, tool name, data type, raw data, summary
- **entities**: Knowledge graph nodes (domain, ip, email, tech, vulnerability)
- **relations**: Knowledge graph edges (HOSTS, USES_TECH, VULNERABLE_TO)
- **global_state**: Key-value store for AI-ready summaries

## RAG System
- **Embeddings**: nomic-embed-text via Ollama (primary) → HuggingFace all-MiniLM-L6-v2 (fallback) → OpenAI text-embedding-3-small (final fallback)
- **Vector Store**: FAISS (CPU)
- **Chunk Size**: 600 characters with 100 overlap
- **Retriever**: Similarity search with configurable k
- **Knowledge Base**: Markdown, text, JSON, CSV, and PDF documents in knowledge_base/
- **Structural Chunking**: JSON via RecursiveJsonSplitter, CSV row-by-row, MD via MarkdownHeaderTextSplitter
- **Context Fusion**: Static RAG knowledge + Live Blackboard state merged intelligently in prompt
