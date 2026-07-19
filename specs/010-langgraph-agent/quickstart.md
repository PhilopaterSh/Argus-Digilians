# Quickstart & Validation Guide

## 1. Validating the RAG Pipeline (LangChain)

To verify the linear execution of the knowledge retrieval engine:

```bash
# 1. Start the Argus virtual environment
source Argus_venv/bin/activate  # Or Windows equivalent

# 2. Run the standalone RAG test script
python -m scripts.test_rag --ingest "docs/sample_target.md" --query "What is the primary vulnerability?"

# Expected Outcome:
# The system should output a direct answer based on the loaded document,
# demonstrating a single linear pass (No graph loops).
```

## 2. Validating the Tactical Agent (LangGraph)

To verify the stateful, cyclical execution of the PenTest Agent:

```bash
# 1. Start a local dummy target (e.g., a simple web server that simulates a WAF)
python -m scripts.mock_waf_target --port 8080 &

# 2. Run the standalone Agent graph test
python -m scripts.test_agent --target "http://localhost:8080"

# Expected Outcome (Console Log):
# [Recon Node] Discovered port 8080
# [Exploit Node] Sending payload_v1... BLOCKED.
# [Reflective Node] WAF detected. Modifying payload to payload_v2 (obfuscated)...
# [Exploit Node] Sending payload_v2... SUCCESS.
# [Post-Exploit Node] Extracting flag.
# [System] State saved to SQLite Blackboard.
```

If the console outputs the cyclical transition (`Exploit -> Reflective -> Exploit`), the architectural implementation is validated.
