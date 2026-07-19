# Implementation Plan: Unify All Branches Into One Version

**Branch**: `027-merge-branches` | **Date**: 2026-07-17 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `specs/027-merge-branches/spec.md`, grounded by
[research.md](./research.md) (cross-verified across 3 independent analyses — Claude, agy, opencode)

## Summary

Unify `main` and 9 divergent contributor branches of the Argus Security Framework into one working
codebase. `research.md` establishes the ground truth: only 6 of 10 refs share real git ancestry (the
other 4 are disconnected histories); `fix/copy-setup-to-scripts` already absorbs 3 of the 6 connected
branches and is the most production-mature branch (pytest/ruff/mypy, CI, 26 completed Spec-Kit
features). The technical approach is therefore **not a single big merge**, but a sequenced series of
independently-tested integration steps — real `git merge` for the 2 remaining connected branches
(`argus/SALMA`, plus `argus-recovery/master`'s toolchain-only contribution), and manual file-level
reconciliation for the 2 remaining disconnected branches worth keeping (`momen`,
`argus/DESKTOP-BVV10T0`), with 2 branches (`argus/MOUSTAFA-PC` partially, plus assorted superseded
branches) triaged down to near-zero remaining work.

## Technical Context

**Language/Version**: Python 3.12 (`Argus_venv`), per `fix/copy-setup-to-scripts` and `main`.
`momen` was built against 3.10 — needs a compatibility check during its reconciliation (research.md §6).

**Primary Dependencies**: LangChain (+`langchain-ollama`/`-classic`/`-huggingface`/`-community`/
`-core`), `langgraph`, Streamlit, FAISS-CPU, `sentence-transformers`, `paramiko`, `duckduckgo-search`,
`torchvision`, `networkx`/`pyvis`.

**Storage**: SQLite (`argus_intelligence.db`, blackboard pattern — both `main` and `argus/SALMA` use
this; schemas must be reconciled, not just files).

**Testing**: pytest (`pytest.ini`, markers `unit`/`integration`/`e2e`/`eval`/`regression`) + Pester
(PowerShell installer tests) — **adopted from `fix/copy-setup-to-scripts`**, the only branch where
this exists today (research.md §6). `momen`'s custom `tests/run_all_tests.py` runner is NOT adopted;
its test *content* gets ported into pytest, its runner does not.

**Target Platform**: Windows 10/11 host + WSL2 (Kali Linux) guest, SSH bridge via `paramiko`.

**Project Type**: Single project, desktop/CLI + Streamlit GUI hybrid (not web frontend/backend split).

**Performance Goals**: N/A for this feature — unification must not regress existing recon/scan
performance, but introduces no new performance target of its own.

**Constraints**: `Argus_venv` isolation must be preserved (Constitution §Technology & Security);
every merge step MUST leave the app startable (`run_argus_cli.py` / `scripts/LAUNCH_STUDIO.bat`);
no unauthorized-use functionality may be introduced (Constitution Principle I).

**Scale/Scope**: 10 refs (`main` + 9 branches) → 1 unified branch; ~1,300 files touched across all
branches combined (per research.md diffstats), but the *actual* remaining integration surface after
accounting for already-absorbed branches is much smaller (see Phase breakdown below).

## Constitution Check

*GATE: Must pass before Phase 0 research (already done — see research.md) and re-checked here after
Phase 1 design.*

| Principle | Check | Status |
|---|---|---|
| I. Authorized Use Only | No branch introduces unauthorized-scanning/evasion functionality per research.md's branch-by-branch review; the one flagged artifact (`Discovery_cultbeauty_co_uk.txt`) is empty and will be dropped, not carried forward. | ✅ PASS |
| II. English-Only Documentation & Code | All branches' docs are in English (Constitution predates this merge but all inspected content already complies). | ✅ PASS |
| III. Centralized, Predictable Project Layout | **Gate at risk**: `momen` uses `core/`/`GUI/` at repo root, not `app/core/`/`app/GUI/`. Plan requires re-homing `momen`'s content under `app/` during its integration step — tracked explicitly as a task, not silently allowed to violate the principle. | ⚠ CONDITIONAL — resolved by design (Integration Step 4) |
| IV. Installer & Documentation Stay in Sync | **Gate at risk pre-merge**: two installers exist (`INSTALL_EVERYTHING.ps1` vs `ARGUS_INSTALLER.ps1`). research.md §4 resolves this: adopt `fix/copy-setup-to-scripts`'s `ARGUS_INSTALLER.ps1` as canonical, but its own task tracker admits clean-environment validation (T013/T014) is not done — plan adds that validation as an explicit task before calling the installer "done," not just adopting it as-is. | ⚠ CONDITIONAL — resolved by design (Integration Step 3) |
| V. Explicit Windows/Kali Boundary | No branch blurs this boundary further; `fix/copy-setup-to-scripts`'s SSH-bridge code is the most mature version and becomes canonical. | ✅ PASS |

No unjustified complexity — see Complexity Tracking (empty; no violations require justification beyond
the two CONDITIONAL gates above, which are resolved by explicit design decisions, not waived).

## Synthesized Design Decisions (reconciled across 3 independent plans — Claude, agy, opencode)

`plan-agy.md` and `plan-opencode.md` (built independently, without seeing this file) converge on the
same integration base and sequencing. Where they added something this file didn't already have, or
made a different judgment call, it's reconciled here rather than in three separate documents:

1. **`momen`'s experimental agent** (`_experimental_advanced_modules/core/agent.py`, 13-step
   sequential pipeline): **both** agy and opencode independently chose "isolate, don't merge or
   delete" (agy: `app/modules/experimental_agent/`; opencode: `app/modules/_experimental/agent.py`).
   Two independent AI runs converging on the same non-obvious call is a meaningful signal.
   **Adopted**, with opencode's added safety condition: it must be **opt-in only, never
   auto-registered in the Tool Registry** — this is what actually satisfies Constitution Principle I
   here (an unreviewed 13-step recon→exploit script must not run just because it's importable).
2. **`Argus_Secure_Sync.exe` binary containment**: agy proposed a concrete
   `security_review_required/` directory, excluded from installer build scripts, rather than just
   "flag it and move on." **Adopted** — more actionable than leaving it in place with a comment.
3. **Installer clean-environment validation** (closing T013/T014): agy specified running it in a
   **Windows Sandbox or a disposable VM**, not the developer's own machine. **Adopted** — avoids
   contaminating the dev environment while still providing a genuine clean-environment test.
4. **`argus/MOUSTAFA-PC`'s memory tables vs. `argus/SALMA`'s blackboard** — **RESOLVED (unanimous,
   3-way discussion round, 2026-07-17)**: opencode did a direct side-by-side read of
   `SALMA:app/core/memory/memory_service.py` vs. `MOUSTAFA-PC:app/core/memory/database.py` and found
   the five tables (`targets`, `findings`, `entities`, `relations`, `global_state`) are **structurally
   identical** — independently re-verified via `git show`/`grep` before accepting. agy then
   independently re-checked the same two files and additionally found MOUSTAFA-PC's split-class
   version *lacks* SALMA's schema-versioning, integrity checks, migration, and safe-backup logic —
   and **explicitly revised its own earlier plan-agy.md position** (which had defaulted to merging
   them) once shown this. **Final decision: discard `argus/MOUSTAFA-PC`'s entire
   `app/core/memory/*.py` — it contributes nothing SALMA doesn't already have, and adopting its
   split-class structure would regress operational robustness.** No further evaluation task needed
   for MOUSTAFA-PC at merge time.
   **Correction (2026-07-17)**: "sole canonical memory module" above was imprecise — it only ruled
   out MOUSTAFA-PC's separate module structure, not SALMA's `memory_service.py` versus the base
   branch's own file of the same name. Direct verification found `fix/copy-setup-to-scripts` already
   has its own `app/core/memory/memory_service.py` (492 lines), sharing a common ancestor with
   `argus/SALMA`'s version (380 lines) — their merge-base version is 336 lines. Both branches
   independently *extended* the same shared file: the base branch added
   `summarize_for_planning`/`get_blackboard_counts`/`get_findings_graph_rows`; SALMA added
   `purge_invalid_targets`/`_looks_like_garbage_domain`. Since they share real ancestry, T007's
   `git merge` should reconcile this file normally (a genuine 3-way merge, not a rename-detection
   miss like `BaseToolService.py`) — the result should contain **both** sets of additions, not one
   file replacing the other. Neither branch's version is "sole canonical"; the merged result is.
5. **`argus/DESKTOP-BVV10T0`'s machine-specific setup docs** — **RESOLVED (3-way discussion round)**:
   both agy and opencode read every file in `01_Infrastructure_Setup/` and `02_AI_Environment/`
   directly rather than guessing. Converged recommendation: **discard all batch/shell installer
   scripts** (`Step_1_Core_Foundation.bat`, `Step_2_AI_Python_Env.bat`, `run_kali_setup.bat`,
   `setup_python_kali.sh`, the `Google Drive` shortcut) as fully superseded by
   `ARGUS_INSTALLER.ps1`. **Extract into `Argus_Master_Documentation.md`** (complementary finds from
   each agent, combined): Win-KeX GUI-mode WSL access instructions, the WSL management command
   cheat-sheet (`wsl --shutdown`, `wsl -l -v`), the HuggingFace GGUF model-sourcing table by GPU
   size, and LM Studio (port 1234) as a documented alternative model provider to Ollama — verify the
   cited HuggingFace repo paths are still live and confirm the team actually wants LM Studio listed
   as a supported provider before finalizing that last item.
6. **Python 3.10 → 3.12 compatibility for `momen`'s ported code** — **RESOLVED (3-way discussion
   round)**: both agents independently converged that 3.10→3.12 porting risk is narrow, not broad.
   Combined checklist (superset of both): grep for `distutils`/`imp` (hard removals in 3.12, both
   agents flagged this); check `torch`/`faiss-cpu` resolve to wheel-compatible versions
   (`torch>=2.1.0`, `faiss-cpu>=1.8.0` — agy's addition, directly relevant since both packages are
   core Argus dependencies); grep for un-raw regex strings (`SyntaxWarning: invalid escape sequence`
   — agy's addition); grep for `.utcnow()`/`.utcfromtimestamp(` (deprecated, not hard-broken — agy's
   addition). Validate with `python -W error::DeprecationWarning -m compileall app/` then `pytest`
   (opencode's addition) after re-homing `momen`'s code under `app/`.

## Project Structure

### Documentation (this feature)

```text
specs/027-merge-branches/
├── spec.md                    # Feature specification
├── plan.md                    # This file — the canonical, panel-reconciled plan
├── research.md                # Phase 0 output — cross-verified 3x (Claude, agy, opencode)
├── research-opencode.md       # opencode's independent research pass (comparison artifact)
├── data-model.md              # Phase 1 output — canonical
├── data-model-agy.md          # agy's independent data model (comparison artifact)
├── data-model-opencode.md     # opencode's independent data model (comparison artifact)
├── quickstart.md              # Phase 1 output — canonical
├── quickstart-agy.md          # agy's independent quickstart (comparison artifact)
├── quickstart-opencode.md     # opencode's independent quickstart (comparison artifact)
├── plan-agy.md                # agy's independently-built plan (comparison artifact)
├── plan-opencode.md           # opencode's independently-built plan (comparison artifact)
├── tasks.md                   # Phase 2 output (/speckit-tasks) — canonical, includes the
│                              # 3-way panel discussion and methodology-research resolutions
└── checklists/requirements.md # Spec Quality Checklist (from /speckit-specify)
```

(No `contracts/` — this feature has no external API surface; it's an internal branch-unification
effort, not a service with callers.)

### Source Code (repository root — inside `Argus-Digilians/`)

```text
Argus-Digilians/
├── app/
│   ├── core/            # agent/, rag/, registry/, memory/ — base structure from
│   │                     # fix/copy-setup-to-scripts; memory/memory_service.py is a real 3-way
│   │                     # merge with argus/SALMA's version of the same file (shared ancestor,
│   │                     # see Synthesized Design Decision #4's correction), not one replacing
│   │                     # the other; argus/SALMA's ArgusBrainV2/agent_factory_v2/BaseToolService
│   │                     # reconciled in; momen's core/*.py re-homed here (flattened → modular,
│   │                     # not copied as-is)
│   ├── GUI/              # Streamlit multi-page app; momen's GUI/app.py content merged in if not
│   │                     # already superseded by fix/copy-setup-to-scripts's dashboard.py
│   ├── tools/            # tool registry + services; argus/MOUSTAFA-PC's memory-store files are
│   │                     # NOT ported here (Synthesized Design Decision #4: discarded in full,
│   │                     # confirmed redundant with argus/SALMA's memory_service.py)
│   └── modules/          # tactical/exploit modules; momen's
│                          # _experimental_advanced_modules/core/agent.py ported here as
│                          # experimental_agent/ (opt-in only, no tool registration — SDD #1)
├── Setup/                # requirements.txt (runtime deps)
├── scripts/
│   └── ARGUS_INSTALLER.ps1   # canonical installer (from fix/copy-setup-to-scripts), validated
│                              # on a clean environment as part of this feature (closes T013/T014)
├── requirements-dev.txt  # ruff/mypy/pytest — adopted from fix/copy-setup-to-scripts
├── pytest.ini             # adopted from fix/copy-setup-to-scripts
├── tests/                 # pytest suite; momen's test *content* (test_argus_comprehensive.py,
│                          # test_xss_scanner.py) ported in; its custom runner is not
└── .specify/, .opencode/  # toolchain dirs ported from argus-recovery/master (additive, no conflict)
```

**Structure Decision**: Single project (Option 1), rooted at `Argus-Digilians/` inside the `Main/`
workspace. No frontend/backend split — Streamlit GUI and CLI are both thin layers over the same
`app/core/` package. The target structure is `fix/copy-setup-to-scripts`'s existing modular layout;
other branches' content is reconciled *into* it, not used as an alternative base.

## Integration Steps (maps to research.md §5's recommended order; becomes /speckit-tasks input)

**Sequencing clarification (added 2026-07-17 — both agy and opencode independently flagged this as
the highest-severity finding in a full cross-document review)**: the numbering below is research.md
§5's *logical* dependency order (what absorbs what, least-redundant-first), not a mandatory strict
execution sequence. `tasks.md` deliberately reprioritizes by Spec-Kit's user-story convention (US1
= P1 = MVP first), which runs Steps 1/2/4/5/6 (Phase 3) before Step 3 (Phase 5). This is safe because
Step 3's work (`argus-recovery/master`'s `.specify`/`.opencode` toolchain port, `Argus_Secure_Sync.exe`
quarantine, installer validation) touches no files that Steps 4/5 (`momen`, `DESKTOP-BVV10T0`) also
touch, and neither direction blocks the other technically — only `spec.md`'s per-step
test-then-commit discipline matters, not the numbering. If a future dependency between these steps
is discovered during implementation, it must be called out explicitly rather than assumed away by
this note.

