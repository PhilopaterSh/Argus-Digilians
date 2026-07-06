import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


def test_dashboard_imports():
    try:
        import app.GUI.dashboard
        assert app.GUI.dashboard is not None
    except RuntimeError:
        pass


def test_pages_imports():
    from app.GUI.tabs.overview import render_dashboard as render_overview
    from app.GUI.tabs.targets import render_targets
    from app.GUI.tabs.agent import render_agent
    from app.GUI.tabs.reports import render_reports
    from app.GUI.tabs.settings import render_settings
    from app.GUI.tabs.knowledge_graph import render_knowledge_graph
    assert callable(render_overview)
    assert callable(render_targets)
    assert callable(render_agent)
    assert callable(render_reports)
    assert callable(render_settings)
    assert callable(render_knowledge_graph)


def test_components_imports():
    from app.GUI.components.status_bar import render_status_bar, check_ollama_status, check_ssh_status
    from app.GUI.components.session_manager import save_session, load_session, list_sessions, delete_session
    from app.GUI.components.export import generate_html_report, generate_markdown_report, generate_json_report
    assert callable(render_status_bar)
    assert callable(save_session)
    assert callable(load_session)
    assert callable(generate_html_report)
    assert callable(generate_markdown_report)
    assert callable(generate_json_report)


def test_utils_imports():
    from app.GUI.utils.blackboard import load_targets, save_target, build_graph_data, init_gui_tables
    from app.GUI.utils.agent_controller import AgentController
    assert callable(load_targets)
    assert callable(build_graph_data)
    assert callable(init_gui_tables)
    controller = AgentController()
    assert controller is not None
    assert hasattr(controller, "start")
    assert hasattr(controller, "stop")
    assert hasattr(controller, "get_status")


def test_export_html_report():
    from app.GUI.components.export import generate_html_report
    findings = [
        {"severity": "critical", "type": "SQL Injection", "summary": "SQLi found in login"},
        {"severity": "high", "type": "XSS", "summary": "Reflected XSS in search"},
        {"severity": "medium", "type": "Info Leak", "summary": "Server header exposed"},
    ]
    html = generate_html_report(findings, "https://example.com")
    assert "<html>" in html
    assert "SQL Injection" in html
    assert "XSS" in html
    assert "Critical" in html or "critical" in html


def test_export_markdown_report():
    from app.GUI.components.export import generate_markdown_report
    findings = [
        {"severity": "high", "type": "XSS", "summary": "Reflected XSS"},
    ]
    md = generate_markdown_report(findings, "https://example.com")
    assert "Argus Security Report" in md
    assert "XSS" in md


def test_export_json_report():
    from app.GUI.components.export import generate_json_report
    findings = [
        {"severity": "low", "type": "Info", "summary": "Test finding"},
    ]
    import json
    report = json.loads(generate_json_report(findings, "https://example.com"))
    assert report["target"] == "https://example.com"
    assert report["findings_count"] == 1
    assert report["findings"][0]["summary"] == "Test finding"


def test_agent_controller_state():
    from app.GUI.utils.agent_controller import AgentController
    import tempfile
    import os

    with tempfile.TemporaryDirectory() as tmpdir:
        controller = AgentController(state_dir=tmpdir)
        status = controller.get_status()
        assert isinstance(status, dict)
        assert "status" in status


def test_session_manager_functions():
    from app.GUI.components.session_manager import save_session, list_sessions, delete_session
    from app.GUI.utils.blackboard import init_gui_tables

    try:
        init_gui_tables()
    except Exception:
        pass

    sessions_before = list_sessions()
    sid = save_session("test_session", [{"url": "https://test.com"}], {"model": "test"})
    assert sid is not None
    sessions_after = list_sessions()
    assert len(sessions_after) > 0
    delete_session(sid)
