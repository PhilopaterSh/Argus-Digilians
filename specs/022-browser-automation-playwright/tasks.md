# Tasks: Browser Automation via Playwright

**Feature**: `022-browser-automation-playwright`

**Status**: Proposed — no tasks started. Scope extended 2026-07-13b (FR-006/007/008: network
capture, console/error capture, session-state extraction) - see `research.md`'s addendum.

- [ ] T001 `app/tools/assets/playwright_probe.py` — JSON-in/JSON-out script, locator fallback
  chain in Playwright's documented priority order (role -> label -> text -> test-id -> CSS,
  corrected 2026-07-10), 30s nav timeout + 60s watchdog; verify whether `--no-sandbox` (NFR-001a)
  is actually required against this project's real Kali WSL setup and record the finding here.
  Also registers `page.on("console")`/`page.on("pageerror")` before every `page.goto()` (FR-007,
  always-on) and conditionally captures network requests (FR-006) / session state (FR-008) per
  the JSON-in flags.
- [ ] T002 `BrowserAutomation` service (`render_page`, `interact`, `extract_session_state`) —
  `app/tools/browser_tool.py` (FR-008's cookie `Secure`/`HttpOnly` flagging + `add_finding()`
  call lives here, not in the Kali-side script, matching every other tool's split of "Kali
  script does the raw capture, Windows service does the judgment call")
- [ ] T003 Wire into `WSLBridgeTools.__init__` — `app/tools/tool_registry.py`
- [ ] T004 Add `Render_Page_JS`, `Browser_Interact`, and `Extract_Session_State` tools —
  `app/core/agent/brain_tools.py`
- [ ] T005 Kali provisioning step (Playwright + Chromium + asset copy) —
  `scripts/ARGUS_INSTALLER.ps1`
- [ ] T006 Mocked unit tests for `browser_tool.py` (no live Kali) —
  `tests/test_tools/test_browser_tool.py`
- [ ] T007 SC-001 fixture test: JS-injected content visible to this tool, invisible to
  `Crawl_Target`'s curl pipeline
- [ ] T008 SC-002 fixture test: fill+click 2-step flow via semantic locators
- [ ] T009 SC-003 fixture test: hung page load returns an honest timeout within budget
- [ ] T009a SC-004 fixture test: a `console.log('<marker>')` payload delivered via
  `Browser_Interact` appears verbatim in the returned `console_logs`
- [ ] T009b SC-005 fixture test: a cookie set without `Secure`/`HttpOnly` is flagged by
  `Extract_Session_State`
- [ ] T010 Live-Kali integration test, marked skip-by-default (matches repo convention for
  tests needing real WSL/SSH) — `tests/test_tools/test_browser_tool_live.py`
- [ ] T011 `CHANGELOG.md` entry + `specs/checklist.md` CHK series +
  `docs/ARCHITECTURE_AUDIT_REPORT.md` traceability row, once implemented

## Explicitly out of scope (see spec.md)

- Screenshot capture/attachment
- In-tool LLM-driven locator resolution
- Multi-tab/persistent cross-call browser sessions
