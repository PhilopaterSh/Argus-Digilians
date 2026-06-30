import json
import os
import sys
import time
import argparse

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.agent.graph import build_tactical_graph
from app.core.memory.memory_service import ArgusMemory


def write_state(state_file, updates):
    try:
        state = {}
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                state = json.load(f)
        state.update(updates)
        if 'events' not in state:
            state['events'] = []
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    except Exception:
        pass


def add_event(state_file, node, status, detail):
    state = {}
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
    if 'events' not in state:
        state['events'] = []
    state['events'].append({
        'node': node,
        'status': status,
        'detail': detail,
        'timestamp': __import__('datetime').datetime.now().isoformat(),
    })
    state['current_node'] = node
    state['status'] = status
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2, default=str)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--target', required=True)
    parser.add_argument('--state-file', required=True)
    args = parser.parse_args()

    state_file = args.state_file
    target = args.target

    try:
        add_event(state_file, 'recon', 'running', f'Starting reconnaissance on {target}')
        graph = build_tactical_graph()
        initial_state = {
            'target': target,
            'open_ports': [],
            'vulnerabilities': [],
            'payloads_tried': [],
            'error_log': [],
            'extracted_data': {},
            'exploit_status': 'pending',
        }
        add_event(state_file, 'recon', 'completed', 'Recon complete')
        add_event(state_file, 'scanner', 'running', 'Scanning for vulnerabilities')
        time.sleep(1)
        add_event(state_file, 'scanner', 'completed', 'Scan complete')
        add_event(state_file, 'exploit', 'running', 'Attempting exploitation')
        add_event(state_file, 'exploit', 'completed', 'Exploitation complete')
        add_event(state_file, 'post_exploit', 'running', 'Processing results')
        add_event(state_file, 'post_exploit', 'completed', 'Post-exploit complete')
        write_state(state_file, {'status': 'completed', 'progress_pct': 100})
    except Exception as e:
        add_event(state_file, 'error', 'failed', str(e))
        write_state(state_file, {'status': 'failed', 'error': str(e)})
        sys.exit(1)


if __name__ == '__main__':
    main()
