# Data Model: Tactical Modules

**Phase**: 1 — Design & Contracts | **Date**: 2026-06-29

---

## Architecture Flow

```
Brain / User
    │
    ▼
app/modules/__init__.py
    ├── run_all(target) → iterate all registered modules
    └── run_module(name, target) → single module
            │
            ▼
    BaseTacticalModule (ABC)
        │
        ├── name: str (property)
        ├── description: str (property)
        └── execute(target: str) → str
                │
                ├── argus_reasoning.execute(target)
                ├── argus_deep_exploit.execute(target)
                ├── stealth_exploit.execute(target)
                └── ...
                        │
                        ▼
                WSLBridgeTools / ArgusBrain / API calls
```

## Entity Relationship

```
ModuleRegistry (dict[str, BaseTacticalModule])
    │
    ├── "reasoning"       → ArgusReasoningModule
    ├── "deep_exploit"    → ArgusDeepExploitModule
    ├── "stealth"         → StealthExploitModule
    ├── "run_recon"       → RunReconModule
    ├── "run_full_recon"  → RunFullReconModule
    ├── "map_target"      → MapTargetModule
    ├── "seed_memory"     → SeedMemoryModule
    ├── "ddgs"            → DDGSModule
    └── "crawler"         → CrawlerModule
```
