import streamlit as st
from datetime import datetime


def render_dashboard():
    st.title(":bar_chart: Dashboard")
    st.markdown("---")

    targets = st.session_state.get("targets", [])
    jobs = st.session_state.get("jobs", [])
    completed_jobs = [j for j in jobs if j.get("status") == "completed"]
    failed_jobs = [j for j in jobs if j.get("status") == "failed"]

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Targets", len(targets))
    with col2:
        st.metric("Active Jobs", len(jobs) - len(completed_jobs) - len(failed_jobs))
    with col3:
        st.metric("Completed", len(completed_jobs))
    with col4:
        st.metric("Failed", len(failed_jobs))

    st.markdown("---")
    st.subheader(":zap: Quick Actions")
    qc1, qc2, qc3, qc4 = st.columns(4)
    with qc1:
        if st.button(":dart: New Target", use_container_width=True):
            st.switch_page("app/GUI/pages/targets.py")
    with qc2:
        if st.button(":rocket: Start Agent", use_container_width=True):
            st.switch_page("app/GUI/pages/agent.py")
    with qc3:
        if st.button(":page_facing_up: Generate Report", use_container_width=True):
            st.switch_page("app/GUI/pages/reports.py")
    with qc4:
        if st.button(":gear: Settings", use_container_width=True):
            st.switch_page("app/GUI/pages/settings.py")

    st.markdown("---")
    st.subheader(":clock3: Recent Activity")

    all_events = []
    for job in jobs:
        for event in job.get("events", []):
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
                f"<small>{ts}</small> <strong>{node}</strong> — {status}: {detail}"
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No recent activity. Add a target and start the agent to begin.")
