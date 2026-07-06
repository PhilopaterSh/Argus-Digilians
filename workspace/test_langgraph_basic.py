"""Test LangGraph create_react_agent with Ollama + custom state + hooks."""
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class TestState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    remaining_steps: int
    target: str
    blackboard_summary: str
    iteration_count: int


def test_prompt(state):
    """Build prompt with dynamic context."""
    return [
        {"role": "system", "content": (
            f"You are Argus AI, a security researcher.\n"
            f"Target: {state['target']}\n"
            f"Blackboard: {state['blackboard_summary']}\n"
            f"Iteration: {state['iteration_count']}\n"
            f"Choose one tool per step. Be brief."
        )}
    ] + state["messages"]


def pre_hook(state):
    """Simulate refreshing blackboard before LLM call."""
    return {
        "blackboard_summary": f"Live findings for {state['target']}: [simulated]",
        "iteration_count": state.get("iteration_count", 0) + 1,
    }


def post_hook(state):
    """Simulate saving findings after LLM response."""
    last = state["messages"][-1] if state["messages"] else None
    if last and hasattr(last, "content"):
        print(f"  [post_hook] LLM said: {last.content[:80]}...")
    return {}


def mock_tool(query: str) -> str:
    """Mock tool that simulates a security scan."""
    return f"Mock scan result for: {query}"


llm = ChatOllama(model="WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest")

agent = create_react_agent(
    llm.bind_tools([mock_tool]),
    [mock_tool],
    state_schema=TestState,
    prompt=test_prompt,
    pre_model_hook=pre_hook,
    post_model_hook=post_hook,
    version="v2",
)

print("Invoking agent...")
result = agent.invoke({
    "messages": [HumanMessage(content="scan https://test.com for vulnerabilities")],
    "remaining_steps": 5,
    "target": "https://test.com",
    "blackboard_summary": "",
    "iteration_count": 0,
})

print(f"\n=== Results ===")
print(f"Messages: {len(result['messages'])}")
for i, m in enumerate(result["messages"]):
    role = type(m).__name__
    content = str(m.content)[:100]
    print(f"  [{i}] {role}: {content}")

print(f"\nTarget: {result['target']}")
print(f"Iterations: {result['iteration_count']}")
print(f"Blackboard: {result['blackboard_summary'][:100]}")
print("\nSUCCESS: create_react_agent + hooks + custom state works!")
