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
