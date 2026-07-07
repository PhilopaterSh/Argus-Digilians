import streamlit as st
import socket
import subprocess
from app.core.config import ArgusConfig


def check_ollama_status():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("127.0.0.1", 11434))
        sock.close()
        return result == 0
    except Exception:
        return False


def check_ssh_status():
    try:
        result = subprocess.run(
            ["powershell", "-Command",
             "Test-NetConnection -ComputerName 127.0.0.1 -Port 22 -ErrorAction SilentlyContinue | "
             "Select-Object -ExpandProperty TcpTestSucceeded"],
            capture_output=True, text=True, timeout=5
        )
        return "True" in result.stdout
    except Exception:
        return False


def render_status_bar():
    ollama_ok = check_ollama_status()
    ssh_ok = check_ssh_status()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if ollama_ok:
            st.markdown(":green_circle: **Ollama** : Online")
        else:
            st.markdown(":red_circle: **Ollama** : Offline")
    with col2:
        if ssh_ok:
            st.markdown(":green_circle: **SSH Bridge** : Active")
        else:
            st.markdown(":yellow_circle: **SSH Bridge** : Inactive")
    with col3:
        try:
            from app.GUI.utils.blackboard import get_blackboard_counts
            # get_blackboard_summary() returns a JSON *string* of nested
            # per-domain detail, not a dict - calling .get() on it always
            # raised AttributeError here, silently swallowed below, so this
            # showed "N/A" unconditionally regardless of what was in the
            # Blackboard. get_blackboard_counts() returns real counts.
            counts = get_blackboard_counts()
            targets = counts.get("target_count", 0)
            findings = counts.get("findings_count", 0)
            st.markdown(f":bar_chart: **Targets**: {targets} | **Findings**: {findings}")
        except Exception as e:
            st.markdown(f":bar_chart: **Blackboard**: N/A ({e})")
    with col4:
        import os
        model = os.getenv("SELECTED_MODEL") or ArgusConfig.load().model_name
        st.markdown(f":robot_face: **Model**: {model.split('/')[-1]}")
