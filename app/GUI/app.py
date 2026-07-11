"""
DEPRECATED shim - re-exports the canonical dashboard.

Converted 2026-07-10 from a full, independently-running 134-line Streamlit
duplicate of app/GUI/dashboard.py to a true one-line re-export, matching
studio.py's pattern. The previous "DeprecationWarning + st.warning()" bolted
on top still fully built its own ArgusBrain with its own hardcoded, drifted
12-tool list (not the canonical 17-tool app/core/agent/brain_tools.py list)
and rendered a full independent UI if launched directly - a real risk, not
just clutter, since anyone who ran this file got a materially worse/stale
experience than the canonical dashboard while believing they were using
Argus normally.

Usage:
    streamlit run app/GUI/app.py
"""

from app.GUI.dashboard import *
