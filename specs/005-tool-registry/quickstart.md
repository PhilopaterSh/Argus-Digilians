# Quickstart: Validating the Tool Registry

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Prerequisites

- Python 3.12+ with `Argus_venv` activated
- Existing `app/tools/*.py` modules

## Validation Steps

### 1. Unit Tests

```bash
cd <project-root>
.\Argus_venv\Scripts\Activate.ps1
pytest tests/test_registry/ -v
```

Expected: 15+ tests passing.

### 2. Registry Smoke Test

```python
from app.core.registry.tool_registry import ToolRegistry
from app.core.registry.base_tool import BaseToolService, ToolMetadata

registry = ToolRegistry()
print(registry.list_tools())  # []

# After registering default tools
from app.tools.tool_registry import WSLBridgeTools
facade = WSLBridgeTools()
print(facade.registry.list_tools())  # 14+ tools listed
```

### 3. Backward Compatibility Test

```python
from app.tools.tool_registry import WSLBridgeTools
tools = WSLBridgeTools()
# All 42 existing methods must still work
print(tools.host)
print(tools.distro)
result = tools.recon_suite("example.com")
print(result)
```

### 4. ArgusBrainV2 Test

```python
from app.core.agent.brain_v2 import ArgusBrainV2
brain = ArgusBrainV2()
result = brain.dispatch("recon", url="example.com")
print(result)
```
