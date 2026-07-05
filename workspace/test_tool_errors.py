"""Test tool error handling in create_react_agent."""
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)

from langgraph.prebuilt import create_react_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, BaseMessage
from typing import TypedDict, Annotated
from langgraph.graph.message import add_messages


class S(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    remaining_steps: int


def only_tool(x: str) -> str:
    """The only available tool."""
    return f"Result: {x}"


llm = ChatOllama(model="llama3.1:latest")
agent = create_react_agent(
    llm.bind_tools([only_tool]),
    [only_tool],
    state_schema=S,
    version="v2",
)

result = agent.invoke({
    "messages": [HumanMessage(content="call scan then stop")],
    "remaining_steps": 3,
})

for i, m in enumerate(result["messages"]):
    role = type(m).__name__
    content = str(m.content)[:150]
    print(f"[{i}] {role}: {content}")
    if hasattr(m, "tool_calls") and m.tool_calls:
        for tc in m.tool_calls:
            print(f"     TOOL_CALL: {tc['name']}")

print(f"\nremaining_steps: {result['remaining_steps']}")
print("DONE")
