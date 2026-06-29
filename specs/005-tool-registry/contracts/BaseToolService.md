# Contract: BaseToolService

**Module**: `app/core/registry/base_tool.py`

---

## Interface

```python
class BaseToolService(ABC):
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata: ...

    @abstractmethod
    def execute(self, **kwargs) -> Any: ...

@dataclass
class ToolMetadata:
    name: str
    description: str
    version: str = "1.0.0"
```

## Behaviour

| Condition | Result |
|-----------|--------|
| `metadata` called | Returns `ToolMetadata` with name, description, version |
| `execute()` called with valid args | Performs the tool's action, returns result |
| `execute()` called with invalid/missing args | Raises `TypeError` or `ValueError` |
| `execute()` fails during operation | Propagates original exception to caller |

## Implementation Requirements

- All concrete services in `app/tools/*.py` must subclass `BaseToolService`
- `execute()` must accept `**kwargs` for flexibility
- `ToolMetadata.name` must be unique within a `ToolRegistry`
