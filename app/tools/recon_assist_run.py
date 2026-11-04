"""Recon-Assist differential-run launcher - the execution half of the
Recon-Assist integration (spec 031 Phase 2).

While ``recon_assist.py`` is the read-side (load the pipeline's brief),
this service is the run-side: it launches the Recon-Assist differential
pipeline from inside Kali via the shared WSL bridge, bounded and scoped.

What it runs (per invocation):
  ./scripts/local_run.sh -d <domain> --stages enum,merge,probe,analyze,dorks,takeover,origin,html

Safety rails (spec 031 Phase 2, section "Guardrails"):
  - The pipeline's own scope guard re-validates every discovered host
    against the authorized roots before any probing.
  - A hard per-run timeout on the bridge call - a wedged run cannot
    block the agent loop.
  - Deep scan, fuzzing and dorks are NOT part of the tool (keep the
    cloud/local footprint minimal; run them manually when needed).

Usage (via the tool registry):
  recon_assist_run  ->  runs the differential pipeline for one domain
  recon_assist_status  ->  shows the latest report.html path + artifact
      summary of the previous run (no new scan).

Args:
  runner: shared CommandRunner (WSL/SSH bridge).
  memory: ArgusMemory (unused by the run itself; kept for parity).
  repo_path: absolute path to the Recon-Assist repo as seen from Kali
      (default: the mounted D-drive checkout).
"""

import re

from app.core import audit

PIPELINE_STAGES = "enum,merge,probe,analyze,dorks,takeover,origin,html"
DEFAULT_RUN_TIMEOUT = 2400  # 40 minutes - full differential pipeline
_DOMAIN_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*\.[a-z]{2,}$")


class ReconAssistRunService:
    """Launch the Recon-Assist differential pipeline through the bridge."""

    def __init__(self, runner, memory=None, repo_path: str = "/mnt/d/CV/Github/GitHub Tools/Github Actions/Recon-Assist", timeout: int = DEFAULT_RUN_TIMEOUT):
        self.runner = runner
        self.memory = memory
        self.repo_path = repo_path.rstrip("/")
        self.timeout = timeout

    # ---------- public API ----------

    def run_differential(self, domain: str) -> str:
        """Run the differential pipeline for one authorized domain.

        Args:
            domain (str): Authorized root, e.g. ``"eg.hm.com"``. Must match
                the domain-format rule and be lowercase-normalized.

        Returns:
            str: Fenced Markdown tail of the pipeline run (stages + counts)
            for the agent loop, or a ``[!]`` error string. Never raises.
        """
        domain = domain.strip().lower()
        if not _DOMAIN_RE.match(domain):
            return "[!] Invalid domain format: " + domain
        audit.log_event("command", "agent", domain, "recon_assist differential run", "executed")

        script = f"{self.repo_path}/scripts/local_run.sh"
        cmd = (
            f'cd "{self.repo_path}" && '
            f'export PATH="$HOME/go/bin:/usr/local/go/bin:$PATH" && '
            f'./scripts/local_run.sh -d "{domain}" '
            f'--stages "{PIPELINE_STAGES}"'
        )
        out = self.runner.run(cmd, timeout=self.timeout)
        tail = _tail(out, 60)
        audit.log_event("command", "agent", domain, "recon_assist differential run", "executed")

        lines = [
            "```markdown",
            f"Recon-Assist differential run: {domain}",
            f"stages: {PIPELINE_STAGES}",
            f"report: {self.repo_path}/local_results/report.html",
            "",
            "=== tail ===",
            tail,
            "```",
        ]
        return "\n".join(lines)

    def run_status(self) -> str:
        """Show the latest local report.html summary (no new scan)."""
        cmd = (
            f'cd "{self.repo_path}" && '
            f'if [ -f local_results/report.html ]; then '
            f'echo "report: local_results/report.html"; '
            f'ls -la local_results/ | head -12; '
            f'else echo "no local_results yet - run run_differential first"; fi'
        )
        out = self.runner.run(cmd, timeout=30)
        return "```bash\n" + _tail(out, 40) + "\n```"


# ---------- helpers ----------


def _tail(text: str, lines: int) -> str:
    lines_out = text.strip().splitlines()[-lines:]
    return "\n".join(lines_out)
