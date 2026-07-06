"""Test custom StateGraph with text-based ReAct and improved prompting."""
from typing import TypedDict, Annotated, Optional
import re
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning)


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    target: str
    phase: str
    blackboard_summary: str
    iteration_count: int
    tool_name: Optional[str]
    tool_input: Optional[str]
    tool_result: Optional[str]
    tool_error: Optional[str]


# ── Tools ────────────────────────────────────────────
TOOL_MAP = {}

def scan_ports(target: str) -> str:
    """Scan target for open ports and running services."""
    return "Open ports: 80 (HTTP), 443 (HTTPS), 22 (SSH). Server: nginx/1.24.0."

def search_cves(query: str) -> str:
    """Search for known CVEs and exploits related to a technology."""
    return "CVE-2024-1234: Critical RCE in nginx 1.24.0. CVSS 9.8. Exploit available."

TOOL_MAP["Scan_Ports"] = scan_ports
TOOL_MAP["Search_CVEs"] = search_cves

TOOL_DESCRIPTIONS = "\n".join(
    f"- {name}: {fn.__doc__}" for name, fn in TOOL_MAP.items()
)

llm = ChatOllama(model="WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest")


# ── Nodes ────────────────────────────────────────────
def agent_node(state: AgentState) -> dict:
    """LLM decides next action using ReAct format."""
    last_result = state.get("tool_result") or "None yet"
    last_error = state.get("tool_error") or "None"

    system = SystemMessage(content=(
        f"ROLE: You are Argus AI, a senior penetration tester.\n"
        f"TARGET: {state['target']}\n"
        f"PHASE: {state['phase']}\n"
        f"ITERATION: {state['iteration_count'] + 1}\n\n"
        f"BLACKBOARD (live findings):\n{state['blackboard_summary']}\n\n"
        f"LAST TOOL OUTPUT: {last_result}\n"
        f"LAST ERROR: {last_error}\n\n"
        f"TOOLS AVAILABLE:\n{TOOL_DESCRIPTIONS}\n\n"
        f"RULES:\n"
        f"1. Choose ONE tool per response.\n"
        f"2. NEVER repeat the same tool with the same input.\n"
        f"3. If a tool fails, try a different approach.\n"
        f"4. Maximum {3 - state['iteration_count']} iterations remaining.\n\n"
        f"OUTPUT FORMAT (EXACT):\n"
        f"Thought: <your reasoning>\n"
        f"Action: <tool name>\n"
        f"Action Input: <input>\n\n"
        f"Once you have enough data:\n"
        f"Final Answer: <your complete security report>"
    ))

    response = llm.invoke([system] + state["messages"])
    return {"messages": [response], "iteration_count": state["iteration_count"] + 1}


def parse_node(state: AgentState) -> dict:
    """Parse LLM output: extract Action or detect Final Answer."""
    last = state["messages"][-1]
    content = last.content if hasattr(last, "content") else str(last)

    print(f"\n--- LLM Response (iter {state['iteration_count']}) ---")
    print(content[:300])
    print("---")

    if "Final Answer:" in content:
        print("  => Final Answer detected, done.")
        return {"phase": "done", "tool_name": None}

    action_match = re.search(r"Action:\s*(\w+)", content)
    input_match = re.search(r"Action Input:\s*(.+)", content)

    if action_match:
        name = action_match.group(1)
        inp = input_match.group(1).strip() if input_match else state["target"]
        print(f"  => Action: {name}({inp})")
        return {"tool_name": name, "tool_input": inp}

    print("  => No Action found, treating as done.")
    return {"phase": "done", "tool_name": None}


def execute_node(state: AgentState) -> dict:
    """Execute the chosen tool and feed result back."""
    tool_name = state.get("tool_name")
    tool_input = state.get("tool_input", state["target"])

    if not tool_name or tool_name not in TOOL_MAP:
        obs = f"Observation: Unknown tool '{tool_name}'. Available: {list(TOOL_MAP.keys())}"
        return {"tool_error": obs, "messages": [HumanMessage(content=obs)]}

    try:
        result = TOOL_MAP[tool_name](tool_input)
        obs = f"Observation: {result}"
        bb = f"{state['blackboard_summary']}\n- [{tool_name}] {tool_input[:50]} -> {result[:100]}"
        return {"tool_result": result, "tool_error": None, "blackboard_summary": bb.strip(),
                "messages": [HumanMessage(content=obs)]}
    except Exception as e:
        obs = f"Observation: Error executing {tool_name}: {e}"
        return {"tool_error": obs, "messages": [HumanMessage(content=obs)]}


# ── Routers ──────────────────────────────────────────
def route_after_agent(state: AgentState) -> str:
    return "parse"

def route_after_parse(state: AgentState) -> str:
    if state.get("phase") == "done":
        return "end"
    if state.get("tool_name"):
        return "execute"
    return "end"

def route_after_execute(state: AgentState) -> str:
    if state["iteration_count"] >= 3:
        return "end"
    return "agent"


# ── Build ────────────────────────────────────────────
builder = StateGraph(AgentState)
builder.add_node("agent", agent_node)
builder.add_node("parse", parse_node)
builder.add_node("execute", execute_node)
builder.add_edge(START, "agent")
builder.add_conditional_edges("agent", route_after_agent)
builder.add_conditional_edges("parse", route_after_parse, {"execute": "execute", "end": END})
builder.add_conditional_edges("execute", route_after_execute, {"agent": "agent", "end": END})

graph = builder.compile()

print("Running custom graph with WhiteRabbitNeo...\n")
result = graph.invoke({
    "messages": [HumanMessage(content="Scan the target and report vulnerabilities.")],
    "target": "https://test.com",
    "phase": "recon",
    "blackboard_summary": "Initializing scan...",
    "iteration_count": 0,
    "tool_name": None,
    "tool_input": None,
    "tool_result": None,
    "tool_error": None,
})

print(f"\n{'='*50}")
print(f"FINAL: {result['iteration_count']} iterations")
print(f"PHASE: {result['phase']}")
for i, m in enumerate(result["messages"]):
    print(f"  [{i}] {type(m).__name__}: {str(m.content)[:120]}")
print("CUSTOM GRAPH TEST PASSED")
