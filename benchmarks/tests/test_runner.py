"""Unit tests for benchmarks/runner.py (specs/025 T004).

Fast, no live Ollama/WSL needed (specs/025 NFR-003) - not collected by a
bare `pytest`/`pytest tests/` run since `benchmarks/` is outside
`pytest.ini`'s `testpaths`; run explicitly with `pytest benchmarks/tests/`.

Follows this codebase's existing convention (tests/test_agent/test_brain_ask.py):
never mock `ArgusBrain` itself - inject a fake LLM via its real `llm=` seam.
"""
import threading
from pathlib import Path

import pytest
from langchain_core.language_models.fake import FakeListLLM

from app.core.config import ArgusConfig
from benchmarks.fixture_base import Subtask
from benchmarks import runner as runner_module
from benchmarks.runner import (
    AggregatedResult,
    FixtureResult,
    SuiteReport,
    _aggregate_trials,
    _apply_config_overrides,
    _compute_scr,
    _compute_sr,
    _compute_tte,
    render_report,
    run_fixture,
    run_suite,
)


# --- _compute_sr ---

def test_compute_sr_matches_case_insensitive():
    """Verify Compute sr matches case insensitive."""
    assert _compute_sr("flag{abc}", "...found FLAG{ABC} in response...") is True


def test_compute_sr_no_match():
    """Verify Compute sr no match."""
    assert _compute_sr("flag{abc}", "nothing relevant here") is False


# --- _compute_scr ---

def test_compute_scr_partial_match():
    """Verify Compute scr partial match."""
    subtasks = [
        Subtask(name="find_env_file", detector_regex=r"\.env"),
        Subtask(name="find_config_backup", detector_regex=r"config\.php\.bak"),
    ]
    completed_steps = ["Observation: found /.env file with 200 status"]
    subtask_results, scr = _compute_scr(subtasks, completed_steps)
    assert subtask_results == {"find_env_file": True, "find_config_backup": False}
    assert scr == 0.5


def test_compute_scr_no_subtasks_is_zero():
    """Verify Compute scr no subtasks is zero."""
    subtask_results, scr = _compute_scr([], ["Observation: anything"])
    assert subtask_results == {}
    assert scr == 0.0


# --- _compute_tte ---

def test_compute_tte_finds_first_matching_completed_step():
    """Verify Compute tte finds first matching completed step."""
    completed_steps = [
        "Observation: scanning directory, no hits",
        "Observation: found /.env - DB_PASSWORD=x, API_KEY=flag{argus_env_leak_db_password}",
        "Observation: verifying content",
    ]
    tte = _compute_tte("flag{argus_env_leak_db_password}", completed_steps)
    assert tte == 2


def test_compute_tte_none_when_flag_absent():
    """Verify Compute tte none when flag absent."""
    assert _compute_tte("flag{missing}", ["Observation: nothing here"]) is None


# --- _apply_config_overrides ---

def test_apply_config_overrides_sets_and_resets(monkeypatch):
    """Verify Apply config overrides sets and resets."""
    _apply_config_overrides({"enable_inter_reflection": False})
    try:
        cfg = ArgusConfig.load()
        assert cfg.enable_inter_reflection is False
    finally:
        ArgusConfig.reset()

    # A later call with no overrides (or different overrides) must not see the
    # previous call's value leak through - proves reset() actually clears state.
    _apply_config_overrides({})
    try:
        cfg = ArgusConfig.load()
        assert cfg.enable_inter_reflection is True
    finally:
        ArgusConfig.reset()


# --- _aggregate_trials ---

def test_aggregate_trials_single_trial_matches_that_trial():
    """A single trial's aggregate must reduce to that trial's own numbers (trials=1 is the default)."""
    trial = FixtureResult(
        fixture_name="info_disclosure_env_leak", config_name="baseline", sr=True, scr=0.67,
        subtask_results={"find_env_file": True, "find_config_backup": False}, tte=2,
        duration_s=12.3, error=None,
    )
    agg = _aggregate_trials([trial])
    assert agg.trials == 1
    assert agg.solved_count == 1
    assert agg.sr_rate == 1.0
    assert agg.mean_scr == 0.67
    assert agg.stddev_scr == 0.0  # population stddev of one sample is defined as 0.0, not an error
    assert agg.mean_tte == 2.0
    assert agg.error_count == 0
    assert agg.subtask_match_rates == {"find_env_file": 1.0, "find_config_backup": 0.0}


def test_aggregate_trials_mixed_results():
    """Verify Aggregate trials mixed results.

    Mirrors this project's own real ablation history (specs/025 T009): two
    trials disagreeing on SR/SCR must average, not silently pick one.
    """
    trials = [
        FixtureResult("xss_reflected", "baseline", sr=False, scr=0.67,
                       subtask_results={"a": True, "b": True}, tte=None, duration_s=90.0, error=None),
        FixtureResult("xss_reflected", "baseline", sr=False, scr=0.33,
                       subtask_results={"a": True, "b": False}, tte=None, duration_s=85.0, error=None),
        FixtureResult("xss_reflected", "baseline", sr=True, scr=1.0,
                       subtask_results={"a": True, "b": True}, tte=5, duration_s=110.0, error="timeout"),
    ]
    agg = _aggregate_trials(trials)
    assert agg.trials == 3
    assert agg.solved_count == 1
    assert agg.sr_rate == pytest.approx(1 / 3)
    assert agg.mean_scr == pytest.approx((0.67 + 0.33 + 1.0) / 3)
    assert agg.mean_tte == 5.0  # only the one solved trial has a TTE
    assert agg.error_count == 1
    assert agg.subtask_match_rates == {"a": 1.0, "b": pytest.approx(2 / 3)}


