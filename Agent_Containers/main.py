import os
import time
import requests
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain.prompts import PromptTemplate
from tools import (
    check_web_headers,
    run_subfinder,
    run_ffuf_discovery,
    run_nmap,
    run_nikto,
    run_gobuster,
    run_whatweb,
)

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
    temperature=0,
)

# ── 2. Tools ──────────────────────────────────────────────────────────────────
tools = [
    Tool(
        name="check_web_headers",
        func=check_web_headers.invoke,
        description=(
            "Fetches HTTP response headers and flags missing/present security headers. "
            "Input: full URL with port, e.g. 'http://juice-shop:3000'"
        ),
    ),
    Tool(
        name="run_nmap",
        func=run_nmap.invoke,
        description=(
            "Scans open ports and detects service versions with Nmap. "
            "Input: bare hostname only (no http://, no port), e.g. 'juice-shop'"
        ),
    ),
    Tool(
        name="run_nikto",
        func=run_nikto.invoke,
        description=(
            "Scans a web server for known vulnerabilities and misconfigurations with Nikto. "
            "Input: full URL with port, e.g. 'http://juice-shop:3000'"
        ),
    ),
    Tool(
        name="run_whatweb",
        func=run_whatweb.invoke,
        description=(
            "Fingerprints the technology stack (frameworks, JS libs, server software) using whatweb. "
            "Input: full URL with port, e.g. 'http://juice-shop:3000'"
        ),
    ),
    Tool(
        name="run_ffuf_discovery",
        func=run_ffuf_discovery.invoke,
        description=(
            "Brute-forces hidden paths using FFUF. "
            "Input: bare hostname only, e.g. 'juice-shop'. Port 3000 is added automatically."
        ),
    ),
    Tool(
        name="run_gobuster",
        func=run_gobuster.invoke,
        description=(
            "Brute-forces directories using Gobuster (complements FFUF). "
            "Input: bare hostname only, e.g. 'juice-shop'. Port 3000 is added automatically."
        ),
    ),
    Tool(
        name="run_subfinder",
        func=run_subfinder.invoke,
        description=(
            "Enumerates subdomains with Subfinder. "
            "Input: bare domain name only, e.g. 'juice-shop'"
        ),
    ),
]

# ── 3. Prompt ─────────────────────────────────────────────────────────────────
template = """You are a security reconnaissance agent. Run all tools against the target, then write a structured report.

Available tools:
{tools}

Use EXACTLY this format for every step — no deviations:

Thought: <one sentence explaining what you will do next>
Action: <tool name, must be one of: {tool_names}>
Action Input: <exact input for the tool>
Observation: <tool result — filled in automatically>
... (repeat Thought/Action/Action Input/Observation until all 7 tools have been used)
Thought: I have collected all reconnaissance data and will now write the final report.
Final Answer: <structured markdown report>

STRICT RULES:
- Run tools in this exact order: check_web_headers → run_nmap → run_nikto → run_wappalyzer → run_ffuf_discovery → run_gobuster → run_subfinder
- Never repeat a tool.
- Never skip a tool, even if a previous result was empty.
- Action Input must be on the very next line after Action, with no blank line between them.
- Only write Final Answer: after all 7 tools have produced an Observation.
- The Final Answer must be a structured report with these sections:
  1. Target Overview
  2. Open Ports & Services (from Nmap)
  3. Technology Stack (from Wappalyzer)
  4. Security Header Analysis (from check_web_headers)
  5. Vulnerability Findings (from Nikto)
  6. Discovered Paths (combined FFUF + Gobuster, deduplicated)
  7. Subdomain Enumeration (from Subfinder)
  8. Risk Summary & Recommendations

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
    max_iterations=20,          # 7 tools × ~2 steps each + buffer
    early_stopping_method="force",
    return_intermediate_steps=True,
)

# ── 5. Run ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    target_domain = "juice-shop"
    target_url = f"http://{target_domain}:3000"

    wait_for_juice_shop(target_url)

    task = (
        f"Perform a full reconnaissance of the target. "
        f"Run all 7 tools in order:\n"
        f"1. check_web_headers on '{target_url}'\n"
        f"2. run_nmap on '{target_domain}'\n"
        f"3. run_nikto on '{target_url}'\n"
        f"4. run_whatweb on '{target_url}'\n"
        f"5. run_ffuf_discovery on '{target_domain}'\n"
        f"6. run_gobuster on '{target_domain}'\n"
        f"7. run_subfinder on '{target_domain}'\n"
        f"Then write a structured Final Answer report."
    )

    result = agent_executor.invoke({"input": task})

    print("\n" + "=" * 60)
    print("FINAL RECONNAISSANCE REPORT")
    print("=" * 60)
    print(result.get("output", "No output produced."))