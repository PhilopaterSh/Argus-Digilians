import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))


@pytest.fixture
def setup_gui_tables():
    from app.GUI.utils.blackboard import init_gui_tables
    try:
        init_gui_tables()
    except Exception:
        pass
    yield


def test_session_save_and_load_roundtrip(setup_gui_tables):
    """Verify Session save and load roundtrip.
    
    Args:
        setup_gui_tables: pytest fixture (see the module's @pytest.fixture definitions).
    """
    from app.GUI.components.session_manager import save_session, load_session, list_sessions, delete_session

    targets = [
        {"id": "1", "url": "https://target1.com", "type": "url", "status": "pending"},
        {"id": "2", "url": "https://target2.com", "type": "url", "status": "completed"},
    ]
    settings = {"model": "test-model", "ollama_endpoint": "http://localhost:11434", "theme": "dark"}
    agent_state = {"status": "completed", "current_node": "post_exploit"}

    session_id = save_session("roundtrip_test", targets, settings, agent_state)
    assert session_id is not None

    loaded = load_session(session_id)
    assert loaded is not None
    assert loaded["name"] == "roundtrip_test"
    assert len(loaded["targets"]) == 2
    assert loaded["targets"][0]["url"] == "https://target1.com"
    assert loaded["settings"]["model"] == "test-model"
    assert loaded["agent_state"]["current_node"] == "post_exploit"

    sessions = list_sessions()
    session_names = [s["name"] for s in sessions]
    assert "roundtrip_test" in session_names

    delete_session(session_id)
    assert load_session(session_id) is None


def test_multiple_sessions(setup_gui_tables):
    """Verify Multiple sessions.
    
    Args:
        setup_gui_tables: pytest fixture (see the module's @pytest.fixture definitions).
    """
    from app.GUI.components.session_manager import save_session, list_sessions, delete_session

    sid1 = save_session("session_a", [], {})
    sid2 = save_session("session_b", [], {})
    sid3 = save_session("session_c", [], {})

    sessions = list_sessions()
    names = [s["name"] for s in sessions]
    assert "session_a" in names
    assert "session_b" in names
    assert "session_c" in names

    for sid in [sid1, sid2, sid3]:
        delete_session(sid)


def test_session_with_empty_targets(setup_gui_tables):
    """Verify Session with empty targets.
    
    Args:
        setup_gui_tables: pytest fixture (see the module's @pytest.fixture definitions).
    """
    from app.GUI.components.session_manager import save_session, load_session, delete_session

    sid = save_session("empty_test", [], {"key": "val"})
    loaded = load_session(sid)
    assert loaded["targets"] == []
    assert loaded["settings"]["key"] == "val"
    delete_session(sid)


def test_session_update(setup_gui_tables):
    """Verify Session update.
    
    Args:
        setup_gui_tables: pytest fixture (see the module's @pytest.fixture definitions).
    """
    from app.GUI.components.session_manager import save_session, load_session, update_session, delete_session

    sid = save_session("update_test", [{"url": "https://initial.com"}], {})
    update_session(sid, targets=[{"url": "https://updated.com"}])
    loaded = load_session(sid)
    assert loaded["targets"][0]["url"] == "https://updated.com"
    delete_session(sid)
