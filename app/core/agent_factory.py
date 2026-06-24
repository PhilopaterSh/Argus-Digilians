from typing import Sequence
import os
import yaml
from langchain_classic.agents import AgentExecutor, create_react_agent
from langchain_core.language_models import BaseLanguageModel
from langchain_core.prompts import PromptTemplate
from langchain_core.tools import BaseTool

# ── Load runtime config from config.yaml ──────────────────────────────────────
_CONFIG_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'config.yaml')
_cfg: dict = {}
if os.path.exists(_CONFIG_PATH):
    try:
        with open(_CONFIG_PATH, 'r') as _f:
            _cfg = yaml.safe_load(_f) or {}
    except Exception:
        pass

DEFAULT_MAX_ITERATIONS: int = 50
_EARLY_STOPPING  = _cfg.get("early_stopping_method", "stop")
_MAX_ITERATIONS  = int(_cfg.get("max_iterations", DEFAULT_MAX_ITERATIONS))

def build_agent_executor(
    *,
    llm: BaseLanguageModel,
    tools: Sequence[BaseTool],
    prompt: PromptTemplate,
    verbose: bool = True,
    max_iterations: int = _MAX_ITERATIONS,
) -> AgentExecutor:
    """
    Build and configure a LangChain ReAct AgentExecutor.
    Runtime settings (early_stopping_method, max_iterations) are read from config.yaml.
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
        early_stopping_method=_EARLY_STOPPING,
    )
