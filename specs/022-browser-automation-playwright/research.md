# Research: Browser Automation via Playwright

**Feature**: `022-browser-automation-playwright`

## Primary source

`docs/history/2603.27127v1.pdf`, Section 3.6.2: "Browser Automation via Playwright: A browser-
level interaction module built on Playwright, enabling automated navigation and interaction with
dynamic web interfaces. The system employs LLM-assisted semantic reasoning to identify robust
element locators, improving resilience against UI changes." Reference [39] in the paper cites
Playwright's own documentation (`playwright.dev`) directly.

## Current Argus implementation reviewed (confirmed absent)

`grep -rli "playwright\|selenium" app/ --include="*.py"` returned zero matches (run 2026-07-10).
`app/tools/crawler.py::CrawlerService.crawl_target()` is the closest existing capability and is
explicitly curl+grep based — confirmed by reading the file directly: `curl -s -L --max-time 15
--connect-timeout 5 {url} | grep -oE 'href="[^"]+"' | cut -d'"' -f2 | sort -u`. This pipeline
cannot see any link injected by client-side JavaScript after page load, which is the specific,
demonstrable gap this spec's SC-001 targets.

## Execution model research (grounding FR-004)

Every existing Argus tool executes via `app/tools/wsl_bridge.py`/`command_runner.py`'s
shell-out-over-SSH-into-Kali pattern — confirmed by reading `wsl_bridge.py` directly
(`WSLConfig` targets `kali-linux` via paramiko SSH, `user=kali`). Playwright's Python API is a
long-running interactive session (`with sync_playwright() as p: browser = p.chromium.launch()...`),
which does not fit a single one-line shell command the way `curl`/`nikto`/`ffuf` do. The
standard way to reconcile this with a "shell out, parse stdout" tool architecture (rather than
requiring a persistent Python process managed across tool calls, which no other Argus tool needs
and which would be a new class of state to manage) is a small standalone script invoked fresh
per call, printing structured (JSON) output to stdout — exactly how `app/tools/assets/
playwright_probe.py` is scoped in `plan.md`. This keeps the tool stateless-per-call, matching
every sibling tool, at the cost of Chromium's cold-start latency on every invocation (a real,
accepted tradeoff — NFR-003's 60s total-script timeout budgets for this).

## Provisioning research

Playwright requires (a) the `playwright` Python package and (b) downloaded browser binaries plus
OS-level dependencies (`playwright install --with-deps chromium`) — this is a real, non-trivial
addition to whatever `scripts/ARGUS_INSTALLER.ps1` already does to provision Kali (confirmed
this file exists and handles Kali-side tool provisioning, per the git status at session start
showing it as a modified file this session already). This spec treats that provisioning step as
in-scope (NFR-001) rather than a silent assumption, because a tool that's spec'd but not
reachable in a fresh install is exactly the kind of "claimed but not actually available" gap
this project's Constitution VIII explicitly guards against.

## Correction (2026-07-10 web-research validation)

Two refinements found by checking this spec against current Playwright documentation and
community guidance:

1. **Locator fallback order was wrong.** The original design ordered fallbacks
   role -> text -> label -> CSS. Playwright's own documentation (`playwright.dev/docs/locators`)
   states the priority as role -> label -> text -> test-id -> CSS/XPath (role is closest to how
   a user/assistive tech perceives the page; most form controls have a label, which is why it
   ranks above generic text matching; test-id and CSS/XPath are explicitly flagged as the most
   brittle, last-resort options). Corrected in `spec.md`/`plan.md`.
2. **Missing `--no-sandbox` consideration.** Community Playwright/WSL setup guidance
   consistently notes Chromium's sandbox often fails to initialize under WSL and containerized
   environments, typically requiring `args=["--no-sandbox"]` (or an equivalent no-sandbox
   context option) at launch. This project's Kali execution environment (SSH into a WSL distro,
   non-root `kali` user per `wsl_bridge.py`) is exactly the class of environment this guidance
   describes. Added as NFR-001a, with an explicit instruction to verify against Argus's actual
   Kali setup at implementation time rather than assume it's needed everywhere `--no-sandbox` is
   mentioned online — sandboxing requirements are environment-specific and deserve a real test,
   not a copy-pasted flag.

The core architectural design (companion script + JSON-in/JSON-out over the existing SSH
execution path, `--with-deps chromium` provisioning) was confirmed correct and unchanged by this
research pass.

## Why this is its own spec, not folded into `021`

`021`'s five tools are all curl-based, matching the existing pattern with zero new runtime
dependencies (NFR-002 there). This tool requires a new Kali-side dependency (Playwright +
Chromium + OS deps) and a new execution shape (a companion script, not a single CLI invocation)
— different enough in kind and provisioning risk to warrant separate review/approval rather than
being bundled with the lower-risk toolkit.
