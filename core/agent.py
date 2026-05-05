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
Analyze the provided target carefully using your tools.
Format your final answer in a clear, structured way with emojis for readability.

Tools available: {tools}

Use the following format:
Question: {input}
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (repeat)
Final Answer: your summary

Question: {input}
Thought: {agent_scratchpad}"""

        prompt = PromptTemplate.from_template(template)
        agent = create_react_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True, handle_parsing_errors=True)

    def ask(self, query):
        return self.agent_executor.invoke({"input": query})
