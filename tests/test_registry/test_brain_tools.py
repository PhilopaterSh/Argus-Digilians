"""Unit tests for app/core/agent/brain_tools.py::build_argus_tools (specs/017,
extended specs/018 CHK090)."""
from unittest.mock import MagicMock

from app.core.agent.brain_tools import build_argus_tools

EXPECTED_TOOL_NAMES = {
    "Check_Reachability", "Subdomain_Enumeration", "Recon_Suite", "Query_Memory",
    "Query_Knowledge_Graph", "Exploit_Suggester", "Smart_Web_Search", "Run_Nikto",
    "Run_FFUF", "System_Self_Heal", "Archive_Research_Subagent", "Run_Kali_Command",
    # specs/018 CHK090: real WSLBridgeTools capabilities that existed but were
    # never wired into this "canonical" list - a separate, independently
    # drifted copy (scripts/run_argus_cli.py) had 4 of these 5 and this list
    # didn't; Secret_Scanner was in neither.
    "Crawl_Target", "Secret_Scanner", "Advanced_Evasion_Probe",
    "Reflective_Pre_Verify", "Task_Difficulty_Assessment",
}


def test_build_argus_tools_returns_expected_tool_set():
    tools = build_argus_tools(MagicMock())
    assert {t.name for t in tools} == EXPECTED_TOOL_NAMES
    assert len(tools) == 17


def test_each_tool_has_a_description_and_is_callable():
    tools = build_argus_tools(MagicMock())
    for tool in tools:
        assert tool.description, f"{tool.name} has no description"
        assert callable(tool.func)


def test_tool_func_delegates_to_the_bound_bridge_method():
    bridge = MagicMock()
    bridge.run_nikto.return_value = "nikto output"
    tools = build_argus_tools(bridge)
    nikto_tool = next(t for t in tools if t.name == "Run_Nikto")

    result = nikto_tool.func("http://example.com")

    bridge.run_nikto.assert_called_once_with("http://example.com")
    assert result == "nikto output"


def test_new_chk090_tools_delegate_to_the_correct_bridge_methods():
    bridge = MagicMock()
    tools = build_argus_tools(bridge)
    tool_by_name = {t.name: t for t in tools}

    tool_by_name["Crawl_Target"].func("http://example.com")
    bridge.crawl_target.assert_called_once_with("http://example.com")

    tool_by_name["Secret_Scanner"].func("http://example.com")
    bridge.analyze_secrets.assert_called_once_with("http://example.com")

    tool_by_name["Advanced_Evasion_Probe"].func("http://example.com")
    bridge.advanced_vuln_probe.assert_called_once_with("http://example.com")

    tool_by_name["Reflective_Pre_Verify"].func("curl -s http://example.com")
    bridge.verify_command.assert_called_once_with("curl -s http://example.com")

    tool_by_name["Task_Difficulty_Assessment"].func("http://example.com")
    bridge.assess_difficulty.assert_called_once_with("http://example.com")
