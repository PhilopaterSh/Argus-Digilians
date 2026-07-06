# Feature Specification: Reflective Verification Hardening

**Feature Branch**: `fix/copy-setup-to-scripts`

**Created**: 2026-06-29

**Status**: Implemented (Phase 007 in `specs/checklist.md`: CHK019–CHK024, 20 tests; verified 2026-07-05).

**Input**: `app/tools/reflective_verification.py` exists with 3 public methods (pre_execute_verify, post_execute_verify, task_difficulty_assessment) but has a TODO for infinite-loop prevention, is not exposed as a LangChain Tool, and has zero tests.

---

## User Scenarios & Testing

### User Story 1 - LangChain Tool Exposure (Priority: P1)

As a user, I want the verification service available as a LangChain Tool in the GUI, so the AI can call verification during reasoning.

### User Story 2 - Infinite-Loop Prevention (Priority: P1)

As a developer, I want the system to detect repeated identical commands and stop execution before it loops forever.

**Acceptance Scenarios**:
1. Given 3 consecutive identical commands, When pre_execute_verify is called, Then it returns a block warning.
2. Given a new unique command, When called, Then it passes validation.

### User Story 3 - Test Coverage (Priority: P2)

As a developer, I want tests for all 3 verification methods covering edge cases.

---

## Requirements

- **FR-001**: Implement infinite-loop detection via blackboard command history.
- **FR-002**: Expose all 3 methods as LangChain Tool-compatible functions.
- **FR-003**: Register verification tools in `WSLBridgeTools` (or via ToolRegistry).
- **FR-004**: Comprehensive test coverage for pre/post/tda methods.

## Key Entities

- `app/tools/reflective_verification.py` — hardened with loop detection
- `app/tools/tool_registry.py` — register new verification tools
- `tests/test_tools/test_reflective_verification.py` — tests
