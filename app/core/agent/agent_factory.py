from typing import Sequence
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool

DEFAULT_MAX_ITERATIONS = 50

def build_agent_executor(
    *,
    llm: BaseLanguageModel,
    tools: Sequence[BaseTool],
    prompt: PromptTemplate,
    verbose: bool = True,
    max_iterations: int = DEFAULT_MAX_ITERATIONS,
) -> AgentExecutor:
    """
    Build and configure a LangChain ReAct AgentExecutor.
    """
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    return AgentExecutor(
        agent=agent,
        tools=list(tools),
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=max_iterations,
        early_stopping_method="generate",
    )
