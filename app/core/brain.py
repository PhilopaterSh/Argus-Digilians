from typing import Any, Sequence

from langchain_core.tools import BaseTool

from core.schemas import SecurityReport

from .agent_factory import build_agent_executor
from .llm_factory import build_ollama_llm
from .parser import ReportParsingService
from .prompts import build_argus_prompt


class ArgusBrain:
    """
    Public service layer for Argus AI.

    This class acts as the main facade for the AI agent. It is responsible only
    for coordinating the required dependencies and exposing simple public methods
    for interacting with the system.

    Responsibilities:
        - Initialize the LLM.
        - Register the available tools.
        - Build the agent prompt.
        - Create the agent executor.
        - Delegate response parsing to the report parser.

    This class intentionally does not contain:
        - Prompt template text.
        - LLM configuration details.
        - Agent construction logic.
        - Output parsing logic.

    Keeping those responsibilities in separate modules improves maintainability,
    testability, and compliance with the Separation of Concerns principle.
    """

    def __init__(self, model_name: str, tools_list: Sequence[BaseTool]):
        """
        Initialize the ArgusBrain service.

        Args:
            model_name:
                Name of the Ollama model used by the agent.

            tools_list:
                Sequence of LangChain-compatible tools that the agent can use
                during reasoning and execution.
        """

        # Create and configure the Ollama language model.
        # The actual LLM configuration is delegated to the LLM factory.
        self.llm = build_ollama_llm(model_name)

        # Store tools as a list to ensure compatibility with LangChain components.
        self.tools = list(tools_list)

        # Initialize the report parsing service using the expected Pydantic schema.
        # This keeps parsing and validation logic outside the brain class.
        self.report_parser = ReportParsingService(SecurityReport)

        # Build the agent prompt using parser-generated format instructions.
        # The prompt content itself is managed inside the prompts module.
        prompt = build_argus_prompt(
            self.report_parser.format_instructions()
        )

        # Create the LangChain AgentExecutor.
        # Agent construction details are delegated to the agent factory.
        self.agent_executor = build_agent_executor(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt,
        )

    def ask(
        self,
        query: str,
        callbacks: list[Any] | None = None,
    ) -> dict[str, Any]:
        """
        Run the full security-analysis agent with tool support.

        This method should be used when the user query requires the agent to
        reason, call tools, collect evidence, and generate a structured security
        report.

        Args:
            query:
                User question or target input to be analyzed by the agent.

            callbacks:
                Optional LangChain callbacks for streaming, tracing, logging,
                or UI progress updates.

        Returns:
            dict[str, Any]:
                Parsed agent result returned by the report parsing service.
        """

        # Include callback configuration only when callbacks are provided.
        config = {"callbacks": callbacks} if callbacks else None

        # Execute the agent using the user query as input.
        raw_result = self.agent_executor.invoke(
            {"input": query},
            config=config,
        )

        # Parse and validate the raw agent output using the report parser service.
        return self.report_parser.parse_agent_result(raw_result)

    def simple_ask(self, prompt: str) -> dict[str, str]:
        """
        Run a direct LLM call without using tools or the agent executor.

        This method is useful for lightweight analysis, rewriting, summarization,
        or any task that does not require reconnaissance tools or multi-step
        agent reasoning.

        Args:
            prompt:
                Direct prompt to send to the language model.

        Returns:
            dict[str, str]:
                Dictionary containing the raw LLM response under the "output" key.
        """

        # Send the prompt directly to the LLM without invoking tools.
        response = self.llm.invoke(prompt)

        # Return a consistent dictionary response format.
        return {"output": response}