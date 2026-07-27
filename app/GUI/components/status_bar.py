import streamlit as st
import socket
from app.core.config import ArgusConfig


@st.cache_data(ttl=5)
def check_ollama_status():
    """Check whether Ollama's local API port is accepting connections.

    Cached for 5s (`st.cache_data(ttl=5)`) - `render_status_bar()` is called
    at the top of every page render, and Streamlit reruns the whole script
    on every widget interaction (any button click, tab switch), so without
    caching this ran on every single click. This check itself is a fast raw
    socket connect, but see `check_ssh_status()` below for why this mattered.

    Returns:
        bool: True if a TCP connection to 127.0.0.1:11434 succeeds.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("127.0.0.1", 11434))
        sock.close()
        return result == 0
    except Exception:
        return False


@st.cache_data(ttl=5)
def check_ssh_status():
    """Check whether the WSL SSH bridge's port is accepting connections.

    Previously spawned a whole new `powershell.exe` process on every call
    (`Test-NetConnection`) just to test one TCP port - PowerShell's own
    cold-start overhead (hundreds of ms, often 1s+) on top of that, and
    `render_status_bar()` calling this on every single click/tab-switch
    (Streamlit reruns the whole script on any widget interaction) made the
    entire GUI feel heavy - live-reported by a user as "the GUI itself
    feels heavy/slow when clicking or navigating tabs". Replaced with the
    same lightweight raw socket connect `check_ollama_status()` already
    uses - no process spawn at all - plus the same 5s cache as a second
    layer of protection against repeated reruns.

    Returns:
        bool: True if a TCP connection to 127.0.0.1:22 succeeds.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(("127.0.0.1", 22))
        sock.close()
        return result == 0
    except Exception:
        return False


def render_status_bar():
    """Render the top status bar: Ollama/SSH connectivity, Blackboard
    counts, and the active model name, as four Streamlit columns."""
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
