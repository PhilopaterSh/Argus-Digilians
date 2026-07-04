import argparse
import json
import os
import sys
import threading
import uuid
from typing import Any, Dict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.agent.contracts import (
    AGENT_RUN_MODE_DEMO,
    AGENT_RUN_MODE_TEST,
    DEFAULT_AGENT_RUN_MODE,
    build_initial_agent_state,
    build_run_event,
    build_run_snapshot,
    normalize_run_mode,
    utc_now_iso,
)
from app.core.agent.graph import build_tactical_graph

DEFAULT_TIMEOUT_SECONDS = 120


def load_state(state_file: str) -> Dict[str, Any]:
    if not os.path.exists(state_file):
        return {}
    try:
        with open(state_file, 'r', encoding='utf-8') as handle:
            return json.load(handle)
    except (json.JSONDecodeError, OSError):
        return {}


def write_state(state_file: str, updates: Dict[str, Any]) -> None:
    state = load_state(state_file)
    state.update(updates)
    state.setdefault('events', [])
    state.setdefault('run_id', updates.get('run_id'))
    state.setdefault('target', updates.get('target'))
    state.setdefault('mode', updates.get('mode', DEFAULT_AGENT_RUN_MODE))
    state.setdefault('started_at', updates.get('started_at', utc_now_iso()))
    state['updated_at'] = updates.get('updated_at', utc_now_iso())
    with open(state_file, 'w', encoding='utf-8') as handle:
        json.dump(state, handle, indent=2, default=str)


def append_event(state_file: str, event: Dict[str, Any]) -> None:
    state = load_state(state_file)
    state.setdefault('events', [])
    state['events'].append(event)
    state['current_node'] = event.get('node', state.get('current_node', 'unknown'))
    state['status'] = event.get('status', state.get('status', 'unknown'))
    state['updated_at'] = event.get('timestamp', utc_now_iso())
    if event.get('target'):
        state['target'] = event['target']
    if event.get('run_id'):
        state['run_id'] = event['run_id']
    if event.get('mode'):
        state['mode'] = event['mode']
    with open(state_file, 'w', encoding='utf-8') as handle:
        json.dump(state, handle, indent=2, default=str)


def add_event(state_file: str, node: str, status: str, detail: str, *, run_id: str, target: str, mode: str) -> None:
    append_event(
        state_file,
        build_run_event(node, status, detail, run_id=run_id, target=target, mode=mode),
    )


def build_demo_final_state(target: str) -> Dict[str, Any]:
    return {
        'open_ports': [8080],
        'vulnerabilities': [],
        'exploit_success': False,
        'extracted_data': {},
        'error_log': ['Demo/test fallback simulation enabled'],
        'retry_count': 0,
        'mode': AGENT_RUN_MODE_DEMO,
        'target': target,
    }


def run_graph(target: str, run_id: str, mode: str, result_box: Dict[str, Any]) -> None:
    graph = build_tactical_graph()
    initial_state = build_initial_agent_state(target, run_id, mode)
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

    write_state(
        state_file,
        build_run_snapshot(
            run_id,
            target,
            mode,
            status='starting',
            current_node='init',
            started_at=started_at,
            updated_at=started_at,
        ),
    )
    add_event(state_file, 'recon', 'running', f'Starting reconnaissance on {target}', run_id=run_id, target=target, mode=mode)
    write_state(state_file, {'status': 'running', 'current_node': 'recon', 'run_id': run_id, 'target': target, 'mode': mode, 'progress_pct': 0})

    result_box: Dict[str, Any] = {}
    worker = threading.Thread(target=run_graph, args=(target, run_id, mode, result_box), daemon=True)
    worker.start()
    worker.join(timeout_seconds)

    if worker.is_alive():
        timeout_message = f'Graph execution timed out after {timeout_seconds}s.'
        if mode in {AGENT_RUN_MODE_DEMO, AGENT_RUN_MODE_TEST}:
            add_event(state_file, 'recon', 'running', f'{timeout_message} Running fallback simulation...', run_id=run_id, target=target, mode=mode)
            add_event(state_file, 'recon', 'completed', 'Recon complete', run_id=run_id, target=target, mode=mode)
            add_event(state_file, 'scanner', 'running', 'Scanning for vulnerabilities', run_id=run_id, target=target, mode=mode)
            add_event(state_file, 'scanner', 'completed', 'Scan complete', run_id=run_id, target=target, mode=mode)
            add_event(state_file, 'exploit', 'running', 'Attempting exploitation', run_id=run_id, target=target, mode=mode)
            add_event(state_file, 'exploit', 'completed', 'Exploitation complete', run_id=run_id, target=target, mode=mode)
            add_event(state_file, 'post_exploit', 'running', 'Processing results', run_id=run_id, target=target, mode=mode)
            add_event(state_file, 'post_exploit', 'completed', 'Post-exploit complete', run_id=run_id, target=target, mode=mode)
            write_state(
                state_file,
                build_run_snapshot(
                    run_id,
                    target,
                    mode,
                    status='completed',
                    current_node='post_exploit',
                    progress_pct=100,
                    started_at=started_at,
                    final_state=build_demo_final_state(target),
                ),
            )
            return

        add_event(state_file, 'error', 'failed', timeout_message, run_id=run_id, target=target, mode=mode)
        write_state(
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
            ),
        )
        sys.exit(1)

    final_state = result_box.get('state')
    if not isinstance(final_state, dict):
        error_message = 'Graph returned no final state.'
        add_event(state_file, 'error', 'failed', error_message, run_id=run_id, target=target, mode=mode)
        write_state(
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
            ),
        )
        sys.exit(1)

    add_event(state_file, 'recon', 'completed', 'Reconnaissance phase complete', run_id=run_id, target=target, mode=mode)

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
    add_event(state_file, 'post_exploit', 'completed', f'Pentest complete on {target}', run_id=run_id, target=target, mode=mode)
    write_state(
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
        ),
    )


if __name__ == '__main__':
    main()
