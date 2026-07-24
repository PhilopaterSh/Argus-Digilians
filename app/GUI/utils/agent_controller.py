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
        """Set up run-state defaults and ensure the state directory exists.

        Args:
            state_dir (str | None): Directory to write run-state/log
                files into; defaults to `<repo_root>/logs/agent_runs`.
        """
        self.process = None
        self.state_dir = state_dir or str(Path(__file__).parent.parent.parent.parent / 'logs' / 'agent_runs')
        os.makedirs(self.state_dir, exist_ok=True)
        self.run_id = None
        self.state_file = None
        self.run_mode = AGENT_RUN_MODE_PRODUCTION
        self.log_file = None
        self.log_path = None

    def start(self, target, options=None):
        """Spawn scripts/run_agent.py as a subprocess to analyze `target`.

        Args:
            target (str): Target URL/host to analyze.
            options (dict, optional): Extra options forwarded to the child
                process via the `AGENT_OPTIONS` env var (JSON-encoded).

        Returns:
            str: This run's id, also passed to the child via `--run-id` so
            the state file's own `run_id` field matches the id used to name
            the file - the child no longer generates its own, disagreeing,
            second id.

        Raises:
            FileNotFoundError: If `scripts/run_agent.py` doesn't exist at
                the expected path.
        """
        self.run_id = str(uuid.uuid4())
        self.state_file = os.path.join(self.state_dir, f'agent_{self.run_id}.json')
        self.run_mode = normalize_run_mode(os.getenv('AGENT_RUN_MODE') or os.getenv('ARGUS_AGENT_MODE'))

        # Written once, before the child process spawns, so the child's own
        # state-file writes (scripts/run_agent.py) never race a second write
        # from this parent process landing moments after Popen() - both sides
        # do non-atomic read-modify-write on the same file with no locking.
        self._write_state(
            build_run_snapshot(
                self.run_id,
                target,
                self.run_mode,
                status='running',
                current_node='recon',
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

        # subprocess.PIPE with nothing ever reading it has two problems, not
        # one: everything the child logs (including any silently-caught
        # exception like a "database is locked" write failure) is discarded
        # with no way to see it, AND if the child ever writes enough to fill
        # the OS pipe buffer, it blocks forever - a real hang risk on a
        # verbose/long scan. Redirect to a real file instead: visible, and
        # never blocks the child.
        self.log_path = os.path.join(self.state_dir, f'agent_{self.run_id}.log')
        self.log_file = open(self.log_path, 'w', encoding='utf-8', errors='replace')

        self.process = subprocess.Popen(
            [
                sys.executable, '-u', str(script),
                '--target', target,
                '--state-file', self.state_file,
                '--run-id', self.run_id,
            ],
            env=env,
            stdout=self.log_file,
            stderr=subprocess.STDOUT,
            cwd=str(project_root),
        )
        return self.run_id

    def stop(self):
        """Terminate the running agent subprocess, if one is active.

        Returns:
            bool: True if a running process was found and terminated
            (state updated to "stopped", log file closed); False if no
            process was running.
        """
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
            self._close_log()
            return True
        return False

    def _close_log(self):
        """Close log."""
        if self.log_file and not self.log_file.closed:
            self.log_file.close()

    def get_log_tail(self, max_lines=200):
        """Read the agent subprocess's captured stdout/stderr for diagnostics.

        Args:
            max_lines (int): Max trailing lines to return.

        Returns:
            str: The last `max_lines` lines of the log file, joined; "" if
            no log file exists yet or it can't be read.
        """
        if not self.log_path or not os.path.exists(self.log_path):
            return ""
        try:
            with open(self.log_path, 'r', encoding='utf-8', errors='replace') as handle:
                lines = handle.readlines()
            return "".join(lines[-max_lines:])
        except OSError:
            return ""

    def get_status(self):
        """Read the current run's state file.

        Returns:
            dict: The parsed state file, or a fallback
            `{"status": "unknown"/"error", ...}` dict if no state file
            exists yet or it fails to parse.
        """
        if not self.state_file or not os.path.exists(self.state_file):
            return {'status': 'unknown', 'current_node': 'idle', 'events': []}
        try:
            with open(self.state_file, 'r', encoding='utf-8') as handle:
                return json.load(handle)
        except (json.JSONDecodeError, OSError):
            return {'status': 'error', 'current_node': 'unknown', 'events': []}

    def get_feed(self):
        """Return the current run's event list.

        Returns:
            list: `get_status()["events"]`, or `[]` if absent.
        """
        state = self.get_status()
        return state.get('events', [])

    def is_running(self):
        """Whether the subprocess is still alive.

        Returns:
            bool: True if a process was started and hasn't exited yet;
            False otherwise (also closes the log file the first time a
            finished process is observed).
        """
        if self.process is None:
            return False
        running = self.process.poll() is None
        if not running:
            self._close_log()
        return running

    def _write_state(self, updates):
        """Merge `updates` into the state file's JSON content and write it back.

        Args:
            updates (dict): Fields to merge into the existing state (or a
                fresh `{}` if the file doesn't exist yet); `started_at`
                is set once, `updated_at` is refreshed on every call.
                Silently does nothing if the write/read fails or
                `self.state_file` isn't set.
        """
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

