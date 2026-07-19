# Feature Specification: Unify All Branches Into One Version

**Feature Branch**: `027-merge-branches`

**Created**: 2026-07-17

**Status**: Draft

**Input**: User description: "دمج كل الفروع في نسخة واحدة موحدة" (merge all branches into one unified version)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consolidate Divergent Contributor Work Into One Codebase (Priority: P1)

As a project maintainer, I need every contributor's branch (`momen`, `argus/PHILOPATERSH`,
`argus/SALMA`, `argus/MOUSTAFA-PC`, `argus/DESKTOP-BVV10T0`, `argus/DESKTOP-JD0PB6T`,
`argus-recovery/master`, `fix/copy-setup-to-scripts`, `fix/setup-script-update`) reviewed
and folded into a single unified branch, so the team works from one source of truth
instead of nine diverging copies of the project.

**Why this priority**: Without this, every other feature/spec built going forward risks
being based on a stale or contradicted copy of the codebase; this is the blocking
prerequisite for all future work.

**Independent Test**: Can be fully tested by checking out the resulting unified branch
and confirming the application (`run_argus_cli.py` / `scripts/LAUNCH_STUDIO.bat`) still
starts, and that no contributor's distinct capability (e.g., momen's RAG/orchestration
work, fix/copy-setup-to-scripts' investigation-depth fixes) is missing from the result.

**Acceptance Scenarios**:

1. **Given** the 9 contributor branches and `main`, **When** the unification is complete,
   **Then** there is exactly one branch (or `main` itself) that contains the union of
   all non-conflicting changes from every branch.
2. **Given** two branches changed the same file in incompatible ways, **When** the
   unification reaches that file, **Then** the conflict is resolved by a documented
   decision (which version won and why) rather than silently dropped.
3. **Given** the unified result, **When** a maintainer runs the existing test suite
   (`tests/`), **Then** it runs (pass/fail known) rather than failing to import/collect.

---

### User Story 2 - Preserve a Recoverable History of Each Contributor's Original Work (Priority: P2)

As a team member whose branch is being merged, I need my original branch and commits to
remain retrievable after unification, so my work isn't silently lost if the merge made
a wrong call.

**Why this priority**: Merging nine long-diverged branches is inherently lossy in
practice (conflicting installer scripts, conflicting `core/` implementations); losing
someone's work without a way to recover it would block that person's future
contributions and destroy trust in the process.

**Independent Test**: Can be tested by picking any original branch after unification and
confirming `git log`/`git show` still resolves its commits (branch or tag still exists,
nothing force-deleted).

**Acceptance Scenarios**:

1. **Given** unification is complete, **When** someone runs `git branch -a` /
   `git tag`, **Then** every original contributor branch is still present or has an
   equivalent recovery tag pointing at its last commit.
2. **Given** a contributor believes their change was dropped or overwritten, **When**
   they compare their original branch to the unified result, **Then** they can identify
   exactly what changed and why (via the conflict-resolution log from Story 1).

---

### User Story 3 - Single Installer and Documentation Set After Unification (Priority: P3)

As a new contributor or operator, I need exactly one installer flow and one set of
top-level docs (`README.md`, `Argus_Master_Documentation.md`, `GEMINI.md`) after
unification, so I don't have to guess which of the several competing installer scripts
(`INSTALL_EVERYTHING.ps1` vs `ARGUS_INSTALLER.ps1`, per `argus-recovery/master`) is
current.

**Why this priority**: Lower priority than getting the code itself unified, but
directly required by Constitution Principle IV (Installer & Documentation Stay in
Sync) — an unresolved installer split would violate the project's own constitution.

**Independent Test**: Can be tested by scanning the unified repo root/`scripts/`/`Setup/`
for installer entry points and confirming only one canonical install path remains,
with docs referencing that path.

**Acceptance Scenarios**:

1. **Given** the unified repo, **When** a maintainer looks for "the installer", **Then**
   there is one unambiguous entry point, not several competing scripts.
2. **Given** the unified repo, **When** a maintainer reads `README.md`'s Quick Start,
   **Then** the referenced files/paths actually exist in the unified tree.

### Edge Cases

- What happens when two branches independently rewrote the same core module (e.g.,
  `app/core/` / `GUI/`) with incompatible architectures (per-branch worktree evidence:
  `argus/PHILOPATERSH` did an arc42 Clean Architecture refactor; `momen` added
  orchestration + RAG)? → Must be resolved by an explicit, documented decision per
  Story 1's second acceptance scenario, not by mechanically taking "whichever merges
  cleanest."
