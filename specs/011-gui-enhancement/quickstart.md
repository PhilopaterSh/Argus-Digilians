# Quickstart: GUI Enhancement Validation

## Prerequisites

- Argus virtual environment activated (`Argus_venv`)
- Streamlit installed (`pip install streamlit`)
- Ollama running on localhost:11434
- Blackboard database initialized

## Validation Scenarios

### Scenario 1: LAUNCH_STUDIO.bat Works

```bash
cd C:\AI_PenTest_Project\remote_Argus_PhilopaterSh
scripts\LAUNCH_STUDIO.bat
```

**Expected**: Browser opens at `http://localhost:12199` showing the unified dashboard with all 5 navigation tabs (Dashboard, Targets, Agent, Reports, Settings).

### Scenario 2: Target Management

1. Open the dashboard
2. Navigate to "Targets" tab
3. Enter `https://example.com` and click "Add Target"
4. **Expected**: Target appears in the list with status "pending"
5. Add 2 more targets, verify all 3 appear

### Scenario 3: Agent Live Feed

1. Navigate to "Agent" tab
2. Select a target from the dropdown
3. Click "Start Agent"
4. **Expected**: Live cards appear showing node transitions (Recon → Scanner → Exploit → Reflective → Post-Exploit)
5. Verify retry loop is visible if WAF block is detected

### Scenario 4: Knowledge Graph

1. Run recon on a target from the Agent tab
2. Navigate to "Knowledge Graph" tab
3. **Expected**: Interactive graph showing entities (domain, IP, technologies) with connections
4. Click a node to see entity details

### Scenario 5: Report Export

1. After completing an agent run, navigate to "Reports" tab
2. Click "Generate Report"
3. Select "HTML" format
4. **Expected**: Professional HTML report downloads with executive summary and findings

### Scenario 6: Session Persistence

1. Add 3 targets to a session
2. Click "Save Session" in Settings
3. Close the browser tab
4. Reopen `http://localhost:12199`
5. Click "Load Session" and select the saved session
6. **Expected**: All 3 targets are restored

## Smoke Test

```bash
# Import validation
python -c "from app.GUI.dashboard import *; print('Dashboard imports OK')"
python -c "from app.GUI.pages.dashboard import *; print('Dashboard page imports OK')"
python -c "from app.GUI.pages.targets import *; print('Targets page imports OK')"
python -c "from app.GUI.pages.agent import *; print('Agent page imports OK')"

# Run pytest
pytest tests/test_gui/ -v
```
