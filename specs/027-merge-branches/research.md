# Phase 0 Research: Unify All Branches Into One Version

**Feature**: [spec.md](./spec.md) | **Date**: 2026-07-17

## Methodology

This is a **synthesized, cross-verified** research pass, combining three independent analyses of
the same 10 refs (`main` + 9 branch worktrees under `branches/`), reconciled against direct,
re-verified git evidence:

1. **Claude (this analysis)** — direct `git log`/`git diff --stat`/`git ls-tree`/`git merge-base`
   inspection, done in two passes (initial + deep-dive).
2. **agy (Google Antigravity CLI, `agy-delegate`)** — dispatched on the identical task; ran out of
   account quota before writing its own file, but its in-progress narration was captured and
   cross-checked below. Every claim it surfaced before stopping was independently re-verified and
   confirmed correct.
3. **opencode (`opencode-delegate`, model `deepseek-v4-flash-free`)** — dispatched independently
   (without seeing this file) and produced a complete `research-opencode.md`. Most findings matched;
   **one factual claim was wrong** and is corrected below (see §7).

Every claim in this file was verified directly against the repository — nothing here is taken on
any single source's word alone.

---

## 1. Root Ancestry — the finding that reshapes the whole plan

`git rev-list --max-parents=0 <branch>` on all 10 refs (confirmed independently by Claude, agy, and
opencode — full three-way agreement) shows **only 6 of 10 share a common root commit** (`b51c42e`,
"Initial commit: Organized Argus Security Framework..."). The other 4 are **disconnected
histories** — a different initial commit entirely, not just a divergence point:

| Branch | Root commit | Shares root w/ `main`? | Merge-base w/ `main`? | Normal `git merge` possible? |
|---|---|---|---|---|
| `main` | `b51c42e` | — | — | — |
| `argus/PHILOPATERSH` | `b51c42e` | ✅ | YES (`3019300`, tip = ancestor of main) | YES (no-op, already in main) |
| `argus/SALMA` | `b51c42e` | ✅ | YES (`5203b75`) | YES |
| `argus/DESKTOP-JD0PB6T` | `b51c42e` | ✅ | YES (its tip IS `b51c42e`) | YES (no-op) |
| `fix/copy-setup-to-scripts` | `b51c42e` | ✅ | YES (`5203b75`) | YES |
| `fix/setup-script-update` | `b51c42e` | ✅ | YES (`3019300`) | YES |
| `momen` | `3dc4ed5` | ❌ | none | NO — needs `--allow-unrelated-histories` or manual porting |
| `argus/MOUSTAFA-PC` | `8e16cd4` | ❌ | none | NO (single-commit branch) |
| `argus/DESKTOP-BVV10T0` | `c098e6e` | ❌ | none | NO |
| `argus-recovery/master` | `bdabc99` | ❌ | none | NO |

**Implication**: the 4 disconnected branches cannot be `git merge`d meaningfully — every file would
read as new/conflicting by construction. They require **content reconciliation / selective
cherry-pick or file-copy**, not a merge command.

## 2. Ancestor Relationships Among the 6 Connected Branches

`git merge-base --is-ancestor` (re-verified directly, twice, after a conflicting claim — see §7):

