"""Login gate for the Argus Security Studio (ARG-01 control-plane auth).

Renders a password form before any dashboard content and stops the script
run when access is not granted. Bare imports (tests, module probing) are
tolerated: without a ScriptRunContext the gate renders nothing and returns,
so importing the dashboard never raises.
"""
import streamlit as st

from app.core.panel_auth import get_stored_hash, verify_password

_SESSION_KEY = "argus_authenticated"


def is_authenticated() -> bool:
    """Return whether this browser session has authenticated.

    Returns:
        bool: True after a successful login in the current session.
    """
    return bool(st.session_state.get(_SESSION_KEY, False))


def _has_script_ctx() -> bool:
    """Return whether this code is running inside a Streamlit script run.

    Returns:
        bool: False during bare module imports (tests/probing), True when
        served by `streamlit run`.
    """
    try:
        from streamlit.runtime.scriptrunner import get_script_run_ctx

        return get_script_run_ctx() is not None
    except Exception:
        return False


def render_login():
    """Render the password form and mark the session on success.

    Fail-closed: with no ``ARGUS_PANEL_PASSWORD_HASH`` configured the form
    renders setup instructions instead and never unlocks.
    """
    stored = get_stored_hash()
    st.markdown("## :lock: Argus Security Studio")
    if not stored:
        st.warning(
            "The control plane is locked because no panel password is configured.\n\n"
            "Generate one on the host, then reload this page:\n\n"
            "`python scripts/set_panel_password.py`"
        )
        return
    with st.form("argus_login"):
        password = st.text_input("Panel password", type="password")
        submitted = st.form_submit_button("Unlock", use_container_width=True)
    if submitted:
        if verify_password(password, stored):
            st.session_state[_SESSION_KEY] = True
            st.rerun()
        else:
            st.error("Wrong password.")


def enforce():
    """Gate the dashboard: render the login and stop, or return when granted.

    Bare-import contexts (no script run) are allowed through so importing
    the dashboard module in tests never raises.
    """
    if is_authenticated():
        return
    if not _has_script_ctx():
        return
    render_login()
    st.stop()
