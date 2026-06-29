# Feature Specification: Tool Registry Abstraction & Testing

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-06-29

**Status**: Draft

**Input**: The `WSLBridgeTools` facade in `app/tools/tool_registry.py` exists with 14 sub-services but has no plugin-based registration pattern, no `brain_v2.py`, no `agent_factory_v2.py`, and zero tests. The architecture doc references components that don't exist yet.

---

## User Scenarios & Testing

### User Story 1 - Plugin-Based Registration (Priority: P1)

As a developer, I want to register new tools without modifying the facade class, so the registry is extensible.

**Acceptance Scenarios**:
1. Given a new tool class implementing `BaseToolService`, When registered via `registry.register()`, Then it becomes available via `registry.get_tool(name)`.
2. Given an unregistered tool name, When queried, Then `get_tool()` returns `None`.

### User Story 2 - brain_v2.py & agent_factory_v2.py (Priority: P1)

As a developer, I want the brain and agent factory components referenced in the architecture doc to exist and work with the tool registry, so the architecture is fully realized.

**Acceptance Scenarios**:
1. Given `brain_v2.py`, When initialized with a registry, Then it can discover and invoke tools by name.
2. Given `agent_factory_v2.py`, When called, Then it produces a configured brain with registry.

### User Story 3 - Test Coverage (Priority: P2)

As a developer, I want unit tests for the registry and its interaction patterns, so regressions are caught.

---

## Requirements

- **FR-001**: `BaseToolService` abstract class defining `name`, `description`, `execute()` interface.
- **FR-002**: `ToolRegistry` class with `register()`, `unregister()`, `get_tool()`, `list_tools()` methods.
- **FR-003**: `WSLBridgeTools` facade refactored to use `ToolRegistry` internally (backward-compatible).
- **FR-004**: `brain_v2.py` with registry-based tool dispatch.
- **FR-005**: `agent_factory_v2.py` with factory functions.
- **FR-006**: All registry methods must have type hints and error handling.
- **FR-007**: Existing `app/tools/*.py` services adapted to `BaseToolService` contract.

## Key Entities

- `app/core/registry/tool_registry.py` — `BaseToolService`, `ToolRegistry`
- `app/core/agent/brain_v2.py` — `ArgusBrainV2`
- `app/core/agent/agent_factory_v2.py` — factory functions
- `app/tools/tool_registry.py` — refactored `WSLBridgeTools`
- `app/tools/*.py` — adapted sub-services (ReconService, etc.)
