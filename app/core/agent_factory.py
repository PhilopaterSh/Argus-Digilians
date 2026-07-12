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

# Literal strings from ARGUS_ADAPTIVE_AGENT_TEMPLATE's own worked example
# in prompts.py. If a model reproduces its fake target as a real Action
# Input, that's a copy-paste failure worth rejecting - see class
# docstring for why this needs its own check on the success path.
_DEMO_FAKE_TARGETS = (
    "sample-demo-host.test",
    "api.sample-demo-host.test",
    "admin.sample-demo-host.test",
)


class LenientReActOutputParser(ReActSingleInputOutputParser):
    """
    Small local models (e.g. WhiteRabbitNeo-7B) frequently skip the
    'Final Answer:' preamble and just dump a raw JSON report the moment
    they're given a concrete target (a URL/domain). The stock LangChain
    parser treats that as a formatting error, which sends the model into
    an error->retry->same-mistake loop until max_iterations is hit.

    This parser tries the normal strict ReAct parse first. If that fails
    AND the text contains a JSON object/array with no "Action:" anywhere,
    it treats the JSON as an implicit Final Answer instead of raising -
    the model clearly meant to finish, it just skipped the "Final
    Answer:" preamble.

    It also guards a sneakier copy-paste failure mode: the adaptive
    template's worked example includes a real-looking Action step
    against a fake target (sample-demo-host.test). That's syntactically
    valid ReAct, so the base parser accepts it without error - meaning a
    model that copies the example's Action Input instead of using the
    real target would otherwise sail through silently and waste a whole
    tool call scanning nothing.
    """

    def parse(self, text: str) -> Union[AgentAction, AgentFinish]:
        try:
            result = super().parse(text)
        except OutputParserException:
            match = _JSON_BLOCK_RE.search(text)
            if match and "Action:" not in text:
                return AgentFinish(
                    {"output": match.group(0)},
                    text,
                )
            raise

        if isinstance(result, AgentAction) and any(
            fake_target in str(result.tool_input) for fake_target in _DEMO_FAKE_TARGETS
        ):
            raise OutputParserException(
                "You used the FAKE example target from the instructions "
                "(sample-demo-host.test or one of its subdomains) as your "
                "Action Input instead of the real target you were actually "
                "given. That example was illustrative only. Re-issue this "
                "Action with the real target from the Question above."
            )

        return result

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