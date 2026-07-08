import streamlit as st


def _reconcile_agent_running_state(session_agent_running, controller):
    """Resolve the true running/finished state against the controller's process
    (specs/010 T029: failed runs must not be displayed as still running).

    Guards against a stale session-state 'agent_running=True' surviving after the
    underlying process has actually finished (completed or failed) - without this
    check, a failed run would keep showing "Running" until the next full page
    reload clears session_state.

    Returns (new_agent_running, current_state).
    """
    if controller is None:
        return session_agent_running, {}
    current_state = controller.get_status()
    process_running = controller.is_running()
    if session_agent_running and not process_running:
        return False, controller.get_status()
    return session_agent_running, current_state


def _render_events(events):
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
            cols = st.columns(3)
            cols[0].metric('Open Ports', len(final_state.get('open_ports', [])))
            cols[1].metric('Vulnerabilities', len(final_state.get('vulnerabilities', [])))
            cols[2].metric('Exploit Success', 'Yes' if final_state.get('exploit_success') else 'No')

            with st.expander(':card_index_drawer: View Full State', expanded=False):
                st.json(current_state)

            if controller:
                log_tail = controller.get_log_tail()
                if log_tail.strip():
                    with st.expander(':page_facing_up: Agent Process Log (stdout/stderr)', expanded=False):
                        st.code(log_tail, language=None)
        else:
            st.info('No results yet. Results populate here once the agent run completes.')

    _live_section()
