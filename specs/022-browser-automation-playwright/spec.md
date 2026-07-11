# Feature Specification: Browser Automation via Playwright

**Feature Branch**: `fix/copy-setup-to-scripts`

**Feature ID**: `022-browser-automation-playwright`

**Created**: 2026-07-10

**Status**: Proposed — spec kit only, not yet implemented.

**Input**: Gap analysis of `docs/history/2603.27127v1.pdf` against Argus's current codebase,
requested by the user 2026-07-10.

---

## Why this feature

Every existing Argus tool (`Recon_Suite`, `Crawl_Target`, `Run_Nikto`, `Run_FFUF`,
`Advanced_Evasion_Probe`, etc., confirmed by reading `app/tools/*.py`) operates through `curl` or
CLI scanners executed inside the Kali WSL distro via `WSLBridge`/`CommandRunner`. None of them
execute JavaScript or render a DOM. Any target that gates its real content behind client-side
rendering (a React/Vue/Angular SPA, an OAuth redirect chain requiring a real browser session, a
form whose submission is wired to a JS event handler rather than a plain HTML `<form>`) is
**functionally invisible** to Argus today — `Crawl_Target`'s `curl | grep href` pipeline
(`app/tools/crawler.py`) will return zero or near-zero links against such a target, and the
agent has no way to know the emptiness is a rendering gap rather than a genuinely link-poor site.

Red-MIRROR's Exploiter Agent includes "Browser Automation via Playwright... enabling automated
navigation and interaction with dynamic web interfaces. The system employs LLM-assisted semantic
reasoning to identify robust element locators" (Section 3.6.2). This is a capability gap, not a
depth gap — no amount of tuning existing tools closes it; it requires a genuinely new execution
primitive (a real browser engine) that nothing in Argus's current toolchain provides.

## Requirements

### Functional Requirements

- **FR-001**: A new tool MUST launch a headless browser (Chromium, via Playwright), navigate to
  a target URL, wait for network idle/DOM content loaded, and return the **rendered** HTML (post
  -JS-execution) — the direct fix for `Crawl_Target`'s blind spot. This alone (no interaction)
  is the minimum useful version.
- **FR-002**: The tool MUST support a small, explicit set of interactions: click an element
  (identified by text content or a CSS selector, not just coordinates — matches the paper's
  "robust element locators" framing), fill a form field, and submit a form — enough to walk
  through a login flow or a JS-driven search box, not full arbitrary scripting.
