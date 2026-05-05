import os
from langchain_community.llms import Ollama
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from tools import check_web_headers, run_subfinder

# 1. Configuration
llm = Ollama(model="dolphin-llama3", base_url="http://ollama-service:11434")

# 2. Explicit Tool Integration
# Note: We wrap the tools in a way that gives the LLM clear "Stop" conditions.
tools = [check_web_headers, run_subfinder]

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
    target = "http://juice-shop:3000"
    # Provide a more descriptive task to the agent
    task = (
        f"Perform a security header analysis on {target}. "
        "If headers are missing, list which common ones are absent. "
        "Do not repeat the same tool call if it returns no results."
    )
    agent_executor.invoke({"input": task})