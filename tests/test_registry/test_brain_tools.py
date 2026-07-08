"""Unit tests for app/core/agent/brain_tools.py::build_argus_tools (specs/017)."""
from unittest.mock import MagicMock

from app.core.agent.brain_tools import build_argus_tools

EXPECTED_TOOL_NAMES = {
    "Check_Reachability", "Subdomain_Enumeration", "Recon_Suite", "Query_Memory",
    "Query_Knowledge_Graph", "Exploit_Suggester", "Smart_Web_Search", "Run_Nikto",
    "Run_FFUF", "System_Self_Heal", "Archive_Research_Subagent", "Run_Kali_Command",
}


def test_build_argus_tools_returns_expected_tool_set():
    tools = build_argus_tools(MagicMock())
    assert {t.name for t in tools} == EXPECTED_TOOL_NAMES
    assert len(tools) == 12


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
