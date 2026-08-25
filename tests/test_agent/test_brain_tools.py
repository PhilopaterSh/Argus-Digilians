"""Unit tests for app/core/agent/brain_tools.py::build_argus_tools (specs/017,
extended specs/018 CHK090, extended specs/020 role partitioning)."""
from unittest.mock import MagicMock

import pytest

from app.core.agent.brain_tools import (
    ROLE_TOOL_PARTITIONS,
    build_argus_tools,
    partition_tools_by_role,
)

pytestmark = pytest.mark.unit

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
    # specs/029: on-demand evidence capture, registered in brain_tools.py
    # when the screenshot feature landed but never added here - so this
    # "canonical" list drifted again and both assertions below failed.
    "Capture_Vulnerability_Screenshot",
    # Dedicated path-traversal / LFI scanner (multi-encoding, hybrid param
    # discovery) - promoted from a branch inside advanced_vuln_probe to a
    # first-class tool and exposed to the ReAct exploiter role. Existed and
    # was fully tested, but was registered nowhere - so no pipeline could
    # call it.
    "Path_Traversal_Scan",
}
EXPECTED_TOOL_COUNT = len(EXPECTED_TOOL_NAMES)


def test_build_argus_tools_returns_expected_tool_set():
    """Verify Build argus tools returns expected tool set."""
    tools = build_argus_tools(MagicMock())
    assert {t.name for t in tools} == EXPECTED_TOOL_NAMES
    assert len(tools) == EXPECTED_TOOL_COUNT


def test_each_tool_has_a_description_and_is_callable():
    """Verify Each tool has a description and is callable."""
    tools = build_argus_tools(MagicMock())
    for tool in tools:
        assert tool.description, f"{tool.name} has no description"
        assert callable(tool.func)


def test_tool_func_delegates_to_the_bound_bridge_method():
    """Verify Tool func delegates to the bound bridge method."""
    bridge = MagicMock()
    bridge.run_nikto.return_value = "nikto output"
    tools = build_argus_tools(bridge)
    nikto_tool = next(t for t in tools if t.name == "Run_Nikto")

    result = nikto_tool.func("http://example.com")

    bridge.run_nikto.assert_called_once_with("http://example.com")
    assert result == "nikto output"


def test_new_chk090_tools_delegate_to_the_correct_bridge_methods():
    """Verify New chk090 tools delegate to the correct bridge methods."""
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


class TestRolePartitioning:
    """specs/020 (multi-agent role separation, feature-flagged off by
    default) - build_argus_tools(role=...) / partition_tools_by_role()."""

    def test_role_none_returns_the_full_tool_set_unchanged(self):
        """Every existing caller (specs/017-019) passes no role argument -
        must be byte-for-byte the same as before this parameter existed.

        The count lives in EXPECTED_TOOL_COUNT rather than being hardcoded:
        this test used to say 17, and adding one tool made it fail for a
        reason that had nothing to do with role partitioning.
        """
        tools = build_argus_tools(MagicMock())
        assert {t.name for t in tools} == EXPECTED_TOOL_NAMES
        assert len(tools) == EXPECTED_TOOL_COUNT

    def test_collector_role_returns_only_recon_tools(self):
        """Verify Collector role returns only recon tools."""
        tools = build_argus_tools(MagicMock(), role="collector")
        assert {t.name for t in tools} == ROLE_TOOL_PARTITIONS["collector"]
        assert "Run_Nikto" not in {t.name for t in tools}

    def test_exploiter_role_returns_only_exploitation_tools(self):
        """Verify Exploiter role returns only exploitation tools."""
        tools = build_argus_tools(MagicMock(), role="exploiter")
        assert {t.name for t in tools} == ROLE_TOOL_PARTITIONS["exploiter"]
        assert "Recon_Suite" not in {t.name for t in tools}

    def test_planner_and_summarizer_roles_get_only_read_only_memory_tools(self):
        """FR-002: Planner and Summarizer get no direct execution tools at
        all - only Query_Memory/Query_Knowledge_Graph."""
        for role in ("planner", "summarizer"):
            tools = build_argus_tools(MagicMock(), role=role)
            assert {t.name for t in tools} == {"Query_Memory", "Query_Knowledge_Graph"}

    def test_every_tool_is_assigned_to_at_least_one_execution_role(self):
        """No tool should be silently unreachable by any role."""
        assigned = ROLE_TOOL_PARTITIONS["collector"] | ROLE_TOOL_PARTITIONS["exploiter"]
        all_names = EXPECTED_TOOL_NAMES - {"Query_Memory", "Query_Knowledge_Graph"}
        assert all_names <= assigned

    def test_partition_tools_by_role_matches_build_argus_tools_role_filtering(self):
        """partition_tools_by_role() (used by ArgusBrain, which only has the
        flat tool list, not a bridge reference) must produce the identical
        split build_argus_tools(bridge, role=...) would from scratch."""
        bridge = MagicMock()
        full_list = build_argus_tools(bridge)

        partitioned = partition_tools_by_role(full_list)

        assert {t.name for t in partitioned["collector"]} == {
            t.name for t in build_argus_tools(bridge, role="collector")
        }
        assert {t.name for t in partitioned["exploiter"]} == {
            t.name for t in build_argus_tools(bridge, role="exploiter")
        }