- How does the process handle branches that look like personal snapshots rather than
  features (`argus/DESKTOP-BVV10T0`, `argus/DESKTOP-JD0PB6T`, `argus/MOUSTAFA-PC` —
  all titled "Intelligence Captured" / per-machine names)? → These MUST be triaged
  first to confirm whether they contain unique work worth merging or are disposable
  local snapshots, before attempting a code merge.
- What happens if a branch fails to merge cleanly at all (hard conflicts across most
  files)? → Documented as a rejected/deferred source with rationale, not force-merged.
- How is `Argus_Secure_Sync.exe` (a committed binary of unclear origin found in `main`)
  handled during unification? → Out of scope to execute/trust. **Updated 2026-07-17** (superseding
  this edge case's original "carry over as-is if depended on" framing, per plan.md Synthesized
  Design Decision #2 and tasks.md T024): quarantined unconditionally into
  `security_review_required/` with a recorded SHA-256 hash, excluded from the installer build,
  regardless of whether any branch depends on it — flagged for a separate security review, not
  executed or trusted either way.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The unification process MUST enumerate all 10 branches (`main` +
  9 contributor branches) and classify each as: "feature work to merge", "personal
  snapshot to triage", or "superseded/duplicate".
- **FR-002**: The process MUST produce a single resulting branch (or updated `main`)
  that contains the union of all classified "feature work to merge" changes.
- **FR-003**: Every file-level conflict encountered MUST be resolved with a recorded
  decision (winning version + one-line reason), not resolved silently or by
  arbitrary tool default.
- **FR-004**: The process MUST NOT delete or force-overwrite any original contributor
  branch; each original branch (or a tag pointing at its tip) MUST remain resolvable
  after unification (see User Story 2).
- **FR-005**: After unification, exactly one installer entry point and one set of
  top-level docs MUST remain canonical, per Constitution Principle IV.
- **FR-006**: The unification MUST respect Constitution Principle I (Authorized Use
  Only) — no merged change may introduce functionality for unauthorized-target
  scanning or defensive-control evasion.
- **FR-007**: After unification, the existing test suite under `tests/` MUST be
  runnable (collectable), even if some tests are already known-failing.

### Key Entities

- **Branch**: One of the 10 existing branches/worktrees; attributes: owner/machine
  name, last commit date, classification (merge / triage / superseded).
- **Conflict Decision**: A record of one resolved file-level conflict — file path,
  competing branches, winning source, one-line rationale.
- **Unified Branch**: The single resulting branch containing the merged codebase.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: All 10 branches are classified (merge/triage/superseded) with a
  one-line rationale each, before any merge commit is made.
- **SC-002**: The unified branch builds/starts successfully (CLI or Studio launch
  reaches its normal startup point) on the first attempt after unification.
- **SC-003**: Zero original branches are deleted or force-overwritten; 100% remain
  retrievable via `git branch -a`/tags after unification.
- **SC-004**: The unified repo has exactly one documented installer entry point
  (down from the 2+ competing ones observed today: `INSTALL_EVERYTHING.ps1` vs
  `ARGUS_INSTALLER.ps1`).
- **SC-005**: Every file-level conflict resolved during unification has a corresponding
  one-line written rationale (100% coverage, not just the contentious ones).

## Assumptions

- The unified result becomes (or replaces) `main`; `master`-style branches
  (`argus-recovery/master`) are treated as candidate sources, not as an alternate
  default branch.
- Per-machine `argus/<HOSTNAME>` branches are assumed to be autonomous-run "captured
  intelligence" output snapshots rather than source-code feature branches unless
  inspection shows otherwise during FR-001 triage; this assumption MUST be confirmed
  (or corrected) during triage before merging.
- Conflict resolution decisions are made by a human maintainer (or an AI agent acting
  on the maintainer's explicit direction) reviewing this spec — this feature does not
  assume a fully automatic, unattended merge.
- The existing `git worktree` checkouts under `branches/` (already created for each
  branch) are the working copies used to review/compare each branch during
  unification; they are not deleted by this feature.
- Binary/generated artifacts (e.g., `Argus_Secure_Sync.exe`, `__pycache__`,
  `node_modules`, `.venv`) are not meaningfully "mergeable" and are carried over
  as-is from whichever source is chosen, not diffed line-by-line.