- **`fix/copy-setup-to-scripts` already fully contains**, as direct ancestors:
  - `fix/setup-script-update` (merge commit `8495f4d`: *"Merge branch 'fix/setup-script-update'
    into fix/copy-setup-to-scripts"*)
  - `argus/DESKTOP-JD0PB6T` (its tip is the shared root commit — trivially an ancestor)
  - `argus/PHILOPATERSH` (its tip `3019300` is an ancestor of `fix/copy-setup-to-scripts`)
- **`argus/SALMA` is NOT an ancestor of `fix/copy-setup-to-scripts`, nor the reverse.** It is a
  genuinely independent line from the shared root (merge-base `16a2824`, well before either tip).
  **This was double-checked after `opencode` incorrectly claimed the two were merged — see §7.**
- **`main` is NOT an ancestor of `fix/copy-setup-to-scripts`** — merge-base is `5203b75`, which is
  behind main's current tip `b563f73`: main kept moving after `fix/copy-setup-to-scripts` branched.

**Decision**: treat `fix/copy-setup-to-scripts` as the integration base for the connected-branch
group — it already absorbs 3 of the other 5 for free. The real reconciliation work for this group
is a genuine **3-way**: `fix/copy-setup-to-scripts` vs `argus/SALMA` vs `main`.
**Rationale**: re-merging the 3 already-absorbed branches individually would redo settled work.
**Alternatives considered**: starting from `main` and merging all 5 individually — rejected, it
would re-litigate conflicts `fix/copy-setup-to-scripts` already resolved.

## 3. Branch Classification (spec.md FR-001)

| Branch | Diffstat vs main | Classification | Evidence |
|---|---|---|---|
| `fix/copy-setup-to-scripts` | 421 files, +39,173/−1,876 (172 commits) | **Feature work to merge (primary base)** | Has `pytest.ini` (testpaths, unit/integration/e2e/eval/regression markers), `ruff.toml`, `mypy.ini`, `.github/` CI + Pester tests, `AGENTS.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, and 26 completed Spec-Kit features (`specs/001`–`026`: RAG pipeline, tool registry, tactical modules, reflective verification, self-healing, GUI, LangGraph agent/workflow, multi-agent role separation, CVE PoC intelligence, ethical-safeguards-RAII). `app/core/` is a mature modular package (`agent/`, `rag/`, `registry/`, `memory/` subpackages) vs. main's flatter layout. Already absorbs `fix/setup-script-update`, `argus/DESKTOP-JD0PB6T`, `argus/PHILOPATERSH`. |
| `argus/SALMA` | 187 files, +17,986/−719 (54 commits) | **Feature work to merge** | Independent line from the shared root (not an ancestor/descendant of `fix/copy-setup-to-scripts`, merge-base `16a2824`). Own work: centralized `ArgusConfig` loader, `BaseToolService` tool-registry ABC, `ArgusBrainV2`/`agent_factory_v2`, blackboard/SQLite, self-healing, reflective verification, new `tests/test_registry/`, `tests/test_tools/`. |
| `argus/PHILOPATERSH` | 2 files, +33/−130 | **Superseded / duplicate** | Diff vs `main` is only `README.md` wording + 1 line in `ARGUS_TECHNICAL_ARCHITECTURE.md`. Its tip is already an ancestor of `fix/copy-setup-to-scripts` — nothing left to merge separately. |
| `fix/setup-script-update` | 165 files, +16,758/−211 (43 commits) | **Superseded / duplicate** | Already an ancestor of `fix/copy-setup-to-scripts` via merge commit `8495f4d`. |
| `argus/DESKTOP-JD0PB6T` | 81 files, +1,151/−3,875 | **Superseded / duplicate** | Single commit, tip *is* the shared root `b51c42e` — trivially already an ancestor of `fix/copy-setup-to-scripts` and main. Zero unique content. |
| `momen` | 126 files, +18,547/−5,784 (2 commits) | **Feature work to merge, disconnected history** | Own root `3dc4ed5`. Flat, single-file-per-concern `core/` (`agent.py`, `agent_ai_driven.py`, `memory.py`, `prompts.py`, `rag_kb.py`, `safety.py`, `schemas.py`, `tools.py` — corrected 2026-07-17, an earlier pass of this file omitted `agent_ai_driven.py` and `prompts.py`) and `GUI/` at repo root — **not** the `app/core/`/`app/GUI/` layout mandated by Constitution Principle III. Also has `_experimental_advanced_modules/core/agent.py` (a hardcoded 13-step sequential recon→exploit pipeline) and a custom, non-pytest test runner (`tests/run_all_tests.py`). Real new work (`tests/test_argus_comprehensive.py`, `tests/test_xss_scanner.py`), but structurally much shallower than `fix/copy-setup-to-scripts`'s modular `app/core/agent/` package (which already has its own recon/scanner/exploit/reflective LangGraph nodes) — likely superseded in capability, not just structure. Needs file-by-file triage, not a layout-preserving port. |
| `argus-recovery/master` | 118 files, +10,362/−2,554 (3 commits) | **Feature work to merge, disconnected history** | Own root `bdabc99`. Contains its own `.specify/` and `.opencode/` toolchain directories (templates, workflows, constitution, integrations) that plain `main` lacks entirely — this predates and is independent of the `.specify/`/`.claude/skills/` setup done separately at the `Main/` workspace level for this merge effort. Also replaced `INSTALL_EVERYTHING.ps1` with `scripts/ARGUS_INSTALLER.ps1` (see §4 for the installer resolution — this file is a **less complete** implementation of the same design `fix/copy-setup-to-scripts` also built). |
| `argus/MOUSTAFA-PC` | 107 files, +3,282/−1,408 (1 commit) | **Triage — mixed** | Single-commit branch, message "[Argus-MOUSTAFA-PC] Intelligence Captured". Bulk of the diff is an unrelated side-project dumped into the repo (`ai_agents_aroject/` — note the typo — with its own `AI_Agent.md`, `ai_memory.json`, `multi_agent_workflow.py`, session report `.md` dumps): **disposable noise, not Argus feature work.** However it *also* adds `app/core/memory/{database,finding_store,graph_store,summary_service,target_store}.py` — a structured memory-store attempt that needs a real look against `argus/SALMA`'s blackboard/SQLite work before being discarded (could be redundant, could have a useful schema idea). |
| `argus/DESKTOP-BVV10T0` | 97 files, +1,476/−4,508 (20 commits) | **Reclassified: real iterative work, disconnected history** (not a pure snapshot — see §7) | Own root `c098e6e`. Despite several auto-generated "[Argus] Intelligence Update" / "[Argus-DESKTOP-BVV10T0] Intelligence Captured" commits, it also has substantive, human-authored commits: *"feat: implement professional AI Agent Studio with modular core and master launcher"*, *"feat: unify workspace with local-first workflow, self-healing bridge, and diagnostics tool"*, *"Disable Nikto scan to improve reconnaissance speed"*, plus a revert commit (real iteration, not just snapshotting). Also carries a 0-byte leftover file `Discovery_cultbeauty_co_uk.txt` (empty — not actual scan data; low-priority cleanup, not a compliance incident — see §7). Needs the same file-by-file triage as `momen`, not a blanket "disposable snapshot" write-off. |

## 4. Conflict Map

- **Installer: `scripts/INSTALL_EVERYTHING.ps1` (main only — corrected 2026-07-17: `git ls-tree -r
  fix/copy-setup-to-scripts -- scripts` shows only `ARGUS_INSTALLER.ps1`, no
  `INSTALL_EVERYTHING.ps1`; an earlier pass of this file wrongly stated both had it) vs
  `scripts/ARGUS_INSTALLER.ps1` (argus-recovery/master, *also present on* `fix/copy-setup-to-scripts`
  with the same design).** Both `fix/copy-setup-to-scripts` and `argus-recovery/master` have their
  own `specs/002-consolidated-installer/` (spec.md is **byte-identical** between the two branches;
  `plan.md`/`tasks.md` differ only in one extra governance line and checkbox-completion state).
  **Resolved by direct comparison, not left as a coin-flip**: `fix/copy-setup-to-scripts`'s
  `ARGUS_INSTALLER.ps1` is 1,613 lines vs. `argus-recovery/master`'s 1,378 lines (694 diff lines
  apart — all three numbers re-confirmed via `git show <branch>:path | wc -l` / `diff`, see §7).
  `fix/copy-setup-to-scripts`'s `tasks.md` has **16 of 21 tasks marked `[x]`** (not "every task," as
  an earlier pass of this file overstated — corrected after an audit pass, see §7); the 5 still open
  are: `T013`/`T014` (clean-environment install + idempotency re-run — **not yet validated**),
  `T018`/`T019` (marked superseded/moot — dual-clone layout no longer applies), and `T020` (final
  commit/push). `argus-recovery/master`'s `tasks.md` has all its tasks unchecked. Same plan either
  way, `fix/copy-setup-to-scripts`'s execution is substantially further along, but its own tracker
  admits it has **not been validated on a clean environment yet** — that gap should be closed before
  or during unification, not assumed away.
  **Decision: `fix/copy-setup-to-scripts`'s `ARGUS_INSTALLER.ps1` should be the canonical installer**,
  satisfying spec.md SC-004 (exactly one installer entry point) — not `main`'s
  `INSTALL_EVERYTHING.ps1` and not `argus-recovery/master`'s earlier draft.
- **Project layout**: `momen` uses `core/`, `GUI/` at the repository root; `fix/copy-setup-to-scripts`
  (and `main`) use `app/core/`, `app/GUI/`. Sharpest structural conflict in the whole set, and directly
  implicates Constitution Principle III — `momen`'s content needs re-homing under `app/`, not a
  literal merge.
- **Requirements files**: `fix/copy-setup-to-scripts` adds `requirements-dev.txt` (ruff, mypy, pytest)
  on top of `Setup/requirements.txt` — additive, not conflicting.
- **Test tooling split**: only `fix/copy-setup-to-scripts` has a real, enforced framework
  (`pytest.ini` with `unit`/`integration`/`e2e`/`eval`/`regression` markers, plus Pester tests for the
  PowerShell installer). `main`'s own `tests/` (`exploit_test.py`, `verify_core.py`) has no
  pytest/unittest markers — ad hoc scripts, not a real suite. `momen` has its own non-pytest custom
  runner (`tests/run_all_tests.py`) that should not replace the pytest suite. This matters for
  spec.md's FR-007: today, "runnable/collectable tests" is only true on `fix/copy-setup-to-scripts`.

## 5. Recommended Integration Order

**Decision** — integrate in this order:

1. **`fix/copy-setup-to-scripts`** as the base (already absorbs `fix/setup-script-update`,
   `argus/DESKTOP-JD0PB6T`, `argus/PHILOPATERSH` for free).
2. **`argus/SALMA`** reconciled against that base — a real 3-way diff/merge is possible since
   history is connected; expect conflicts in `app/core/`, `app/tools/`, `tests/`.
3. **`argus-recovery/master`**'s non-installer contribution (`.specify/`/`.opencode/` toolchain
   directories) ported in — its installer work is superseded per §4, but the toolchain directories
   are additive and don't exist on `fix/copy-setup-to-scripts` at all.
4. **`momen`** reconciled — highest-effort, most manual step (disconnected history + different
   layout); doing it after 1–3 means the target `app/` layout is already stable to port into. The
   13-step experimental pipeline needs an explicit human call: port into `app/modules/`, or drop as
   superseded by the LangGraph-based agent already on the base branch.
5. **`argus/DESKTOP-BVV10T0`** triaged file-by-file (not blanket-discarded, per its reclassification
   in §3) — likely candidates: the "local-first workflow, self-healing bridge, diagnostics tool" work;
   likely discards: machine-specific setup docs, the empty scan-artifact file.
6. **`argus/MOUSTAFA-PC`** triaged — discard `ai_agents_aroject/` side-project noise; specifically
   evaluate `app/core/memory/*.py` against `argus/SALMA`'s blackboard/SQLite work before deciding.

**Rationale**: does the free, already-settled absorption first (step 1), tackles connected-history
reconciliation before disconnected-history reconciliation (lower-risk before higher-risk), and
processes the two disconnected non-toolchain branches last, once there's a stable target to diff
each of their files against.

**Alternatives considered**: merging in branch-creation-date order — rejected, since git already
proves several of these branches are fully contained in `fix/copy-setup-to-scripts` and processing
them separately would be redundant.

## 6. Technical Context Inputs (for plan.md)

- **Language/Version**: Python 3.12 (`Argus_venv`) on `main`/`fix/copy-setup-to-scripts`; `momen`'s
  compiled `.pyc` artifacts show `cpython-310`, suggesting that branch was developed against 3.10 —
  a version-consistency item to resolve during its reconciliation.
- **Primary Dependencies**: LangChain (+`langchain-ollama`, `langchain-classic`,
  `langchain-huggingface`, `langchain-community`, `langchain-core`), `langgraph` (on
  `fix/copy-setup-to-scripts`), Streamlit, FAISS-CPU, `sentence-transformers`, `paramiko` (SSH
  bridge), `duckduckgo-search`, `torchvision`, `networkx`/`pyvis` (knowledge-graph viz, on
  `fix/copy-setup-to-scripts`).
- **Development Dependencies**: `ruff`, `mypy`, `pytest`, `pytest-cov` (`requirements-dev.txt`,
  `fix/copy-setup-to-scripts` only).
- **Testing**: pytest (`pytest.ini`, markers `unit`/`integration`/`e2e`/`eval`/`regression`) +
  Pester (PowerShell installer tests) on `fix/copy-setup-to-scripts` only — **decision: adopt this
  as the unified test setup**, since it's the only branch where spec.md's FR-007 is already true.
- **CI**: GitHub Actions workflow present on `fix/copy-setup-to-scripts` (`.github/`), including a
  Pester test job for the installer — not present on `main`.
- **Target Platform**: Windows 10/11 host + WSL2 (Kali Linux distro) guest via SSH bridge
  (`paramiko`), confirmed across all branches' docs and `.env.example` (`WSL_DISTRO`, `WSL_HOST`,
  `WSL_PORT`).
- **Constraints**: `Argus_venv` isolation must be preserved; the WSL/Kali dependency is
  unconditional in every branch inspected.

## 7. Cross-Verification Notes (what the three analyses disagreed on, and how it was resolved)

- **opencode claimed** `fix/copy-setup-to-scripts` "is built on top of argus/SALMA work via merge
  commit 8495f4d." **This is incorrect** — directly re-verified: commit `8495f4d` is *"Merge branch
  'fix/setup-script-update' into fix/copy-setup-to-scripts"* (a different branch, similar name), and
  `git merge-base --is-ancestor argus/SALMA fix/copy-setup-to-scripts` returns `NO`, confirmed twice.
  The likely source of the confusion: an much earlier, unrelated commit on the *shared trunk itself*
  (`6e06b9a`, "integrate SALMA tools, smart search, and optimize environment" — present on `main`
  and every connected branch, from before any of them diverged) mentions "SALMA" in its message.
  This is a good illustration of why the delegate-skills' own guidance says to re-verify a
  delegate's self-report rather than accept it — a free/lightweight model conflated a commit-message
  keyword match with an actual branch-merge relationship.
- **opencode flagged** `Discovery_cultbeauty_co_uk.txt` (on `argus/DESKTOP-BVV10T0`) as a possible
  Constitution Principle I (Authorized Use Only) concern — a committed scan artifact against a named
  third-party domain. **Checked directly: the file is 0 bytes.** No actual scan data was committed;
  it's an empty leftover artifact. Downgraded from "compliance concern" to "delete during cleanup,"
  but worth keeping in mind as a reminder to grep other branches for non-empty scan-output files
  before finalizing the unified branch.
- **opencode classified `argus/DESKTOP-BVV10T0` as "personal snapshot to triage"** (same bucket as
  `argus/MOUSTAFA-PC`). Direct inspection of its full (non-"Intelligence Captured") commit log shows
  real, iterative, human-described feature work ("self-healing bridge," "diagnostics tool," "Docker-
  based workflow" transition, a revert). **Reclassified above** to its own category — real work with
  disconnected history — rather than lumped in with `MOUSTAFA-PC`'s mostly-disposable content.
- **agy's partial run** (before hitting its account quota) independently reached the same root-
  ancestry conclusion (§1) via its own sequential `git` commands, and separately confirmed
  `argus/PHILOPATERSH` is "very close to main" and that `fix/copy-setup-to-scripts` "merged
  `fix/setup-script-update` into itself" — both fully consistent with the direct verification here.
- **A dedicated agy audit pass** (once its quota reset) fact-checked this file's claims end-to-end
  and reported 87 claims checked. Its findings were themselves re-verified — mixed result:
  - **Correct catch**: this file originally claimed "every task in `tasks.md` marked `[x]`" for
    `fix/copy-setup-to-scripts`'s installer spec. Actual count: **16 of 21** (`grep -c '\[x\]'` /
    `'\[ \]'` on the real file) — 5 remain open, including the clean-environment validation tasks.
    **Corrected in §4 above.**
  - **Incorrect claims from the same audit**: it reported the installer line counts as 1,411 /
    1,202 / 592-diff-lines, disagreeing with this file's original 1,613 / 1,378 / 694. Re-running
    `git show <branch>:scripts/ARGUS_INSTALLER.ps1 | wc -l` and `diff` directly a third time
    confirmed the **original 1,613 / 1,378 / 694 numbers were correct all along** — the audit run's
    own numbers were wrong (likely a Windows `Get-Content`/line-ending artifact in how it counted,
    since it used PowerShell's `Measure-Object -Line` on the worktree file rather than `git show`).
  - **Net effect**: the audit was net-useful (it surfaced one real error) but was not itself
    error-free — reinforcing that even a dedicated fact-check pass needs its own conclusions spot-
    checked, not accepted wholesale.

## Open Questions — Status After the 2026-07-17 3-Way Discussion Round (Claude + agy + opencode)

1. **`momen`'s `_experimental_advanced_modules/core/agent.py`** — **RESOLVED**: port to
   `app/modules/experimental_agent/`, opt-in only, never auto-registered in the Tool Registry. See
   plan.md Synthesized Design Decision #1 (both agy and opencode independently converged on this).
2. **`argus/MOUSTAFA-PC`'s `app/core/memory/*.py` files** — **RESOLVED**: discard entirely.
   opencode's direct side-by-side read found the SQLite schema is structurally identical to
   `argus/SALMA`'s (same 5 tables); agy independently re-verified this and additionally found
   MOUSTAFA-PC's version lacks SALMA's migration/integrity/versioning logic, and **explicitly
   revised its own earlier plan-agy.md position** (which had proposed merging them) after seeing the
   evidence. See plan.md Synthesized Design Decision #4.
3. **Binary policy for `Argus_Secure_Sync.exe`**: still out of scope to execute/trust — quarantined
   into `security_review_required/` during Integration Step 3 (plan.md), excluded from installer
   build. Still flagged for a separate security review before any decision to use it.
4. **`argus/DESKTOP-BVV10T0`'s machine-specific setup docs** — **RESOLVED**: both agy and opencode
   read every file directly. Discard all batch/shell scripts (superseded by `ARGUS_INSTALLER.ps1`);
   extract Win-KeX GUI access instructions, the WSL management command cheat-sheet, the HuggingFace
   GGUF model-sourcing table, and LM Studio (port 1234) as an alternative model provider into
   `Argus_Master_Documentation.md` — pending verification the cited HF repo paths are still live and
   the team wants LM Studio documented as a supported provider. See plan.md Synthesized Design
   Decision #5.
