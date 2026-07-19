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

    def on_graph_event(self, status: str, detail: str) -> None:
        """Record a step from a raw LangGraph `StateGraph.stream()` loop (specs/018).

        The four hooks above are LangChain's `AgentExecutor`-specific
        callback dispatch, which a plain `StateGraph` (e.g.
        `app/core/agent/react_workflow.py`'s custom graph) never triggers.
        `ArgusBrain`'s structured-graph path calls this directly instead,
        once per streamed state update, reusing the same event contract.

        Args:
            status (str): "running"/"completed"/"failed", per
                `app/core/agent/contracts.py`'s event status convention.
            detail (str): Human-readable description of the step.
        """
        self._emit(status, detail)


class ConsoleTraceCallbackHandler:
    """Prints every ReAct step live to stdout - the CLI's equivalent of
    `LiveFeedCallbackHandler` above, which writes to the GUI's state-file
    feed instead. Added 2026-07-10: `scripts/run_argus_cli.py` previously
    passed no callbacks at all to `brain.ask()`, so a CLI run showed only
    individual tools' own `print()` statements and the final JSON report -
    every `Thought:`/`Action:` the model actually reasoned through, every
    `Observation:` it received, and every specs/019 `Reflection:` note was
    invisible. This is the single source of truth for CLI trace-printing -
    `scripts/run_argus_cli.py` and `scripts/_diagnostic_cli_verbose.py` both
    import it rather than each keeping their own copy (Constitution IX).

    Only implements `on_graph_event`, matching how `ArgusBrain`'s current
    production path (`react_workflow.py`'s custom `StateGraph`) actually
    drives callbacks - see `LiveFeedCallbackHandler.on_graph_event`'s own
    docstring for why the four `AgentExecutor`-specific hooks above are not
    triggered by this path.
    """

    def __init__(self):
        """Init  ."""
        self._step = 0

    def on_graph_event(self, status: str, detail: str) -> None:
        """Print one step, labeled by what it actually contains.

        `detail` carries raw message text with no separate structured type
        field, so the label is inferred from the message's own prefix -
        `react_workflow.py`'s `_build_reflection_note()`/`_inter_reflect()`
        (specs/019) messages start with "Reflection:", tool results start
        with "Observation:" (`execute_node`), everything else is the
        model's own Thought/Action/Final-Answer text (`agent_node`).
        """
        if detail.startswith("Reflection:"):
            print(f"\n[REFLECTION] ({status})")
            print(detail)
        elif detail.startswith("Observation:"):
            print("\n[TOOL RESULT]")
            print(detail)
        else:
            self._step += 1
            print(f"\n{'=' * 70}")
            print(f"STEP {self._step} - AI Reasoning ({status})")
            print("=" * 70)
            print(detail)
