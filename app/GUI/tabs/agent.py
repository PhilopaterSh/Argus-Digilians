import streamlit as st

from app.GUI.components.export import (
    generate_run_report_markdown,
    run_report_filename,
)


def _reconcile_agent_running_state(session_agent_running, controller):
    """Resolve the true running/finished state against the controller's process
    (specs/010 T029: failed runs must not be displayed as still running).

    Guards against a stale session-state 'agent_running=True' surviving after the
    underlying process has actually finished (completed or failed) - without this
    check, a failed run would keep showing "Running" until the next full page
    reload clears session_state.

    Args:
        session_agent_running (bool): The session's current
            `agent_running` flag.
        controller: An AgentController, or `None` if no run has started
            yet this session.

    Returns:
        tuple: `(new_agent_running, current_state)` - `current_state` is
        `{}` if `controller` is `None`, else `controller.get_status()`.
    """
    if controller is None:
        return session_agent_running, {}
    current_state = controller.get_status()
    process_running = controller.is_running()
    if session_agent_running and not process_running:
        return False, controller.get_status()
    return session_agent_running, current_state


def _render_events(events):
    """Render the last 20 agent events as styled HTML feed entries.

    Args:
        events (list[dict]): Event dicts with `node`/`status`/`detail`/
            `timestamp` keys.

    Returns:
        str: HTML markup for the feed (one styled `<div>` per event,
        color-coded by status).
    """
    feed_html = ''
    for event in events[-20:]:
        node = event.get('node', '?')
        status = event.get('status', '?')
        detail = event.get('detail', '')
        ts = event.get('timestamp', '')
        color = '#00ff41' if status == 'completed' else '#ffaa00' if status == 'running' else '#ff4444'
        feed_html += (
            f"<div style='background:#1a1d24; padding:10px; border-radius:4px; margin:6px 0; "
            f"border-left:3px solid {color};'>"
            f"<small style='color:#888;'>{ts}</small><br>"
            f"<strong style='color:{color};'>{node}</strong> - {detail}"
            f"</div>"
        )
    return feed_html


