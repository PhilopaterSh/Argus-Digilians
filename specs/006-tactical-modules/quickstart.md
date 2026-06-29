# Quickstart: Validating Tactical Modules

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Validation Steps

### 1. Import Validation Test

```bash
cd <project-root>
.\Argus_venv\Scripts\Activate.ps1
pytest tests/test_modules/test_imports.py -v
```

Expected: 9 tests passing (one per module).

### 2. Base Module Smoke Test

```python
from app.modules.base import BaseTacticalModule

class TestModule(BaseTacticalModule):
    @property
    def name(self): return "test"
    @property
    def description(self): return "Test module"
    def execute(self, target): return f"Test: {target}"

m = TestModule()
print(m.execute("example.com"))  # "Test: example.com"
```

### 3. Run All Smoke Test

```python
from app.modules import run_all
results = run_all("example.com")
print(results)  # Dict of module_name → result_string
```
