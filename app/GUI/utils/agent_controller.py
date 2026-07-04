import json
import os
import signal
import subprocess
import sys
import uuid
from pathlib import Path

from app.core.agent.contracts import (
    AGENT_RUNNER_ENTRYPOINT,
    AGENT_RUN_MODE_PRODUCTION,
    build_run_snapshot,
    normalize_run_mode,
    utc_now_iso,
)


class AgentController:
    def __init__(self, state_dir=None):
        self.process = None
        self.state_dir = state_dir or str(Path(__file__).parent.parent.parent.parent / 'logs' / 'agent_runs')
        os.makedirs(self.state_dir, exist_ok=True)
        self.run_id = None
        self.state_file = None
        self.run_mode = AGENT_RUN_MODE_PRODUCTION

    def start(self, target, options=None):
        self.run_id = str(uuid.uuid4())
        self.state_file = os.path.join(self.state_dir, f'agent_{self.run_id}.json')
        self.run_mode = normalize_run_mode(os.getenv('AGENT_RUN_MODE') or os.getenv('ARGUS_AGENT_MODE'))

        self._write_state(
            build_run_snapshot(
                self.run_id,
                target,
                self.run_mode,
                status='starting',
                current_node='init',
                progress_pct=0,
            )
        )

        project_root = Path(__file__).parent.parent.parent.parent
        script = project_root / AGENT_RUNNER_ENTRYPOINT
        if not script.exists():
            raise FileNotFoundError(script)

        env = os.environ.copy()
        env['PYTHONPATH'] = f"{project_root};{env.get('PYTHONPATH', '')}"
        env['AGENT_RUN_MODE'] = self.run_mode
        env['AGENT_STATE_FILE'] = self.state_file
        env['AGENT_TARGET'] = target
        if options:
            env['AGENT_OPTIONS'] = json.dumps(options)

        self.process = subprocess.Popen(
            [sys.executable, '-u', str(script), '--target', target, '--state-file', self.state_file],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(project_root),
        )
        self._write_state({
            'status': 'running',
            'current_node': 'recon',
            'updated_at': utc_now_iso(),
            'run_id': self.run_id,
            'target': target,
            'mode': self.run_mode,
            'progress_pct': 0,
        })
        return self.run_id

    def stop(self):
        if self.process and self.process.poll() is None:
            if sys.platform == 'win32':
                self.process.kill()
            else:
                os.kill(self.process.pid, signal.SIGTERM)
            self._write_state({
                'status': 'stopped',
                'current_node': 'terminated',
                'updated_at': utc_now_iso(),
            })
            return True
        return False

    def get_status(self):
        if not self.state_file or not os.path.exists(self.state_file):
            return {'status': 'unknown', 'current_node': 'idle', 'events': []}
        try:
            with open(self.state_file, 'r', encoding='utf-8') as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            return {'status': 'error', 'current_node': 'unknown', 'events': []}

    def get_feed(self):
        state = self.get_status()
        return state.get('events', [])

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
                with open(self.state_file, 'r', encoding='utf-8') as handle:
                    state = json.load(handle)
            state.update(updates)
            if 'events' not in state:
                state['events'] = []
            state.setdefault('started_at', utc_now_iso())
            state['updated_at'] = updates.get('updated_at', utc_now_iso())
            with open(self.state_file, 'w', encoding='utf-8') as handle:
                json.dump(state, handle, indent=2, default=str)
        except (OSError, json.JSONDecodeError):
            pass

