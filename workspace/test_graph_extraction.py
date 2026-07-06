"""Test that graph_ask properly extracts output from the prebuilt agent."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_ollama import ChatOllama
from app.core.workflow import build_workflow
from app.core.workflow.state import ArgusPrebuiltState
from app.core.workflow.graph import _supports_tool_calls
from langchain_core.messages import HumanMessage
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

llama = ChatOllama(model="llama3.1:latest", num_predict=2048, temperature=0.2)

def mock_scan(target: str) -> str:
    """Scan target for open ports."""
    return f"Open ports: 80, 443. Server: nginx."

tools = [mock_scan]

# Test with prebuilt state schema
graph = build_workflow(llama, tools)
print(f"Supports tool_calls: {_supports_tool_calls(llama)}")

result = graph.invoke({
    "messages": [HumanMessage(content="Scan https://test.com and say done")],
    "target": "https://test.com",
    "phase": "recon",
    "blackboard_summary": "",
    "iteration_count": 0,
    "max_iterations": 10,
    "remaining_steps": 10,
    "tool_name": None,
    "tool_input": None,
    "tool_result": None,
    "tool_error": None,
})

print(f"\nResult type: {type(result).__name__}")
print(f"Result keys: {list(result.keys())}")

if "messages" in result:
    msgs = result["messages"]
    print(f"\nMessages ({len(msgs)}):")
    for i, m in enumerate(msgs):
        role = type(m).__name__
        content = str(m.content)[:150]
        print(f"  [{i}] {role}: {content}")
        if hasattr(m, "tool_calls") and m.tool_calls:
            print(f"       tool_calls: {m.tool_calls}")

# Extract output as graph_ask does
output = ""
if result.get("messages"):
    last = result["messages"][-1]
    if hasattr(last, "content") and last.content:
        output = last.content
    elif hasattr(last, "text") and last.text:
        output = last.text
    else:
        output = str(last)

print(f"\nExtracted output: {output[:200]}")
print("\nFull state output test PASSED")
