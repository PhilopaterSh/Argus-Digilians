# Research: GUI Alignment & Tkinter Desktop

**Phase**: 0 — Technical Research | **Date**: 2026-06-29

---

## Current State

### Files in `app/GUI/`

| File | LOC | Type | Status |
|------|-----|------|--------|
| `app.py` | 123 | Streamlit Studio | ✅ Clean imports from `app.*` |
| `argus_gui.py` | 165 | Streamlit (claims Tkinter) | ❌ Legacy imports: `from core.tools` |
| `__init__.py` | — | Bare init | ✅ |
| `Launch_Argus.bat` | — | Batch launcher | ✅ |
| `Run_Argus_Studio.bat` | — | Batch launcher | ✅ |

### Architecture Doc References

The architecture v2 doc (§3.1, §5.1) references:
- `gui_app.py` — **DOES NOT EXIST**
- `argus_gui.py` as Tkinter — **ACTUALLY STREAMLIT**
- `studio.py` — **DOES NOT EXIST**

### Import Issues in `argus_gui.py`

```python
# Line 1-2 (current, broken):
from core.tools import WSLBridgeTools
from core.agent import ArgusBrain

# Should be:
from app.tools.tool_registry import WSLBridgeTools
from app.core.brain import ArgusBrain
```

### Desktop Tkinter Design

Minimal Tkinter app with:
- Target URL input field
- Run Analysis button
- Output text area with scrollbar
- Status bar
- Graceful fallback if Tkinter not installed
