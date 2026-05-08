import os
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_react_agent, Tool
from langchain.prompts import PromptTemplate
from tools import run_ffuf_discovery # Only importing the relevant tool

# 1. Configuration
llm = Ollama(model="dolphin-llama3", base_url="http://ollama-service:11434")

# 2. Focused Tool Integration
# We only include FFUF in the list so the agent has no other options.
tools = [
    Tool(
        name="run_ffuf_discovery",
        func=run_ffuf_discovery,
        description="Active discovery tool. Use this to brute-force directories for a local domain. Input: domain name only (e.g., 'juice-shop')."
    )
]

# 3. Simplified Prompt Template
# This forces the agent to use FFUF and then immediately summarize the output.
template = """You are a Cybersecurity Reconnaissance Tool.
Your sole task is to run a directory discovery scan and report the findings.

FORMAT:
Question: the target to scan
Thought: I will run the directory discovery tool.
Action: run_ffuf_discovery
Action Input: the domain name
Observation: the tool output
Thought: I have the results.
Final Answer: [List the discovered paths here]

RULES:
1. ONLY use 'run_ffuf_discovery'.
2. Do not engage in conversation or ask for context.
3. If the observation contains file names like '.git' or '.passwd', list them all in the Final Answer.

Begin!

Question: {input}
Thought: {agent_scratchpad}"""

prompt = PromptTemplate.from_template(template)

# 4. Initialize Agent
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True,
    max_iterations=3 # Reduced as only one tool run is needed
)

if __name__ == "__main__":
    target_domain = "juice-shop" 

    # Simplified task
    task = f"Run a directory discovery scan on the target domain: {target_domain}"

    # Invoke the agent
    agent_executor.invoke({"input": task})