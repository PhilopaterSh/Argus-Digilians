import glob
import json
import os

import streamlit as st

_AGENT_RUNS_DIR = os.path.join("logs", "agent_runs")


def _load_recent_runs(limit=20):
    """Reads real agent run snapshots from disk (the same state files
    scripts/run_agent.py writes and the Agent tab already polls) instead of
    st.session_state.jobs, which is initialized to [] in dashboard.py and
    nothing ever appends to - so "Recent Activity" and the metrics above it
    were permanently empty/static regardless of real agent activity.

    Args:
        limit (int): Max number of most-recently-modified run files to
            return.

    Returns:
        list[dict]: Up to `limit` parsed run-state dicts, most recently
        modified first; unreadable/corrupt files are skipped.
    """
    paths = glob.glob(os.path.join(_AGENT_RUNS_DIR, "agent_*.json"))
    paths.sort(key=os.path.getmtime, reverse=True)
    runs = []
    for path in paths[:limit]:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                runs.append(json.load(handle))
        except (OSError, json.JSONDecodeError):
            continue
    return runs


def render_dashboard():
    """Render the Dashboard tab: run-count metrics, quick-action buttons,
    and a recent-activity feed built from real agent run state files."""
    st.title(":bar_chart: Dashboard")
    st.markdown("---")

    runs = _load_recent_runs()
    targets = st.session_state.get("targets", [])
    completed_runs = [r for r in runs if r.get("status") == "completed"]
    failed_runs = [r for r in runs if r.get("status") == "failed"]
    active_runs = [r for r in runs if r.get("status") in ("running", "starting")]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Targets", len(targets))
    with col2:
        st.metric("Active Jobs", len(active_runs))
    with col3:
        st.metric("Completed", len(completed_runs))
    with col4:
        st.metric("Failed", len(failed_runs))

    st.markdown("---")
    st.subheader(":zap: Quick Actions")
    qc1, qc2, qc3, qc4 = st.columns(4)
    # These previously set session_state flags (targets_tab_open, etc.) that
    # nothing ever read - dashboard.py's navigation is driven entirely by the
    # sidebar radio widget (key='nav_radio'), so clicking these did an
    # st.rerun() but never actually navigated anywhere. Setting nav_radio
    # directly here raises StreamlitAPIException: that widget was already
    # instantiated earlier in this same run (dashboard.py renders the sidebar
    # radio before calling into this tab). Setting _pending_nav instead and
    # letting dashboard.py apply it before the widget is (re)created on the
    # next run is the actual fix.
    with qc1:
        if st.button(":dart: New Target", use_container_width=True):
            st.session_state["_pending_nav"] = "Targets"
            st.rerun()
    with qc2:
        if st.button(":rocket: Start Agent", use_container_width=True):
            st.session_state["_pending_nav"] = "Agent"
            st.rerun()
    with qc3:
        if st.button(":page_facing_up: Generate Report", use_container_width=True):
            st.session_state["_pending_nav"] = "Reports"
            st.rerun()
    with qc4:
        if st.button(":gear: Settings", use_container_width=True):
            st.session_state["_pending_nav"] = "Settings"
            st.rerun()

    st.markdown("---")
    st.subheader(":clock3: Recent Activity")

    all_events = []
    for run in runs:
        for event in run.get("events", []):
            all_events.append(event)
    all_events.sort(key=lambda e: e.get("timestamp", ""), reverse=True)

    if all_events:
        for event in all_events[:10]:
            node = event.get("node", "?")
            status = event.get("status", "?")
            detail = event.get("detail", "")
            ts = event.get("timestamp", "")
            st.markdown(
                f"<div style='background:#1a1d24; padding:8px; border-radius:4px; margin:4px 0; border-left:3px solid #00ff41;'>"
                f"<small>{ts}</small> <strong>{node}</strong> - {status}: {detail}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No recent activity. Add a target and start the agent to begin.")
