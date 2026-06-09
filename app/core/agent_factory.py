from typing import Sequence

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool


DEFAULT_MAX_ITERATIONS = 50
"""Default safety limit for the maximum number of reasoning/action steps an agent can execute."""


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

    This factory function centralizes the creation of the ReAct agent and its
    executor configuration. Keeping this logic in one place improves
    maintainability and ensures that all agents are created with the same
    execution rules.

    Args:
        llm:
            The language model responsible for reasoning and generating actions.

        tools:
            A sequence of LangChain tools available to the agent during execution.

        prompt:
            The prompt template that defines the agent behavior, instructions,
            available tool format, and reasoning structure.

        verbose:
            Enables detailed execution logs when set to True. Useful during
            development and debugging.

        max_iterations:
            Maximum number of reasoning/action cycles allowed before the agent
            stops. This prevents infinite loops or excessive tool usage.

    Returns:
        AgentExecutor:
            A configured LangChain AgentExecutor ready to receive user input.
    """

    # Create the ReAct agent using the provided language model, tools, and prompt.
    agent = create_react_agent(
        llm=llm,
        tools=tools,
        prompt=prompt,
    )

    # Wrap the agent inside an AgentExecutor to manage execution behavior,
    # tool invocation, parsing errors, iteration limits, and stopping strategy.
    return AgentExecutor(
        agent=agent,
        tools=list(tools),
        verbose=verbose,
        handle_parsing_errors=True,
        max_iterations=max_iterations,
        early_stopping_method="generate",
    )