"""Unit tests for app.core.agent.graph.should_continue (specs/010 T027).

Covers the tactical graph's termination/retry-bound logic in isolation, using
a mocked save_entry so no real blackboard DB is touched.
"""
from unittest.mock import patch

from langgraph.graph import END

from app.core.agent.graph import should_continue


def _make_state(**overrides):
    state = {
        "target_ip": "10.0.0.1",
        "retry_count": 0,
        "current_payload": "payload.py",
        "error_log": [],
        "exploit_success": False,
    }
    state.update(overrides)
    return state


def test_terminates_on_exploit_success():
    """Verify Terminates on exploit success."""
    state = _make_state(exploit_success=True)
    assert should_continue(state) == "post_exploit"


def test_routes_to_self_heal_on_dependency_error_within_retry_budget():
    """Verify Routes to self heal on dependency error within retry budget."""
    state = _make_state(error_log=["nmap: command not found"], retry_count=0)
    assert should_continue(state) == "self_heal"


def test_terminates_when_retry_budget_exhausted_despite_dependency_error():
    """Verify Terminates when retry budget exhausted despite dependency error."""
    state = _make_state(error_log=["nmap: command not found"], retry_count=3)
    with patch("app.core.agent.graph.save_entry") as mock_save:
        result = should_continue(state)
    assert result == END
    mock_save.assert_called_once()
    assert mock_save.call_args[0][2] == "FAILED"


def test_terminates_when_retry_count_reaches_max_retries():
    """Verify Terminates when retry count reaches max retries."""
    state = _make_state(retry_count=3)
    with patch("app.core.agent.graph.save_entry") as mock_save:
        result = should_continue(state)
    assert result == END
    mock_save.assert_called_once_with("10.0.0.1", dict(state), "FAILED")


def test_terminates_when_no_current_payload():
    """Verify Terminates when no current payload."""
    state = _make_state(current_payload=None, retry_count=0)
    with patch("app.core.agent.graph.save_entry") as mock_save:
        result = should_continue(state)
    assert result == END
    mock_save.assert_called_once()


def test_routes_to_reflective_when_still_within_budget_with_payload():
    """Verify Routes to reflective when still within budget with payload."""
    state = _make_state(retry_count=1, current_payload="payload.py", error_log=[])
    assert should_continue(state) == "reflective"


def test_retry_budget_is_config_driven_not_hardcoded(monkeypatch):
    """A custom max_retries must be honored, proving the bound isn't hardcoded.
    
    Args:
        monkeypatch: test parameter provided by this test's own setup (a pytest fixture or a mock/patch injected via a decorator - see the test's parameters/decorators for which).
    """
    from app.core.config import ArgusConfig

    class _FakeConfig:
        max_retries = 1

    monkeypatch.setattr(ArgusConfig, "load", classmethod(lambda cls: _FakeConfig()))
    state = _make_state(retry_count=1, current_payload="payload.py")
    with patch("app.core.agent.graph.save_entry") as mock_save:
        result = should_continue(state)
    assert result == END
    mock_save.assert_called_once()
