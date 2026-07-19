import streamlit as st
import uuid
from datetime import datetime, timezone


def render_targets():
    st.title(":dart: Target Management")
    st.markdown("---")

    if "targets" not in st.session_state:
        st.session_state.targets = []

    with st.expander(":heavy_plus_sign: Add New Target", expanded=False):
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            url = st.text_input("Target URL / Domain / IP", placeholder="https://example.com")
        with col2:
            target_type = st.selectbox("Type", ["url", "domain", "ip", "cidr"])
        with col3:
            tags = st.text_input("Tags (comma separated)", placeholder="critical,web")
        if st.button("Add Target", type="primary"):
            if url:
                new_target = {
                    "id": str(uuid.uuid4()),
                    "url": url,
                    "type": target_type,
                    "status": "pending",
                    "tags": [t.strip() for t in tags.split(",") if t.strip()],
                    "added_at": datetime.now(timezone.utc).isoformat(),
                }
                st.session_state.targets.append(new_target)
                st.success(f"Target added: {url}")
                st.rerun()
            else:
                st.error("Please enter a target URL/domain/IP.")

    st.markdown("---")
    targets = st.session_state.targets

    if not targets:
        st.info("No targets yet. Add one above.")
        return

    search = st.text_input(":mag: Search targets", placeholder="Filter by URL or tag...")
    filtered = targets
    if search:
        filtered = [t for t in targets if search.lower() in t["url"].lower() or any(search.lower() in tag.lower() for tag in t.get("tags", []))]

    for i, target in enumerate(filtered):
        status_icon = {
            "pending": ":gray_circle:",
            "running": ":yellow_circle:",
            "completed": ":green_circle:",
            "failed": ":red_circle:",
        }.get(target["status"], ":gray_circle:")

        with st.container():
            cols = st.columns([4, 1, 1, 1, 1])
            with cols[0]:
                st.markdown(f"**{target['url']}**  ")
                if target.get("tags"):
                    tag_badges = " ".join([f":blue-badge[{t}]" for t in target["tags"]])
                    st.markdown(tag_badges)
            with cols[1]:
                st.markdown(f"{status_icon} {target['status'].title()}")
            with cols[2]:
                st.markdown(f":bust_in_silhouette: {target['type']}")
            with cols[3]:
                if st.button(":rocket: Run", key=f"run_{target['id']}"):
                    target["status"] = "running"
                    controller = st.session_state.get("agent_controller")
                    if controller:
                        controller.start(target["url"])
                    st.session_state.agent_running = True
                    st.session_state.current_agent_target = target["url"]
                    st.rerun()
            with cols[4]:
                if st.button(":wastebasket:", key=f"del_{target['id']}"):
                    st.session_state.targets = [t for t in st.session_state.targets if t["id"] != target["id"]]
                    st.rerun()
        st.markdown("---")
