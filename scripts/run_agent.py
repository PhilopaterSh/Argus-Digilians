import argparse
import os
import sys
import threading
import uuid
from typing import Any, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.agent.brain_tools import build_argus_tools
from app.core.agent.contracts import (
    AGENT_RUN_MODE_DEMO,
    AGENT_RUN_MODE_TEST,
    append_run_event,
    build_run_event,
    build_run_snapshot,
    load_json_file,
    normalize_run_mode,
    persist_run_snapshot,
    utc_now_iso,
)
from app.core.agent.react_callback import LiveFeedCallbackHandler
from app.core.agent.brain import ArgusBrain
from app.core.config import ArgusConfig
from app.tools.tool_registry import WSLBridgeTools


# ArgusBrain's ReAct loop (app/core/agent/agent_factory.py, max_iterations=50)
# can make far more tool calls than the old fixed 3-phase pipeline it
# replaces (specs/017-restore-react-agent) - each real recon/scan tool call
# can itself take 60-180s. 900s is the same default the old pipeline needed
# for a single recon->scanner->exploit pass; a full free-form run exploring
# many tools may need more. Override via AGENT_TIMEOUT_SECONDS if a run
# needs more headroom than this.
#
# Raised 900 -> 1800 (30 min) so the "full" scan profile can complete: the
# full deterministic pipeline (Subdomain_Enumeration + Recon_Suite + Run_Nikto
# + Run_FFUF + Path_Traversal_Scan + Advanced_Evasion_Probe) plus chained
# follow-ups can exceed the old 900s budget on a slow target. Set
# ARGUS_SCAN_PROFILE=fast for the trimmed run, or override AGENT_TIMEOUT_SECONDS.
DEFAULT_TIMEOUT_SECONDS = 1800

ANALYSIS_QUERY_TEMPLATE = (
    "CONSULT MEMORY FIRST using 'Query_Memory'. Then perform a comprehensive security "
    "analysis for {target}. If findings like SQLi, Path Traversal, or sensitive files "
    "already exist in memory, use 'Exploit_Suggester' and 'Smart_Web_Search' to CHAIN "
    "them and reach maximum impact (RCE). Finally, provide a deep risk assessment "
    "including the full attack chain."
)


def run_brain_analysis(target: str, run_id: str, mode: str, state_file: str, result_box: Dict[str, Any]) -> None:
    """Run ArgusBrain's free-form ReAct loop against `target`.

    Args:
        target (str): Target URL/host to analyze.
        run_id (str): This run's id, threaded through every live-feed event.
        mode (str): production/demo/test - attached to every live-feed event.
        state_file (str): Path to the JSON state file the GUI polls; also
            where `LiveFeedCallbackHandler` appends each ReAct step live.
        result_box (Dict[str, Any]): Mutated in place with either `result`
            (ArgusBrain.ask()'s return value) or `error` (str) - this
            function runs on a background thread, so exceptions here would
            otherwise be silently lost to the caller.
    """
    try:
        model_name = os.getenv('SELECTED_MODEL') or ArgusConfig.load().model_name
        bridge = WSLBridgeTools()
        tools = build_argus_tools(bridge)
        brain = ArgusBrain(model_name, tools, memory=bridge.memory)
        handler = LiveFeedCallbackHandler(state_file, run_id, target, mode)
        query = ANALYSIS_QUERY_TEMPLATE.format(target=target)

        # Run the DETERMINISTIC pipeline, not the free-form ReAct loop. With a
        # weak local model the ReAct loop repeatedly re-calls a single tool
        # (observed: Smart_Web_Search x N) and never fires the exploit tools,
        # so nothing is ever detected. Passing on_phase makes brain.ask()
        # dispatch to ask_deterministic(): fixed Python-ordered phases
        # (recon -> scan -> Path_Traversal_Scan/Advanced_Evasion_Probe) plus a
        # single LLM call to synthesize the SecurityReport. Detection is
        # guaranteed by the pipeline, not left to the model's tool choice.
        def on_phase(index, total, tool_name, observation):
            event = build_run_event(
                'agent', 'completed',
                f'[Phase {index}/{total}] {tool_name}\n{str(observation)[:500]}',
                run_id=run_id, target=target, mode=mode,
            )
            append_run_event(state_file, event)

        result_box['result'] = brain.ask(query, callbacks=[handler], on_phase=on_phase)
    except Exception as e:
        result_box['error'] = str(e)


def _build_final_state(result: Dict[str, Any], mode: str, target: str) -> Dict[str, Any]:
    """Shape ArgusBrain's raw `ask()` return value into the persisted final_state.

    Args:
        result (Dict[str, Any]): `{"output": ...}` from `ArgusBrain.ask()` -
            `output` is a `SecurityReport`-shaped dict on successful
            structured parsing, or a raw string/dict otherwise (see
            `ArgusBrain._process_output`).
        mode (str): production/demo/test.
        target (str): The analyzed target.

    Returns:
        Dict[str, Any]: Always has `summary`/`attack_surface_stats`/
        `findings`/`overall_risk_score`/`next_steps`/`output`/`mode`/
        `target`. When the agent's output wasn't a valid structured
        report, those fields are left empty/None and `parse_warning`
        explains why - never fabricated to look like a real empty report
        (Constitution VIII - Truthful Runtime).
    """
    output = result.get('output') if isinstance(result, dict) else None
    if isinstance(output, dict) and 'error' not in output:
        return {
            'summary': output.get('summary', ''),
            'attack_surface_stats': output.get('attack_surface_stats', ''),
            'findings': output.get('findings', []),
            'overall_risk_score': output.get('overall_risk_score'),
            'next_steps': output.get('next_steps', []),
            'output': output.get('output', ''),
            'mode': mode,
            'target': target,
        }
    return {
        'summary': '',
        'attack_surface_stats': '',
        'findings': [],
        'overall_risk_score': None,
        'next_steps': [],
        'output': str(output) if output is not None else '',
        'mode': mode,
        'target': target,
        'parse_warning': 'Agent output was not a structured SecurityReport; showing raw output.',
    }


