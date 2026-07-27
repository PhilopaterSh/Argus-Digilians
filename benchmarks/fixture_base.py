"""Shared fixture contract for the subtask-level benchmark suite (specs/025).

Each fixture directory under `benchmarks/fixtures/<name>/` provides four files:
`server.py` (a `start_server(port=0) -> (base_url, stop_fn)` contract function),
`query.txt` (the natural-language task, with a `{target_url}` placeholder),
`flag.txt` (the ground-truth flag string), and `subtasks.yaml` (an ordered list
of `{name, detector_regex}` pairs used to compute the Subtask Completion Rate).
"""
import functools
import importlib.util
import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml


@dataclass
class Subtask:
    name: str
    detector_regex: str


@dataclass
class Fixture:
    name: str
    query_template: str
    flag: str
    subtasks: list[Subtask]
    fixture_dir: Path

    @classmethod
    def load(cls, fixture_dir: Path) -> "Fixture":
        """Read a fixture's four contract files from `fixture_dir`.

        Args:
            fixture_dir (Path): `benchmarks/fixtures/<name>/`.

        Returns:
            Fixture: parsed fixture ready for `start()`.
        """
        query_template = (fixture_dir / "query.txt").read_text(encoding="utf-8").strip()
        flag = (fixture_dir / "flag.txt").read_text(encoding="utf-8").strip()
        raw_subtasks = yaml.safe_load((fixture_dir / "subtasks.yaml").read_text(encoding="utf-8")) or []
        subtasks = [Subtask(name=s["name"], detector_regex=s["detector_regex"]) for s in raw_subtasks]
        return cls(
            name=fixture_dir.name,
            query_template=query_template,
            flag=flag,
            subtasks=subtasks,
            fixture_dir=fixture_dir,
        )

    def start(self, resolve_wsl_host: bool = True) -> tuple[str, Callable[[], None]]:
        """Start this fixture's mock server on an OS-assigned ephemeral port.

        Loads `server.py` as a standalone module (not a package import, so
        fixtures need no `__init__.py`) and calls its required
        `start_server(port: int = 0) -> (base_url, stop_fn)` contract
        function.

        Args:
            resolve_wsl_host (bool): If True (default), rewrite the returned
                `base_url`'s `127.0.0.1`/`localhost` host to an address
                reachable from inside the WSL/Kali guest (see
                `_wsl_reachable_host()` - confirmed live: Argus's tools run
                inside a separate WSL network namespace, Constitution IV, so
                a fixture bound on the Windows host is NOT reachable from
                there via plain loopback). Callers that never make a real
                network request against `base_url` (e.g. a fast unit test
                using a fake LLM that never triggers a tool call) should pass
                `False` to avoid the WSL subprocess round-trip entirely.

        Returns:
            tuple[str, Callable[[], None]]: `(base_url, stop_fn)` - `stop_fn`
                MUST be called (typically in a `finally` block) to shut the
                server down and free the port.
        """
        server_path = self.fixture_dir / "server.py"
        spec = importlib.util.spec_from_file_location(f"benchmarks.fixtures.{self.name}.server", server_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Cannot load fixture server module from {server_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        base_url, stop_fn = module.start_server(port=0)
        if resolve_wsl_host:
            base_url = re.sub(r"127\.0\.0\.1|localhost", _wsl_reachable_host(), base_url)
        return base_url, stop_fn

    def render_query(self, base_url: str) -> str:
        """Substitute `{target_url}` in `query_template` with `base_url`.

        Args:
            base_url (str): The fixture server's actual running URL.

        Returns:
            str: The natural-language task to give `ArgusBrain.ask()`.
        """
        return self.query_template.replace("{target_url}", base_url)


@functools.lru_cache(maxsize=1)
def _wsl_reachable_host() -> str:
    """Resolve the Windows host's address as seen from inside the WSL/Kali guest.

    Argus's tools execute inside a separate WSL network namespace
    (Constitution IV); a mock fixture server bound on the Windows host is
    NOT reachable from there via `127.0.0.1` - confirmed live (2026-07-23):
    a fixture server bound to `127.0.0.1` returned curl exit code 7
    ("failed to connect") from inside `kali-linux`, while the same server
    bound to `0.0.0.0` and addressed via WSL's own default-gateway IP
    (`ip route show default` inside the guest) worked. That gateway address
    is WSL2-version/machine-specific, so it is resolved live rather than
    hardcoded. Cached for the life of the process (one benchmark run).

    Returns:
        str: an IP address reachable from inside the WSL guest that routes
            to the Windows host, or `"127.0.0.1"` as a same-host fallback if
            WSL is unavailable or the lookup fails for any reason.
    """
    distro = os.environ.get("WSL_DISTRO", "kali-linux")
    try:
        result = subprocess.run(
            ["wsl", "-d", distro, "--", "ip", "route", "show", "default"],
            capture_output=True, text=True, timeout=15,
        )
        match = re.search(r"default via (\d+\.\d+\.\d+\.\d+)", result.stdout)
        if match:
            return match.group(1)
    except (OSError, subprocess.SubprocessError):
        pass
    return "127.0.0.1"


def flag_pattern_hint(flag: str) -> re.Pattern:
    """Case-insensitive regex matching an exact flag substring.

    Args:
        flag (str): The fixture's ground-truth flag string.

    Returns:
        re.Pattern: compiled case-insensitive substring pattern.
    """
    return re.compile(re.escape(flag), re.IGNORECASE)
