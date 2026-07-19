# Data Model: GUI

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## GUI Components

```
User
    │
    ├── app/GUI/app.py (Streamlit Studio)
    │       └── browser-based UI → WSLBridgeTools → ArgusBrain
    │
    ├── app/GUI/argus_gui.py (Streamlit Legacy)
    │       └── browser-based UI → WSLBridgeTools → ArgusBrain
    │
    └── app/GUI/desktop_gui.py (Tkinter Desktop) ← NEW
            └── native window → WSLBridgeTools → ArgusBrain
```

## Desktop GUI Layout

```
┌─────────────────────────────────────┐
│  Argus Desktop Security Studio      │
├─────────────────────────────────────┤
│  Target: [___________________]      │
│  [RUN ANALYSIS]                     │
├─────────────────────────────────────┤
│                                     │
│  ┌─ Output ──────────────────────┐  │
│  │  Analysis results appear here │  │
│  │  ...                          │  │
│  └───────────────────────────────┘  │
├─────────────────────────────────────┤
│  Status: Ready                   │
└─────────────────────────────────────┘
```
