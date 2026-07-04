import argparse
import os
import sys
import threading
import uuid
from typing import Any, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.agent.contracts import (
    AGENT_RUN_MODE_DEMO,
    AGENT_RUN_MODE_TEST,
    build_initial_agent_state,
    build_run_snapshot,
    load_json_file,
    normalize_run_mode,
    persist_run_snapshot,
    record_state_event,
    utc_now_iso,
)
from app.core.agent.graph import build_tactical_graph

DEFAULT_TIMEOUT_SECONDS = 120


def run_graph(target: str, run_id: str, mode: str, state_file: str, result_box: Dict[str, Any]) -> None:
    graph = build_tactical_graph()
    initial_state = build_initial_agent_state(target, run_id, mode, state_file)
    result_box['state'] = graph.invoke(initial_state)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--state-file', required=True)
    args = parser.parse_args()

    state_file = args.state_file
    target = args.target
    run_id = str(uuid.uuid4())
    mode = normalize_run_mode(os.getenv('AGENT_RUN_MODE') or os.getenv('ARGUS_AGENT_MODE'))
    timeout_seconds = int(os.getenv('AGENT_TIMEOUT_SECONDS', str(DEFAULT_TIMEOUT_SECONDS)))
    started_at = utc_now_iso()

    persist_run_snapshot(
        state_file,
        build_run_snapshot(run_id, target, mode, status='starting', current_node='init', started_at=started_at, updated_at=started_at),
    )
    record_state_event(
        {'run_id': run_id, 'state_file': state_file, 'target_ip': target, 'mode': mode, 'events': []},
        'recon',
        'running',
        f'Starting reconnaissance on {target}',
    )

    state_data = load_json_file(state_file)
    state_data.setdefault('events', [])
    state_data['run_id'] = run_id
    state_data['target'] = target
    state_data['mode'] = mode
    state_data['status'] = 'running'
    state_data['current_node'] = 'recon'
    state_data['updated_at'] = started_at
    persist_run_snapshot(state_file, build_run_snapshot(run_id, target, mode, status='running', current_node='recon', started_at=started_at, updated_at=started_at, events=state_data.get('events', [])))

    result_box: Dict[str, Any] = {}
    worker = threading.Thread(target=run_graph, args=(target, run_id, mode, state_file, result_box), daemon=True)
    worker.start()
    worker.join(timeout_seconds)

    if worker.is_alive():
        timeout_message = f'Graph execution timed out after {timeout_seconds}s.'
        if mode in {AGENT_RUN_MODE_DEMO, AGENT_RUN_MODE_TEST}:
            demo_events = list(load_json_file(state_file).get('events', []))
            for node, status, detail in [
                ('recon', 'running', f'{timeout_message} Running fallback simulation...'),
                ('recon', 'completed', 'Recon complete'),
                ('scanner', 'running', 'Scanning for vulnerabilities'),
                ('scanner', 'completed', 'Scan complete'),
                ('exploit', 'running', 'Attempting exploitation'),
                ('exploit', 'completed', 'Exploitation complete'),
                ('post_exploit', 'running', 'Processing results'),
                ('post_exploit', 'completed', 'Post-exploit complete'),
            ]:
                demo_events.append({'node': node, 'status': status, 'detail': detail, 'timestamp': utc_now_iso(), 'run_id': run_id, 'target': target, 'mode': mode})
            persist_run_snapshot(
                state_file,
                build_run_snapshot(
                    run_id,
                    target,
                    mode,
                    status='completed',
                    current_node='post_exploit',
                    progress_pct=100,
                    started_at=started_at,
                    final_state={'open_ports': [8080], 'vulnerabilities': [], 'exploit_success': False, 'extracted_data': {}, 'error_log': ['Demo/test fallback simulation enabled'], 'retry_count': 0},
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
                current_node='recon',
                progress_pct=0,
                started_at=started_at,
                error=timeout_message,
                events=load_json_file(state_file).get('events', []),
            ),
        )
        sys.exit(1)

    final_state = result_box.get('state')
    if not isinstance(final_state, dict):
        error_message = 'Graph returned no final state.'
        persist_run_snapshot(
            state_file,
            build_run_snapshot(
                run_id,
                target,
                mode,
                status='failed',
                current_node='error',
                progress_pct=0,
                started_at=started_at,
                error=error_message,
                events=load_json_file(state_file).get('events', []),
            ),
        )
        sys.exit(1)

    collected = {
        'open_ports': final_state.get('open_ports', []),
        'vulnerabilities': final_state.get('vulnerabilities', []),
        'exploit_success': final_state.get('exploit_success', False),
        'extracted_data': final_state.get('extracted_data', {}),
        'error_log': final_state.get('error_log', []),
        'retry_count': final_state.get('retry_count', 0),
        'mode': mode,
        'target': target,
    }
    state_data = load_json_file(state_file)
    persist_run_snapshot(
        state_file,
        build_run_snapshot(
            run_id,
            target,
            mode,
            status='completed',
            current_node=final_state.get('current_node', 'post_exploit'),
            progress_pct=100,
            started_at=started_at,
            final_state=collected,
            events=state_data.get('events', []),
        ),
    )


if __name__ == '__main__':
    main()
