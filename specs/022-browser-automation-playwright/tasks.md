# Tasks: Browser Automation via Playwright

**Feature**: `022-browser-automation-playwright`

**Status**: Proposed — no tasks started.

- [ ] T001 `app/tools/assets/playwright_probe.py` — JSON-in/JSON-out script, locator fallback
  chain in Playwright's documented priority order (role -> label -> text -> test-id -> CSS,
  corrected 2026-07-10), 30s nav timeout + 60s watchdog; verify whether `--no-sandbox` (NFR-001a)
  is actually required against this project's real Kali WSL setup and record the finding here
- [ ] T002 `BrowserAutomation` service (`render_page`, `interact`) —
  `app/tools/browser_tool.py`
- [ ] T003 Wire into `WSLBridgeTools.__init__` — `app/tools/tool_registry.py`
- [ ] T004 Add `Render_Page_JS` and `Browser_Interact` tools —
  `app/core/agent/brain_tools.py`
- [ ] T005 Kali provisioning step (Playwright + Chromium + asset copy) —
  `scripts/ARGUS_INSTALLER.ps1`
- [ ] T006 Mocked unit tests for `browser_tool.py` (no live Kali) —
  `tests/test_tools/test_browser_tool.py`
- [ ] T007 SC-001 fixture test: JS-injected content visible to this tool, invisible to
  `Crawl_Target`'s curl pipeline
- [ ] T008 SC-002 fixture test: fill+click 2-step flow via semantic locators
- [ ] T009 SC-003 fixture test: hung page load returns an honest timeout within budget
- [ ] T010 Live-Kali integration test, marked skip-by-default (matches repo convention for
  tests needing real WSL/SSH) — `tests/test_tools/test_browser_tool_live.py`
- [ ] T011 `CHANGELOG.md` entry + `specs/checklist.md` CHK series +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row, once implemented

## Explicitly out of scope (see spec.md)

- Screenshot capture/attachment
- In-tool LLM-driven locator resolution
- Multi-tab/persistent cross-call browser sessions
