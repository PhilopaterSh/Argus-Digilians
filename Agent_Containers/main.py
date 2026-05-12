import os
import time
import requests
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain.prompts import PromptTemplate
from tools import check_web_headers, run_subfinder, run_ffuf_discovery

# ── Wait for Juice Shop ────────────────────────────────────────────────────────
def wait_for_juice_shop(url, timeout=60):
    print(f"Waiting for Juice Shop to be ready at {url}...")
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = requests.get(url, timeout=3, verify=False)
            if r.status_code < 500:
                print("Juice Shop is up!")
                return True
        except Exception:
            pass
        print("  Not ready yet, retrying in 5s...")
        time.sleep(5)
    print("Juice Shop did not become ready in time.")
    return False

# ── 1. LLM ────────────────────────────────────────────────────────────────────
llm = Ollama(
    model=os.environ.get("AGENT_MODEL", "dolphin-llama3"),
    base_url=os.environ.get("OLLAMA_HOST", "http://ollama-service:11434"),
    temperature=0,  # deterministic, less hallucination
)

# ── 2. Tools ──────────────────────────────────────────────────────────────────
tools = [
    Tool(
        name="check_web_headers",
        func=check_web_headers.invoke,
        description="Fetches HTTP security headers. Input: full URL e.g. http://juice-shop:3000",
    ),
    Tool(
        name="run_ffuf_discovery",
        func=run_ffuf_discovery.invoke,
        description="Brute-forces hidden paths using FFUF. Input: bare domain e.g. juice-shop",
    ),
    Tool(
        name="run_subfinder",
        func=run_subfinder.invoke,
        description="Enumerates subdomains. Input: bare domain e.g. juice-shop",
    ),
]

# ── 3. Prompt ─────────────────────────────────────────────────────────────────
template = """You are a security agent. Use tools to recon the target then write a report.

Tools available:
{tools}

Use EXACTLY this format, nothing else:

Thought: <one sentence>
Action: <tool name from: {tool_names}>
Action Input: <input>
Observation: <result>
Thought: <one sentence>
Action: <tool name>
Action Input: <input>
Observation: <result>
Thought: <one sentence>
Action: <tool name>
Action Input: <input>
Observation: <result>
Thought: I have all results.
Final Answer: <report>

Rules:
- Always write Action Input: on the line immediately after Action:
- Never skip a line between Action: and Action Input:
- Run all 3 tools exactly once in order: check_web_headers, run_ffuf_discovery, run_subfinder
- Only write Final Answer: after all 3 tools have run

Begin!

Question: {input}
{agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

# ── 4. Agent ──────────────────────────────────────────────────────────────────
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True,
    max_iterations=12,
    early_stopping_method="force",
    return_intermediate_steps=True,
)

# ── 5. Run ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    target_domain = "juice-shop"
    target_url = f"http://{target_domain}:3000"

    wait_for_juice_shop(target_url)

    task = (
        f"Run check_web_headers on '{target_url}', "
        f"then run_ffuf_discovery on '{target_domain}', "
        f"then run_subfinder on '{target_domain}', "
        f"then write a Final Answer report."
    )

    result = agent_executor.invoke({"input": task})

    print("\n" + "=" * 60)
    print("FINAL REPORT")
    print("=" * 60)
    print(result.get("output", "No output produced."))