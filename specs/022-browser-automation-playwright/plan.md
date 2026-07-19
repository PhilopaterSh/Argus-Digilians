# Implementation Plan: Browser Automation via Playwright

**Feature**: `022-browser-automation-playwright` | **Spec**: `spec.md` | **Research**: `research.md`

## Summary

A new companion script executed inside Kali via the existing SSH/`CommandRunner` path, wrapped
by a new `app/tools/browser_tool.py` service on the Windows side that shells out to it and
parses JSON stdout - matching every existing tool's "shell out, parse stdout" shape while
accommodating Playwright's session-based Python API via a fresh-process-per-call script.

## Design

### `app/tools/assets/playwright_probe.py` (new, lives/runs inside Kali)
- Plain script, no Argus imports (it runs in Kali's Python environment, separate from the
  Windows-host `app/` package): `sys.argv`-based JSON-in (`{"url": ..., "actions": [...],
  "capture_network": false, "extract_session": false}`, actions = ordered list of
  `{"type": "fill"|"click"|"wait", "locator": "...", "value": "..."}`) / JSON-out
  (`{"html": ..., "final_url": ..., "error": null, "console_logs": [...], "page_errors": [...],
  "network_requests": [...] | null, "cookies": [...] | null, "local_storage": {...} | null,
  "session_storage": {...} | null}`) contract.
- `console_logs`/`page_errors` (FR-007) are ALWAYS populated (registered via
  `page.on("console", ...)`/`page.on("pageerror", ...)` before `page.goto()`, so nothing emitted
  during initial load is missed) - not gated behind a flag, since they're the concrete mechanism
  for verifying payload execution and cost nothing extra to capture.
- `network_requests` (FR-006) is populated only when `capture_network` is true, via
  `page.on("request")`/`page.on("response")` pairs matched by URL, capped at a fixed count
  (proposed: 50 entries, each `{url, method, status}` only - not full request/response bodies,
  keeping output size bounded per FR-005's truncation precedent).
- `cookies`/`local_storage`/`session_storage` (FR-008) populated only when `extract_session` is
  true, via `context.cookies()` and two `page.evaluate("() => JSON.stringify(localStorage)")`-
  style calls. Each cookie entry flags `secure`/`http_only` booleans directly from
  `context.cookies()`'s own return shape, so the Windows-side wrapper can flag a missing
  attribute as a finding without re-deriving it.
- `browser = p.chromium.launch(args=["--no-sandbox"], ...)` (NFR-001a - required in most
  WSL/containerized setups; verify against this project's actual Kali WSL environment and drop
  only if proven unnecessary there). Uses `browser.new_context()`, `page.goto(url, timeout=30000,
  wait_until="networkidle")` (NFR-003's 30s navigation timeout). Locator resolution, in
  Playwright's own documented priority order (FR-003's corrected order): try
  `page.get_by_role(...)`, then `get_by_label(...)`, then `get_by_text(...)`, then
  `get_by_test_id(...)`, then raw CSS selector as the last resort, catching each `TimeoutError`
  before falling through.
- Wraps the whole run in a hard 60s watchdog (`signal.alarm` on the Kali/Linux side, or a
  `threading.Timer`-based kill - Linux target makes `signal.alarm` viable, unlike the
  Windows-host code elsewhere in this project) so a hung page cannot exceed NFR-003's total
  budget even if Playwright's own per-step timeouts are somehow bypassed.

### `app/tools/browser_tool.py` (new, `BrowserAutomation` service)
- `__init__(self, runner, memory)` - same constructor shape as every sibling tool.
- `render_page(url, full_html=False, capture_network=False) -> str`: builds the JSON-in payload
  with an empty `actions` list, calls `runner.run(f"python3 ~/argus_assets/playwright_probe.py
  '{json_payload}'")`, parses the JSON-out, returns either the full HTML or a truncated
  summary (FR-005) - always appends a `console_logs`/`page_errors` section (FR-007) and, when
  `capture_network` is set, a `network_requests` section (FR-006).
- `interact(url, actions: list[dict]) -> str`: same call shape with a populated `actions` list
  (FR-002), for the fill/click/submit flow - also always appends `console_logs`/`page_errors`
  (FR-007), the primary use case for this data (verifying an injected payload actually ran).
- `extract_session_state(url) -> str` (FR-008, new): builds the JSON-in payload with
  `extract_session: true`, no actions; formats cookies with an explicit
  `"[!] Missing Secure/HttpOnly"` flag per cookie that lacks either attribute (a direct,
  checkable finding written to `memory.add_finding()`), plus the raw `local_storage`/
  `session_storage` contents for the calling agent to inspect or pass to `Secret_Scanner`-style
  review.
- All three methods check for the specific "playwright: command not found" / "ModuleNotFoundError"
  signatures in the runner's stderr/stdout and translate them into NFR-002's specific, actionable
  error message rather than passing through a raw traceback.

### `app/tools/tool_registry.py` (`WSLBridgeTools`)
- `self.browser = BrowserAutomation(self.runner, self.memory)` in `__init__`.

### `app/core/agent/brain_tools.py`
- Three new `Tool(...)` entries: `Render_Page_JS` (wraps `render_page`), `Browser_Interact`
  (wraps `interact`), and `Extract_Session_State` (wraps `extract_session_state`, FR-008) - kept
  as separate tools rather than one parameterized tool, matching the existing convention of one
  clearly-scoped tool per capability (e.g., `Check_Reachability` vs. `Recon_Suite` are separate
  tools rather than one parameterized one) so the LLM's action-selection prompt stays simple.
  If `020`'s role partition is ever promoted to default, `Render_Page_JS`/`Extract_Session_State`
  belong in `ROLE_TOOL_PARTITIONS["collector"]` (discovery) and `Browser_Interact` in
  `ROLE_TOOL_PARTITIONS["exploiter"]` (interaction/payload delivery) - not decided now since `020`
  isn't the default path.

### `scripts/ARGUS_INSTALLER.ps1`
- New Kali-provisioning step alongside the existing Nikto/FFUF/WhatWeb installs: `pip3 install
  playwright && playwright install --with-deps chromium` run inside the Kali WSL distro, plus
  copying `app/tools/assets/playwright_probe.py` to `~/argus_assets/` on the Kali side (the
  installer already has an established pattern for pushing files/config into Kali per its
  existing SSH-key/service-setup steps - reuse that, don't invent a second file-transfer
  mechanism).

## Testing Strategy

Windows-side (`browser_tool.py`) tests mock `runner.run()` to return canned JSON-out strings -
no live Kali/Playwright needed, matching every other tool's test convention. A **separate**,
explicitly-marked-as-requiring-live-Kali integration test (skipped by default, matching this
repo's existing pattern for anything needing real WSL/SSH) exercises the actual
`playwright_probe.py` script against a local static HTML fixture served from
`http.server` (mirroring `tests/ai_benchmark.py`'s existing mock-server pattern) - this is how
SC-001/SC-002/SC-003 get proven against a real browser engine without requiring live
infrastructure for routine CI runs.

## Rollout

New tool, no flag needed (same rationale as `021`) - but `NFR-002`'s honest-error path is the
de facto safety net for any environment where the installer step hasn't been run yet.
