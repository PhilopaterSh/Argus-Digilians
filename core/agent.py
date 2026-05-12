from langchain_ollama import OllamaLLM
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.tools import Tool
from langchain_core.prompts import PromptTemplate

class ArgusBrain:
    def __init__(self, model_name, tools_list):
        self.llm = OllamaLLM(model=model_name, timeout=120, temperature=0.1)
        self.tools = tools_list
        self.agent_executor = self._setup_agent()

    def _setup_agent(self):
        template = """You are Argus AI, a senior security researcher.
Your task is to analyze security reconnaissance data.

CRITICAL RULES:
1. First, check if the target is reachable using 'Check_Reachability'.
2. If reachable, use 'Recon_Suite' to gather data.
3. After gathering data, provide a FINAL ANSWER immediately. Do NOT repeat tools.

Tools: {tools}

Format:
Question: {input}
Thought: I need to check reachability first.
Action: Check_Reachability
Action Input: (target)
Observation: (result)
Thought: Now I will perform the recon suite.
Action: Recon_Suite
Action Input: (target)
Observation: (recon data)
Thought: I have enough data to provide an analysis.
Final Answer: (Detailed security summary based on observations)

Available tool names: {tool_names}

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(
            agent=agent, 
            tools=self.tools, 
            verbose=True, 
            handle_parsing_errors=True,
            max_iterations=5,
            early_stopping_method="generate"
        )

    def ask(self, query):
        return self.agent_executor.invoke({"input": query})
