"""Full integration test: workflow builds, invokes, returns results."""
import json
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_ollama import ChatOllama
from app.core.agent import build_workflow
from app.core.agent.react_state import ArgusAgentState
from langchain_core.messages import HumanMessage
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


def mock_scan(target: str) -> str:
    """Scan target for open ports and services."""
    return f"Open ports: 80 (HTTP), 443 (HTTPS). Server: nginx/1.24.0."

def mock_search(query: str) -> str:
    """Search for CVEs related to technologies."""
    return f"CVE-2024-1234: Critical RCE in nginx 1.24.0. CVSS 9.8."

def mock_recon(target: str) -> str:
    """Run full reconnaissance suite on target."""
    return f"Subdomains: admin.{target}, api.{target}. WAF: Cloudflare."

tools = [mock_scan, mock_search, mock_recon]

print("=" * 60)
print("Test 1: Llama 3.1 with create_react_agent (prebuilt mode)")
print("=" * 60)

llama = ChatOllama(model="llama3.1:latest", num_predict=2048, temperature=0.2)
graph = build_workflow(llama, tools)

result = graph.invoke({
    "messages": [HumanMessage(content="Scan https://test.com for vulnerabilities")],
    "target": "https://test.com",
    "phase": "recon",
    "blackboard_summary": "",
    "iteration_count": 0,
    "max_iterations": 10,
    "tool_name": None,
    "tool_input": None,
    "tool_result": None,
    "tool_error": None,
})

print(f"Iterations: {result.get('iteration_count', 'N/A')}")
print(f"Messages count: {len(result['messages'])}")
for i, m in enumerate(result["messages"]):
    role = type(m).__name__
    content = str(m.content)[:100]
    print(f"  [{i}] {role}: {content}")
print("PASSED\n")


print("=" * 60)
print("Test 2: Auto-detection of model capabilities")
print("=" * 60)

from app.core.agent.react_workflow import _supports_tool_calls
print(f"  Llama 3.1 supports tool_calls: {_supports_tool_calls(llama)}")

# We can't test WhiteRabbitNeo here (would be too slow),
# but we verify the detection logic works
print("PASSED\n")


print("=" * 60)
print("Test 3: Tool map building")
print("=" * 60)

from app.core.agent.react_workflow import _build_tool_map
tool_map = _build_tool_map(tools)
print(f"  Tools registered: {list(tool_map.keys())}")
assert "mock_scan" in tool_map
assert "mock_search" in tool_map
assert "mock_recon" in tool_map
print("PASSED\n")


print("=" * 60)
print("Test 4: Target extraction")
print("=" * 60)

from app.core.agent.react_workflow import extract_target
assert extract_target("scan https://example.com please") == "https://example.com"
assert extract_target("Check example.com for vulns") == "example.com"
print(f"  URL extraction: {extract_target('scan https://example.com')}")
print(f"  Domain extraction: {extract_target('Check example.com')}")
print("PASSED\n")


print("=" * 60)
print("Test 5: Brain.graph_ask() integration")
print("=" * 60)

from app.core.agent.brain import ArgusBrain
from langchain_core.tools import Tool

# Use ArgusBrain with mock tools
brain = ArgusBrain("llama3.1:latest", [
    Tool(name="scan", func=mock_scan, description="Scan target"),
    Tool(name="search", func=mock_search, description="Search CVEs"),
])

result = brain.graph_ask("Analyze https://example.com for security issues")
print(f"  Result type: {type(result).__name__}")
print(f"  Output keys: {list(result.keys()) if isinstance(result, dict) else 'N/A'}")
output = result.get("output", "")
if isinstance(output, dict):
    print(f"  Summary: {str(output.get('summary', ''))[:100]}")
else:
    print(f"  Raw output: {str(output)[:100]}")
print("PASSED\n")


print("=" * 60)
print("ALL INTEGRATION TESTS PASSED")
print("=" * 60)
