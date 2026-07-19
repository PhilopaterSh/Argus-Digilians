import streamlit as st
import os
from app.core.config import ArgusConfig
from app.GUI.components.session_manager import list_sessions, save_session, load_session, delete_session


def render_settings():
    st.title(":gear: Settings")
    st.markdown("---")

    settings = st.session_state.get("settings", {})

    st.subheader(":brain: Model Configuration")
    default_model = os.getenv("SELECTED_MODEL") or ArgusConfig.load().model_name
    settings["model"] = st.text_input("Model Name", value=settings.get("model", default_model))
    settings["ollama_endpoint"] = st.text_input("Ollama Endpoint", value=settings.get("ollama_endpoint", "http://localhost:11434"))

    st.markdown("---")
    st.subheader(":satellite: SSH Bridge")
    settings["ssh_user"] = st.text_input("SSH Username", value=settings.get("ssh_user", "kali"))
    settings["ssh_pass"] = st.text_input("SSH Password", type="password", value=settings.get("ssh_pass", ""))

    st.markdown("---")
    st.subheader(":art: Appearance")
    settings["theme"] = st.selectbox("Theme", ["dark", "light"], index=0 if settings.get("theme", "dark") == "dark" else 1)

    st.session_state.settings = settings

    st.markdown("---")
    st.subheader(":floppy_disk: Session Management")

    sessions = list_sessions()
    session_names = [s["name"] for s in sessions] if sessions else []

    col1, col2 = st.columns(2)
    with col1:
        session_name = st.text_input("Session Name", placeholder="My Session")
        if st.button(":inbox_tray: Save Session", type="primary"):
            if session_name:
                sid = save_session(
                    name=session_name,
                    targets=st.session_state.get("targets", []),
                    settings=st.session_state.get("settings", {}),
                )
                st.session_state.active_session = sid
                st.success(f"Session saved: {session_name}")
                st.rerun()
            else:
                st.error("Please enter a session name.")

    with col2:
        if sessions:
            selected_session = st.selectbox("Load Session", session_names)
            if st.button(":outbox_tray: Load Session"):
                session_data = next((s for s in sessions if s["name"] == selected_session), None)
                if session_data:
                    loaded = load_session(session_data["session_id"])
                    if loaded:
                        st.session_state.targets = loaded.get("targets", [])
                        st.session_state.settings = loaded.get("settings", st.session_state.settings)
                        st.session_state.active_session = loaded["session_id"]
                        st.success(f"Session loaded: {selected_session}")
                        st.rerun()

            if st.button(":wastebasket: Delete Selected"):
                session_data = next((s for s in sessions if s["name"] == selected_session), None)
                if session_data:
                    delete_session(session_data["session_id"])
                    st.success(f"Session deleted: {selected_session}")
                    st.rerun()

    st.markdown("---")
    st.subheader(":page_with_curl: Logs")
    log_path = os.path.join("logs", "gui.log")
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            log_content = f.read()
        with st.expander("View Logs"):
            st.code(log_content[-5000:], language="text")
    else:
        st.info("No log file found yet.")
