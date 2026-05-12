from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

class ArgusBrain:
    def __init__(self, model_name, tools_list):
        self.llm = OllamaLLM(model=model_name, timeout=120)
        self.tools = tools_list
        self.agent_executor = self._setup_agent()

    def _setup_agent(self):
        template = """You are Argus AI, a senior security researcher.
CRITICAL MANDATE: Before using any other tool or performing any analysis on a target, you MUST first verify its reachability using the 'Check_Reachability' tool. 

If the target is unreachable, stop immediately and report the failure. 
If the target is reachable, proceed with further reconnaissance or analysis as requested.

Tools available: {tools}

Use the following format:
Question: {input}
Thought: I must first check if the target is reachable.
Action: Check_Reachability
Action Input: (the domain or URL)
Observation: (result of the reachability check)
... (proceed only if reachable)

When you have the final answer, use this format:
Final Answer: your summary

Available tool names: {tool_names}

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def ask(self, query):
        return self.agent_executor.invoke({"input": query})
