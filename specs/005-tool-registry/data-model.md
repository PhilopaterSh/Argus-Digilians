# Data Model: Tool Registry

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Architecture Flow

```
External Call (GUI / Brain / Script)
    │
    ▼
WSLBridgeTools (legacy facade, unchanged API)
    │  delegates to
    ▼
ToolRegistry (app/core/registry/tool_registry.py)
    │
    ├── .register() → stores BaseToolService
    ├── .get_tool() → returns registered service by name
    ├── .list_tools() → returns metadata for all tools
    └── .unregister() → removes a tool
            │
            ▼
    BaseToolService.execute(**kwargs)
            │
            ├── ReconService.execute()
            ├── VulnerabilityScanners.execute()
            ├── PayloadSuggester.execute()
            ├── SecretAnalyzer.execute()
            ├── SmartWebSearch.execute()
            ├── ReachabilityService.execute()
            ├── CrawlerService.execute()
            ├── EvasionService.execute()
            ├── SelfHealingService.execute()
            ├── ReflectiveVerificationService.execute()
            └── CommandRunner.execute()
                    │
                    ▼
                WSLBridge → Kali WSL / SSH
```

## Entity Relationship

```
ToolRegistry (1) ──── (*) BaseToolService
    │                        │
    │                        ├── ToolMetadata (name, description, version)
    │                        └── execute(**kwargs)
    │
    └── WSLBridgeTools (legacy facade, HAS-A ToolRegistry)

ArgusBrainV2 (1) ──── (1) ToolRegistry (receives via constructor DI)
    │
    └── dispatch(tool_name, **kwargs)
            │
            └── ToolRegistry.get_tool(name).execute(**kwargs)

AgentFactoryV2
    └── create_brain(registry) → ArgusBrainV2
    └── create_default_registry() → ToolRegistry (with all 14 services)
```

## Data Flow

### Registration Flow

```
Caller → registry.register(service)
    ├── Validate service is BaseToolService
    ├── Check for name conflict → warn if duplicate
    ├── Store in self._tools[service.metadata.name]
    └── Log registration
```

### Dispatch Flow

```
Caller → brain.dispatch("recon", url="example.com")
    ├── registry.get_tool("recon")
    │       ├── Found → return service
    │       └── Not found → return None / raise KeyError
    ├── service.execute(url="example.com")
    │       ├── Validate args
    │       ├── Execute via WSL bridge
    │       └── Return result
    └── Return result to caller
```

## State Categories

| State | Condition | Action |
|-------|-----------|--------|
| Unregistered | Tool name not in `_tools` | `get_tool()` returns None |
| Registered | Tool name in `_tools` | `get_tool()` returns service |
| Executing | `execute()` running | Blocking call; result queued |
| Failed | `execute()` raised | Exception propagated to caller |
