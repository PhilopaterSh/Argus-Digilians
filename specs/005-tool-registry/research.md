# Research: Tool Registry Abstraction & Testing

**Phase**: 0 — Technical Research | **Date**: 2026-06-29

---

## Current State Analysis

### Existing Files

| File | LOC | Role |
|------|-----|------|
| `app/tools/tool_registry.py` | 104 | `WSLBridgeTools` facade — 42 public methods, 14 sub-services |
| `app/tools/command_runner.py` | — | `CommandRunner` |
| `app/tools/wsl_bridge.py` | — | `WSLBridge`, `WSLConfig` |
| `app/tools/recon.py` | — | `ReconService` |
| `app/tools/scanners.py` | — | `VulnerabilityScanners` |
| `app/tools/payloads.py` | — | `PayloadSuggester` |
| `app/tools/secrets.py` | — | `SecretAnalyzer` |
| `app/tools/web_search.py` | — | `SmartWebSearch` |
| `app/tools/reachability.py` | — | `ReachabilityService`, `JSONReportWriter` |
| `app/tools/crawler.py` | — | `CrawlerService` |
| `app/tools/evasion.py` | — | `EvasionService` |
| `app/tools/self_heal.py` | — | `SelfHealingService` |
| `app/tools/reflective_verification.py` | — | `ReflectiveVerificationService` |
| `app/tools/simulation.py` | — | `ZEROAPTSimulation` |

**Missing components from Architecture v2**:
- `app/core/agent/brain_v2.py` — referenced in §3.1 C4 diagram but does not exist
- `app/core/agent/agent_factory_v2.py` — referenced but does not exist
- No `app/core/registry/` directory at all

### Key Issues

1. **Hardcoded dependency injection**: `WSLBridgeTools.__init__()` creates every service explicitly — adding a new tool requires editing the facade.
2. **No plugin registration**: Tools cannot be registered dynamically; all are created eagerly at init.
3. **No tool metadata**: No `name`, `description`, or `version` attributes on services — LangChain Tool wrappers in GUI duplicate this info.
4. **Missing architecture components**: `brain_v2.py` and `agent_factory_v2.py` are referenced in the C4 diagram but don't exist.
5. **Zero tests**: No unit tests for any registry or service file.

### Existing Usage Patterns

```python
# Current usage (GUI/app.py line 30):
tools = WSLBridgeTools()

# Current usage (brain/agent.py):
# The current brain imports and instantiates tool_registry.WSLBridgeTools directly
```

## Design Approach

### BaseToolService (ABC)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class ToolMetadata:
    name: str
    description: str
    version: str = "1.0.0"

class BaseToolService(ABC):
    @property
    @abstractmethod
    def metadata(self) -> ToolMetadata: ...
    
    @abstractmethod
    def execute(self, **kwargs) -> Any: ...
```

### ToolRegistry

```python
class ToolRegistry:
    def __init__(self):
        self._tools: dict[str, BaseToolService] = {}
    
    def register(self, tool: BaseToolService) -> None: ...
    def unregister(self, name: str) -> None: ...
    def get_tool(self, name: str) -> Optional[BaseToolService]: ...
    def list_tools(self) -> list[ToolMetadata]: ...
    def get_tool_names(self) -> list[str]: ...
```

### WSLBridgeTools Refactoring

Keep the 42-method public API exactly as-is. Internally, replace direct service creation with:

```python
class WSLBridgeTools:
    def __init__(self):
        self.memory = ArgusMemory()
        self.registry = ToolRegistry()
        self._register_defaults()
    
    def _register_defaults(self):
        # Register all 14 services via ToolRegistry
        ...
    
    # Existing delegation methods unchanged
    def recon_suite(self, url, ...):
        return self.registry.get_tool("recon").execute(url=url, ...)
```

### BrainV2

```python
class ArgusBrainV2:
    def __init__(self, registry: ToolRegistry, ...): ...
    def dispatch(self, tool_name: str, **kwargs) -> Any: ...
```

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Breaking changes to 42-method API | Low | Critical | Keep all delegation methods; add @property access to registry |
| Circular imports between registry and tools | Low | Medium | Registry lives in `app/core/registry/`, tools in `app/tools/` |
| Legacy brain not updated to use brain_v2 | Medium | Medium | Keep both; brain_v2 is opt-in initially |
