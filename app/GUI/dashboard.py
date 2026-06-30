import streamlit as st
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

st.set_page_config(
    page_title="Argus Security Studio",
    page_icon=":shield:",
    layout="wide",
    initial_sidebar_state="expanded",
)

from app.GUI.components.status_bar import render_status_bar
from app.GUI.utils.blackboard import init_gui_tables

try:
    init_gui_tables()
except Exception:
    pass

if "targets" not in st.session_state:
    st.session_state.targets = []
if "jobs" not in st.session_state:
    st.session_state.jobs = []
if "settings" not in st.session_state:
    st.session_state.settings = {
        "model": os.getenv("SELECTED_MODEL", "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"),
        "ollama_endpoint": "http://localhost:11434",
        "ssh_user": os.getenv("WSL_USER", "kali"),
        "ssh_pass": os.getenv("WSL_PASS", "kali"),
        "theme": "dark",
    }
if "active_session" not in st.session_state:
    st.session_state.active_session = None
if "agent_running" not in st.session_state:
    st.session_state.agent_running = False

st.markdown("""
    <style>
    .main > div { padding-top: 1rem; }
    .stApp { background-color: #0e1117; }
    h1, h2, h3 { color: #00ff41 !important; }
    .stSidebar .sidebar-content { background-color: #1a1d24; }
    div[data-testid="stSidebarNav"] { background-color: #1a1d24; }
    div[data-testid="stSidebarNav"] li { color: #ccc; }
    </style>
""", unsafe_allow_html=True)

st.sidebar.title(":shield: Argus Studio")
st.sidebar.markdown("---")

page = st.sidebar.radio(
    "Navigation",
    ["Dashboard", "Targets", "Agent", "Knowledge Graph", "Reports", "Settings"],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
render_status_bar()

if page == "Dashboard":
    from app.GUI.pages.dashboard import render_dashboard
    render_dashboard()
elif page == "Targets":
    from app.GUI.pages.targets import render_targets
    render_targets()
elif page == "Agent":
    from app.GUI.pages.agent import render_agent
    render_agent()
elif page == "Knowledge Graph":
    from app.GUI.pages.knowledge_graph import render_knowledge_graph
    render_knowledge_graph()
elif page == "Reports":
    from app.GUI.pages.reports import render_reports
    render_reports()
elif page == "Settings":
    from app.GUI.pages.settings import render_settings
    render_settings()
