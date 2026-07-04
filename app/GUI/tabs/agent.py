import streamlit as st
import time


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
            f"<strong style='color:{color};'>{node}</strong> — {detail}"
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

    current_state = controller.get_status() if controller else {}
    process_running = controller.is_running() if controller else False
    if st.session_state.get('agent_running') and controller and not process_running:
        st.session_state.agent_running = False
        current_state = controller.get_status()

    with col3:
        status_label = current_state.get('status', 'idle')
        run_mode = current_state.get('mode', 'production')
        updated_at = current_state.get('updated_at', 'N/A')
        if st.session_state.get('agent_running'):
            st.markdown('**Status**: 🟢 Running')
            st.markdown(f"**Target**: {st.session_state.get('current_agent_target', 'N/A')}")
        elif status_label == 'completed':
            st.markdown('**Status**: ✅ Completed')
            st.markdown(f"**Target**: {current_state.get('target', selected_target)}")
        elif status_label == 'failed':
            st.markdown('**Status**: 🔴 Failed')
            st.markdown(f"**Target**: {current_state.get('target', selected_target)}")
        else:
            st.markdown('**Status**: ⚪ Idle')
        st.caption(f"Mode: `{run_mode}` | Updated: `{updated_at}`")

    st.markdown('---')
    st.subheader(':scroll: Agent Feed')

    feed_placeholder = st.empty()

    if controller:
        st.caption(f"Run file: {controller.state_file}")

    if st.session_state.get('agent_running') and controller:
        for _ in range(60):
            state_snapshot = controller.get_status()
            if not controller.is_running() and state_snapshot.get('status') not in ('running', 'starting'):
                st.session_state.agent_running = False
                current_state = state_snapshot
                break

            events = controller.get_feed()
            if events:
                feed_placeholder.markdown(_render_events(events), unsafe_allow_html=True)
            else:
                feed_placeholder.info('Waiting for the first agent event...')

            time.sleep(1)

        state = controller.get_status()
        if state.get('status') == 'completed':
            st.success(':white_check_mark: Agent completed successfully!')
        elif state.get('status') == 'failed':
            st.error(f":x: Agent failed: {state.get('error', 'Unknown error')}")
    else:
        if controller:
            events = controller.get_feed()
            if events:
                feed_placeholder.markdown(_render_events(events), unsafe_allow_html=True)
            else:
                feed_placeholder.info('Agent feed will appear here when running. Select a target and click Start Agent.')
        else:
            feed_placeholder.info('Agent feed will appear here when running. Select a target and click Start Agent.')

    st.markdown('---')
    st.subheader(':bar_chart: Final Results')

    if controller:
        state = controller.get_status()
        final_state = state.get('final_state', {})
        if state.get('status') in ('completed', 'failed') or final_state:
            cols = st.columns(3)
            cols[0].metric('Open Ports', len(final_state.get('open_ports', [])))
            cols[1].metric('Vulnerabilities', len(final_state.get('vulnerabilities', [])))
            cols[2].metric('Exploit Success', 'Yes' if final_state.get('exploit_success') else 'No')

            with st.expander(':card_index_drawer: View Full State', expanded=False):
                st.json(state)
