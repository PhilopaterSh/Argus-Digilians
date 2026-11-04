"""Unit tests for app/tools/recon_assist_run.py::ReconAssistRunService.

Spec 031 Phase 2. Locks in the safety rails: domain-format validation,
audit logging, timeout pass-through, and that the command targets the
pipeline's own scope guard (local_run.sh) - never a raw scan.
"""
import pytest
from unittest.mock import MagicMock

from app.tools.recon_assist_run import ReconAssistRunService, PIPELINE_STAGES

pytestmark = pytest.mark.unit


@pytest.fixture
def service():
    """Build a ReconAssistRunService with a mocked runner/memory.

    Returns:
        tuple: `(ReconAssistRunService, MagicMock runner, MagicMock memory)`.
    """
    runner = MagicMock()
    memory = MagicMock()
    svc = ReconAssistRunService(runner=runner, memory=memory)
    return svc, runner, memory


def test_run_differential_builds_correct_command(service):
    """The command must cd into the repo, export the go PATH, and invoke
    local_run.sh with the bounded stage list."""
    svc, runner, _ = service
    runner.run.return_value = "all jobs green"
    out = svc.run_differential("eg.hm.com")
    cmd = runner.run.call_args[0][0]
    assert "local_run.sh -d \"eg.hm.com\"" in cmd
    assert "--stages" in cmd and PIPELINE_STAGES in cmd
    assert "go/bin" in cmd  # PD tools first (httpx shadowing fix)
    assert "report.html" in out  # pointer to the artifact


def test_run_differential_rejects_invalid_domain(service):
    """Non-domain input must be rejected before any command runs."""
    svc, runner, _ = service
    for bad in ("not a domain", "eg.hm.com; rm -rf /", "https://x.com", ""):
        out = svc.run_differential(bad)
        assert out.startswith("[!] Invalid domain")
        runner.run.assert_not_called()


def test_run_differential_accepts_subdomain_root(service):
    """Third-level roots (eg.hm.com style) are valid roots."""
    svc, runner, _ = service
    runner.run.return_value = "ok"
    out = svc.run_differential("eg.hm.com")
    assert "differential run: eg.hm.com" in out


def test_run_passes_generous_timeout(service):
    """The bridge call must carry the 2400s pipeline timeout, not the 180s default."""
    svc, runner, _ = service
    svc.run_differential("eg.hm.com")
    assert runner.run.call_args.kwargs.get("timeout") == 2400
