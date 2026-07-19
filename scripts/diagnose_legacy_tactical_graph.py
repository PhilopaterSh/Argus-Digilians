"""Manual diagnostic for app/core/agent/graph.py's superseded LangGraph node graph
(spec 010: Recon -> Scanner -> Exploit <-> Reflective -> Post-Exploit).

Renamed 2026-07-10 from `test_agent.py` (misleading - it's not part of the pytest
suite and does not exercise ArgusBrain's current production ReAct loop, which is
`app/core/agent/react_workflow.py` per specs 017/018/019). Retained per
Constitution VII (010's graph itself is retained, not deleted) as a way to
manually smoke-test that legacy graph still runs; it does not need to be kept in
sync with the current agent's behavior.
"""
import argparse
from app.core.agent.graph import build_tactical_graph

def main():
    parser = argparse.ArgumentParser(description="Test cyclical LangGraph Pentest Agent")
    parser.add_argument("--target", help="Target URL or IP", required=True)
    args = parser.parse_args()

    print(f"Initializing Tactical Agent Graph...")
    graph = build_tactical_graph()

    print(f"\nStarting execution against target: {args.target}")
    print("-" * 50)
    
    # Initialize the state
    initial_state = {
        "target_ip": args.target,
        "open_ports": [],
        "vulnerabilities": [],
        "current_payload": None,
        "failed_payloads": [],
        "exploit_success": False,
        "extracted_data": {},
        "error_log": [],
        "retry_count": 0
    }

    # Execute the graph
    for output in graph.stream(initial_state):
        # We can print node transitions if desired
        pass
    
    print("-" * 50)
    print("Agent graph execution completed.")

if __name__ == "__main__":
    main()
