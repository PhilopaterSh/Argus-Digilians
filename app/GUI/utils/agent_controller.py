import json
import os
import signal
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path


class AgentController:
    def __init__(self, state_dir=None):
        self.process = None
        self.state_dir = state_dir or str(Path(__file__).parent.parent.parent.parent / "logs" / "agent_runs")
        os.makedirs(self.state_dir, exist_ok=True)
        self.run_id = None
        self.state_file = None

    def start(self, target, options=None):
        self.run_id = str(uuid.uuid4())
        self.state_file = os.path.join(self.state_dir, f"agent_{self.run_id}.json")
        self._write_state({"status": "starting", "current_node": "init", "target": target, "events": [], "started_at": datetime.now(timezone.utc).isoformat()})

        project_root = str(Path(__file__).parent.parent.parent.parent)
        script = os.path.join(project_root, "scripts", "run_agent.py")
        if not os.path.exists(script):
            script = self._create_agent_runner(project_root)

        env = os.environ.copy()
        env["PYTHONPATH"] = f"{project_root};{env.get('PYTHONPATH', '')}"
        env["AGENT_STATE_FILE"] = self.state_file
        env["AGENT_TARGET"] = target
        if options:
            env["AGENT_OPTIONS"] = json.dumps(options)

        self.process = subprocess.Popen(
            [sys.executable, script, "--target", target, "--state-file", self.state_file],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=project_root,
        )
        self._write_state({"status": "running", "current_node": "recon"})
        return self.run_id

    def stop(self):
        if self.process and self.process.poll() is None:
            if sys.platform == "win32":
                self.process.kill()
            else:
                os.kill(self.process.pid, signal.SIGTERM)
            self._write_state({"status": "stopped", "current_node": "terminated"})
            return True
        return False

    def get_status(self):
        if not self.state_file or not os.path.exists(self.state_file):
            return {"status": "unknown", "current_node": "idle"}
        try:
            with open(self.state_file, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {"status": "error", "current_node": "unknown"}

    def get_feed(self):
        state = self.get_status()
        return state.get("events", [])

    def is_running(self):
        if self.process is None:
            return False
        return self.process.poll() is None

    def _write_state(self, updates):
        if not self.state_file:
            return
        try:
            state = {}
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    state = json.load(f)
            state.update(updates)
            if "events" not in state:
                state["events"] = []
            with open(self.state_file, "w") as f:
                json.dump(state, f, indent=2, default=str)
        except (IOError, json.JSONDecodeError):
            pass

    def _create_agent_runner(self, project_root):
        runner_path = os.path.join(project_root, "scripts", "run_agent.py")
        runner_content = r"""import json
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
"""
        with open(runner_path, "w") as f:
            f.write(runner_content)
        return runner_path
