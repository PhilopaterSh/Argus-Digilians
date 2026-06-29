# Feature Specification: Self-Healing Expansion

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-06-29

**Status**: Draft

**Input**: `app/tools/self_heal.py` is a 31-line service that only handles `pip install` and `apt-get install`. The architecture v2 mandates proactive health monitoring, watchdog, process restart, and config repair — none of which exist.

---

## User Scenarios & Testing

### User Story 1 - Proactive Health Monitoring (Priority: P1)

As an operator, I want the system to periodically check that WSL, Ollama, and critical services are running, so failures are detected before the AI tries to use them.

**Acceptance Scenarios**:
1. Given healthy WSL and Ollama, When `health_check()` runs, Then it returns `{"wsl": "ok", "ollama": "ok"}`.
2. Given stopped Ollama, When `health_check()` runs, Then it returns `{"ollama": "failed"}` and triggers restart.

### User Story 2 - Service Restart (Priority: P1)

As an operator, I want Argus to restart failed services automatically, so manual intervention is minimized.

**Acceptance Scenarios**:
1. Given failed Ollama, When `restart_service("ollama")` runs, Then it attempts restart and reports success/failure.
2. Given failed WSL bridge, When `restart_service("wsl")` runs, Then it reinitializes the WSL bridge.

### User Story 3 - Test Coverage (Priority: P2)

As a developer, I want tests for all health check and restart methods.

---

## Requirements

- **FR-001**: `health_check()` method checking WSL, Ollama, and venv Python.
- **FR-002**: `restart_service(name)` method for common services.
- **FR-003**: `SelfHealingService` registered in `WSLBridgeTools` facade.
- **FR-004**: All new methods with type hints and error handling.
- **FR-005**: Comprehensive test coverage.

## Key Entities

- `app/tools/self_heal.py` — expanded service
- `app/tools/tool_registry.py` — register new methods
- `tests/test_tools/test_self_heal.py` — tests
