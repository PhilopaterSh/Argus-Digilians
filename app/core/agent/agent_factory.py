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

    Args:
        llm (BaseLanguageModel): The LLM the agent reasons with.
        tools (Sequence[BaseTool]): Tools available to the agent.
        prompt (PromptTemplate): The ReAct prompt template.
        verbose (bool): Passed through to `AgentExecutor`.
        max_iterations (int): Max ReAct loop iterations before giving up.

    Returns:
        AgentExecutor: Configured with `handle_parsing_errors=True` and
        `early_stopping_method="generate"`.
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
