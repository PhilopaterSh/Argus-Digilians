"""Test the custom text-based ReAct mode with a mock LLM."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from typing import Any
from langchain_core.messages import AIMessage, HumanMessage
from app.core.workflow.graph import _build_custom_workflow, _build_tool_map


class MockLLM:
    """Simulates a model that does NOT support tool_calls (like WhiteRabbitNeo)."""
    def __init__(self):
        self.call_count = 0
        self.responses = [
            # Response 1: Call scan tool
            "Thought: I should scan the target first.\nAction: mock_scan\nAction Input: https://test.com",
            # Response 2: Got scan results, now search
            "Thought: Found open ports. Search for CVEs.\nAction: mock_search\nAction Input: nginx 1.24",
            # Response 3: Final answer
            "Thought: I have enough data.\nFinal Answer: Target: https://test.com\nRisk: MEDIUM\nFindings: Open ports 80/443, nginx 1.24 with known CVEs.",
        ]

    def invoke(self, messages, **kwargs):
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        print(f"  [MOCK LLM #{self.call_count}] {response[:80]}...")
        return AIMessage(content=response)


def mock_scan(target: str) -> str:
    """Scan target for open ports and services."""
    return "Open ports: 80 (HTTP), 443 (HTTPS). Server: nginx/1.24.0."


def mock_search(query: str) -> str:
    """Search for CVEs related to technologies."""
    return "CVE-2024-1234: Critical RCE in nginx 1.24.0. CVSS 9.8."


tools = [mock_scan, mock_search]
tool_map = _build_tool_map(tools)
print(f"Tool map: {list(tool_map.keys())}")

graph = _build_custom_workflow(MockLLM(), tools)

initial = {
    "messages": [HumanMessage(content="Scan https://test.com")],
    "target": "https://test.com",
    "phase": "recon",
    "blackboard_summary": "",
    "iteration_count": 0,
    "max_iterations": 5,
    "tool_name": None,
    "tool_input": None,
    "tool_result": None,
    "tool_error": None,
}

result = graph.invoke(initial)

print(f"\n{'='*50}")
print(f"Total iterations: {result['iteration_count']}")
print(f"Final phase: {result['phase']}")
print(f"Messages ({len(result['messages'])}):")
for i, m in enumerate(result["messages"]):
    role = type(m).__name__
    content = str(m.content)[:120]
    print(f"  [{i}] {role}: {content}")

assert result["iteration_count"] == 3, f"Expected 3, got {result['iteration_count']}"
assert "Final Answer:" in result["messages"][-1].content
print("\nCUSTOM MODE TEST PASSED!")
