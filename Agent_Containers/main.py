import os
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain.prompts import PromptTemplate
from tools import check_web_headers, run_subfinder, run_ffuf_discovery

# 1. Configuration
llm = Ollama(model="dolphin-llama3", base_url="http://ollama-service:11434")

# 2. Explicit Tool Integration
# Note: We wrap the tools in a way that gives the LLM clear "Stop" conditions.
tools = [
    Tool(
        name="check_web_headers",
        func=check_web_headers,
        description="Useful for analyzing HTTP security headers of a URL. Input should be a full URL (e.g., 'http://juice-shop:3000')."
    ),
    Tool(
        name="run_subfinder",
        func=run_subfinder,
        description="Passive discovery tool. Use this to find subdomains that are publicly indexed. Input should be a domain name (e.g., 'juice-shop')."
    ),
    Tool(
        name="run_ffuf_discovery",
        func=run_ffuf_discovery,
        description="Active discovery tool. Use this to brute-force directories or subdomains for a local domain using a wordlist. Input should be the domain name only (e.g., 'juice-shop')."
    )
]

# 3. Create an EXPLICIT Prompt Template
# This replaces hub.pull("hwchase17/react") to give you more control.
template = """Answer the following questions as best you can. You have access to the following tools:

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

IMPORTANT RULES:
1. If 'check_web_headers' returns 'No security headers found', do NOT try again. This IS your finding.
2. If 'run_subfinder' returns 'None' or an error, do not keep trying. 
3. 'run_subfinder' only works on domains (e.g., example.com), not URLs with ports like :3000.
4. If you cannot find information, state that clearly in your Final Answer.

Begin!

Question: {input}
Thought:{agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

# 4. Initialize Agent
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True,
    max_iterations=5  # Hard limit to prevent infinite loops
)

if __name__ == "__main__":
    # The URL for header analysis and the target for fuzzing
    target_url = "http://juice-shop:3000" 
    target_domain = "juice-shop" 

    # The updated task focusing on headers and active fuzzing
    task = (
        f"Use the 'run_ffuf_discovery' tool to scan the domain '{target_domain}'. "
        "This is your primary priority. Do not perform any other actions "
        "until you have the results from this specific tool."
    )

    # Invoke the agent with the new instructions
    agent_executor.invoke({"input": task})