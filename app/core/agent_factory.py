import re
from typing import Sequence, Union

from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_classic.agents.output_parsers import ReActSingleInputOutputParser
from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.exceptions import OutputParserException
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool

DEFAULT_MAX_ITERATIONS = 8
DEFAULT_MIN_ACTIONS_BEFORE_FINISH = 3

# Matches a JSON object or array anywhere in the text
_JSON_BLOCK_RE = re.compile(r"\{[\s\S]*\}|\[[\s\S]*\]")

# Literal strings lifted straight from the one-shot demo in prompts.py.
# If a model reproduces these verbatim, it copy-pasted the example
# instead of doing any real work - always reject regardless of step count.
_DEMO_ECHO_MARKERS = (
    "Example high-level executive summary",
    "Discovered 1 active host with port 80 open",
    "Everything checks out fine",
)


class LenientReActOutputParser(ReActSingleInputOutputParser):
    """
    Small local models (e.g. WhiteRabbitNeo-7B) frequently skip the
    'Final Answer:' preamble and just dump a raw JSON report the moment
    they're given a concrete target (a URL/domain). The stock LangChain
    parser treats that as a formatting error, which sends the model into
    an error->retry->same-mistake loop until max_iterations is hit.

    This parser tries the normal strict ReAct parse first. If that fails
    AND the text contains a JSON object/array, it *may* treat the JSON as
    an implicit Final Answer - but only if it isn't just a verbatim copy
    of the prompt's own demo text. Minimum-tool-call enforcement (has the
    model actually done anything yet) happens separately in brain.py,
    since intermediate step history isn't visible from inside a parser.
    """

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        try:
            return super().parse(text)
        except OutputParserException:
            match = _JSON_BLOCK_RE.search(text)
            if match and "Action:" not in text:
                if any(marker in text for marker in _DEMO_ECHO_MARKERS):
                    raise OutputParserException(
                        "You copied the example JSON from the instructions "
                        "verbatim instead of producing a real finding. "
                        "You must run actual tools (Check_Reachability, "
                        "Recon_Suite, etc.) and report what THEY returned, "
                        "not the example text. Continue with Thought: / "
                        "Action: / Action Input:."
                    )
                return AgentFinish(
                    {"output": match.group(0)},
                    text,
                )
            raise

_GENERIC_FORMAT_REMINDER = (
    "Invalid format. You forgot to include an 'Action:' step. "
    "Reminder: Thought: <reasoning>\nAction: <one tool name>\n"
    "Action Input: <raw value>\nOR, if you are truly finished, "
    "Final Answer: <json>."
)


def _describe_parsing_error(error: Exception) -> str:
    """
    AgentExecutor's handle_parsing_errors, when passed a plain string,
    discards the actual exception message and always sends that same
    fixed string back to the model - which means a specific correction
    (like "you copied the demo verbatim") never reaches the model, and
    it just repeats the same mistake forever. Passing a callable instead
    lets us forward whatever the parser actually said, falling back to a
    generic reminder only if the parser didn't raise anything specific.
    """
    msg = str(error).strip()
    return msg if msg else _GENERIC_FORMAT_REMINDER


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
        output_parser=LenientReActOutputParser(),
    )

    return AgentExecutor(
        agent=agent,
        tools=list(tools),
        verbose=verbose,
        handle_parsing_errors=_describe_parsing_error,
        max_iterations=max_iterations,
        early_stopping_method="generate",
        return_intermediate_steps=True,
    )