"""Real runtime smoke tests for app/GUI/dashboard.py using Streamlit's AppTest
harness (streamlit.testing.v1) - this actually RUNS the script in a simulated
session, catching runtime errors that a plain import check cannot (e.g. bad
session_state access, widget rendering issues). No live Ollama/WSL needed.
"""
import pytest
from streamlit.testing.v1 import AppTest

PAGES = ["Dashboard", "Targets", "Agent", "Knowledge Graph", "Reports", "Settings"]


def test_dashboard_loads_without_exception():
    at = AppTest.from_file("app/GUI/dashboard.py")
    at.run(timeout=30)
    assert not at.exception


@pytest.mark.parametrize("page", PAGES)
def test_dashboard_page_renders_without_exception(page):
    at = AppTest.from_file("app/GUI/dashboard.py")
    at.run(timeout=30)
    at.radio(key="nav_radio").set_value(page).run(timeout=30)
    assert not at.exception, f"{page} raised: {at.exception}"
