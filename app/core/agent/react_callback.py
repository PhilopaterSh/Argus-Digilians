"""Streams ArgusBrain's ReAct steps into the agent-run state file (specs/017).

Replaces StreamlitCallbackHandler (which only works when the agent runs in
the same process/session as the Streamlit script - see the historical
`PHILOPATERSH` branch's app/GUI/app.py). The current architecture runs the
agent in a separate subprocess (scripts/run_agent.py) for GUI responsiveness,
so this instead reuses the *existing* state-file event contract
(app/core/agent/contracts.py) that app/GUI/tabs/agent.py's "Agent Feed"
already polls and renders - no GUI changes needed to see these live.
"""
from typing import Any, Optional
from uuid import UUID

from langchain_core.agents import AgentAction, AgentFinish
from langchain_core.callbacks import BaseCallbackHandler

from app.core.agent.contracts import append_run_event, build_run_event

_TRUNCATE_CHARS = 500


class LiveFeedCallbackHandler(BaseCallbackHandler):
    """Appends each ReAct step (thought/action/observation) as a run event."""

    def __init__(self, state_file: str, run_id: str, target: str, mode: str):
        """Store the run identity needed to shape each appended event.

        Args:
            state_file (str): Path to the JSON state file
                `app/core/agent/contracts.py::append_run_event` writes to -
                the same file `AgentController`/`app/GUI/tabs/agent.py`
                already poll for this run.
            run_id (str): The current run's id, attached to every event.
            target (str): The target being analyzed, attached to every event.
            mode (str): The run mode (production/demo/test), attached to
                every event.
        """
        self.state_file = state_file
        self.run_id = run_id
        self.target = target
        self.mode = mode

    def _emit(self, status: str, detail: str) -> None:
        event = build_run_event(
            "agent", status, detail[:_TRUNCATE_CHARS],
            run_id=self.run_id, target=self.target, mode=self.mode,
        )
        append_run_event(self.state_file, event)

    def on_agent_action(self, action: AgentAction, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        """Record the LLM's chosen next step (its `Thought:`/`Action:` text).

        Args:
            action (AgentAction): The parsed action; `action.log` holds the
                raw LLM output for this step (includes the `Thought:` text
                per app/core/prompts.py's required format), `action.tool`
                and `action.tool_input` the parsed tool call.
        """
        thought = action.log.strip() if action.log else f"Action: {action.tool}"
        self._emit("running", f"{thought}\nAction Input: {action.tool_input}")

    def on_tool_end(self, output: Any, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        """Record a tool's result (the ReAct loop's "Observation")."""
        self._emit("completed", f"Observation: {output}")

    def on_tool_error(self, error: BaseException, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        """Record a tool execution failure as a real (non-fabricated) event."""
        self._emit("failed", f"Tool error: {error}")

    def on_agent_finish(self, finish: AgentFinish, *, run_id: UUID, parent_run_id: Optional[UUID] = None, **kwargs: Any) -> None:
        """Record that the agent produced its final answer."""
        self._emit("completed", "Agent finished - producing final security report.")
