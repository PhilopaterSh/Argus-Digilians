# Contract: GUI Modules

**Module**: `app/GUI/`

---

## Interface (desktop_gui.py)

```python
class DesktopArgusGUI:
    def __init__(self): ...
    def run(self) -> None: ...   # Start Tkinter main loop
    def analyze(self, target: str) -> str: ...   # Run analysis, return result
```

## Behaviour

| File | Condition | Result |
|------|-----------|--------|
| `desktop_gui.py` | Tkinter available | Opens native window, functional |
| `desktop_gui.py` | No Tkinter | Prints error message, exits with code 1 |
| `desktop_gui.py` | User clicks Run | Calls `WSLBridgeTools` + `ArgusBrain`, shows output |
| `argus_gui.py` | After fix | All imports resolve to `app.*` paths |
| `studio.py` | Imported | Re-exports `app.py` functionality |

## Test Contract

- Test all 3 GUI files import without errors
- Test desktop_gui detects missing Tkinter gracefully
- Test argus_gui imports resolve after fix
