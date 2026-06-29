# Tasks: Consolidated Single-File Installer

**Input**: Spec at `specs/002-consolidated-installer/spec.md`

**Note**: Tasks marked [P] can run in parallel. Tasks without [P] must be sequential.

---

## Phase 1: Analysis & Preparation

**Purpose**: Understand current installer structure and plan the embedding.

- [x] T001 Read and analyze all current files: `INSTALL_EVERYTHING.ps1`, `Step_*.bat`, `check_and_install.sh`, `requirements.txt`, `setup_python_kali.sh`, `argus_recon_fixed.sh`
- [x] T002 Identify all file dependencies that must be embedded: `requirements.txt` (15 lines), `check_and_install.sh` (382 lines), `argus_recon_fixed.sh` (49 lines)
- [x] T003 Identify step functions that reference external files: `Invoke-StepAiEnvironment` (references `$SetupRoot\requirements.txt`), `Invoke-StepKaliTools` (references `$SetupRoot\check_and_install.sh`)

---

## Phase 2: Build ARGUS_INSTALLER.ps1

**Purpose**: Create the single self-contained installer script.

- [x] T004 Create `scripts/ARGUS_INSTALLER.ps1` — copy all code from `scripts/INSTALL_EVERYTHING.ps1` as the base
- [x] T005 Add embedded here-strings at the top of the script for `requirements.txt`, `check_and_install.sh`, and `argus_recon_fixed.sh` content
- [x] T006 Add helper function `Write-EmbeddedFile` that takes here-string content and writes it to a temp path (Windows or WSL)
- [x] T007 Modify `Invoke-StepAiEnvironment` — instead of reading `$SetupRoot/requirements.txt`, use the embedded here-string. Write it to a temp file inside the venv or to `/tmp/argus_requirements.txt` for WSL-side usage
- [x] T008 Modify `Invoke-StepKaliTools` — instead of referencing `$SetupRoot/check_and_install.sh`, write the embedded here-string to `/tmp/argus_check_and_install.sh` inside WSL and execute from there
- [x] T009 Add post-install cleanup step (Step 7): rename `Setup/` to `Setup_legacy/` after successful first run
- [x] T010 Add guard: if `Setup_legacy/` already exists, skip the rename step
- [x] T010b Update `-DryRun` logic to cover cleanup step

---

## Phase 3: Verification & Testing

**Purpose**: Ensure the new installer works correctly before syncing.

- [x] T011 Run `ARGUS_INSTALLER.ps1 -DryRun` and verify all steps report correctly without making changes
- [x] T012 Compare original `INSTALL_EVERYTHING.ps1` behavior vs `ARGUS_INSTALLER.ps1` — same step order, same output format, same exit codes
- [ ] T013 Test on a clean environment (or test VM): run `ARGUS_INSTALLER.ps1` and verify full installation + health check
- [ ] T014 Re-run `ARGUS_INSTALLER.ps1` and verify idempotency (all steps skip, health check passes)

> **Note**: T013-T014 require a clean Windows VM and have not been executed in this environment. They are deferred to manual end-to-end validation.

---

## Phase 4: Cleanup & Documentation

**Purpose**: Archive old files and update documentation.

- [x] T015 Add comment header in `ARGUS_INSTALLER.ps1` documenting its self-contained nature and how to run it
- [x] T016 Update `Setup/README.md` to point users to `scripts/ARGUS_INSTALLER.ps1` as the primary installer (Setup/ now archived as `Setup_legacy/`)
- [x] T017 Update `scripts/README.md` to reference `ARGUS_INSTALLER.ps1` instead of `INSTALL_EVERYTHING.ps1`

---

## Phase 5: Sync & Deploy

**Purpose**: Ensure identical deployment across both branches and push to GitHub.

- [x] T018 Copy `scripts/ARGUS_INSTALLER.ps1` from `Argus` to `remote_Argus_PhilopaterSh`
- [x] T019 Verify identical hashes for `ARGUS_INSTALLER.ps1` across both directories
- [x] T020 Commit and push `fix/copy-setup-to-scripts` branch to GitHub

---

## Phase 6: Approved Additions (Plan.md §5)

**Purpose**: Close gaps identified during the post-review of the initial plan.

- [x] T021 Wire `ARGUS_INSTALLER.ps1` as the primary installer in `INSTALL.bat` (was pointing to the removed `INSTALL_EVERYTHING.ps1`)
- [x] T022 Archive/remove the broken `INSTALL_EVERYTHING.ps1` (it referenced the deleted `Setup/` directory)
- [x] T023 Remove `scripts/CHECK_HEALTH.bat` (logic now embedded) and clean up all stale `.bat`/`.md` references
- [x] T024 Add `-OnlyHealthCheck` switch + `INSTALL.bat health` token (Plan §5.3)
- [x] T025 Add `wsl --update` after enabling WSL features (Plan §5.4)
- [x] T026 Add model response verification after model pull (Plan §5.4)

---

## Phase 0: Commit Strategy (Cross-Cutting)

**Purpose**: Ensure every Spec-Kit phase produces a clean git commit.

- [x] T000 Follow commit-per-phase strategy: commit after `/speckit.specify`, `/speckit.plan`, `/speckit.tasks`, each task in `/speckit.implement`, `/speckit.analyze`, and `/speckit.converge`. See `Plan.md` §4 for the full table.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1**: No dependencies — can start immediately
- **Phase 2**: Depends on Phase 1 completion
- **Phase 3**: Depends on Phase 2 completion
- **Phase 4**: Depends on Phase 3 completion
- **Phase 5**: Depends on Phase 4 completion
- **Phase 6**: Post-implementation additions (independent)

### Parallel Opportunities

- T006, T007, T008 all modify the same file (`ARGUS_INSTALLER.ps1`) — must be sequential
- T016 and T017 (README updates) can run in parallel [P]
- T018 (copy files) is blocked until all other phases complete

### Execution Order

1. T001 → T002 → T003 (Phase 1: analysis)
2. T004 → T005 → T006 → T007 → T008 → T009 → T010 → T010b (Phase 2: build)
3. T011 → T012 → T013 → T014 (Phase 3: test)
4. T015 → T016 [P] + T017 [P] (Phase 4: docs)
5. T018 → T019 → T020 (Phase 5: deploy)
6. T021 → T026 (Phase 6: approved additions)