def render_agent():
    """Render the Agent Control tab: target selection, Start/Stop
    controls, and a live-polling feed of the current/last run."""
    st.title(':robot_face: Agent Control')
    st.markdown('---')

    targets = st.session_state.get('targets', [])
    controller = st.session_state.get('agent_controller')

    if not targets:
        st.warning('No targets available. Add a target in the Targets tab first.')
        return

    target_urls = [t['url'] for t in targets]
    selected_target = st.selectbox('Select Target', target_urls, key='agent_target_select')

    st.markdown('---')

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button(':rocket: Start Agent', type='primary', disabled=st.session_state.get('agent_running', False)):
            if controller:
                target_obj = next((t for t in targets if t['url'] == selected_target), None)
                if target_obj:
                    controller.start(selected_target)
                    st.session_state.agent_running = True
                    st.session_state.current_agent_target = selected_target
                    st.rerun()

    with col2:
        if st.button(':stop_sign: Stop', disabled=not st.session_state.get('agent_running', False)):
            if controller:
                controller.stop()
                st.session_state.agent_running = False
                st.rerun()

    with col3:
        st.caption(f"Run file: {controller.state_file}" if controller and controller.state_file else 'No active run yet.')

    st.markdown('---')

    # Everything below needs to keep updating while a run is in flight
    # without blocking the rest of the page. The previous implementation
    # used `for _ in range(60): ...; time.sleep(1)` inside the main script
    # run - a plain Python sleep loop that froze this ENTIRE Streamlit
    # session (every button, every tab switch) for up to 60 straight
    # seconds, since Streamlit is single-threaded per session and nothing
    # else can be processed while that loop is sleeping. st.fragment with
    # run_every re-executes only this fragment on a timer, in the
    # background, while the rest of the page (Start/Stop buttons, sidebar
    # navigation) stays fully interactive. run_every is only set while a
    # run is actually active, so an idle page does no polling at all.
    run_every = '2s' if st.session_state.get('agent_running') else None

    @st.fragment(run_every=run_every)
    def _live_section():
        """Render the polling status/feed/results section as an isolated
        Streamlit fragment, re-run on its own timer while a run is active
        instead of blocking the whole page (see the comment above)."""
        controller = st.session_state.get('agent_controller')
        if controller is None:
            st.info('Agent feed will appear here when running. Select a target and click Start Agent.')
            return

        new_agent_running, current_state = _reconcile_agent_running_state(
            st.session_state.get('agent_running', False), controller
        )
        st.session_state.agent_running = new_agent_running

        status_label = current_state.get('status', 'idle')
        run_mode = current_state.get('mode', 'production')
        updated_at = current_state.get('updated_at', 'N/A')
        if new_agent_running:
            st.markdown('**Status**: :green_circle: Running')
            st.markdown(f"**Target**: {st.session_state.get('current_agent_target', 'N/A')}")
        elif status_label == 'completed':
            st.markdown('**Status**: :white_check_mark: Completed')
            st.markdown(f"**Target**: {current_state.get('target', selected_target)}")
        elif status_label == 'failed':
            st.markdown('**Status**: :red_circle: Failed')
            st.markdown(f"**Target**: {current_state.get('target', selected_target)}")
        else:
            st.markdown('**Status**: :white_circle: Idle')
        st.caption(f"Mode: `{run_mode}` | Updated: `{updated_at}`")

        st.subheader(':scroll: Agent Feed')
        events = current_state.get('events', [])
        if events:
            st.markdown(_render_events(events), unsafe_allow_html=True)
        elif new_agent_running:
            st.info('Waiting for the first agent event...')
        else:
            st.info('Agent feed will appear here when running. Select a target and click Start Agent.')

        if status_label == 'completed' and not new_agent_running:
            st.success(':white_check_mark: Agent completed successfully!')
        elif status_label == 'failed' and not new_agent_running:
            st.error(f":x: Agent failed: {current_state.get('error', 'Unknown error')}")

        st.markdown('---')
        st.subheader(':bar_chart: Final Results')
        final_state = current_state.get('final_state', {})
        if status_label in ('completed', 'failed') or final_state:
            # ArgusBrain's ReAct agent (specs/017-restore-react-agent) returns a
            # SecurityReport (summary/findings/overall_risk_score/next_steps),
            # not the old deterministic pipeline's open_ports/vulnerabilities/
            # exploit_success - this section reflects that report shape.
            findings = final_state.get('findings', [])
            risk_score = final_state.get('overall_risk_score')

            if final_state.get('parse_warning'):
                st.warning(final_state['parse_warning'])

            cols = st.columns(2)
            cols[0].metric('Overall Risk Score', f"{risk_score}/10" if risk_score is not None else 'N/A')
            cols[1].metric('Findings Count', len(findings))

            if final_state.get('summary'):
                st.markdown(f"**Summary**: {final_state['summary']}")
            if final_state.get('attack_surface_stats'):
                st.caption(f"Attack surface: {final_state['attack_surface_stats']}")

            if findings:
                st.markdown(f"**Findings ({len(findings)})**")
                for f in findings:
                    st.markdown(
                        f"**[{f.get('severity', '?')}] {f.get('issue', 'Unknown issue')}** - `{f.get('target', '?')}`\n\n"
                        f"{f.get('description', '')}\n\n"
                        f"*Proof-of-concept payload*: `{f.get('suggested_payload') or 'n/a'}`  \n"
                        f"*Remediation*: {f.get('remediation') or 'n/a'}"
                    )
                    st.markdown('---')
            elif status_label == 'completed':
                st.info('No vulnerabilities were confirmed by the tools run in this assessment.')

            next_steps = final_state.get('next_steps', [])
            if next_steps:
                st.markdown('**Next steps**')
                for step in next_steps:
                    st.markdown(f"- {step}")

            # Everything else - the step-by-step tool trace, each tool's raw
            # output, the model's own long-form report and the process log -
            # goes into a downloadable file rather than onto the screen. Those
            # used to be four inline expanders (including a raw `st.json` dump
            # of the entire run state), which buried the actual findings.
            st.markdown('---')
            report_markdown = generate_run_report_markdown(
                current_state,
                controller.get_log_tail() if controller else '',
            )
            st.download_button(
                label=':inbox_tray: Download full report (.md)',
                data=report_markdown,
                file_name=run_report_filename(current_state),
                mime='text/markdown',
                help='Complete record: every tool call and its output, the full '
                     'process log, and the conclusion.',
                key=f"dl_{current_state.get('run_id', 'run')}",
            )
        else:
            st.info('No results yet. Results populate here once the agent run completes.')

    _live_section()
