# Data Model: Unify All Branches Into One Version

Derived from spec.md's Key Entities, grounded in research.md's concrete findings.

## Branch

Represents one of the 10 existing refs (`main` + 9 contributor branches/worktrees).

| Field | Type | Notes |
|---|---|---|
| `name` | string | e.g. `argus/SALMA`, `fix/copy-setup-to-scripts` |
| `worktree_path` | path | `branches/<flattened-name>/`, or `Argus-Digilians/` for `main` |
| `root_commit` | SHA | from `git rev-list --max-parents=0` |
| `shares_root_with_main` | bool | research.md §1 |
| `classification` | enum | `feature-work-to-merge` \| `superseded-duplicate` \| `feature-work-disconnected-history` \| `triage-discard` (corrected 2026-07-17: research.md §3's actual final classifications don't map cleanly onto the original 4 values — e.g. `argus/DESKTOP-BVV10T0` was reclassified from a snapshot guess to real iterative work with disconnected history, and `argus/MOUSTAFA-PC` resolved from "mixed" to a clean discard once its memory files were confirmed redundant. This enum reflects the actual 4 outcomes used in research.md §3/plan.md, not the earlier, less-informed guess.) |
| `absorbed_by` | Branch reference \| null | e.g. `argus/PHILOPATERSH.absorbed_by = fix/copy-setup-to-scripts` |
| `integration_step` | int \| null | which Integration Step (plan.md) processes this branch, if any |

**State transitions**: `unclassified → classified → (merged | ported | triaged-dropped)`. A branch
never skips `classified` — every branch must have a recorded classification with evidence (spec.md
FR-001) before any merge/port action is taken on it.

## Conflict Decision

One resolved file-level (or module-level) conflict encountered during integration.

| Field | Type | Notes |
|---|---|---|
| `file_or_module` | path | e.g. `app/core/tools/tool_registry.py` |
| `competing_branches` | Branch[] | which branches' versions competed |
| `winning_source` | Branch reference | which branch's version was kept (or "synthesized") |
| `rationale` | string (1 line) | required by spec.md FR-003 — no silent resolution allowed |
| `integration_step` | int | which Integration Step (plan.md) this decision belongs to |

**Validation rule**: every entry in git's conflict markers during a real `git merge` step MUST
produce exactly one `Conflict Decision` record before the merge commit is made. For manual
file-porting steps (disconnected-history branches), any file present in both the source branch and
the current target with materially different content also requires a record.

## Unified Branch

The single resulting branch/state after all Integration Steps complete.

| Field | Type | Notes |
|---|---|---|
| `base_commit` | SHA | `fix/copy-setup-to-scripts`'s tip at the start of integration |
| `applied_steps` | int[] | which of plan.md's 6 Integration Steps have landed |
| `installer_validated` | bool | true only after clean-environment validation (closes T013/T014) |
| `test_pass_rate` | float | pytest pass rate; must not regress step-over-step (spec.md SC-002) |
| `original_branches_preserved` | bool | must stay true throughout — spec.md FR-004 / SC-003 |

## Relationships

```text
Branch (1) --absorbed_by--> Branch (0..1)          # e.g. PHILOPATERSH absorbed_by fix/copy-setup-to-scripts
Branch (*) --produces--> Conflict Decision (*)      # a branch's integration can produce many decisions
Conflict Decision (*) --belongs to--> Unified Branch (1)
Branch (*) --contributes to--> Unified Branch (1)   # once classified feature-work and merged/ported
```