def test_aggregate_trials_none_solved_has_no_tte():
    """Verify Aggregate trials none solved has no tte."""
    trials = [
        FixtureResult("f", "c", sr=False, scr=0.0, subtask_results={}, tte=None, duration_s=1.0, error=None),
        FixtureResult("f", "c", sr=False, scr=0.0, subtask_results={}, tte=None, duration_s=1.0, error=None),
    ]
    agg = _aggregate_trials(trials)
    assert agg.mean_tte is None


# --- render_report ---

def test_render_report_shape():
    """Verify Render report shape."""
    agg = AggregatedResult(
        fixture_name="info_disclosure_env_leak", config_name="baseline", trials=1, solved_count=1,
        sr_rate=1.0, mean_scr=0.67, stddev_scr=0.0, mean_tte=2.0, error_count=0,
        subtask_match_rates={"find_env_file": 1.0, "find_config_backup": 0.0},
    )
    report = SuiteReport(timestamp="20260723T000000Z", configs={"baseline": {}}, trials=1, results={"baseline": [agg]})
    markdown = render_report(report)
    assert "# Benchmark Suite Report - 20260723T000000Z" in markdown
    assert "## Aggregate" in markdown
    assert "| baseline | 1/1 | 0.67 (+/- 0.00) | 2.0 |" in markdown
    assert "## Per-fixture detail - baseline" in markdown
    assert "info_disclosure_env_leak" in markdown
    assert "find_env_file: 100%" in markdown


# --- run_suite trials wiring ---

def test_run_suite_calls_run_fixture_trials_times(monkeypatch, tmp_path: Path):
    """Verify run_suite() actually runs each (fixture, config) pair `trials` times.

    Monkeypatches run_fixture itself so this stays fast/hermetic - the
    aggregation math is already covered by the _aggregate_trials tests above.
    """
    call_log = []

    def _fake_run_fixture(fixture_dir, config_overrides=None, config_name="default", timeout_s=1800, **kwargs):
        """Fake run fixture."""
        call_log.append((fixture_dir.name, config_name))
        return FixtureResult(fixture_dir.name, config_name, sr=False, scr=0.0, subtask_results={}, tte=None, duration_s=0.1, error=None)

    monkeypatch.setattr(runner_module, "run_fixture", _fake_run_fixture)

    fixture_dir = tmp_path / "fake_fixture"
    fixture_dir.mkdir()
    report = run_suite([fixture_dir], {"baseline": {}}, results_dir=tmp_path / "results", trials=3)

    assert call_log == [("fake_fixture", "baseline")] * 3
    assert report.trials == 3
    assert report.results["baseline"][0].trials == 3


# --- run_fixture wiring (fake LLM, no live Ollama/WSL) ---

@pytest.fixture
def trivial_fixture_dir(tmp_path: Path) -> Path:
    """Trivial fixture dir."""
    fixture_dir = tmp_path / "trivial_fixture"
    fixture_dir.mkdir()
    (fixture_dir / "query.txt").write_text("Say the flag for {target_url}.", encoding="utf-8")
    (fixture_dir / "flag.txt").write_text("flag{trivial}", encoding="utf-8")
    (fixture_dir / "subtasks.yaml").write_text("[]\n", encoding="utf-8")
    (fixture_dir / "server.py").write_text(
        "def start_server(port=0):\n"
        "    return 'http://127.0.0.1:0', lambda: None\n",
        encoding="utf-8",
    )
    return fixture_dir


def test_run_fixture_wiring_with_fake_llm(trivial_fixture_dir: Path):
    """Verify Run fixture wiring with fake llm.

    Proves run_fixture() correctly starts/stops the fixture, builds a real
    ArgusBrain with the injected fake LLM, and scores SR against the final
    output - without needing live Ollama/WSL/Kali.
    """
    llm = FakeListLLM(responses=["Final Answer: The flag is flag{trivial}."])
    try:
        result = run_fixture(
            trivial_fixture_dir,
            config_name="test",
            llm=llm,
            rag_config={"enabled": False},
            timeout_s=30,
            resolve_wsl_host=False,  # no real tool call happens - skip the live WSL round-trip
        )
    finally:
        ArgusConfig.reset()

    assert result.error is None
    assert result.sr is True
    assert result.config_name == "test"
    assert result.fixture_name == "trivial_fixture"


def test_run_fixture_timeout(trivial_fixture_dir: Path):
    """Verify Run fixture timeout.

    A worker that never finishes within timeout_s must be reported as a
    timeout error, not hang the test suite or silently score as unsolved.
    """
    class _HangingLLM:
        def invoke(self, messages, **kwargs):
            """Invoke."""
            threading.Event().wait(5)  # simulate a stuck call, longer than timeout_s below
            return None

    try:
        result = run_fixture(
            trivial_fixture_dir,
            config_name="test",
            llm=_HangingLLM(),
            rag_config={"enabled": False},
            timeout_s=1,
            resolve_wsl_host=False,
        )
    finally:
        ArgusConfig.reset()

    assert result.error == "timeout"
    assert result.sr is False
