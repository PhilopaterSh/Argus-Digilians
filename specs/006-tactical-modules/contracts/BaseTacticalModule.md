# Contract: BaseTacticalModule

**Module**: `app/modules/base.py`

---

## Interface

```python
class BaseTacticalModule(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def execute(self, target: str) -> str: ...
```

## Module Registration (`app/modules/__init__.py`)

```python
_modules: dict[str, BaseTacticalModule] = {}

def register(module: BaseTacticalModule) -> None: ...
def run_module(name: str, target: str) -> str: ...
def run_all(target: str) -> dict[str, str]: ...
def list_modules() -> list[tuple[str, str]]: ...  # [(name, description), ...]
```

## Behaviour

| Condition | Result |
|-----------|--------|
| `execute("example.com")` | Executes the tactical workflow, returns result string |
| `execute("")` | Returns error message "No target provided" |
| `register(module)` | Module added to `_modules` dict |
| `run_module("reasoning", target)` | Finds module by name, calls `execute(target)` |
| `run_module("nonexistent", target)` | Raises `KeyError` |
| `run_all(target)` | Returns `{name: result}` for all registered modules |

## Test Contract

- Test BaseTacticalModule cannot be instantiated directly (ABC)
- Test concrete subclass with valid target
- Test execute with empty target
- Test register + run_module
- Test run_all returns correct structure
- Test all 9 existing modules import cleanly after refactor
