# Quickstart: Validating GUI

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Validation Steps

### 1. Import Validation

```bash
pytest tests/test_gui/test_imports.py -v
```

Expected: 3 tests passing (app.py, argus_gui.py, desktop_gui.py).

### 2. Tkinter Desktop

```bash
python app/GUI/desktop_gui.py
```

Expected: Window appears with target input and Run button.

### 3. Tkinter Fallback

If Tkinter not installed:
```
Error: Tkinter is not available.
Install with: sudo apt-get install python3-tk
```

### 4. Streamlit Studio (existing)

```bash
streamlit run app/GUI/app.py
```

Expected: Browser opens at localhost:12199 (canonical port per `012` §2.6) with the Argus Studio interface.
