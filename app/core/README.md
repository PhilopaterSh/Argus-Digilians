app/core/ — Core components

Files of interest:
- brain.py: Builds ArgusBrain, wraps AgentExecutor and parses LLM output to Pydantic models.
- llm_factory.py: Config and wrapper for Ollama LLM (non-streaming defaults).
- agent_factory.py: Constructs the LangChain AgentExecutor with config-derived parameters.
- prompts.py: Long operational prompt template (rules, JSON output schema).
- schemas.py: Pydantic models (Finding, SecurityReport).
- memory/: SQLite-backed memory and knowledge graph (targets, findings, entities, relations).

Developer notes:
- Edit config.yaml (repo root) to change runtime values (model name, timeouts, truncation).