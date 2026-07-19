"""
DEPRECATED shim - re-exports the canonical dashboard.

Converted 2026-07-10 from a full, independently-running 179-line Streamlit
duplicate of app/GUI/dashboard.py to a true one-line re-export, matching
studio.py's pattern. The previous "DeprecationWarning" bolted on top still
fully built its own ArgusBrain with its own hardcoded, drifted 3-tool list
(not the canonical 17-tool app/core/agent/brain_tools.py list) and rendered
a full independent UI if launched directly.

Usage:
    streamlit run app/GUI/argus_gui.py
"""

from app.GUI.dashboard import *
