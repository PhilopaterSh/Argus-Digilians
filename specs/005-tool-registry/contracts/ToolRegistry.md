# Contract: ToolRegistry

**Module**: `app/core/registry/tool_registry.py`

---

## Interface

```python
class ToolRegistry:
    def register(self, tool: BaseToolService) -> None: ...
    def unregister(self, name: str) -> None: ...
    def get_tool(self, name: str) -> Optional[BaseToolService]: ...
    def list_tools(self) -> list[ToolMetadata]: ...
    def get_tool_names(self) -> list[str]: ...
    def __len__(self) -> int: ...
    def __contains__(self, name: str) -> bool: ...
```

## Behaviour

| Condition | Result |
|-----------|--------|
| `register(tool)` with unique name | Tool added to internal dict; log message |
| `register(tool)` with duplicate name | Warn and overwrite |
| `register(non-BaseToolService)` | Raises `TypeError` |
| `get_tool(existing_name)` | Returns the `BaseToolService` instance |
| `get_tool(non_existent_name)` | Returns `None` |
| `unregister(existing_name)` | Removes tool; log message |
| `unregister(non_existent)` | Silently no-op |
| `list_tools()` | Returns list of `ToolMetadata` for all registered tools |
| `__contains__("name")` | Returns True if tool is registered |

## Thread Safety

Registration and lookup are in-memory operations. The registry is not designed for concurrent access from multiple threads (single-threaded async architecture assumed).

## Test Contract

- Test register, unregister, get_tool, list_tools, __len__, __contains__
- Test duplicate registration warning
- Test TypeError on non-BaseToolService
- Test get_tool returns None for unknown name
- Test unregister of non-existent tool is safe
