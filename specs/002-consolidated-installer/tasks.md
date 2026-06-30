# Tasks for 002-consolidated-installer

## Task List

| Task ID | Description | Spec File | Status |
|---------|-------------|-----------|--------|
| T001 | Create `tasks.md` and `converge.md` files | specs/002-consolidated-installer/tasks.md | ✅ Done |
| T002 | Add Pester test suite for installer | tests/pester/install_tests.tests.ps1 | ✅ Done |
| T003 | Implement `-WhatIf` option in `ARGUS_INSTALLER.ps1` | scripts/ARGUS_INSTALLER.ps1 | ⏳ Pending |
| T004 | Add CI workflow (GitHub Actions) to run Pester tests | .github/workflows/installer.yml | ⏳ Pending |
| T005 | Update README with new usage examples | README.md | ⏳ Pending |
| T006 | Add execution guard and rewrite self-elevation Pester tests | tests/pester/install_tests.tests.ps1 | ✅ Done |

*All tasks should be committed individually according to the Speckit commit strategy.*