- **FR-003**: Element location MUST prefer semantic, resilient selectors over raw CSS/XPath,
  matching the paper's "LLM-assisted semantic reasoning... resilience against UI changes" intent
  — but MUST NOT require an *additional* LLM call inside the tool itself for the first version;
  the calling agent supplies a semantic hint (e.g., `"the Login button"`) as a plain string
  argument, and the tool's own fallback chain resolves it. **Corrected fallback order from
  2026-07-10 web-research validation**: `get_by_role` -> `get_by_label` -> `get_by_text` ->
  `get_by_test_id` -> raw CSS (last resort) — this matches Playwright's own documented locator
  priority (playwright.dev/docs/locators: role is closest to how users/assistive tech perceive a
  page; label is next since most form controls have one; text is for non-interactive elements;
  test-id and CSS/XPath are explicitly called out as most brittle, last resort only). The
  original design's order (role -> text -> label) had text and label swapped relative to this
  documented priority. A dedicated in-tool LLM-driven locator resolution is a valid follow-up,
  not required initially (keeps this tool's latency and complexity bounded for a first version).
- **FR-004**: The tool MUST execute **inside the existing Kali WSL environment** via the
  existing `CommandRunner`/SSH execution path, not as a new Windows-host-side dependency —
  consistent with every other tool and with the project's documented Windows-orchestrator /
  Kali-execution split (`docs/history/2603.27127v1.pdf` Section 4.2.1 describes the same split
  for Red-MIRROR itself). Concretely: a small standalone Python script
  (`app/tools/assets/playwright_probe.py`) is copied/present on the Kali side, invoked via
  `runner.run("python3 playwright_probe.py <json-args>")`, printing a JSON result to stdout that
  the Windows-side tool wrapper parses — the same "shell out, parse stdout" shape every existing
  tool already uses, just with a Python script instead of a bare CLI tool as the thing being
  shelled out to.
- **FR-005**: A results MUST include a truncated screenshot-free text summary by default (full
  rendered HTML can be large); an optional `full_html: bool` argument returns the complete
  rendered DOM when the agent needs it. Screenshots are explicitly out of scope for v1 (FR
  omission is deliberate — see Explicitly out of scope) since Argus's GUI/report pipeline has no
  image-attachment channel today.

### Non-Functional Requirements

- **NFR-001a** (added 2026-07-10 web-research validation): the browser launch (`playwright_probe.py`,
  `plan.md`) MUST pass `args=["--no-sandbox"]` to `chromium.launch()`. Confirmed via community
  Playwright/WSL setup guidance that Chromium's sandbox commonly fails to initialize under
  WSL/containerized environments, and this project's own SSH session into Kali runs as a
  non-root, potentially namespace-restricted user (`WSLConfig`'s default `kali`/`kali`, per
  `app/tools/wsl_bridge.py`) — the same class of environment where this is a known, common
  requirement. This MUST be verified against the project's actual Kali WSL setup at
  implementation time (T001 in `tasks.md`), not just assumed from general guidance.
- **NFR-001**: Provisioning (installing Playwright + Chromium + its OS dependencies inside the
  Kali WSL distro) MUST be added to `scripts/ARGUS_INSTALLER.ps1`'s existing Kali-provisioning
  steps, not left as a manual post-install step — consistent with how every other Kali-side tool
  dependency (Nikto, FFUF, WhatWeb per the existing installer) is already provisioned.
- **NFR-002**: A missing-Playwright-in-Kali failure MUST produce an honest, specific error
  ("Playwright not installed in Kali — run the installer's browser-automation step") rather than
  a generic command-not-found string the agent has no way to act on — Constitution VIII.
- **NFR-003**: Every browser launch MUST have an explicit hard timeout (proposed: 30s navigation
  timeout, 60s total script timeout) — a hung page load must not consume the agent's
  `max_iterations` budget indefinitely, the same lesson `018`'s CHK090 already learned for curl.

## Success Criteria

- **SC-001**: Against a mock local page containing content injected only via JavaScript (a
  simple test fixture, e.g., an HTML file with `<div id=x></div><script>x.innerText='secret'
  </script>`), the tool returns rendered HTML containing "secret"; a parallel `Crawl_Target`-
  style curl fetch of the same fixture does not — proving this closes a real, demonstrable gap,
  not just a theoretical one.
- **SC-002**: A test simulating a 2-step flow (fill a field, click a button, observe a changed
  page state) passes using semantic locators against a fixture page, without hardcoded CSS
  selectors in the test's assertions about the *tool's* behavior (the fixture itself can have
  any markup — the point is the tool resolves it semantically).
- **SC-003**: A test simulating a hung/never-resolving page load confirms the tool returns
  within NFR-003's timeout with an honest timeout error, not a hang.

## Assumptions

- Target sites are assumed reachable from the Kali WSL distro's network path exactly as every
  other existing tool already assumes (no new network topology).
- No CAPTCHA-solving or anti-bot-evasion capability is assumed or added — a target with bot
  detection sophisticated enough to block headless Chromium is out of scope for this tool.

## Explicitly out of scope

- Screenshot capture/attachment — no image channel exists in Argus's current report pipeline
  (`SecurityReport` schema, GUI dashboard); adding one is a separate, larger UI feature.
- In-tool LLM-driven locator resolution (an LLM call *inside* the tool to interpret ambiguous
  semantic hints) — FR-003's fallback chain (role -> text -> CSS) is the v1 approach; smarter
  resolution is a follow-up once real usage shows the fallback chain's limits.
- Multi-tab/multi-context browser sessions, persistent cookie jars across separate tool calls —
  each invocation is a fresh, isolated browser context, matching the stateless-per-call shape
  every other Argus tool already has.
