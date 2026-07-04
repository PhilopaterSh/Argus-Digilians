from app.core.agent.contracts import (
    AgentRunEvent,
    build_initial_agent_state,
    build_run_snapshot,
    persist_run_snapshot,
    record_state_event,
    load_json_file,
)


def test_build_initial_agent_state_includes_runtime_fields(tmp_path):
    state_file = tmp_path / "agent_state.json"

    state = build_initial_agent_state("https://example.com", "run-123", "production", str(state_file))

    assert state["run_id"] == "run-123"
    assert state["state_file"] == str(state_file)
    assert state["target_ip"] == "https://example.com"
    assert state["events"] == []
    assert state["last_probe_output"] is None
    assert state["messages"][0].content == "Execute pentest on https://example.com"


def test_record_state_event_appends_to_state_and_file(tmp_path):
    state_file = tmp_path / "agent_state.json"
    state = build_initial_agent_state("target.local", "run-456", "test", str(state_file))

    record_state_event(state, "recon", "running", "Starting reconnaissance")

    assert len(state["events"]) == 1
    event = state["events"][0]
    assert event["node"] == "recon"
    assert event["status"] == "running"
    assert event["detail"] == "Starting reconnaissance"

    persisted = load_json_file(str(state_file))
    assert persisted["current_node"] == "recon"
    assert persisted["status"] == "running"
    assert persisted["events"][0]["run_id"] == "run-456"


def test_persist_run_snapshot_round_trips_events(tmp_path):
    state_file = tmp_path / "snapshot.json"
    events: list[AgentRunEvent] = [
        {
            "node": "scanner",
            "status": "completed",
            "detail": "Scan finished",
            "timestamp": "2026-07-04T00:00:00+00:00",
            "run_id": "run-789",
            "target": "target.local",
            "mode": "demo",
        }
    ]

    persist_run_snapshot(
        str(state_file),
        build_run_snapshot(
            "run-789",
            "target.local",
            "demo",
            status="completed",
            current_node="scanner",
            progress_pct=50,
            events=events,
        ),
    )

    saved = load_json_file(str(state_file))
    assert saved["run_id"] == "run-789"
    assert saved["current_node"] == "scanner"
    assert saved["events"][0]["detail"] == "Scan finished"