def main() -> None:
    """CLI entry point: run the agent against `--target`, write `--state-file`.

    Parses `--target`/`--state-file`/`--run-id` (see `--run-id`'s own help
    text), runs `run_brain_analysis` on a worker thread bounded by
    `AGENT_TIMEOUT_SECONDS`, and persists the final run snapshot
    (`_build_final_state`'s shape) to `--state-file` - `completed`,
    `failed`, or a demo/test-mode fallback on timeout. Exits with status 1
    on failure/timeout (outside demo/test mode) so the parent process (e.g.
    `AgentController`) can detect it via the subprocess's return code.

    Returns:
        None
    """
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--state-file', required=True)
    parser.add_argument(
        '--run-id',
        help=(
            'Run id to use for every event/snapshot written to --state-file. '
            'AgentController already generates one to name the state file itself '
            'before spawning this process - without this flag, this process used '
            'to silently generate a SECOND, different run_id and overwrite the '
            "state file's run_id field with it, so the file's name and its own "
            'contents disagreed about the run\'s identity. Falls back to a fresh '
            'uuid4 for standalone/manual invocations.'
        ),
    )
    args = parser.parse_args()

    state_file = args.state_file
    target = args.target
    run_id = args.run_id or str(uuid.uuid4())
    mode = normalize_run_mode(os.getenv('AGENT_RUN_MODE') or os.getenv('ARGUS_AGENT_MODE'))
    timeout_seconds = int(os.getenv('AGENT_TIMEOUT_SECONDS', str(DEFAULT_TIMEOUT_SECONDS)))
    started_at = utc_now_iso()

    persist_run_snapshot(
        state_file,
        build_run_snapshot(run_id, target, mode, status='starting', current_node='init', started_at=started_at, updated_at=started_at),
    )

    state_data = load_json_file(state_file)
    state_data.setdefault('events', [])
    persist_run_snapshot(state_file, build_run_snapshot(run_id, target, mode, status='running', current_node='agent', started_at=started_at, updated_at=started_at, events=state_data.get('events', [])))

    result_box: Dict[str, Any] = {}
    worker = threading.Thread(target=run_brain_analysis, args=(target, run_id, mode, state_file, result_box), daemon=True)
    worker.start()
    worker.join(timeout_seconds)

    if worker.is_alive():
        timeout_message = f'Agent execution timed out after {timeout_seconds}s.'
        if mode in {AGENT_RUN_MODE_DEMO, AGENT_RUN_MODE_TEST}:
            demo_events = list(load_json_file(state_file).get('events', []))
            for node, status, detail in [
                ('agent', 'running', f'{timeout_message} Running fallback simulation...'),
                ('agent', 'completed', 'Demo/test fallback analysis complete'),
            ]:
                demo_events.append({'node': node, 'status': status, 'detail': detail, 'timestamp': utc_now_iso(), 'run_id': run_id, 'target': target, 'mode': mode})
            persist_run_snapshot(
                state_file,
                build_run_snapshot(
                    run_id,
                    target,
                    mode,
                    status='completed',
                    current_node='agent',
                    progress_pct=100,
                    started_at=started_at,
                    final_state={
                        'summary': 'Demo/test fallback - no live analysis performed.',
                        'attack_surface_stats': '', 'findings': [], 'overall_risk_score': None,
                        'next_steps': [], 'output': 'Demo/test fallback simulation enabled',
                        'mode': mode, 'target': target,
                    },
                    events=demo_events,
                ),
            )
            return

        persist_run_snapshot(
            state_file,
            build_run_snapshot(
                run_id,
                target,
                mode,
                status='failed',
                current_node='agent',
                progress_pct=0,
                started_at=started_at,
                error=timeout_message,
                events=load_json_file(state_file).get('events', []),
            ),
        )
        sys.exit(1)

    state_data = load_json_file(state_file)
    if 'error' in result_box:
        persist_run_snapshot(
            state_file,
            build_run_snapshot(
                run_id, target, mode, status='failed', current_node='agent', progress_pct=0,
                started_at=started_at, error=result_box['error'], events=state_data.get('events', []),
            ),
        )
        sys.exit(1)

    result = result_box.get('result')
    if not isinstance(result, dict):
        persist_run_snapshot(
            state_file,
            build_run_snapshot(
                run_id, target, mode, status='failed', current_node='agent', progress_pct=0,
                started_at=started_at, error='Agent returned no result.', events=state_data.get('events', []),
            ),
        )
        sys.exit(1)

    persist_run_snapshot(
        state_file,
        build_run_snapshot(
            run_id, target, mode, status='completed', current_node='agent', progress_pct=100,
            started_at=started_at, final_state=_build_final_state(result, mode, target),
            events=state_data.get('events', []),
        ),
    )


if __name__ == '__main__':
    main()
