import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app.tools.tool_registry import WSLBridgeTools
from app.core.agent.brain_tools import build_argus_tools
from app.core.agent.brain import ArgusBrain
from app.core.config import ArgusConfig

config = ArgusConfig.load()


class PrintCallback:
    def on_graph_event(self, status, detail):
        print(f"\n--- [{status}] ---\n{detail}\n")


def main():
    target_url = sys.argv[1] if len(sys.argv) > 1 else "https://www.cultbeauty.co.uk/"
    bridge = WSLBridgeTools()
    tools = build_argus_tools(bridge)
    brain = ArgusBrain(config.model_name, tools, memory=bridge.memory)

    query = (
        f"Perform a comprehensive security analysis for {target_url}. "
        f"Start with reachability, then map the attack surface, and finally "
        f"provide a deep risk assessment."
    )
    result = brain.ask(query, callbacks=[PrintCallback()])
    print("\n=== FINAL RESULT ===")
    print(result)


if __name__ == "__main__":
    main()
