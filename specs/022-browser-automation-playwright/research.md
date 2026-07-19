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

## Addendum (2026-07-13): "AI Browser Agent" vs. plain headless browser - confirmed FR-003's design choice is correct

User asked specifically about "AI Browser Agent" frameworks (e.g. Browser-Use) as an alternative
to a plain headless-browser tool, given the real gap this spec targets (JS/DOM-rendered content
Argus can't see today - live-confirmed 2026-07-11/12 against a real PortSwigger lab, which had
nothing JS-dependent, but the class of lab that *is* JS-dependent, e.g. DOM XSS labs, remains
untestable). Researched before answering:

1. **The distinction**: a headless browser (Playwright/Puppeteer) is a real browser engine
   controlled by deterministic code you write - "navigate, click X, extract Y." An "AI Browser
   Agent" (Browser-Use, Skyvern, etc.) is an LLM sitting *on top of* a headless browser, deciding
   what to do at each step from a goal description rather than a fixed script - more resilient to
   layout changes, but non-deterministic and, critically, an *additional independent LLM decision
   loop* running underneath whatever already-existing agent calls it.
   (Sources: [Headless Browser vs AI Agents: When to Use Each (2026), TinyFish](https://www.tinyfish.ai/blog/headless-browser-vs-ai-agents),
   [Browser Tools for AI Agents Part 1: Playwright, Puppeteer (dev.to)](https://dev.to/stevengonsalvez/browser-tools-for-ai-agents-part-1-playwright-puppeteer-and-why-your-agent-picked-playwright-k71).)
2. **Vision is not strictly required for an AI Browser Agent** - some open-source frameworks
   support a text-only mode (a simplified DOM/accessibility tree fed to the LLM as text, no
   screenshots), which would in principle run on a small local model like WhiteRabbitNeo-V3-7B via
   Ollama without needing a second, vision-capable model - this removes what would otherwise have
   been an immediate feasibility blocker.
   (Sources: [browser-use GitHub](https://github.com/browser-use/browser-use),
   [Supported Models - Browser Use docs](https://docs.browser-use.com/open-source/supported-models),
   [Using Ollama with Browser-Use to Leverage Local LLMs (Medium)](https://medium.com/@tossy21/using-ollama-with-browser-use-to-leverage-local-llms-6e1fba532b58).)
3. **Decision: still don't adopt a full AI Browser Agent framework.** Argus already has its own
   LLM decision loop (the ReAct graph deciding which tool to call next). Layering a second,
   independent LLM-driven decision loop *inside* a browser tool means two nested agents reasoning
   about the same task - directly repeating the exact lesson `020`'s NFR-001 measurement just
   demonstrated with real numbers (every additional LLM decision point costs several real seconds
   against this project's local model; `020` measured a 2.00x call-count overhead from a much
   lighter one-extra-decision-per-step design than a full nested agent would add). Recent
   pentesting-specific research independently points the same way: "Playwright MCP" - exposing
   browser primitives (navigate, click, extract) as callable tools for an *existing* agent to
   invoke - is the pattern several 2026 agentic pentesting write-ups actually use, not a
   separately-reasoning browser agent.
   (Sources: [AWE: Adaptive Agents for Dynamic Web Penetration Testing (arXiv:2603.00960)](https://arxiv.org/html/2603.00960),
   [Top 10 Agentic AI Penetration Testing Tools in 2026 (zerothreat.ai)](https://zerothreat.ai/blog/top-10-agentic-ai-penetration-testing-tools),
   [autopentest-ai (GitHub)](https://github.com/bhavsec/autopentest-ai).)

**Conclusion**: this spec's existing FR-003 ("MUST NOT require an additional LLM call inside the
tool itself for the first version... a dedicated in-tool LLM-driven locator resolution is a valid
follow-up, not required initially") and "Explicitly out of scope" section (in-tool LLM-driven
locator resolution) were already the right call before this research pass existed - confirmed,
not changed. `FR-001`/`FR-002`'s plain tool-wrapper shape (Argus's existing agent calls
`Browser_Navigate_And_Extract_DOM`/a fill-and-submit tool directly, using its own existing
decision loop, not a second one) is the design to build, not an "AI Browser Agent" framework.

## Addendum (2026-07-13b): 3 additional browser techniques worth adding to the same tool surface

User asked for further research into related techniques/tools beyond the original render+interact
pair, aiming for the best-fit, evidence-backed set for this project (per the new Constitution
Principle XI, documented here rather than left in chat). Researched three concrete extensions,
each independently validated by real-world Playwright-based pentesting tooling already built by
others (not just theorized):

1. **Network/HAR capture - closes a second, distinct blind spot beyond rendering.** Even with
   `Render_Page_JS` fixing the DOM-rendering gap, a SPA's real attack surface is often the AJAX/
   fetch calls it makes to backend API endpoints *after* load - these never appear in any HTML,
   rendered or not, only in network traffic. Playwright's `page.on("request")`/`page.on("response")`
   (or the CLI's `--save-har`) captures every request a page makes while rendering, which is the
   standard technique for discovering hidden API endpoints in SPA testing.
   (Sources: [How to Intercept API Calls Requests in Playwright](https://roundproxies.com/blog/intercept-network-playwright/),
   [Network | Playwright (official docs)](https://playwright.dev/docs/network),
   [Mock APIs | Playwright (official docs)](https://playwright.dev/docs/mock).)
2. **Console/page-error capture - a real, content-based way to verify payload execution, not
   just check appearance.** `page.on("console")`/`page.on("pageerror")` captures actual browser
   console output and uncaught JS exceptions - if an injected test payload contains something
   like `console.log('argus_xss_<random>')`, seeing that exact string in the captured console
   output is direct proof the payload *executed*, not just that it appears unescaped in the
   response body (which can still be a false positive if e.g. the browser's own XSS auditor or a
   CSP blocked it from actually running). This is the same "verify by real signal, not
   appearance" philosophy already applied to `SENSITIVE_CONTENT_INDICATORS`
   (`app/tools/utils.py`) for traversal/SQLi - extending it to the one vulnerability class
   (XSS) that specifically requires a real browser to verify at all. Confirmed as an established,
   real technique: a dedicated "XSS Vulnerability Tester" MCP server (Playwright-based) uses
   exactly this - payload injection + console/error monitoring - as its core detection mechanism.
   (Sources: [XSS Vulnerability Tester MCP Server (PulseMCP)](https://www.pulsemcp.com/servers/xss-vulnerability-tester),
   [How to Monitor JavaScript Logs & Exceptions with Playwright (Checkly)](https://www.checklyhq.com/blog/how-to-monitor-javascript-logs-and-exceptions-with-playwright/),
   [XSS Tester: Automated Cross-Site Scripting Vulnerability Tool](https://mcpmarket.com/server/xss-tester).)
3. **Session-state extraction (cookies + localStorage/sessionStorage) - a real, flaggable
   finding, not just convenience.** `context.cookies()` reads the browser's actual cookie jar,
   including `HttpOnly` cookies - notably, this is something `document.cookie` (plain JS, what a
   curl-based tool could never do anyway) *cannot* see, since `HttpOnly` is specifically designed
   to hide a cookie from page JS. That asymmetry means a `Secure`/`HttpOnly`-missing session
   cookie is a concrete, checkable misconfiguration finding this project has no way to detect
   today. `page.evaluate()` separately reads `localStorage`/`sessionStorage` contents, which are
   a real, previously-documented class of information-disclosure bug (sensitive tokens/PII kept
   client-side where they shouldn't be) - and pairs naturally with the existing
   `Secret_Scanner`/`SENSITIVE_CONTENT_INDICATORS` pattern-matching once extracted as text.
   (Sources: [Storage & Authentication - Playwright (official docs)](https://playwright.dev/agent-cli/commands/storage),
   [Using Playwright's storageState (BrowserStack)](https://www.browserstack.com/guide/playwright-storage-state),
   [Cookies and localStorage Manipulation in Playwright](https://scrolltest.com/playwright-cookies-localstorage-manipulation/).)

**Broader validation this is the right general direction:** multiple independent, real
Playwright-based MCP (Model Context Protocol) servers built specifically for agentic pentesting
already combine exactly this toolset (render/interact + network capture + console monitoring +
screenshots) as callable primitives for an *external* AI agent to invoke - not as a
separately-reasoning agent of their own, consistent with the 2026-07-13(a) addendum's
tool-not-agent conclusion above.
(Sources: [mcp-browser (GitHub, badchars)](https://github.com/badchars/mcp-browser),
[hexstrike-ai (GitHub)](https://github.com/0x4m4/hexstrike-ai),
[MCP Server Pentest (mcpservers.org)](https://mcpservers.org/servers/9olidity/MCP-Server-Pentest).)

**Decision**: extend `spec.md` with three new functional requirements (FR-006/007/008 - network
capture, console/error capture, session-state extraction) rather than treating render+interact as
the complete tool surface - each is independently well-established, each closes a real,
previously-undetectable gap, and none require an in-tool LLM decision loop (consistent with
FR-003's existing stance).

## Why this is its own spec, not folded into `021`

`021`'s five tools are all curl-based, matching the existing pattern with zero new runtime
dependencies (NFR-002 there). This tool requires a new Kali-side dependency (Playwright +
Chromium + OS deps) and a new execution shape (a companion script, not a single CLI invocation)
— different enough in kind and provisioning risk to warrant separate review/approval rather than
being bundled with the lower-risk toolkit.
