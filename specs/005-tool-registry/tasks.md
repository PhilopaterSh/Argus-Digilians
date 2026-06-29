---

description: "Task list for Tool Registry Abstraction & Testing"
---

# Tasks: Tool Registry Abstraction & Testing

**Input**: Design documents from `specs/005-tool-registry/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

---

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [ ] T001 Create `app/core/registry/` package with `__init__.py`
- [ ] T002 [P] Create `app/core/agent/` package with `__init__.py`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story

- [ ] T003 Create `BaseToolService` ABC + `ToolMetadata` dataclass in `app/core/registry/base_tool.py`
- [ ] T004 Create `ToolRegistry` class in `app/core/registry/tool_registry.py` (register, unregister, get_tool, list_tools, __len__, __contains__)

**Checkpoint**: Foundation ready — BaseToolService and ToolRegistry exist with full interface

---

## Phase 3: User Story 1 — Plugin-Based Registration (Priority: P1) 🎯 MVP

**Goal**: Register tools dynamically without modifying the facade class

**Independent Test**: `registry.register(service)` then `registry.get_tool(name)` returns the service

### Implementation for User Story 1

- [ ] T005 [US1] Implement `register()` with duplicate-name warning in `app/core/registry/tool_registry.py`
- [ ] T006 [US1] Implement `unregister()`, `get_tool()`, `list_tools()`, `__len__`, `__contains__` in `app/core/registry/tool_registry.py`
- [ ] T007 [P] [US1] Add structured logging to all registry operations
- [ ] T008 [US1] Refactor `WSLBridgeTools` in `app/tools/tool_registry.py` to use `ToolRegistry` internally — add `_register_defaults()` method, keep all 42 public methods unchanged
- [ ] T009 [US1] Adapt `SelfHealingService` in `app/tools/self_heal.py` to implement `BaseToolService` (add `metadata` property, rename `system_self_heal` → `execute` with backward-compat alias)

**Checkpoint**: At this point, plugin-based registration works and WSLBridgeTools is backward-compatible

---

## Phase 4: User Story 2 — brain_v2.py & agent_factory_v2.py (Priority: P1)

**Goal**: Architecture-mandated components exist and work with the registry

**Independent Test**: `brain = ArgusBrainV2(registry); brain.dispatch("recon", url="...")` returns result

### Implementation for User Story 2

- [ ] T010 [US2] Create `ArgusBrainV2` class in `app/core/agent/brain_v2.py` with `dispatch()`, `get_available_tools()`, `get_tool_names()`
- [ ] T011 [US2] Implement default registry creation in `ArgusBrainV2.__init__()` if no registry provided
- [ ] T012 [US2] Create factory functions in `app/core/agent/agent_factory_v2.py`: `create_default_registry()`, `create_brain()`, `register_all_tools()`
- [ ] T013 [US2] Implement `register_all_tools()` to register all 14 services (ReconService, VulnerabilityScanners, PayloadSuggester, SecretAnalyzer, SmartWebSearch, ReachabilityService, CrawlerService, EvasionService, SelfHealingService, ReflectiveVerificationService, CommandRunner, WSLBridge, JSONReportWriter)

**Checkpoint**: Both architecture-mandated components exist and work with the registry

---

## Phase 5: User Story 3 — Test Coverage (Priority: P2)

**Goal**: Comprehensive unit tests for registry patterns

**Independent Test**: `pytest tests/test_registry/ -v` passes

### Implementation for User Story 3

- [ ] T014 [P] [US3] Create `tests/test_registry/` directory with `__init__.py`
- [ ] T015 [P] [US3] Write tests for `BaseToolService` (ABC cannot be instantiated, concrete subclass works) in `tests/test_registry/test_base_tool.py`
- [ ] T016 [P] [US3] Write tests for `ToolRegistry` (register, unregister, get_tool, list_tools, __len__, __contains__, duplicate warning, TypeError) in `tests/test_registry/test_tool_registry.py`
- [ ] T017 [P] [US3] Write tests for `ArgusBrainV2` (dispatch, KeyError, get_available_tools) in `tests/test_registry/test_brain_v2.py`
- [ ] T018 [P] [US3] Write tests for `agent_factory_v2.py` (create_default_registry returns 14 tools, create_brain returns working brain) in `tests/test_registry/test_agent_factory.py`

**Checkpoint**: All user stories complete, all tests passing

---

## Phase 6: Polish & Cross-Cutting

**Purpose**: Improvements that affect multiple user stories

- [ ] T019 [P] Run import validation: `python -c "from app.core.registry import ToolRegistry; from app.core.agent import ArgusBrainV2; print('OK')"`
- [ ] T020 [P] Run full test suite: `pytest tests/test_registry/ -v`
- [ ] T021 [P] Run quickstart.md validation steps manually
- [ ] T022 Update spec/005-tool-registry plan.md alignment table if needed

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies
- **Foundational (Phase 2)**: Depends on Setup — BLOCKS all user stories
- **US1 (Phase 3)**: Depends on Foundational
- **US2 (Phase 4)**: Depends on Foundational + US1 (needs ToolRegistry)
- **US3 (Phase 5)**: Depends on US1 + US2
- **Polish (Phase 6)**: Depends on all stories

### Within Each User Story

- Core implementation before integration
- Story complete before moving to next priority

### Commit Strategy

- Commit after each completed Phase block
- Preview: `git status` + `git diff` before committing
