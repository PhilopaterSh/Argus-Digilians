import subprocess
import os
from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

# Configuration
DISTRO_NAME = "kali-linux"
MODEL_NAME = "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B" # "dolphin-llama3"  Or "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B"

def run_wsl_command(command: str) -> str:
    """Executes a command inside the Kali WSL distribution and returns the output."""
    try:
        # Construct the WSL command
        full_command = f"wsl -d {DISTRO_NAME} bash -c \"{command}\""
        result = subprocess.run(full_command, capture_output=True, text=True, shell=True)
        
        if result.returncode != 0:
            return f"Error executing command: {result.stderr}"
        return result.stdout
    except Exception as e:
        return f"Exception occurred: {str(e)}"

# Define the tools
def whatweb_tool(url: str) -> str:
    """Identify technologies used by a website using WhatWeb."""
    return run_wsl_command(f"whatweb {url}")

def curl_tool(url: str) -> str:
    """Fetch the content of a URL using curl."""
    return run_wsl_command(f"curl -skI -A 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36' {url}")

def wget_tool(url: str) -> str:
    """Download a file or webpage using wget."""
    return run_wsl_command(f"wget -q -O - --no-check-certificate --user-agent='Mozilla/5.0' {url} | head -n 50")

def recon_workflow(url: str) -> str:
    """A comprehensive reconnaissance workflow that runs WhatWeb, Curl (headers), and Wget (content snippet) to understand a site's stack."""
    print(f"[*] Starting Multi-Tool Recon Workflow for: {url}")

    whatweb_res = whatweb_tool(url)
    curl_res = curl_tool(url)
    wget_res = wget_tool(url)

    report = f"""
### --- Argus Recon Report for {url} ---

#### 1. Technology Fingerprinting (WhatWeb):
{whatweb_res}

#### 2. HTTP Headers Analysis (Curl):
{curl_res}

#### 3. Initial Content Snippet (Wget):
{wget_res}

-------------------------------------------
"""
    return report

# Create LangChain Tool objects
tools = [
    Tool(
        name="Recon_Workflow",
        func=recon_workflow,
        description="The primary tool for initial analysis. It runs WhatWeb, Curl, and Wget together to identify technologies, headers, and site structure. Use this first for any new URL."
    ),
    Tool(
        name="WhatWeb",
        func=whatweb_tool,
        description="Useful for identifying web technologies, server headers, and CMS used by a website. Input should be a URL."
    ),
    Tool(
        name="Curl",
        func=curl_tool,
        description="Useful for fetching raw HTML content or performing HTTP requests. Input should be a URL."
    ),
    Tool(
        name="Wget",
        func=wget_tool,
        description="Useful for downloading content from a URL. Input should be a URL."
    )
]


# Initialize the LLM
try:
    llm = OllamaLLM(model=MODEL_NAME)
except Exception as e:
    print(f"Warning: Could not initialize Ollama with model {MODEL_NAME}. Ensure Ollama is running.")
    llm = None

# Set up the agent
if llm:
    # Get the standard ReAct prompt
    # You can also define a custom prompt for better security focus
    template = """You are Argus AI, a security research assistant. 
You have access to the following tools:

{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

    prompt = PromptTemplate.from_template(template)

    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True)

    def run_agent(query: str):
        print(f"\n[*] Argus Agent is processing: {query}")
        response = agent_executor.invoke({"input": query})
        return response["output"]

if __name__ == "__main__":
    print("--- Argus AI Agent Prototype ---")
    if llm:
        while True:
            user_input = input("\nEnter your security query (or 'exit' to quit): ")
            if user_input.lower() == 'exit':
                break
            try:
                answer = run_agent(user_input)
                print(f"\n[+] Argus Response:\n{answer}")
            except Exception as e:
                print(f"\n[!] Error: {str(e)}")
    else:
        print("Agent could not be started because the LLM is not initialized.")
