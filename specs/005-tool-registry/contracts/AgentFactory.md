# Contract: AgentFactory

**Module**: `app/core/agent/agent_factory_v2.py`

---

## Interface

```python
def create_default_registry() -> ToolRegistry: ...
def create_brain(
    registry: Optional[ToolRegistry] = None,
    model_name: Optional[str] = None
) -> ArgusBrainV2: ...
def register_all_tools(registry: ToolRegistry) -> None: ...
```

## Behaviour

| Function | Result |
|----------|--------|
| `create_default_registry()` | Returns `ToolRegistry` with all 14 services registered |
| `create_brain(None)` | Creates default registry + `ArgusBrainV2` |
| `create_brain(registry=my_registry)` | Creates `ArgusBrainV2` with given registry |
| `register_all_tools(registry)` | Registers all tools from `app/tools/` into the given registry |

## Tool Registration List

`register_all_tools` must register these services:

| Service Class | Module | Tool Name |
|--------------|--------|-----------|
| `ReconService` | `app.tools.recon` | `recon` |
| `VulnerabilityScanners` | `app.tools.scanners` | `scanners` |
| `PayloadSuggester` | `app.tools.payloads` | `payloads` |
| `SecretAnalyzer` | `app.tools.secrets` | `secrets` |
| `SmartWebSearch` | `app.tools.web_search` | `web_search` |
| `ReachabilityService` | `app.tools.reachability` | `reachability` |
| `CrawlerService` | `app.tools.crawler` | `crawler` |
| `EvasionService` | `app.tools.evasion` | `evasion` |
| `SelfHealingService` | `app.tools.self_heal` | `self_heal` |
| `ReflectiveVerificationService` | `app.tools.reflective_verification` | `reflective_verification` |
| `CommandRunner` | `app.tools.command_runner` | `command_runner` |
| `WSLBridge` | `app.tools.wsl_bridge` | `wsl_bridge` |

## Test Contract

- Test `create_default_registry()` returns registry with all 14 tools
- Test `create_brain()` returns working `ArgusBrainV2`
- Test `register_all_tools()` on empty registry
