# Contract: ArgusBrainV2

**Module**: `app/core/agent/brain_v2.py`

---

## Interface

```python
class ArgusBrainV2:
    def __init__(self, registry: ToolRegistry, model_name: Optional[str] = None): ...
    def dispatch(self, tool_name: str, **kwargs) -> Any: ...
    def get_available_tools(self) -> list[ToolMetadata]: ...
    def get_tool_names(self) -> list[str]: ...
```

## Behaviour

| Condition | Result |
|-----------|--------|
| `dispatch("recon", url="x.com")` | Finds tool in registry, calls execute, returns result |
| `dispatch("nonexistent", ...)` | Raises `KeyError(f"Tool not found: nonexistent")` |
| `dispatch` with tool that raises | Exception propagates to caller |
| `get_available_tools()` | Delegates to `registry.list_tools()` |
| Initialized without registry | Creates a default `ToolRegistry` with all 14 services |

## Dependency

- Requires `ToolRegistry` from `app/core/registry/tool_registry.py`
- Requires `BaseToolService` from `app/core/registry/base_tool.py`

## Test Contract

- Test dispatch calls the correct tool's execute method
- Test dispatch raises KeyError for unknown tool
- Test get_available_tools returns correct metadata
- Test default registry creation in __init__
