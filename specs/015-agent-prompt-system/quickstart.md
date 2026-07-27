# Quickstart: Agent Prompt System (Canonical)

**Phase**: 1 - Validation | **Date**: 2026-07-06 | **Spec**: `specs/015-agent-prompt-system/spec.md`

---

## Purpose

How to validate the canonical prompt system. The builders are pure functions, so most checks run
without Ollama; the final AI-eval needs a runtime.

## Prerequisites

- Python 3.12. `langchain-core` for the message types (already in `config/requirements.txt`).
- Run from the repository root.

---

## Check 1: One canonical source (legacy warns)

```bash
python -c "import warnings; warnings.simplefilter('error');
import app.core.prompts" 2>&1 | head -3
```

**Expected (after Phase 5)**: importing `app.core.prompts` raises/emits a `DeprecationWarning`
pointing to `app.core.agent.react_prompts` (SC-001, FR-001).

---

## Check 2: Required sections present

```bash
python - <<'PY'
from app.core.agent.react_prompts import build_react_system_prompt
state = {"target": "example.com", "phase": "recon", "iteration_count": 0,
         "max_iterations": 10, "blackboard_summary": "none",
         "_tools": {"Check_Reachability": lambda: None}}
p = build_react_system_prompt(state)
required = ["Argus AI", "PHASE", "Reflective", "Content-Length", "LIVE", "Final Answer"]
missing = [s for s in required if s.lower() not in p.lower()]
print("MISSING:", missing or "none")
PY
```

**Expected (after Phase 1-3)**: `MISSING: none` - methodology + reflective-verification + fusion
sections are present (SC-002, FR-002/003/008).

---

## Check 3: Structured output primary, no anti-JSON rule

```bash
python -c "from app.core.agent import react_prompts as r; import inspect;
src = inspect.getsource(r);
print('anti-JSON rule present:', 'NEVER provide a JSON' in src)"
```

**Expected**: `False` - the legacy anti-JSON instruction is gone; JSON Action is the preferred format
(SC-003, FR-005, ADR-13).

---

## Check 4: Tool names come from the registry

```bash
python - <<'PY'
from app.core.agent.react_prompts import build_react_system_prompt
tools = {"Recon_Suite": lambda: None, "Run_Nikto": lambda: None}
p = build_react_system_prompt({"_tools": tools})
print("all tool names rendered:", all(t in p for t in tools))
PY
```

**Expected**: `True` - the rendered names match the passed tool map, not a hard-coded list
(SC-004, FR-006).

---

## Check 5: Final-answer contract

```bash
python -c "from app.core.schemas import SecurityReport; print('SecurityReport fields:', list(SecurityReport.model_fields.keys()))"
```

**Expected**: includes `summary`, `attack_surface_stats`, `findings`, `overall_risk_score`,
`next_steps`, `output` (FR-007).

---

## Check 6: Prompt version

```bash
python -c "from app.core.agent import react_prompts as r; print('PROMPT_VERSION' , getattr(r,'PROMPT_VERSION','MISSING'))"
```

**Expected (after Phase 4)**: a version string (FR-009).

---

## Check 7: Unit tests

```bash
pytest tests/test_agent/test_react_prompts.py -q
```

**Expected**: pass - required sections, registry tool names, purity (NFR-002).

---

## Check 8: AI-evaluation (requires Ollama)

```bash
pytest -m eval -k prompt
```

**Expected**: a full agent run produces a final answer that validates against `SecurityReport`, and
the loop terminates within `max_iterations` (SC-005, `012` section 6).

---

## Validation checklist

| Check | Expected | Source |
|-------|----------|--------|
| Legacy warns | DeprecationWarning | SC-001 |
| Sections present | methodology + verification + fusion | SC-002 |
| No anti-JSON rule | structured output primary | SC-003 |
| Registry tool names | match tool map | SC-004 |
| Report contract | SecurityReport fields | FR-007 |
| Prompt version | present | FR-009 |
| Unit tests | pass | NFR-002 |
| AI-eval | report valid, loop bounded | SC-005 |