1. **Adopt `fix/copy-setup-to-scripts` as the working base.** No-op absorption of
   `fix/setup-script-update`, `argus/DESKTOP-JD0PB6T`, `argus/PHILOPATERSH` comes for free (already
   ancestors). *Test gate*: app starts (`run_argus_cli.py` reaches its normal startup point);
   `pytest` collects without import errors.
2. **Reconcile `argus/SALMA` into the base** via real `git merge` (connected history). Expected
   conflicts: `app/core/` (SALMA's `BaseToolService`/`ArgusBrainV2` vs. base's `agent/` package),
   `app/tools/`, `tests/`. Every conflict gets a one-line recorded decision (spec.md FR-003).
   *Test gate*: `pytest` passes at the same rate as before this step (no net regression); merged
   `tool_registry` exposes both branches' tools.
3. **`argus-recovery/master`'s toolchain contribution** (`.specify/`, `.opencode/`) — **correction
   2026-07-18 (T023): no port needed.** The working base (`fix/copy-setup-to-scripts`) already has its
   own, more evolved copy (constitution v1.3.0 vs. `argus-recovery/master`'s v1.0.0; zero files unique
   to the latter). Quarantine `Argus_Secure_Sync.exe` into `security_review_required/`
   (excluded from installer build), and **validate the canonical installer**
   (`ARGUS_INSTALLER.ps1`) in a **Windows Sandbox or disposable VM** (not the dev machine), closing
   its own tracker's open T013/T014. *Test gate*: sandboxed clean-environment install run completes
   and the embedded health check passes.
