"""Unit tests for app.GUI.tabs.agent._reconcile_agent_running_state (specs/010 T029).

Proves a failed (or completed) run is not displayed as still running once the
underlying process has actually finished - no Streamlit context required since
this is a pure function extracted from render_agent().
"""
from unittest.mock import MagicMock

from app.GUI.tabs.agent import _reconcile_agent_running_state


def _make_controller(is_running: bool, status: dict):
    controller = MagicMock()
    controller.is_running.return_value = is_running
    controller.get_status.return_value = status
    return controller


def test_failed_run_is_not_reported_as_running():
    """The core T029 regression: session thinks it's running, but the process
    has actually finished with status=failed - must flip agent_running to False."""
    controller = _make_controller(is_running=False, status={"status": "failed", "error": "boom"})

    new_running, current_state = _reconcile_agent_running_state(True, controller)

    assert new_running is False
    assert current_state["status"] == "failed"


def test_completed_run_is_not_reported_as_running():
    controller = _make_controller(is_running=False, status={"status": "completed"})

    new_running, current_state = _reconcile_agent_running_state(True, controller)

    assert new_running is False
    assert current_state["status"] == "completed"


def test_genuinely_running_process_stays_running():
    controller = _make_controller(is_running=True, status={"status": "running"})

    new_running, current_state = _reconcile_agent_running_state(True, controller)

    assert new_running is True
    assert current_state["status"] == "running"


def test_idle_session_stays_idle_without_polling_controller_status_change():
    controller = _make_controller(is_running=False, status={"status": "idle"})

    new_running, current_state = _reconcile_agent_running_state(False, controller)

    assert new_running is False
    assert current_state["status"] == "idle"


def test_no_controller_returns_session_flag_unchanged_and_empty_state():
    new_running, current_state = _reconcile_agent_running_state(True, None)

    assert new_running is True
    assert current_state == {}
