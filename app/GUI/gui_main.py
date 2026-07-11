"""
DEPRECATED shim - re-exports the canonical dashboard.

Converted 2026-07-10 from a full, independently-running 95-line Streamlit
duplicate of app/GUI/dashboard.py to a true one-line re-export, matching
studio.py's pattern. The previous "DeprecationWarning" bolted on top still
fully built its own ArgusBrain with its own hardcoded, drifted 9-tool list
and a hardcoded stale model name (not reading ArgusConfig at all) and
rendered a full independent UI if launched directly.

Usage:
    streamlit run app/GUI/gui_main.py
"""

from app.GUI.dashboard import *