4. **Reconcile `momen`** — re-home `core/`→`app/core/`, `GUI/`→`app/GUI/`, running the Python
   3.10→3.12 compatibility checklist (Synthesized Design Decision #6) before porting: grep
   `distutils`/`imp`, verify `torch>=2.1.0`/`faiss-cpu>=1.8.0`, grep un-raw regex escapes, grep
   `.utcnow()`/`.utcfromtimestamp(`, then `compileall`+`pytest` to confirm. Port
   `_experimental_advanced_modules/core/agent.py`'s 13-step pipeline to
   `app/modules/experimental_agent/`, **opt-in only, never auto-registered in the Tool Registry**
   (Constitution Principle I). Port `momen`'s test content into pytest (not its custom runner).
   *Test gate*: same as step 2, plus momen's ported tests pass under pytest, plus a check that the
   experimental agent is NOT reachable through the normal agent/tool-registry entry points.
5. **Triage `argus/DESKTOP-BVV10T0`**: port the "local-first workflow / self-healing bridge /
   diagnostics tool" work if not already superseded by step 1–4's result; discard all batch/shell
   installer scripts and the empty `Discovery_cultbeauty_co_uk.txt` (Synthesized Design Decision #5);
   extract the identified doc content (Win-KeX, WSL cheat-sheet, GGUF model table, LM Studio
   alternative-provider note) into `Argus_Master_Documentation.md`. *Test gate*: any ported code
   passes its own tests or gets tests added before landing.
6. **Discard `argus/MOUSTAFA-PC`'s memory files and side-project noise** — no evaluation task
   remains here; Synthesized Design Decision #4 already settled it (`app/core/memory/*.py` discarded
   in full, `ai_agents_aroject/` discarded as noise). *Test gate*: none needed — nothing from this
   branch lands in the unified codebase.

Each step is independently testable and committed on its own before the next step starts — per
spec.md's requirement that every part be moved and tested separately before being joined to the rest
of the plan.

## Complexity Tracking

*No entries — the two CONDITIONAL Constitution Check gates (III, IV) are resolved by explicit design
steps above (Integration Steps 3 and 4), not by taking on unjustified complexity or waiving the gate.*
