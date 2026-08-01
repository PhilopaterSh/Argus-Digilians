# CHANGELOG

All notable changes to this project will be documented in this file.

## Fixed: vulnerability-hint nudge let the model treat `Exploit_Suggester` as equivalent to a live test (2026-08-01)

Live run `bc915491` against a PortSwigger path-traversal lab: `Recon_Suite`'s own output
named the vulnerability class in the page title ("File path traversal"), the deterministic
`_extract_vulnerability_hints` nudge fired correctly, but its wording -
`"Prioritize testing it directly (e.g. Advanced_Evasion_Probe or Exploit_Suggester for that
specific class)"` - presented the two tools as interchangeable. `Exploit_Suggester`
(`bridge.suggest_payloads`) only returns static reference payload text from a local
PayloadsAllTheThings mirror; it never sends a request to the target. The model called it
three times in a row with the identical input, hit the duplicate-call guard, and gave an
honest "stopped early" Final Answer - `Advanced_Evasion_Probe` (the only tool that actually
attempts exploitation, and only for SQL injection / Path Traversal per its own Tool
description) was never called, so the real, live-testable vulnerability went unverified even
though nothing was fabricated.

Fixed in `react_workflow.py`: new `_matched_vuln_keywords()` (keyword-matching logic factored
out of `_extract_vulnerability_hints`) and `_live_test_directive()`, which name the one
specific tool that actually tests a matched class live (`_LIVE_TEST_TOOL_BY_KEYWORD`, currently
`Advanced_Evasion_Probe` for path/directory traversal and SQL injection) and explicitly state
that `Exploit_Suggester` does not touch the target and does not count as testing - falling back
to a `Run_Kali_Command`/`Run_Nikto`/`Run_FFUF` suggestion for classes with no dedicated live
tool. Applied at both nudge call sites (the production single-loop `execute_node` and the
experimental multi-role `_run_specialist_step`).

## Added: Phase 1-2 (connectivity/recon) coverage enforcement, same day as the zero-tool-call fix (2026-07-26)

Follow-up to the zero-tool-call fix below, at the user's explicit request to make the agent
actually run through all of `react_prompts.py`'s PHASE 1-8 progression, not just avoid the
worst case (zero tool calls at all). New `PHASE_1_2_TOOLS = frozenset({"Check_Reachability",
"Subdomain_Enumeration", "Recon_Suite", "Crawl_Target"})` in `react_workflow.py`, and a new
one-time nudge in `parse_node` - mirrors the existing Phase 5/6 nudge exactly: if `tried_names` is
non-empty (so `zero_tool_check` doesn't apply) but doesn't intersect `PHASE_1_2_TOOLS`, and this
hasn't fired yet this run, the Final Answer is rejected once with a nudge to establish real
connectivity/recon on this specific target before concluding. New state field `phase12_nudged: bool`
(`react_state.py`, initialized in `brain.py`); new `"phase12_check"` phase added to
`route_after_parse`'s bounded-loop-back set, checked before the existing phase56 check (Phase 1-2
logically precedes Phase 5/6).

**Known tradeoff, flagged and accepted by the user before implementing:** this can add a real extra
LLM round-trip on runs that legitimately start with a non-recon tool (e.g. `Query_Memory` to check
for prior findings before deciding whether to re-scan) - directly in tension with this project's own
recent "why does a run take so long" concern. Kept as a hard, always-on nudge (not a
`config.yaml`-gated toggle) per explicit user decision.

**Test impact:** this broke 15 previously-passing tests - any test using a generic, non-"real-tool-named"
mock (`mock_scan`, `mock_search`, `mock_probe`, `mock_title_tool`, `mock_flag_tool`) as its only
tool call now needs one additional canned Final-Answer response queued up to absorb the new phase12
nudge before the run concludes, exactly the same mechanical pattern this project's own history
already established when `phase56_nudged` was first added (specs/019). All 15 fixed by adding one
more repeated Final Answer response per affected test and adjusting `iteration_count`/message-count
assertions to match; two tests using a real Phase 5/6 tool (`Run_Nikto`) needed the same treatment
since `Run_Nikto` satisfies Phase 5/6 but not Phase 1-2. `tests/test_agent/test_langgraph_workflow.py`
+ `test_brain_ask.py` + `tests/test_tools/test_evasion.py`: 116/116 passing. `ruff check` clean;
`mypy --follow-imports=skip` clean.

## Fixed: agent could give a Final Answer with fabricated findings and zero tool calls (2026-07-26)

Live-discovered TWICE independently, different targets, different days: a PortSwigger lab
(`agent_a3cfdea1-...json`) and a real production site, `www.cultbeauty.co.uk`
(`agent_766068d2-...json`). In both, the model wrote `Final Answer:` directly inside or right
after its very first `Thought`, before ever executing a single tool - zero `Observation` events in
either run log. The synthesized report that followed still contained specific, plausible-sounding
but entirely fabricated findings (SQLi at `/login.php`, path traversal at `/download.php` with a
suggested payload, an exposed `/admin.php` in one run; a fabricated "scanned with Smart_Web_Search,
no SQLi found" claim in the other, even though `Smart_Web_Search` was never called either). Neither
run's target structure even matches those invented paths.

This is a direct violation of this project's own stated Constitution VIII ("never fabricate a
report") - `_finalize_graph_output()`'s "Final Answer:" requirement is meant to uphold that, but a
bare string match on the literal text `"Final Answer:"` can't by itself distinguish a genuine,
evidence-backed conclusion from one with nothing behind it. This was previously a **documented,
known gap**, not a surprise: `app/core/agent/react_workflow.py`'s `parse_node` had an explicit
comment stating a Final Answer with zero tool calls was "a different, broader problem... out of
scope for this check."

Fixed: `parse_node` now checks `tool_call_history` when it sees `phase == "done"`. If it's
completely empty (no tool was ever executed this run) and this is the first time this run, the
Final Answer is rejected with an explicit nudge explaining that any claim in it is unverified and
telling the model to start with `Check_Reachability`/`Recon_Suite` first - mirroring the existing
Phase 5/6 nudge's one-time-per-run design (a target CAN legitimately need no further tooling, but
only after actually checking, not before ever trying). New state field
`zero_tool_final_answer_nudged: bool` (`react_state.py`, initialized in `brain.py`'s `ask()`); new
`"zero_tool_check"` phase added to `route_after_parse`'s bounded-loop-back set (same `max_iterations`
safety net as `format_error`/`duplicate_call`/`phase56_check`).

Three pre-existing tests asserted the OLD (buggy) behavior and were updated to prove the corrected
one instead: `test_final_answer_with_zero_tool_calls_gets_nudged_to_investigate_first` (renamed from
`..._is_not_nudged`), `test_custom_graph_immediate_final_answer_gets_nudged_first` (renamed from
`..._immediate_final_answer`, iteration count 1 -> 2), and
`test_custom_graph_uses_structured_action_end_to_end` (iteration count 1 -> 2). One test in
`test_brain_ask.py` (`test_ask_retries_once_on_transient_ollama_cuda_crash`) needed its
`llm.call_count` assertion updated 2 -> 3 for the same reason (its post-crash recovery response is
itself a zero-tool-call Final Answer) - the crash-retry mechanism that test actually covers is
unaffected (still exactly 1 retry). New test:
`test_zero_tool_call_nudge_is_skipped_once_a_real_tool_executes` (proves the guard doesn't fire
again once the model recovers with a genuine tool call). `tests/test_agent/test_langgraph_workflow.py`
+ `test_brain_ask.py` + `tests/test_tools/test_evasion.py`: 116/116 passing. `ruff check` clean;
`mypy --follow-imports=skip` clean.

## Fixed: `Advanced_Evasion_Probe` (path traversal) silently failed against real targets - two confirmed root causes (2026-07-25)

Found by directly testing `EvasionService.advanced_vuln_probe()` against this project's own
`benchmarks/fixtures/path_traversal_download` fixture's real server (not a mock) - a live PortSwigger
run log from the same day confirmed the same class of gap independently.

**Root cause 1 - hardcoded query parameter name.** The probe always appended the payload as
`?item=<payload>` (or `?id=` for SQLi). Confirmed via direct `curl` against the benchmark fixture's
real server that it uses `?file=`, not `?item=` - `?item=../../secret.txt` returns the harmless
welcome page every time, while `?file=../secret.txt` returns the real flag content. This exactly
matches this project's own `benchmarks/results/*.md` history: `path_traversal_download` scored
0% on `traverse_to_secret_file`/`retrieve_flag` in **every** recorded run, only ever completing
`find_download_endpoint` (100%) - the probe finds the endpoint via recon, then can never actually
traverse it. Real-world targets (PortSwigger labs included) commonly use `file`/`filename`/`path`/
`document` instead of `item`.

**Root cause 2 - unsanitized tool_input.** A live run's log (`agent_0221f988-...json`) showed the
model calling `Advanced_Evasion_Probe` with tool_input
`"https://<lab>.web-security-academy.net/ path traversal"` - free text appended after the URL
(primed by `Exploit_Suggester`'s own preceding output style). Un-sanitized, this spliced straight
into the curl command, producing a broken URL (a literal embedded space, garbage path appended)
that was guaranteed to fail against ANY target, vulnerable or not - unrelated to root cause 1,
compounding it in that specific run.

Fixed, both in `app/tools/evasion.py`:
- `_extract_clean_url()` - a new module-level helper, applied at the top of
  `advanced_vuln_probe()`, that extracts the first `http(s)://`-prefixed whitespace-free token
  from `url` and drops any trailing free text the model appended.
- Path-traversal parameter handling: if `url` already carries a query string (a discovered
  endpoint's own real parameter, e.g. crawled as `?filename=x.jpg`), that parameter name is reused
  for every payload instead of guessing. Otherwise, a short candidate list is tried per payload -
  `item` first (exact backward compatibility with every existing call site/test), then `file`,
  `filename`, `path`, `document` - locking in whichever one confirms a hit so subsequent payloads
  go straight to it instead of re-fuzzing every time (bounds the added request volume).

Explicitly NOT changed: `SENSITIVE_CONTENT_INDICATORS` (`app/tools/utils.py`) still only recognizes
real OS-level artifacts (`root:x:0:0:`, `DB_PASSWORD`, `appSettings`, `uid=`) - the benchmark
fixture's own synthetic flag text (`CONFIDENTIAL INTERNAL NOTE` / `flag{...}`) isn't one of them,
so a full live run against that specific fixture still won't self-report a finding even after this
fix (a separate, narrower gap specific to that one synthetic fixture, not touched without checking
first - real targets like PortSwigger's actual `/etc/passwd` reads are unaffected, since that
content genuinely contains `root:x:0:0:`).

This is also the direct answer to "why did the headless-browser screenshot feature (specs/029)
show nothing" in several live runs: `capture_vulnerability()` only ever fires on a *confirmed*
`advanced_vuln_probe()` hit, and the JSON evidence report is only written when a screenshot was
actually captured - with detection itself silently failing for the two reasons above, zero
findings meant zero screenshots and zero reports, exactly as designed (not a bug in the screenshot
feature itself, which was independently live-verified working via
`scripts/diagnose_browser_manager.py` on 2026-07-25).

Tests: 4 new cases in `tests/test_tools/test_evasion.py`
(`TestAdvancedVulnProbeParameterFuzzingAndUrlCleaning`) proving the URL-cleaning, existing-param
reuse, fallback-candidate fuzzing, and confirmed-param lock-in behaviors independently; all 11
pre-existing `test_evasion.py` cases pass unchanged (the `item`-first ordering was chosen
specifically to preserve this). `ruff check` clean; `mypy --follow-imports=skip` clean.

## Fixed: ReAct agent could burn all `max_iterations` in a duplicate-call loop without a Final Answer (2026-07-25)

Live bug, hit by the user running Argus Studio against a real PortSwigger lab: the run took
~11 minutes, reported `'error': 'no_final_answer'`, and the run log showed `Recon_Suite` invoked
18 times in a row (`Exploit_Suggester`: 5, `Query_Memory`: 1, `Advanced_Evasion_Probe`: 1 - so the
screenshot feature above was not the cause, it fired exactly once). Root cause traced to
`app/core/agent/react_workflow.py`'s `parse_node`: its duplicate-call guard (tracks
`tool_call_history`, allows a call twice, blocks the third identical attempt with guidance text)
correctly blocks *execution* but was unbounded in how many times *that same block-and-retry cycle*
could repeat - a model that keeps re-proposing the same (or another already-tried) tool after being
told not to was only ever stopped by the generic `max_iterations` cap, silently consuming the
entire iteration budget with zero new information gained.

Fix: a new `MAX_CONSECUTIVE_DUPLICATE_BLOCKS = 3` constant and a `consecutive_duplicate_blocks`
counter on `ArgusAgentState` (`react_state.py`, `NotRequired[int]`, initialized to `0` in
`brain.py`'s `ask()`). `parse_node` increments it every time the duplicate-call guard fires and
resets it to `0` in `execute_node` on any genuinely executed (non-duplicate) tool call. Once the
counter reaches the threshold, the graph now stops itself early with `phase="done"` and an honest,
explicit Final Answer (worded as a partial result caused by a tool-selection loop, not a completed
assessment, listing which tools actually ran) instead of continuing to burn iterations that the
guard's own logic guarantees will produce identical guidance every time.

Chosen threshold (3) verified not to regress the pre-existing
`test_custom_graph_duplicate_call_loop_respects_max_iterations` test: in that test the first
duplicate-call block coincides with `iteration_count` already hitting a low `max_iterations`, so
the existing `route_after_parse` cap fires first, before the new counter (at 1) could ever trigger -
confirmed both by manual trace and by the full suite passing unchanged.

Added: `test_custom_graph_gives_up_early_after_consecutive_duplicate_blocks` (proves the graph now
concludes well before `max_iterations=25` on a sustained loop) and
`test_custom_graph_recovering_between_blocks_resets_consecutive_counter` (proves one genuine
intervening action resets the counter, so a model that recovers isn't penalized for an earlier
stumble). `tests/test_agent/test_langgraph_workflow.py` + `tests/test_agent/test_brain_ask.py`:
68/68 passing. `ruff check` clean; `mypy --follow-imports=skip` clean on all three touched files
(`react_workflow.py`, `react_state.py`, `brain.py`) - `--follow-imports=skip` used only to route
around a pre-existing, unrelated mypy parser crash on `app/tools/recon.py`'s Python-3.12-only
f-string syntax, confirmed via `git diff` to be untouched by this change.

**Follow-up same day (web-research-backed):** the duplicate-call guard's `call_key` compared
`tool_input` via exact string equality only, so two calls that are semantically identical but
textually different (e.g. `"https://test.com"` vs `"https://test.com/"` - a trailing slash) never
registered as the "same" call at all, silently bypassing the guard rather than tripping it - one
credible way a run could reach 18 `Recon_Suite` calls despite the guard's own "block the 3rd
identical attempt" design. Added `_normalize_call_input()` (whitespace collapsing + a single
trailing slash stripped, applied to all three `call_key` construction sites, both graphs) -
deliberately does NOT lowercase or otherwise touch payload content, since several Phase 5/6 tools
pass case-sensitive payloads as `tool_input` where two differently-cased strings are genuinely
different attack attempts. New test:
`test_custom_graph_blocks_near_duplicate_call_differing_only_by_trailing_slash`. All 68 tests
still passing; `ruff`/`mypy` clean.

## Implemented specs/029 (vulnerability screenshot evidence capture via Playwright) (2026-07-25)

User requested a Playwright-based headless-browser module distinct from the still-proposed
`specs/022-browser-automation-playwright`: a persistent `BrowserManager` (opens once when a
target is set, stays open for the whole test run, not a fresh process per call), wired into the
existing path-traversal detection path so a confirmed finding gets an automatic screenshot,
producing a JSON evidence report - via spec-kit, with the needed items added to Requirements.
Full spec/research/plan/tasks in `specs/029-vulnerability-screenshot-evidence/`.

Ported the same day from an equivalent implementation independently built in a teammate's
separate local clone of this repo (`IBRAHIM`'s working copy, at a different commit than this
clone despite sharing the same GitHub remote) - reverted there per the user's request and rebuilt
here against this clone's own current file contents (fuller docstrings from an intervening
`specs/016-docstring-enforcement` pass, `pytestmark = pytest.mark.unit`, etc. - same design,
re-applied). See `specs/029-vulnerability-screenshot-evidence/research.md`'s "Provenance" note.

Scoped as its own feature rather than folded into `022` because the two are architecturally
incompatible: `022` is a stateless, fresh-subprocess-per-call design executed inside Kali over
SSH for DOM-rendering purposes, with screenshots explicitly out of scope; `029` is a persistent,
host-side (no Kali/SSH) session whose entire purpose is the screenshot `022` deliberately
excluded. `022` is untouched by this work and remains its own, separately-approved unit of work.

Implemented:
- `app/tools/browser_manager.py` - `BrowserManager` (Playwright sync API): `start()`/`close()`
  lifecycle instead of a `with` block (so one Chromium session survives across many
  `capture_vulnerability()` calls), auto-start-on-first-capture, idempotent `close()`, context
  manager support, `BrowserManagerError` for a missing Playwright install.
- `app/tools/vuln_report_writer.py` - `VulnerabilityReportWriter.save_report()`, mirroring
  `reachability.py`'s existing `JSONReportWriter` convention exactly.
- `app/tools/evasion.py` - `EvasionService` gained an optional, defaulted-to-`None`
  `browser_manager` constructor argument (every existing call site and test is unaffected). A
  confirmed path-traversal hit now triggers `capture_vulnerability()`; a capture failure is caught
  and logged **and surfaced in the returned result text itself** (not just `logger.warning()`,
  which is too easy to miss depending on logging config - the exact "no report at all, no visible
  error" symptom the user hit while testing this on the `IBRAHIM` clone before this port). A JSON
  evidence report is written and its path appended when at least one screenshot was captured.
- `app/tools/tool_registry.py` - `WSLBridgeTools` now owns one `BrowserManager` instance, passed
  into `EvasionService`; new `close_browser()`/`capture_vulnerability_screenshot()` delegates and
  a `"capture_screenshot"` registry entry.
- `app/core/agent/brain_tools.py` - new `Capture_Vulnerability_Screenshot` tool (18-tool list, up
  from 17), added to `ROLE_TOOL_PARTITIONS["exploiter"]`.
- `scripts/run_agent.py` - `run_brain_analysis()`'s `bridge` usage now runs inside `try/finally`,
  closing the browser once the run is unambiguously finished.
- `config/requirements.txt` - added `playwright` (Chromium's binary itself, `playwright install
  chromium`, remains a documented one-time local step).
- `scripts/diagnose_browser_manager.py` - standalone, offline-capable 4-step diagnostic (package
  import -> Chromium launch -> screenshot capture -> JSON report round-trip) with actionable fix
  messages. Live-verified in the assistant's own sandbox (no Chromium binary downloaded there):
  correctly caught `BrowserType.launch: Executable doesn't exist...` at step 2 and printed the
  exact fix (`playwright install chromium`).
- Tests: `tests/test_tools/test_browser_manager.py` (new, mocked Playwright) and new
  `TestAdvancedVulnProbeScreenshotEvidence` cases in `tests/test_tools/test_evasion.py`, alongside
  every pre-existing case, unchanged and still passing.

## Implemented specs/025 (subtask-level benchmark suite: SR/SCR/TTE + ablation) - found and fixed a real WSL-networking bug live (2026-07-23)

Implemented `specs/025-subtask-benchmark-suite` T001-T004/T006-T008/T010: `benchmarks/fixture_base.py`
(shared 4-file fixture contract), `benchmarks/runner.py` (`run_fixture()`/`run_suite()`,
SR/SCR/TTE scoring via a `TraceCaptureCallback` on `ArgusBrain.ask()`'s `on_graph_event` seam -
not `tool_call_history`, which the return value does not expose, a real gap in `plan.md`'s
original design found by reading `brain.py` directly), 4 fixtures (`info_disclosure_env_leak`
migrated from `tests/manual/ai_benchmark.py`'s scenario, fixing its hand-picked 2-tool-subset
gap with the real 17-tool `build_argus_tools()`; new `xss_reflected`/`idor_object_access`/
`ssti_template_injection`, all real in-process vulnerable logic - genuine
`jinja2.Template(...).render()` for SSTI, no Docker/`subprocess` needed), `benchmarks/tests/test_runner.py`
(10 unit tests, fake-LLM-via-`ArgusBrain`'s-own-`llm=`-seam convention, no live Ollama needed),
`benchmarks/README.md`.

A bounded live sanity run (real Ollama + WSL) found a real, previously-undiscovered bug shared
with the original `ai_benchmark.py`: fixture servers bound to `127.0.0.1` on the Windows host
are unreachable from inside the WSL/Kali guest where Argus's tools actually execute (confirmed
via `wsl -d kali-linux -- curl 127.0.0.1:<port>/.env` -> curl exit code 7, "failed to connect").
Fixed via `fixture_base.py`'s new `_wsl_reachable_host()` (resolves WSL's own default-gateway
IP live via `ip route show default` inside the guest, cached per-process, `127.0.0.1` fallback
if WSL is unavailable) plus rebinding all four fixture servers to `0.0.0.0`. A second live run
confirmed the fix: the agent reached the target via the resolved gateway IP, used real tools
(Nikto, subdomain enumeration, secrets analysis), and produced partial credit (SCR 0.33, found
`/.env`) - a genuine baseline data point about this model's behavior, not a wiring failure
(Constitution VIII: reported honestly, not smoothed over).

`tests/manual/ai_benchmark.py` removed (T008) once the migrated fixture's wiring was confirmed
correct end-to-end; its `tests/manual/README.md` entry removed with it.

T005 (full 4-fixture baseline) and T009 (ablation once `enable_inter_reflection` is toggled)
are unblocked but intentionally left for a human-scheduled run (`python benchmarks/runner.py`),
each being a 15-30 minute live-Ollama run per fixture per configuration.

Verified: `pytest benchmarks/tests/` 10/10 passing (no live Ollama needed); two live sanity
runs against real Ollama/WSL, both completed without crash/hang/timeout.

**Update same day**: ran T005 (full 4-fixture baseline) and T009 (ablation) live.
Baseline: SR 0/4, mean SCR 0.33 - the agent consistently found the right endpoint on every
fixture but didn't complete extraction/reporting on any of them, a genuine capability gap
this suite now makes visible rather than a harness defect. Ablation (`baseline` vs.
`no_inter_reflection`): `019`'s reflection helped directionally (mean SCR 0.33 vs. 0.25) -
the project's first real Table-6-shaped ablation result, though SR stayed 0/4 both ways and
per-fixture SCR varied noticeably run-to-run (real local-7B-model ReAct variance, not a
scoring bug) - treat as directional signal on this 3-new-fixture set, not a settled result.
Reports: `benchmarks/results/20260723T143037Z_report.md`,
`benchmarks/results/20260723T144350Z_report.md`.

**Second update same day**: added a 5th fixture (`path_traversal_download` - real
filesystem-backed path traversal in a private temp sandbox, no simulation) and re-ran the full
baseline+ablation suite across all 5 fixtures
(`benchmarks/results/20260723T150717Z_report.md`). This time `baseline` and
`no_inter_reflection` scored **identically** (SR 0/5, mean SCR 0.33 both) - the earlier
ablation run's directional signal (0.33 vs. 0.25) did not replicate. Reported plainly rather
than keeping only the more flattering first result (Constitution VIII): at this suite's
current scale, `enable_inter_reflection`'s measured effect is not yet distinguishable from
this local 7B model's own run-to-run ReAct variance. All three reports are kept on disk
(FR-005 - every run kept, not just the latest).

## Fixed the mypy errors surfaced by merging specs/020's core-agent code onto current main (2026-07-19)

Merging `specs/020` (below) into today's `main` required rebasing every touched file onto
substantial independent history (the SALMA merge, mypy/docstring passes, this session's own
knowledge-graph and archive-cleanup work) rather than a blind overwrite - verified via `git log
<base>..main -- <path>` per file, not assumed safe from a clean `git merge-tree` alone (which
would have missed a real conflict in `specs/022/spec.md` caught the same way earlier in this
session). One real textual conflict in `brain.py`'s graph-construction call site, resolved by
hand. Two new mypy errors (`planner_node`/`summarizer_node` passing the `ArgusAgentState`
TypedDict directly to prompt builders typed as plain `dict`) fixed using the exact `{**state,
...}` dict-literal pattern `_run_specialist_step` already used successfully elsewhere in the same
file, not a new workaround. Verified: 336/336 pytest, ruff clean, mypy clean (CI's exact 10-file
list), both the default and flagged graph-construction paths smoke-tested directly against a fake
LLM/tool set.

## Implemented specs/020 (multi-agent role separation) as an experimental, feature-flagged-off path - measured, not promoted to default (2026-07-11)

Recovered from uncommitted work (`wip/multi-agent-role-separation`, preserved and merged onto
current `main` on 2026-07-19 - see the entry above for that merge's own details) and landed here
in its original, still-accurate form:

User proposed starting `specs/020` (Planner/Collector/Exploiter/Summarizer role separation),
initially as a heavier multi-*model* design (Dolphin-Llama3 as Coordinator, DeepSeek-Coder as
Exploit Analyst, an abliterated Llama-3-8B as Verifier). Researched that specific proposal before
building anything: this machine's actual VRAM (confirmed via `nvidia-smi`: 16GB total, RTX 2000
Ada) can't hold more than ~2 of those 7-8B models resident at once, making 4-model swapping a
real, unmeasured latency risk, not the "close to one 33B model" the proposal assumed;
abliteration measurably regresses TruthfulQA specifically (-7.1, other benchmarks near-unchanged)
- the wrong tradeoff for a Verifier role whose entire job is judging true vs. false findings;
and recent research ("Persona-Pruner") shows the field moving toward extracting multiple personas
from one dense model rather than deploying several full models - validating `specs/020`'s
original FR-001 scope (one shared model, role-scoped prompts/tools) over the heavier alternative.
Full findings + sources in `specs/020-multi-agent-role-separation/research.md`'s 2026-07-11
addendum. User approved proceeding with FR-001 exactly as originally scoped.

Implemented:
- `app/core/agent/react_prompts.py`: 4 new role-scoped prompt builders (`build_collector_prompt`,
  `build_exploiter_prompt`, `build_planner_prompt`, `build_summarizer_prompt`).
- `app/core/agent/brain_tools.py`: `build_argus_tools(bridge, role=...)` plus new
  `ROLE_TOOL_PARTITIONS` (the single source of truth for FR-002's tool split - Collector gets
  recon/discovery tools, Exploiter gets scanning/exploitation tools, Planner/Summarizer get only
  read-only `Query_Memory`/`Query_Knowledge_Graph`) and `partition_tools_by_role()` (so
  `ArgusBrain`, which only holds the flat tool list and no `WSLBridgeTools` reference, gets the
  identical split without rebuilding tools from a bridge).
- `app/core/agent/react_state.py`: `current_role`/`role_history` fields, `NotRequired` so the
  production single-loop graph is unaffected.
- `app/core/agent/react_workflow.py`: new standalone `_build_multi_role_workflow()` - `planner`
  makes a structured routing decision (new `_PlannerDecision`/`_try_planner_decision`, mirroring
  `_try_structured_action`'s exact schema-constrained-decoding-first pattern) -> `collector`/
  `exploiter` each execute exactly one tool call per visit -> back to `planner` -> ... ->
  `summarizer` (terminal). Deliberately a standalone graph, not a generalization of the
  production `_build_custom_workflow`'s closures, so the proven single-loop path stays provably
  unaffected regardless of this experimental path's behavior - `_parse_react_output` was safely
  extracted to module level first (a pure function, zero behavior change; full suite re-verified
  green before building on top of it) so both graphs share it without duplicating the parsing
  logic.
- `app/core/agent/react_workflow.py` also gained `_extract_vulnerability_hints()` - a separate,
  always-active (not behind the `enable_multi_agent_roles` flag) deterministic scan of tool
  results for page-title/keyword vulnerability signals, injecting an explicit Reflection nudge.
  Applies to the production `_build_custom_workflow` path too. Research-backed
  (arXiv:2606.16364 - prompt-only fixes recover at most ~23% of this tool-selection failure
  mode), same nudge-message mechanism `_check_early_termination` already uses. Confirmed with the
  human before including, since it is a real production-behavior change bundled into the same
  file as the flagged-off specs/020 work, not itself part of specs/020.
- `config.yaml`/`config.py`: `enable_multi_agent_roles` flag, default `false`. 22 new tests across
  `tests/test_agent/{test_react_prompts,test_brain_tools}.py`, `tests/test_agent/
  test_langgraph_workflow.py`.

**NFR-001 measurement** (`tests/manual/specs020_wallclock_comparison.py`, mocked but fixed
per-call latency so the comparison isolates orchestration overhead from inference-time noise): on
an equivalent-effort scenario (2 real tool calls, then a report), the multi-role graph took
**2.00x the LLM calls** of the single-loop graph (6 vs. 3) - structural, not scenario-specific,
since every Collector/Exploiter action pairs with one Planner routing decision in this topology.
Converted to this project's own already-measured *real* per-call latency (**10.96s** average for
a real WhiteRabbitNeo-V3-7B ReAct call): the same 2-tool-call scenario would cost single-loop
3 x 10.96s ~= 33s vs. multi-role 6 x 10.96s ~= 66s - a real ~33s of added latency for just 2 tool
calls, compounding further over the 5-10-tool-call runs typical of live testing.

**Honest result: borderline, lands exactly at NFR-001's own pre-agreed 2x rollback threshold, not
clearly under it.** Not promoted to default (`enable_multi_agent_roles` stays `false`).

## Fixed false "unreachable" on WAF/CDN-fronted targets, wired PayloadsAllTheThings into Advanced_Evasion_Probe, and gave RAG real security content (2026-07-10)
User asked to test against a real PortSwigger Web Security Academy lab, then asked to wire
`Advanced_Evasion_Probe` up to PayloadsAllTheThings automatically and "make use of RAG." Three
real, live-verified changes:

**1. `check_reachability()` false-DOWN on ICMP-blocked-but-HTTP-live targets.** Live-discovered
against the actual PortSwigger lab URL: `curl` independently confirmed `HTTP_CODE:200`, but
`Check_Reachability` (ping-only) reported it DOWN and the agent gave up immediately - the same
root cause the 2026-07-07 entry already fixed for `recon_suite`'s nmap scan (WAFs/CDNs/load
balancers routinely drop ICMP while still serving HTTP), but `check_reachability()` never got the
equivalent fix. Now falls back to a direct HTTP(S) `curl` probe (trying the opposite scheme too,
matching `run_nikto`/`run_ffuf`'s existing scheme-retry pattern) when ping gets no reply. New
tests in `tests/test_tools/test_reachability.py` (3 new, 8 total). Live-reverified: the same
PortSwigger lab now correctly reports `"REACHABLE (ICMP blocked, confirmed via HTTP HTTPS -
status 200)"` and the run proceeds into real recon - `Recon_Suite`'s tech fingerprint even
captured the lab's actual page title, `Title[File path traversal, simple case...]` (PortSwigger
names the vulnerability class directly in the title). Honest follow-up finding: the model never
acted on that signal - it ran a generic Nikto scan instead, which came back inconclusive, and
produced a Final Answer without ever calling `Advanced_Evasion_Probe`. Nothing in the current
prompt tells the model to specifically watch for and act on a strong signal like a page title
naming the vulnerability class - tracked as a new open follow-up.

**2. `Advanced_Evasion_Probe` wired to PayloadsAllTheThings.** Researched first: confirmed
PayloadsAllTheThings ships a dedicated `<Category>/Intruder/` subfolder per vulnerability class
with plain one-payload-per-line wordlists (built for Burp Intruder/ffuf) - far more reliable to
parse than scraping `README.md` prose/code-fences the way `suggest_payloads()` already does.
Verified live in Kali WSL: `Directory Traversal/Intruder/dotdotpwn.txt` (21k+ real payloads,
confirmed plain `../../../etc/passwd`-style entries) and `SQL Injection/Intruder/Generic_ErrorBased.txt`
(154 lines, real payloads) both exist and match. New `fetch_intruder_payloads()` in
`app/tools/payloads.py` samples a small, bounded (`limit=4`) random subset via `shuf -n N` and
merges it (deduplicated) into `advanced_vuln_probe()`'s existing static lists - fails soft (`[]`)
if the local mirror or file is missing, so a fresh install without it behaves exactly as before,
never worse. New `tests/test_tools/test_payloads.py` (6 tests) plus 2 new tests in
`test_evasion.py`.

**3. RAG given real security content.** The only knowledge-base document
(`argus_security_knowledge.md`) was 100% self-referential Argus architecture description - zero
actual exploitation knowledge - and even that description was stale (still described the
pre-specs/017 `AgentExecutor`/`SimpleChain` path). Corrected the stale line; added new
`knowledge_base/exploitation_techniques.md` with real, public OWASP/PayloadsAllTheThings-class
methodology (traversal OS-target selection and bypass encodings, SQLi WAF-evasion techniques,
verification pitfalls/false-positive patterns, guidance on chaining a confirmed finding further)
so the RAG fusion that already runs on every `ask()` call actually retrieves something relevant
to pentesting reasoning.

Full suite after all three changes: **272 passed**, 1 pre-existing unrelated failure (same
DuckDuckGo network flake observed since CHK082).

## Fixed advanced_vuln_probe's Path Traversal detection - Linux payloads + real content verification instead of HTTP-status-only (2026-07-10)
User asked whether Argus could handle a real PortSwigger Web Security Academy lab, then recalled
the project used to handle Path Traversal specifically. Investigated rather than assumed: the old
node-graph pipeline's historical `path_traversal` probe (referenced in the 2026-07-07 CHANGELOG
entry) did run as part of a reflective retry loop, but that specific live run came back
`exploit_success: false` (an honest negative against a target - `example.com` - with nothing to
traverse anyway) - so the memory of "it used to work" wasn't quite accurate, but it pointed at a
real, separate, currently-live gap worth fixing.

`app/tools/evasion.py::advanced_vuln_probe()` - the actual tool the current agent calls to attempt
exploitation - only ever tried Windows/IIS-style `web.config`, never Linux's `/etc/passwd` (what
PortSwigger's own labs, and most real-world Linux-hosted targets, actually test), and judged
success by bare HTTP status (`200` for traversal, `500` for SQLi) alone - both a false-negative
risk (wrong file for the OS) and a false-positive risk (any 200 response "succeeds"). Meanwhile
`app/tools/reflective_verification.py::post_execute_verify()` already had a real, content-
signature-based verifier (checks for `root:x:0:0:`, `DB_PASSWORD`, `uid=`, etc. actually appearing
in the response body) sitting on `WSLBridgeTools` but never exposed as a callable tool to the
ReAct agent - a legitimate verification mechanism going unused right next to a weaker one that was
active.

Fixed:
- Extracted the indicator dict into a shared `SENSITIVE_CONTENT_INDICATORS` constant in
  `app/tools/utils.py` (previously duplicated only inside `reflective_verification.py`;
  Constitution IX - one place now, not a soon-to-drift second copy).
- `advanced_vuln_probe()` now fetches real response bodies (not `-o /dev/null` status-only) and
  checks them against that dict; added Linux `/etc/passwd`-style traversal payloads (plain,
  URL-encoded, and dot-slash-obfuscated variants) alongside the original Windows ones.
- SQLi check extended to also look for real SQL-error text in the response body, not just a bare
  `500` status.
- New `tests/test_tools/test_evasion.py` (no prior coverage existed for this module) - 6 tests.
  Full suite: **262 passed**, 1 pre-existing unrelated failure (the same DuckDuckGo network flake
  observed since CHK082).

Live verification: stood up a mock vulnerable server *inside* WSL Kali itself (serving real fake
`/etc/passwd` content, confirmed reachable via `curl` first - deliberately avoiding the WSL-to-
Windows-host networking gap a prior local-mock attempt hit). The live agent run reached
`Run_Nikto` first, got an inconclusive-but-nudge-satisfying result, and produced a Final Answer
without ever calling `Advanced_Evasion_Probe` - an honest negative, not a bug: the PHASE 5/6
enforcement only requires *at least one* of Nikto/FFUF/Exploit_Suggester/Advanced_Evasion_Probe,
not all four. The fix itself is verified by the 6 new unit tests; observing it fire inside a live
non-deterministic agent run remains an open follow-up (same status as the still-open PHASE 7
live-chaining verification below).

Also clarified, on request, how `Exploit_Suggester` (PayloadsAllTheThings-backed) and RAG actually
relate to `Advanced_Evasion_Probe`'s payload list - confirmed live via WSL `ls` that
`/opt/payloads/PayloadsAllTheThings/` is a real local mirror and all 8 of `payloads.py`'s
vulnerability-type mappings resolve correctly. But `Exploit_Suggester` only returns research text;
it has no automatic pipeline into `Advanced_Evasion_Probe`'s hardcoded payload list, and RAG's
actual content (`knowledge_base/argus_security_knowledge.md`, 58 lines - a general architecture
summary) is not a payload source at all. Wiring these together was proposed as a follow-up, not
yet implemented.

## Restored PHASE 7 (Chaining & Escalation) and raised max_iterations 15 -> 25, on top of specs/018/019's reliability fixes (2026-07-10)
User recalled that the old, pre-specs/018 agent (`app/core/prompts.py` + `agent_factory.py`'s
classic `AgentExecutor`, `max_iterations=50`, free-text parsing, a 9-phase prompt) used to run for
roughly an hour producing results, and asked why current runs are shorter. Investigated honestly
instead of assuming either "old was better" or "old was fine as-is": the old system's long
runtimes were often the exact failure-retry loop specs/018's own incident proved (CHK070 - a real
900s/26-retries/zero-results run against `cultbeauty.co.uk`, caused by the model repeating
malformed non-ReAct output forever), not necessarily extra thoroughness. But a real, separate
tradeoff also exists: the current 7-phase prompt has no analogue of the old template's "Chaining &
Escalation" phase, and `DEFAULT_MAX_ITERATIONS=15` left little headroom for one even if added.

User approved restoring that depth **on top of** (not instead of) the reliability work already
in place, and set a standing project direction: `docs/history/2603.27127v1.pdf` (the Red-MIRROR
paper) is a continuing reference for the rest of this project's development, not a one-time gap
analysis - recorded durably in `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md` (new paragraph after the
canonical-reconciliation note) and `specs/checklist.md`'s Backlog section header.

Changes:
- **`app/core/agent/react_prompts.py`**: added **PHASE 7 (Chaining & Escalation)** between the
  existing Exploitation and Final Analysis phases - if Phase 4-6 confirmed anything exploitable
  (leaked credentials, a working injection, an exposed config/backup file), the agent is now
  instructed to chain further via `Run_Kali_Command`/`Secret_Scanner` (e.g. try leaked creds
  against a discovered login endpoint, fetch and read a discovered backup file, rescan whatever
  that exposes) instead of stopping at the first confirmation - explicitly skippable when Phase
  4-6 found nothing to chain from. Deliberately does **not** reference `Run_Specialized_Module`
  (the old template's Phase 7/8 tool) - confirmed absent from `brain_tools.py`'s real tool list
  via `grep 'name="' app/core/agent/brain_tools.py` before writing a single line of prompt text,
  so the restored phase only points at tools that actually exist today. Final Analysis renumbered
  PHASE 7 -> PHASE 8.
- **`app/core/agent/brain.py`**: `DEFAULT_MAX_ITERATIONS` raised 15 -> 25, so PHASE 7 has room to
  actually execute a multi-step chain without reverting to the old system's unreliable
  50-iteration free-text ceiling. Verified `PHASE_5_6_TOOLS`/`EXPLOITATION_TOOLS` enforcement
  (specs/019) is keyed on tool-name sets, not prompt phase numbers, before changing the numbering
  - no other code needed updating for the renumbering to be safe.
- **`tests/test_registry/test_react_prompts.py`**: existing `PHASE 7` assertion moved to
  `PHASE 8` (Final Analysis's new number); new
  `test_includes_chaining_and_escalation_phase` locks in PHASE 7's real-tools-only content.

Verification:
- Full suite: **256 passed**, 1 pre-existing unrelated failure
  (`test_smart_web_search.py::test_attempt_limit` - a real-network DuckDuckGo call returning no
  results in this sandbox, first observed at CHK082/085, unrelated to this change).
- Live-reverified against `https://scanme.nmap.org`: 5 clean steps, zero repeated/malformed
  output (no regression to the old failure-retry loop that motivated specs/018 in the first
  place); the PHASE 5/6 nudge correctly forced a `Run_Nikto` attempt before allowing a Final
  Answer; Inter-reflection's majority vote fired on that result
  (`INCONCLUSIVE/NO FINDING`); since Nikto found nothing actually exploitable (only an outdated
  Apache version - no CVE/injection/leaked credentials), the model correctly did **not** force
  PHASE 6/7 further, matching PHASE 7's own "skip only if nothing to chain from" instruction.
  This particular run didn't exercise PHASE 7's chaining path itself, since this target has
  nothing to chain from - that remains to be observed live on a future authorized target that
  actually has a confirmed vulnerability worth chaining (tracked in `specs/checklist.md` CHK109).

## Enforced config.yaml as the single source of truth - audited every config-like value in the codebase (2026-07-10)
User asked, after watching a `similarity_threshold` value need manual syncing across 3 files
earlier today, to make `config.yaml` genuinely the one authoritative source everywhere -
not something several independent hardcoded defaults merely happen to agree with. Ran a
dedicated audit (Explore agent, every `RAGConfig(...)` construction site plus every
config.yaml-shadowing value project-wide) before changing anything.

Findings, categorized:
- **Already correct** (no drift risk): production `ArgusBrain` (`brain.py`), `scripts/run_argus_cli.py`,
  `scripts/run_agent.py`, `LAUNCH_STUDIO.bat`, and the RAG subsystem's own internals
  (`document_processor.py`/`rag_engine.py`/`vector_store.py`/`embeddings.py`) all correctly
  resolve through `ArgusConfig.load()` / `RAGConfig.from_central()`.
- **Confirmed real drift, fixed**:
  - `scripts/test_rag.py` constructed `RAGConfig(...)` directly (bypassing config.yaml for
    `chunk_size`/`retriever_k`/`similarity_threshold`/`knowledge_base_dir` entirely) and
    hardcoded the *old* Ollama-tag-style model name (`WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest`),
    disagreeing with config.yaml's current GGUF-tagged `model_name`. Now uses
    `RAGConfig.from_central()` and `ArgusConfig.load().model_name`.
  - `scripts/TEST_ARGUS.bat`'s "LLM Model Test" menu option hardcoded the same stale model name -
    would have silently tested a different model than whatever config.yaml actually points
    `ArgusBrain` at. Now reads `ArgusConfig.load().model_name`.
  - `tests/manual/ai_benchmark.py` - same stale hardcoded model name, same fix.
  - `Setup/Step_2_AI_Python_Env.bat` (legacy manual-fallback installer, auto-archived to
    `Setup_legacy/` after a normal `ARGUS_INSTALLER.ps1` run) had the old model name as its
    pull-time default - a fresh install via this fallback path would have downloaded a
    *different* model than config.yaml expects `ArgusBrain` to use at runtime. Corrected to
    match `ARGUS_INSTALLER.ps1`'s (the primary installer's) already-correct default.
  - **`app/tools/command_runner.py::DEFAULT_COMMAND_TIMEOUT`** - confirmed via grep that
    `ArgusConfig.command_timeout_seconds` (`600` in config.yaml) was **read nowhere in the
    entire codebase** - every real `.run(..., timeout=N)` call site hardcodes its own
    tool-specific value (deliberately left untouched - nmap's 180s vs DNS's 20s are
    well-tuned per-tool bounds, not something a single global setting should override), so
    `command_timeout_seconds` was dead configuration with no effect whatsoever. Wired
    `DEFAULT_COMMAND_TIMEOUT` to read it (with a `180` fallback only if `ArgusConfig.load()`
    itself fails) - this is exactly the fallback used when a caller passes no `timeout=` at
    all (e.g. `subfinder`/`assetfinder` in `recon.py`, `apt-get install` in `self_heal.py`,
    raw `Run_Kali_Command` passthrough), so config.yaml's declared 600s now actually governs
    that fallback instead of being silently overridden by a hardcoded 180.
- **Deliberately left alone**: `tests/manual/verify_parsing_fix.py` also has the stale model
  name, but its own docstring already documents the whole script as testing a `use_react`
  mechanism that no longer exists on `ArgusBrain` at all (historical reference only) - fixing
  just the model name would misleadingly polish a script whose core logic is already dead.
  `app/tools/wsl_bridge.py::WSLConfig` (`WSL_HOST`/`USER`/`PASS`/`PORT`/`DISTRO` via `.env`) is
  an intentional exception, not drift - confirmed `config.yaml` has no WSL section at all, and
  `.env.example` already documents these exact 5 vars; `WSL_PASS` being a credential is a
  legitimate reason to keep this split (secrets don't belong in a checked-in yaml).

Verified live: `command_runner.py` imports cleanly and reports `600` (not the old `180`);
`scripts/test_rag.py --smoke --no-llm` still works after switching to `from_central()` -
and, as a side effect of the still-fresh `similarity_threshold` fix (previous entry), now
actually retrieves and prints a real chunk, where it previously always returned nothing. Full
suite: 255 passed, 1 pre-existing unrelated failure.

## Fixed RAG's similarity_threshold default - it was silently rejecting every real match (2026-07-10)
Found while live-verifying the RAG source-attribution feature (previous entry): querying the
real `nomic-embed-text` + FAISS pipeline with a question that directly matches the knowledge
base's own content returned **zero** chunks - not because nothing was relevant, but because the
closest real match scored 0.643 (FAISS L2 distance) against a `similarity_threshold` default of
0.5, with the rest of the document's chunks scoring 1.0-1.08. The threshold rejected even the
most topically relevant chunk available. This means RAG had been silently contributing zero
context to every live run this session (and likely long before) - `_enrich_with_rag()`'s
`if combined:` branch never printed `[BRAIN] Fusion context...` because `combined` was always
empty, with no error or warning to indicate why.

User confirmed raising the default to 0.7 (admits the 0.643 real match, still rejects the
clearly-unrelated ~1.0+ chunks) after reviewing the actual measured score distribution. Updated
the 3 places this default is declared: `config.yaml`, `app/core/config.py::RAGSettings`,
`app/core/rag/config.py::RAGConfig`. Verified live with the real, un-overridden production
default (not a test override): the same query that returned nothing at 0.5 now correctly
retrieves and attributes `argus_security_knowledge.md`. Existing tests that pin their own
explicit `similarity_threshold` values (`tests/test_rag/test_rag_engine_threshold.py`) are
unaffected by the default change. Full suite: 255 passed, 1 pre-existing unrelated failure.

## Restored RAG source attribution - which knowledge_base/ documents a run actually used (2026-07-10)
User recalled an old version showing which sources RAG actually retrieved and relied on during a
run, and asked to recover this. Investigated (Explore agent + independent verification): a
source-attribution UI genuinely existed once - `app/core/rag/rag_gui.py` (commit `8e16cd4`,
`st.expander(f"Raw JSON {index} | Source: {source}")`) - but only on a teammate's side branch
(`origin/argus/MOUSTAFA-PC`) that was never merged into mainline (`git merge-base
--is-ancestor` confirmed it is not an ancestor of HEAD). In current mainline,
`RAGResult.sources` existed in `rag_engine.py` but `ArgusBrain._enrich_with_rag()` only ever
called `format_combined_context()` (which returns a flattened string), never `query()` (which
populates `.sources`) - so the data was computed nowhere reachable and then simply never
existed downstream. Separately confirmed `knowledge_base/` currently holds only
`argus_security_knowledge.md` (no PayloadsAllTheThings content) - the user's memory likely also
conflates this with `app/tools/payloads.py::PayloadSuggester`, an unrelated, non-RAG tool that
also self-labels `"Source: PayloadsAllTheThings (Local Mirror)"` via a live grep against Kali's
filesystem.

Implemented without duplicating the retrieval call: `format_context()` (called inside
`format_combined_context()`) already tags each retrieved chunk `[Source: <basename>]` in the
fused prompt text - `_enrich_with_rag()` now extracts those tags via regex from the string it
already computes, storing them as `self._last_rag_sources` (deduped, order-preserved). Added
`SecurityReport.sources_used: List[str]` (`app/core/schemas.py`, `default_factory=list`,
explicit field description noting it's Argus-populated, not model-generated). New
`ArgusBrain._attach_rag_sources()` overwrites `output["sources_used"]` with the real list after
the final report is built (structured-decoding path and the Pydantic/regex-JSON fallback path
both covered; a no-op when RAG contributed nothing, or when there's no report dict to attach
to). Also emits a `"Reflection: retrieved knowledge base sources: ..."` graph event when
sources are found, so `ConsoleTraceCallbackHandler` (added earlier today) and the GUI's live
feed both surface it live, not just in the final JSON.

6 new tests (`tests/test_registry/test_brain_ask.py`): sources attach to the final report,
dedup with order preserved, `sources_used` stays `[]` when RAG contributes nothing, and the
live-feed event fires with the right content - using a `_FakeRagEngine` returning a fixed
`[Source: ...]`-tagged string (no real FAISS/embedding backend needed). Full suite: 255 passed,
1 pre-existing unrelated failure.

## Fixed a real crash in RAGEngine.add_document() found while auditing scripts/ (2026-07-10)
While reviewing whether `scripts/test_rag.py` was still useful (part of a `scripts/` cleanup
pass), running it (`--smoke --no-llm`) crashed: `AttributeError: 'list' object has no attribute
'page_content'`. Root cause: `DocumentProcessor.load_file()` returns `Optional[List[Document]]`
(one input file can legitimately produce multiple Document chunks - markdown split by headers,
CSV split row-by-row, per `document_processor.py`'s structural chunking design) but
`RAGEngine.add_document()` wrapped that already-a-list return value in a *second* list
(`splitter.split_documents([doc])`) before passing it to `split_documents()`, which expects
`Iterable[Document]` - it iterated once and got the inner list itself where it expected a bare
`Document`, crashing on `.page_content`. This code path had zero existing test coverage.

Fixed to `splitter.split_documents(docs)` (no extra wrapping) and `if not docs:` (handles both
`None` and an empty list) instead of `if doc is None:`. Added 4 new regression tests in
`tests/test_rag/test_add_document.py` (ingesting a real markdown file, a CSV that splits into
multiple Documents - the exact shape that exposed the bug, an unsupported extension, and a
missing file), following the existing `_FakeVectorStore`/mocked-embeddings pattern from
`test_rag_engine_threshold.py`. Verified live: `scripts/test_rag.py --smoke --no-llm` now
completes successfully instead of crashing. Full suite: 247 passed, 1 pre-existing unrelated
failure.

## Enforced Rule 5 (attempt Phase 5/6 before concluding) structurally instead of leaving it advisory-only (2026-07-10)
User asked why a live run only used 3 of 17 tools (Check_Reachability, Subdomain_Enumeration,
Recon_Suite) then gave a Final Answer. Root cause confirmed by reading `react_workflow.py`
directly: `if re.search(r"Final Answer:", content): return {"phase": "done"}` accepts a Final
Answer completely unconditionally - `react_prompts.py`'s Rule 5 ("attempt Phase 5/6 before
concluding") is advisory text the model isn't required to follow, the same category of problem
`019`'s duplicate-call blocking was written to fix for a different rule.

Added a one-time structural nudge (not a hard block - forcing a scan against a target with no
reachable web service would be pointless): when a Final Answer appears with at least one tool
already called but none of `Run_Nikto`/`Run_FFUF`/`Exploit_Suggester`/`Advanced_Evasion_Probe`
(`PHASE_5_6_TOOLS`) among them, `parse_node` now returns `phase="phase56_check"` instead of
accepting it, with a message telling the model to either try one of those tools or explicitly
justify skipping them; a new `phase56_nudged` state flag ensures this fires at most once per
run. `route_after_parse` treats `phase56_check` like `format_error`/`duplicate_call` - bounded
by `max_iterations`, same safety net.

This is a genuine behavior change, not just an addition - it broke 8 pre-existing tests that
reasonably expected a Final Answer to be accepted on the first attempt after a non-Phase-5/6
tool call. Fixed each by adding one more mock LLM response (absorbing the one-time nudge) and
updating the affected iteration/message-count assertions, rather than weakening the new check to
avoid touching them. 3 new dedicated tests confirm: the nudge fires exactly once for a
non-Phase-5/6 run, never fires when a Phase 5/6 tool was used, and never fires for a
zero-tool-call Final Answer (a different, broader problem, out of scope here). Full suite: 243
passed, 1 pre-existing unrelated failure.

## Repo-wide organization pass: real duplicate GUI apps, a real nikto naming bug, and 7 docs consolidated into 1 (2026-07-10)
User asked for a full pass so files/folders are useful and correctly organized rather than
having many discrepancies. Ran a dedicated audit (Explore agent across root/`docs/`/`app/`/
`scripts/`/`tests/`) first, then independently verified every claim before acting - two of the
audit's own claims turned out to need correction (found while verifying, not assumed): `app/
modules/`'s files looked near-empty in one `ls` pass but a `find` confirmed all 7 tactical
module files are genuinely present; `desktop_gui.py` was initially grouped with the GUI
duplicates but is a legitimately distinct Tkinter fallback (different framework, not a
Streamlit duplicate) and was left alone.

Presented 4 concrete decisions to the user before touching anything (GUI duplicates: delete vs.
shim; `tests/` ad hoc scripts: delete vs. relocate; `docs/history/` overlapping docs: merge vs.
leave; `data/argus_intelligence.db` git tracking: stop vs. leave) - executed per the user's
choices:

- **Real bug** (not just clutter): `app/GUI/{app.py, argus_gui.py, gui_main.py}` were not the
  "deprecation shims" this project's own architecture docs claimed - each was a full,
  independently-running 90-180-line Streamlit app with its own hardcoded, drifted tool list (12,
  3, and 9 tools respectively, none matching the canonical 17-tool `brain_tools.py` list;
  `gui_main.py` additionally hardcoded a stale model name bypassing `ArgusConfig` entirely).
  Converted all 3 to true one-line re-export shims matching `studio.py`'s existing pattern.
  `desktop_gui.py` left alone (genuinely distinct Tkinter fallback, not a duplicate).
- **Real bug**: `app/tools/scanners.py::run_nikto()`'s Nikto `-o` output path already had a
  `.txt` suffix, but Nikto's own `-Format txt -o <path>` appends `.txt` itself regardless -
  confirmed via real `reports/nikto/*.txt.txt` files on disk. Fixed both the primary and
  fallback command construction; new regression test in `tests/test_tools/test_scanners.py`.
- Created `tests/manual/`, moved 6 ad hoc/non-pytest scripts into it (`verify_core.py`,
  `check_integration.py`, `ai_benchmark.py`, `exploit_test.py`, `test_cd.bat`, and
  `docs/history/verify_parsing_fix.py`). Fixed `verify_core.py`'s broken pre-reorg import
  (`ModuleNotFoundError: No module named 'core'`, confirmed live) and a **real bug the move
  itself would have introduced**: `ai_benchmark.py`'s relative path bootstrap needed one more
  `..` for its new, one-level-deeper location - confirmed via direct invocation
  (`ModuleNotFoundError: No module named 'app'` before the fix, clean run after). New
  `tests/manual/README.md`.
- Consolidated 7 separate `docs/history/` writeups of the single 2026-06-25 "Invalid Format:
  Missing 'Action:'" incident into one chronological file. Found in the process that the
  original audit's "6 overlapping files" both over- and under-counted: `STREAMLIT_JAVASCRIPT_FIX.txt`
  (in the audit's list) documents an unrelated browser-cache issue, left alone; `QUICK_START_FIX.txt`
  and `TESTING_JSON_FIX.md` (not in the audit's list) turned out to document the same incident -
  the real count was 7. The consolidated file explicitly connects this incident's confident,
  tested-at-the-time claims to `specs/018`'s later finding (2 weeks afterward) that the exact
  fallback mechanism it describes never actually worked - preserved as a documented lesson.
- Low-risk fixes applied alongside: `scripts/TEST_ARGUS.bat`'s dangling `CHECK_HEALTH.bat`
  reference (file never existed) replaced with a real call into `self_heal.py`'s existing
  health-check logic; deleted a stray untracked zip in `artifacts/`; moved the self-labeled-legacy
  `ARGUS_TECHNICAL_ARCHITECTURE_v1.5_LEGACY.md` into `docs/history/`; renamed
  `scripts/test_agent.py` (misleadingly named - it exercises the superseded `010` graph, not
  current production) to `scripts/diagnose_legacy_tactical_graph.py`.
- `data/argus_intelligence.db`'s git-tracked status left unchanged per explicit user decision.

Verification: full `pytest tests/` re-run after every relocation/rename - 240 passed, 1
pre-existing failure (`test_smart_web_search.py`, already independently confirmed unrelated to
any work this session). `specs/checklist.md` (new "Repo Organization Pass" section, CHK101-108),
`docs/ARCHITECTURE_AUDIT_REPORT.md` (C3/C6 entries updated with real outcomes), `docs/README.md`,
and `scripts/README.md` all updated to match what's actually on disk now, not what was true
before this pass.

## Fixed docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md: it described deleted code as current (2026-07-10)
User asked to add specs/019's changes to the architecture doc. Found first: the doc itself
predates specs/013/017/018 entirely - Section 6.1's sequence diagram and Section 5.3's component
diagram still described `use_react`/`brain_v2.py`/`_get_react_agent()`/`_get_simple_chain()`,
the exact non-functional dual-path `018` proved never worked (both branches called the identical
`AgentExecutor`) and deleted. ADR-15 still claimed the `010` LangGraph node graph was "the
production agent," contradicting this project's own `docs/ARCHITECTURE_AUDIT_REPORT.md`, which
already documented `010` as superseded by `017`. Adding `019`'s info on top of this would have
made the document more self-contradictory, not more accurate - asked the user how to proceed;
they chose a full refresh over `017`/`018`/`019` together.

Rewrote: Section 5.1 (Core Components - added `react_workflow.py`/`react_state.py`/
`react_prompts.py`/`react_callback.py` as the real reasoning-loop building blocks; clarified
`brain_tools.py`'s 17-tool ReAct list is distinct from and not the same as `WSLBridgeTools`'s
separate, unused-in-production generic `ToolRegistry` facade; flagged `app/modules/` as
confirmed-by-grep unreachable from `ArgusBrain`'s production path); Section 5.3 (component
diagram - removed `Agent_Factory_V2`/`brain_v2` nodes, added the real ones); Section 6.1
(complete rewrite of the sequence diagram - structured-output-first tool selection, `018`'s
target-extraction-ordering fix, `019`'s Intra-reflection/Inter-reflection/early-termination,
live-feed streaming via `on_graph_event`); Section 6.3 (context-fusion diagram - same ordering
fix + reflection notes block); Section 8 (Cross-Cutting Concepts - replaced the vague "Guided
Reflection"/"mandatory verification" language with `018`/`019`'s actual, distinct mechanisms);
Section 9 (corrected ADR-15's false "production agent" claim in place, rather than deleting the
historical record of the decision; added ADR-17/18/19 for `017`/`018`/`019`); footer.

Verification discipline for this pass specifically (per explicit user request to confirm, not
assume): every file path and function/class name written into the updated sections was checked
with `ls`/`grep` against the real codebase first - 18 files/paths confirmed to exist
(`react_workflow.py`, `react_state.py`, `react_prompts.py`, `react_callback.py`'s
`LiveFeedCallbackHandler.on_graph_event`, `brain_tools.py`, `agent_factory.py::build_agent_executor`,
`llm_factory.py::build_llm`/`build_chat_llm`, `graph.py`/`nodes/`, `app/modules/`'s 7 tactical
module files, etc.), and `019`'s own newly-added symbols (`EXPLOITATION_TOOLS`,
`_build_reflection_note`, `_inter_reflect`, `_check_early_termination`, `summarize_for_planning`,
`reflection_notes`, `enable_inter_reflection`) re-confirmed present by exact grep match.
Separately confirmed `brain_v2.py`/`agent_factory_v2.py` are genuinely absent - searched the
**entire repo**, not just `app/core/agent/`, to rule out them having moved rather than been
deleted. `app/core/agent/graph.py`/`nodes/` and all 7 files under `app/modules/` (including
`argus_reasoning.py`/`argus_deep_exploit.py`/`stealth_exploit.py`, initially miscounted as
near-empty by one `ls` invocation, corrected via `find`) are confirmed still present on disk -
retained per Constitution VII, legacy relative to `017`, not deleted.

## Closed out specs/019's two open tasks with real, measured data - live model, not assumptions (2026-07-10)
User asked to finish specs/019's remaining tasks (T013 live-cost measurement, T014
checklist/audit-report indexing) "after research and confirmation that we get the best
results." Confirmed Ollama + Kali WSL/SSH were actually live before measuring anything (not
assumed): model `hf.co/bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M` reachable,
`kali-linux` WSL distro running, SSH port 22 open.

**T013**: Deliberately did not run a full end-to-end scan comparison (`enable_inter_reflection`
on vs. off against a real target) - variable tool/network latency would dominate and confound
the specific question (what does the vote itself cost). Instead isolated the operation: 3
interleaved, warm-up-controlled rounds comparing one normal ReAct action-generation call against
one full `_inter_reflect()` 3x-vote call, same live model, same prompt shape. Result: single
call averaged **10.96s** (10.28/13.80/8.79s across rounds); `_inter_reflect()` averaged **0.82s**
(0.80/0.84/0.83s - notably consistent, unlike the single-call times). The 3x-vote is **~8% of a
single call's cost, not ~300%** as the spec's original NFR-002 worried - the vote prompt
constrains output to one word, and this model's decode time is bound by output token count, not
input size or round-trip count. `enable_inter_reflection=true` is confirmed safe as the default
by a real measurement, not left as an unverified assumption. Recorded in
`specs/019-shared-memory-reflection-upgrade/{spec,tasks}.md` and `specs/checklist.md` CHK099.

**T014**: `specs/checklist.md` gained a full "Phase 019" section (CHK091-100, mirroring the
detail level of every other completed phase) and its Backlog table's `019` row updated from
"Proposed" to "Implemented 2026-07-10". `docs/ARCHITECTURE_AUDIT_REPORT.md`'s traceability
matrix row for `019` updated the same way, including both implementation deviations from the
original plan (documented previously) and the T013 finding. `specs/019-shared-memory-reflection-
upgrade/tasks.md` now shows T001-T014 all complete.

## Implemented specs/019 (shared-memory + Dual-Phase Reflection upgrade) - first of the 8 backlog phases (2026-07-10)
User asked to web-validate the 8 backlog spec kits (see entry below), then to start implementing
`019` (lowest-risk, recommended first). Implemented:
- `ArgusMemory.summarize_for_planning(k=3, max_chars=3000)` (`app/core/memory/memory_service.py`)
  - a new, additive per-`(domain, tool_name)`-bounded aggregation method, adapting Red-MIRROR's
  SRMM `GetAggregatedContext` (Algorithm 2) to Argus's real schema. Deliberately did NOT modify
  `get_blackboard_summary()` itself as originally planned - reading its actual callers/tests
  before touching it found its exact `{domain: {data_type: summary}}` shape (one survivor per
  domain+data_type, no `tool_name`) is asserted verbatim by existing tests and consumed as-is by
  `Query_Memory`/TDA/GUI - changing it risked a real regression for no benefit the new method
  doesn't already provide. Also added an `f.id DESC` query tiebreaker after finding, while
  writing this method's own test, that same-microsecond timestamps under a tight write loop
  made "most recent" ambiguous.
- Structured Intra-reflection (`_build_reflection_note()`) replacing the previous generic "try
  something different" duplicate-call guidance with a response-aware suggestion (WAF-block,
  timeout, 404, 500 keyword heuristics) - `app/core/agent/react_workflow.py`.
- Inter-reflection (`_inter_reflect()`): 3x self-consistency majority vote (Wang et al., ICLR
  2023 - the same technique Red-MIRROR itself cites), scoped to `EXPLOITATION_TOOLS`
  (`Advanced_Evasion_Probe`, `Secret_Scanner`, `Run_Nikto`, `Run_FFUF`) via a new
  `enable_inter_reflection` config flag (default on, `config.yaml`/`app/core/config.py`).
- Early-termination flag detection (`_check_early_termination()`) - a nudge appended to the
  observation stream when a `flag{...}`-shaped string appears in a tool result, not a forced
  structural exit (`_finalize_graph_output()`'s "Final Answer:" requirement stays the single
  source of truth for completion, per Constitution VIII).
- Observability: reflection notes flow through `brain.py`'s existing per-message streaming loop
  as `"Reflection:"`-prefixed messages rather than requiring new callback plumbing threaded into
  `react_workflow.py`'s node functions (which don't currently receive callbacks at all -
  confirmed by reading `_emit_graph_step()` before implementing, differing from the original
  plan's assumption); `_emit_graph_step()` gained one new status branch (`"reflecting"`).

Verification: 18 new unit tests (13 in `tests/test_langgraph_workflow.py`, 5 in
`tests/test_memory.py`), all passing. Full regression: `tests/test_memory.py` +
`tests/test_langgraph_workflow.py` + `tests/test_registry/` = 91 passed, 0 failed. Full repo
suite = 239 passed, 1 failed (`test_smart_web_search.py::test_attempt_limit`) - confirmed via
`git stash` (re-running with today's changes fully reverted still fails identically) that this
is pre-existing and unrelated: a live-network-dependent test in a file this phase never touched.
`specs/019-shared-memory-reflection-upgrade/tasks.md` updated with per-task outcomes, including
the two implementation-detail deviations from the original plan above. Not yet done: T013 (live
wall-clock cost measurement, needs real Ollama/WSL) and T014's checklist/audit-report indexing.

## Added: 8 new Spec Kit backlog phases (019-026) from a Red-MIRROR paper gap analysis - planning only, no code (2026-07-10)
User asked to read and fully analyze `docs/history/2603.27127v1.pdf` ("Red-MIRROR: Agentic
LLM-based Autonomous Penetration Testing with Reflective Verification and Knowledge-augmented
Interaction," arXiv:2603.27127v1) and evaluate Argus completely against it - what actually
exists vs. what doesn't. Confirmed by direct file reads and grep against `app/`, not assumed:
Argus has no JWT/IDOR/Playwright/benchmark/ablation/RBAC code anywhere, a single-agent ReAct
loop (not the paper's 4-role multi-agent split), a real but unpartitioned/unbounded-by-source
Blackboard memory, and a real but minimally-populated RAG knowledge base. Genuine matches found:
the Windows-orchestrator/Kali-execution-via-SSH split matches the paper's own Section 4.2.1
setup, and `018`'s independently-arrived-at structured-output fix matches the paper's own stated
reason (parsing-noise reduction) for its measured gains over baselines.

Following up, user asked for a Spec Kit phase for each addable capability from the paper. Wrote
8 full spec kits (`spec.md`/`research.md`/`plan.md`/`tasks.md` each, all tasks unchecked - no
implementation started):
- `specs/019-shared-memory-reflection-upgrade/` - SRMM-style per-source bounded memory
  aggregation + Dual-Phase Reflection (structured intra-reflection, 3x-majority-vote
  inter-reflection), adapted to Argus's existing single-loop `ArgusMemory`/`react_workflow.py`.
  Lowest risk, recommended first - upgrades existing mechanisms, no new subsystem.
- `specs/020-multi-agent-role-separation/` - the paper's full Planner/Collector/Exploiter/
  Summarizer split. Explicitly flagged high-risk/optional: Argus's single-loop design was a
  deliberate `017`/`018` stability choice, and the paper's own ablation doesn't isolate how much
  of its gain comes from role-separation alone vs. SRMM/Reflection riding on top of it.
  Recommended to defer until `019` ships and its residual gap is measured.
- `specs/021-specialized-exploitation-toolkit/` - JWT attack, IDOR tester, file-upload
  exploiter, context-aware XSS fuzzer, SSTI/XXE code-injection tester - 5 new tools following
  the exact `(runner, memory)`/curl-with-timeout/`add_finding` pattern every existing tool
  already uses, independently shippable per tool.
- `specs/022-browser-automation-playwright/` - closes a real, demonstrated blind spot:
  `crawler.py`'s curl+grep pipeline cannot see JS-rendered content at all.
- `specs/023-cve-poc-intelligence/` - version-to-CVE correlation + PoC retrieval via NVD/GitHub,
  distinct from the existing static-local-mirror `payloads.py` and generic `web_search.py`.
- `specs/024-lora-fine-tuning-pipeline/` - offline dataset-curation + LoRA training pipeline,
  isolated from `app/`'s runtime deps (Argus currently has zero training capability -
  `requirements.txt` has no torch/transformers/peft). Scoped honestly against the paper's own
  RQ2 finding that fine-tuning a mid-scale model narrows but doesn't close the gap to a
  frontier commercial model.
- `specs/025-subtask-benchmark-suite/` - SR/SCR/TTE metrics + ablation-comparison harness. Also
  documents a real pre-existing gap in `tests/ai_benchmark.py` (calls `ArgusBrain` with a
  hand-picked 2-tool subset, not production's real `build_argus_tools()`) to be fixed as part
  of migrating it into the new suite.
- `specs/026-ethical-safeguards-raii/` - authorization-acknowledgment gate, hash-chained
  tamper-evident audit log, opt-in payload watermarking, RAG source-allowlist gating - each
  deliberately scoped down from the paper's full RBAC/audit proposal to match Argus's actual
  single-operator local-tool deployment shape, not the paper's multi-tenant research-system
  threat model.

Updated `specs/checklist.md` (new "Backlog - Proposed Future Phases" section, sequencing
recommendations) and `docs/ARCHITECTURE_AUDIT_REPORT.md`'s traceability matrix (8 new rows,
status "Proposed") to index the new phases without conflating them with implemented work.

## Added: 5 real, working tools the agent had no way to invoke; fixed a hang risk found while verifying them (2026-07-09, specs/018 CHK090)
User asked to get the greatest benefit from all existing files. Auditing every real public
method on `WSLBridgeTools` against `brain_tools.py`'s supposedly-canonical tool list found real,
working capabilities the agent couldn't use: `analyze_secrets` (leaked API key/credential
detection) was in *no* tool list anywhere; `crawl_target`/`advanced_vuln_probe`/`verify_command`/
`assess_difficulty` existed in a *sixth*, independently-drifted copy (`scripts/run_argus_cli.py`)
but not in the "canonical" `brain_tools.py` - the original consolidation had silently become
incomplete relative to a list it was supposed to replace.

Added all 5 as new tools (`Secret_Scanner`, `Crawl_Target`, `Advanced_Evasion_Probe`,
`Reflective_Pre_Verify`, `Task_Difficulty_Assessment`) to `brain_tools.py` (12 -> 17 tools);
`scripts/run_argus_cli.py` now imports `build_argus_tools()` instead of re-declaring its own
drifted list. Updated `react_prompts.py`'s PHASE guidance to reference all 5, and reframed
Phase 6 as real exploitation (research with `Exploit_Suggester` *then* attempt with
`Advanced_Evasion_Probe` - research alone isn't exploitation).

Live-verifying all 5 directly found and fixed a real bug: `crawl_target`/`analyze_secrets`'s
curl calls had no `--max-time`/`--connect-timeout`, unlike `advanced_vuln_probe`'s existing
ones, so a check against a currently-unreachable practice site showed these would otherwise
block on `command_runner.py`'s much longer generic default timeout instead of failing fast -
fixed to match the existing pattern.

New `tests/test_tools/{test_crawler,test_secrets}.py` (no prior coverage existed for either
module) and extended `test_brain_tools.py`/`test_react_prompts.py`. Full suite: 222 passed, 1
pre-existing unrelated failure.

## Fixed: GUI felt heavy on every click - a PowerShell subprocess was spawned on every rerun (2026-07-09, specs/018 CHK089)
User reported the GUI itself feels heavy/slow when clicking or navigating tabs. Root cause:
`render_status_bar()` runs at the top of every page render, and Streamlit reruns the *entire
script* on any widget interaction (any click, any tab switch) - so `check_ssh_status()`, which
spawned a whole new `powershell.exe` process (`Test-NetConnection`) on every call, ran on every
single click anywhere in the app. PowerShell's cold-start overhead (hundreds of ms, often 1s+)
on top of the actual check made the whole GUI feel heavy.

Also found, while diagnosing this same report, an unrelated but real issue: a stale Streamlit
process from **2 days earlier** was still bound to port 12199 alongside a freshly-started one,
silently serving some requests on pre-fix code the whole time it went unnoticed - killed.

Fixed `check_ssh_status()`: replaced the PowerShell/`Test-NetConnection` subprocess with the
same lightweight raw socket connect `check_ollama_status()` already used for Ollama's port - no
process spawn at all. Both status checks also wrapped in `@st.cache_data(ttl=5)` as a second
layer of protection against repeated reruns. New `tests/test_gui/test_status_bar.py` (no prior
coverage existed) - 6 tests. Full suite: 213 passed, 1 pre-existing unrelated failure.

## Fixed: run_id mismatch between AgentController and its subprocess; confirmed GUI live-feed is genuinely incremental (2026-07-09, specs/018 CHK088)
User asked why the Agent tab's live feed seemed to only update after the whole run finished
rather than in real time. Verified directly rather than assumed: started a real run through
`AgentController` (the actual GUI mechanism) and watched the state file's `events` array grow
with real timestamps - a Thought/Action appeared, then ~3s later a real ping's Observation, then
the next Thought, then **54 seconds later** a real subdomain-enumeration Observation. The
live-feed mechanism genuinely writes and the GUI genuinely polls incrementally, not in one
batch - the perceived "batch" feeling is real external tool latency (30s-3min per tool), not a
code bug.

While investigating, found and fixed a real, separate bug: `AgentController.start()` generates a
`run_id` to name the state file, but `scripts/run_agent.py::main()` independently generated a
SECOND, different `run_id` and overwrote the state file's own `run_id` field with it - the
file's name and its content disagreed about the run's identity. Fixed: `start()` now passes
`--run-id` to the subprocess; `main()` uses it verbatim, falling back to a fresh uuid4 only for
standalone/manual invocations without the flag.

New tests in `tests/test_modules/test_run_agent.py` verify the run_id is used verbatim when
provided and a fallback is generated when it's not. Full suite: 207 passed, 1 pre-existing
unrelated failure.

## Fixed: three more issues found live-testing the duplicate-call fix, then loosened it to allow one genuine retry (2026-07-09, specs/018 CHK086-087)
A follow-up live run against `https://scanme.nmap.org` with CHK085's duplicate-call block active
surfaced three more distinct, real issues, all fixed and live-reverified together:

1. **Oscillation between two blocked tools**: once `Run_Nikto` and `Smart_Web_Search` were both
   individually blocked as duplicates, the model alternated re-proposing those same two for 3
   more turns instead of trying `Run_FFUF`, which had never been attempted. Fixed: the
   duplicate-block Observation now explicitly names every tool not yet tried this run.
2. **`Run_Nikto`/`Run_FFUF` targeting the wrong closed port**: the model called `Run_Nikto`
   against `https://scanme.nmap.org` (port 443, closed per its own earlier Nmap scan) instead of
   the actually-open port 80/http. Fixed at the code level: `app/tools/scanners.py` now
   auto-retries once with the opposite scheme on a connection failure/empty result, mirroring
   `app/tools/recon.py`'s existing nmap fallback pattern.
3. **`overall_risk_score` inconsistent with findings' severities**: one run produced
   `overall_risk_score: 10` while every finding was `Low` severity with "No remediation needed".
   Fixed with a new prompt rule requiring the score to match the findings' actual severities.

A closer look at the duplicate-call block itself then found it was *stricter* than intended: it
blocked on the very first repeat, whereas the original `app/core/prompts.py` design explicitly
tolerated a tool+input pair running "not more than **TWICE**" - a model that doubts a result
(e.g. a transient network blip) needs room for one real retry, not zero. Loosened the block to
match: only a *third* identical attempt is now blocked.

Live-reverified all three original fixes together: the model picked `Smart_Web_Search` then
`Run_Nikto` (two genuinely different tools, zero oscillation) after `Recon_Suite` was blocked;
`Run_Nikto`'s scheme-fallback fired and succeeded, producing real findings (outdated Apache
2.4.7, `mod_negotiation`/MultiViews); the final report had two `High`-severity findings and
`overall_risk_score: 8` - consistent. New test files with no prior coverage:
`tests/test_tools/test_scanners.py` (7 tests) and `tests/test_registry/test_react_prompts.py`
(5 tests). Full suite: 205 passed, 1 pre-existing unrelated failure.

## Fixed: agent repeated an identical, already-succeeded tool call 4 times in a row (2026-07-09, specs/018 CHK085)
Live testing against `https://scanme.nmap.org` (immediately after the CHK084 ping fix) surfaced
a new, real, repeating bug: the model called `Recon_Suite` with the *identical* input 4 times in
a row, despite getting a complete, successful result on the very first call. `react_prompts.py`'s
own Rule 2 ("NEVER repeat the same tool with the exact same input") turned out to be advisory
text the model doesn't reliably follow - each repeat burned a real nmap scan for zero benefit.

Fixed structurally instead of trusting the prompt alone: `react_workflow.py`'s `execute_node`
now appends each successful `"{tool}::{input}"` pair to a new state field, `tool_call_history`;
`parse_node` blocks any repeat of a pair already in that history with a "you already called
this" Observation instead of re-executing it (new `phase: "duplicate_call"`, routed through the
same `max_iterations`-bounded loop `format_error` already used). Also surfaced
`tool_call_history` directly in the prompt itself (`react_prompts.py`'s new
`TOOLS ALREADY CALLED THIS RUN` block) so the model has explicit visibility into what it already
tried, rather than relying on it to infer that from the Blackboard/conversation history -
prevention on top of the reactive block.

New tests in `tests/test_langgraph_workflow.py`:
`test_custom_graph_blocks_identical_repeated_tool_call` (verifies the real tool only executes
once and the model receives exactly one duplicate warning) and
`test_custom_graph_duplicate_call_loop_respects_max_iterations` (a model that keeps re-proposing
a blocked call still terminates cleanly). Live-reverified against the exact scenario that
exposed the bug: `Recon_Suite` now runs once, a repeat attempt is blocked with zero extra nmap
scans, and the model immediately produces a complete, correct `SecurityReport` instead. Full
suite: 193 passed, 1 pre-existing unrelated failure.

## Changed: switched the production model to a Q5_K_M quantization to fix the VRAM-headroom crash root cause (2026-07-09, specs/018 T021)
CHK081's intermittent Ollama/CUDA crash was mitigated with a scoped retry, but the root
contributing factor - the F16 `WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest` model (~15GB) leaving
only ~500MB of VRAM headroom on a 16GB card - was still present. Researched alternatives
(quantization-source quality across bartowski/mradermacher/unsloth; a base-model swap to Qwen3,
cited in 2026 benchmarks as the most reliable small local model for tool-calling) before deciding:
switched to `hf.co/bartowski/WhiteRabbitNeo_WhiteRabbitNeo-V3-7B-GGUF:Q5_K_M` (~5.4GB, ~95% of F16
quality), keeping the same base model rather than swapping to Qwen3 - no mature small
uncensored/pentest-tuned Qwen3 variant exists, and WhiteRabbitNeo's security-domain fine-tuning
was judged more valuable than a tool-calling-reliability gain this phase's scaffolding work
(CHK077-082) already largely captured. User-confirmed direction.

Updated `config.yaml`'s `model_name`, `app/core/config.py`'s dataclass default, `.env.example`'s
`SELECTED_MODEL`, and `scripts/ARGUS_INSTALLER.ps1`'s default `$OLLAMA_MODEL` (fresh installs now
pull the same quantized model). Live-verified end-to-end via `scripts/_diagnostic_cli_verbose.py`:
the quantized model produced valid `Thought:`/`Action:` structured JSON tool calls and a correctly
parsed `SecurityReport` final answer, with GPU usage at ~7.9GB/16GB throughout the run (vs
~15.8GB with the old F16 model) - no crash.

## Fixed: four more live-run failures found re-testing specs/018 against a real target (2026-07-09, specs/018 addendum)
The T011 follow-up ("live Ollama/WSL re-run... nice-to-have, not a blocker") was performed
against `https://www.cultbeauty.co.uk/` and surfaced four additional real bugs the mock-LLM
tests couldn't reach, plus one infrastructure crash outside the application's control:

1. **`OllamaLLM.with_structured_output()` raises `NotImplementedError`.** `_try_structured_action`/
   `_try_structured_final_answer` both call `llm.with_structured_output(...)`, but `ArgusBrain`
   built its LLM via `llm_factory.py::build_llm()`, which returns a completion-style `OllamaLLM`
   - confirmed live that this raises, silently degrading every run to the weaker regex-fallback
   path. Fix: new `llm_factory.py::build_chat_llm()` returns a chat-style `ChatOllama` (verified
   working with `with_structured_output`); `build_llm()` is untouched (still used by
   `reflective_node`/`rag_engine.py`, which don't need structured output).
2. **Blackboard context grows unbounded.** `get_blackboard_summary()` pulled every finding across
   every target ever scanned (56 findings from 3 targets in this run), producing a 6123-char
   fused prompt that contributed to a context-window overflow. Fix: `get_blackboard_summary(max_chars=3000)`
   default bound, greedily filling by priority/recency and never truncating mid-entry; explicit
   larger `max_chars` still available for callers that want everything.
3. **`ChatOllama` silently routes to the untested prebuilt graph.** `ChatOllama.bind_tools()`
   succeeds where `OllamaLLM.bind_tools()` didn't, so `react_workflow.build_workflow()`'s
   auto-detection picked the prebuilt tool-calling graph (`ArgusPrebuiltState`) instead of the
   custom graph this phase built and tested - `ArgusBrain`'s output parsing didn't match its
   shape, always reporting `no_final_answer`. Fix: `ArgusBrain` now calls
   `react_workflow._build_custom_workflow()` directly, bypassing auto-detection.
4. **`extract_target()` read a corrupted target from the RAG-enriched query.** `_enrich_with_rag()`
   prepends the Blackboard JSON block before the actual question text; `extract_target()`'s
   dot/whitespace heuristic grabbed a JSON key (e.g. `www.cultbeauty.co.uk:80":`, with a stray
   quote and colon) as the "target," breaking every tool call with a shell syntax error. Fix:
   `ArgusBrain.ask()` now extracts the target from the raw, pre-enrichment query and passes it
   explicitly into the graph, instead of re-deriving it from the enriched text.
5. **Intermittent Ollama/CUDA/Windows crash, not fixable from application code**: `llama-server
   process has terminated: exit status 0xc0000409: ... stack-based buffer overrun ... CUDA error`
   - reproduced twice, independent of context size (once at 8192 tokens, once at 439 chars),
   matching upstream `ollama/ollama` GitHub issue #16650. Mitigated (not solved) with a
   scoped one-time retry in `ArgusBrain._run_structured_graph()` keyed on this exact error
   signature (`_TRANSIENT_INFRA_ERROR_MARKERS`) - the server reloads the model fresh on the next
   request, so one retry is a pragmatic mitigation for a driver-level bug outside this
   codebase's control. Also applied `OLLAMA_KV_CACHE_TYPE=q8_0` + `OLLAMA_FLASH_ATTENTION=1` in
   `scripts/LAUNCH_STUDIO.bat` to reduce VRAM pressure, one contributing factor.

Verified via mock LLMs (no live GPU needed for the regression suite): `_CrashOnceThenSucceedLLM`
confirms exactly one retry then success; `_PersistentErrorLLM` confirms a non-matching error is
*not* retried (Constitution VIII - no masking unrelated failures behind a retry).
`tests/test_memory.py::test_large_insert_performance` updated for the new bounded-by-default
behavior. Full suite: 186 passed (1 pre-existing, unrelated, network-dependent failure in
`test_smart_web_search.py::test_attempt_limit`, excluded from this session's baseline all along).

## Fixed: ArgusBrain hung 900s with zero results on its first real production run (2026-07-08, specs/018)
First live run of `017`'s restored `ArgusBrain` (against `https://www.cultbeauty.co.uk/`) timed
out completely: `logs/agent_runs/agent_9a5671bc-....json` shows WhiteRabbitNeo-V3-7B repeating
the *identical* malformed, non-ReAct output (a raw dump of Blackboard/RAG context data) on
every one of ~26 retries over 15 minutes, each rejected by LangChain
(`"Invalid Format: Missing 'Action:' after 'Thought:'"`), until the wall-clock timeout killed
the run with `Overall Risk Score: N/A`, `Findings Count: 0`.

Root cause: `ArgusBrain`'s docstring claimed *"When WhiteRabbitNeo has format issues with
ReAct, automatically falls back to a simpler sequential execution model"* - but
`_get_react_agent()` and `_get_simple_chain()` both built the identical
`agent_factory.py::build_agent_executor()` (classic free-text `AgentExecutor`), differing only
in a `verbose` flag. No real fallback ever existed.

Researched the standard fix (Ollama's own structured-outputs docs, LangChain/LangGraph
reliability write-ups - full citations in `specs/018-structured-agent-reliability/research.md`):
constrain the model's output at the sampling level via a JSON schema, which "eliminates parsing
problems at the root... near-100% parse success," instead of hoping free text matches a regex.
**This exact technique already existed, fully built and tested, in this repo** -
`app/core/agent/react_workflow.py::_try_structured_action()` (built for the orphaned
`013-langgraph-workflow`, using `llm.with_structured_output()`) - just disconnected from
`ArgusBrain`, the same situation `017` found and fixed for the agent as a whole.

Also found and fixed an independent bug while reusing that module: `route_after_parse()`'s
format-error retry branch had **no `max_iterations` check at all** (unlike the tool-execution
path 8 lines below it) - a model that never once produces valid output would have looped there
unbounded except by LangGraph's default `recursion_limit` (25), raising an ungraceful
`GraphRecursionError` instead of a clean, honest result.

Changes:
- `app/core/agent/react_workflow.py`: new `_try_structured_final_answer()` (same structured-
  decoding fix applied to the final report shape, not just tool selection); `route_after_parse()`
  now checks `max_iterations` on the format-error path too.
- `app/core/agent/brain.py`: removed the non-functional `_get_react_agent`/`_get_simple_chain`/
  `use_react` dual-path; `ArgusBrain` now drives `react_workflow.py`'s structured-output-first
  custom graph via `.stream(stream_mode="values")` instead of `agent_factory.py`'s classic
  `AgentExecutor`. `max_iterations` reduced from the old executor's 50 to **15** (structured
  decoding needs far fewer retries, and it bounds worst-case wall-clock time). `ask()`'s
  external contract is unchanged - `017`'s `scripts/run_agent.py`, `brain_tools.py`, and
  `app/GUI/tabs/agent.py` needed zero changes.
- `app/core/agent/react_callback.py`: new `LiveFeedCallbackHandler.on_graph_event()` - a raw
  `StateGraph` doesn't fire `AgentExecutor`'s callback hooks, so `ArgusBrain`'s new streaming
  loop calls this directly instead, once per new message, reusing the same live-feed contract.

Verified: directly reproduced the live incident with a mock LLM that repeats the exact
malformed behavior - confirmed it now terminates within `max_iterations` (15) with an honest
`no_final_answer` error instead of hanging. A separate well-behaved mock confirms the happy
path (real structured report + live-feed events) is unaffected. New regression test for the
`route_after_parse` bug fix. Zero regressions: all existing `tests/test_registry/`,
`tests/test_langgraph_workflow.py`, and `017` tests pass unmodified.

Note: `app/core/prompts.py` (the prompt file `017` originally restored) is no longer what
drives `ArgusBrain`'s tool selection - `react_workflow.py`'s shorter `react_prompts.py` is, for
reliability (flatter prompts are also a documented reliability lever for smaller local models).
`app/core/prompts.py` remains in place, used by `agent_factory.py`'s classic executor for other
callers (Constitution VII - not deleted).

## Restored: ArgusBrain (prompt-driven ReAct agent) as the production Agent driver (2026-07-08, specs/017)
The user pointed out that `app/core/prompts.py` defines the project's originally-intended
operating model: the AI follows a structured prompt, freely picks whichever tool it judges
best, observes the result, and decides the next action - a classic ReAct loop, not a fixed
sequence. Investigation confirmed that engine already exists and works
(`app/core/agent/brain.py::ArgusBrain`, using `app/core/prompts.py` via
`app/core/agent/agent_factory.py::build_agent_executor()`, which always builds a real
`create_react_agent` + `AgentExecutor`) - but `ArgusBrain(...)` was only ever instantiated by
the deprecated GUI shims (`app/GUI/{app,argus_gui,gui_main}.py`, `desktop_gui.py`). The
canonical `app/GUI/dashboard.py` instead drove `scripts/run_agent.py` ->
`app/core/agent/graph.py::build_tactical_graph()`, a deterministic recon->scanner->exploit->
reflective state machine with only one narrow single-token LLM call - no free tool choice
anywhere in the production path.

This is a genuine Constitution VII (Canonical Reconciliation Authority) event, reversing the
2026-07-06 decision that made the deterministic graph canonical. Full details:
`specs/017-restore-react-agent/spec.md`.

Changes:
- `app/core/agent/brain_tools.py` (new): one canonical `build_argus_tools()` wrapping the 12
  `WSLBridgeTools` methods still present (of the historical 13-tool list on the `PHILOPATERSH`
  branch; `run_specialized_module` no longer exists and was dropped) - replacing the pattern of
  hand-copying this list into every GUI file.
- `app/core/agent/react_callback.py` (new): `LiveFeedCallbackHandler` streams each ReAct step
  (Thought/Action/Observation, tool errors, final answer) into the *existing*
  `app/core/agent/contracts.py::append_run_event` state-file contract - `app/GUI/tabs/agent.py`'s
  "Agent Feed" shows it live with zero GUI polling changes, since `StreamlitCallbackHandler`
  (the historical approach) only works when the agent runs in-process, and the current
  architecture deliberately runs it in a subprocess for GUI responsiveness.
- `scripts/run_agent.py`: rewritten to drive `ArgusBrain.ask()` instead of
  `build_tactical_graph()`. Same `threading.Thread(...).join(timeout)` bounding and demo/test
  fallback path, unchanged. `_build_final_state()` persists the real `SecurityReport` shape
  (`summary`/`findings`/`overall_risk_score`/`next_steps`/`output`) and explicitly flags
  `parse_warning` rather than fabricating empty structured fields when the LLM's output didn't
  parse (Constitution VIII - Truthful Runtime).
- `app/GUI/tabs/agent.py`: "Final Results" now renders risk score, a findings expander, next
  steps, and the full report - not the old open_ports/vulnerabilities/exploit_success metrics.
- `app/core/agent/graph.py` and its nodes are **retained, not deleted** (Constitution VII); their
  existing tests (`tests/test_modules/test_tactical_graph_termination.py`) still pass.

Verified: end-to-end wiring smoke-tested with an injected `FakeListLLM` (no live Ollama/WSL
needed) - both the successful-structured-report path and the unparseable-output fallback path.
New Agent tab UI verified with a real Streamlit `AppTest` run against a completed-run state
file: zero exceptions, findings/report content confirmed present in rendered output. 13 new
unit tests (`tests/test_registry/{test_brain_tools,test_react_callback}.py`,
`tests/test_modules/test_run_agent.py`), all passing.

## Fixed: same real site fragmented into multiple Blackboard targets (2026-07-08)
Found while verifying the SQLite lock-contention fix against a real scan: a run
against `https://www.cultbeauty.co.uk/` correctly incremented Targets by +1, but
Findings jumped by +54 for a scan that found 27 real vulnerabilities. Direct
inspection of `data/argus_intelligence.db` showed the same site split across two
target rows - `www.cultbeauty.co.uk` (2 findings) and `www.cultbeauty.co.uk:80`
(53 findings) - fragmenting both the counters and the Knowledge Graph.

Root cause: `app/tools/recon.py::recon_suite()` derives its Blackboard domain key
from the bare original URL (no port), while `app/tools/scanners.py`,
`evasion.py`, `reflective_verification.py` (x2), `secrets.py`, `simulation.py`,
and `crawler.py` each independently derived theirs from a port-qualified
`target_url` (e.g. `http://example.com:80`) using the same
`url.replace("https://", "").replace("http://", "").split("/")[0]` expression,
which strips the scheme but not the port - so the same real site wrote to two
different domain keys depending on which module recorded it.

Fixed by extracting one canonical `normalize_domain_for_memory()` into
`app/tools/utils.py` (strips both scheme and port) and repointing all 8 call
sites at it instead of each hand-rolling the same incomplete expression
(Constitution IX - Single Source of Truth). Verified the fix produces matching
keys for both URL forms directly; existing fragmented data in a live DB is not
retroactively merged by this fix, only future writes are correct. Full test
suite (`tests/test_tools/`, `tests/test_memory.py`, unit tier): 60/60 passing,
zero regressions.

## Fixed: Dashboard "Quick Actions" crashed with StreamlitAPIException on click (2026-07-08)
Reported live: clicking "New Target" (or Start Agent/Generate Report/Settings) on
the Dashboard tab crashed with `st.session_state.nav_radio cannot be modified
after the widget with key nav_radio is instantiated`.

Root cause: `app/GUI/dashboard.py` instantiates the sidebar navigation
`st.radio(..., key='nav_radio')` before dispatching to any tab, including
`render_dashboard()`. That tab's Quick Action buttons then tried to set
`st.session_state.nav_radio` directly to navigate - but Streamlit forbids
writing to a widget's own key once that widget has already run in the current
script pass, regardless of the `st.rerun()` that follows.

Fixed with the standard indirection: the buttons now set a plain
`st.session_state["_pending_nav"]` flag instead, and `dashboard.py` applies it
to `nav_radio` *before* the radio widget is (re)created on the next run -
which is allowed, since the widget hasn't been instantiated yet in that pass.

Verified with a real Streamlit `AppTest` run (not just a syntax check):
loaded the dashboard, clicked "New Target", confirmed zero exception, and
confirmed `session_state["nav_radio"]` actually changed to "Targets" -
i.e. the feature now works, not just "no longer crashes".

## Investigated + fixed: dashboard header showed "Targets: 0 | Findings: 0" after a real, completed scan (2026-07-08)
Reported symptom: a full recon->scanner->exploit run against a real target completed
successfully (13 real findings visible in the Agent Feed and final_state), but the
dashboard's top-of-page "Targets: N | Findings: N" counter stayed at zero.

Traced the write path end to end: `recon_node` -> `ReconService.recon_suite()` ->
`ArgusMemory.add_finding()`, which is the only Blackboard write in the entire
LangGraph pipeline (scanner_node/exploit_node only mutate in-memory state, never
the DB). Confirmed via direct inspection that `data/argus_intelligence.db` was
genuinely empty after the real run - the write never landed. Called `add_finding()`
directly (outside the agent) and it worked perfectly, proving the function itself
is correct; the failure is specific to the live agent-subprocess context.

Root cause (well-evidenced, not 100% reproduced live): each LangGraph node
re-instantiates `WSLBridgeTools()` -> fresh `ArgusMemory()` -> several SQLite
connections per run (migration check, init, integrity check, the actual write),
all against the same file the Streamlit GUI's status bar concurrently polls via
its `st.fragment` refresh. A single "database is locked" hit on the one
`add_finding()` call per run silently drops that write with zero retry - and,
separately, would have been invisible either way, because `AgentController`
captured the agent subprocess's stdout/stderr via `subprocess.PIPE` and never
read it (also a latent hang risk if the child ever filled the pipe buffer).

Fixed both layers:
- `app/core/memory/memory_service.py::_get_conn()`: SQLite busy-timeout raised
  10s -> 30s, giving concurrent access from the GUI and the agent subprocess a
  realistic window to resolve instead of failing fast and silently.
- `app/GUI/utils/agent_controller.py`: agent subprocess stdout/stderr now
  redirected to a real log file (`logs/agent_runs/agent_<run_id>.log`) instead
  of an unread `subprocess.PIPE`, exposed via a new `get_log_tail()` method.
- `app/GUI/tabs/agent.py`: added an "Agent Process Log" expander next to
  "View Full State" so any future failure (this one or otherwise) is visible
  in the GUI itself instead of requiring code inspection to diagnose.

Not yet independently confirmed via a live re-run with the fix in place (would
require another full multi-minute scan); the increased timeout is a well-reasoned
mitigation for the evidenced lock-contention pattern, and the logging fix means
the exact failure - if it recurs - will now be visible instead of silent.

## Fixed: pipeline gave up entirely on WAF/Cloudflare-protected targets (2026-07-07)
recon -> scanner -> exploit each had a single, unconditional failure point:
recon required nmap to parse a port; scanner required recon's port list to
be non-empty; exploit required scanner's payload to be non-None. Against a
target like `https://example.com` fronted by Cloudflare, the heavy
`nmap -sV --top-ports 100` scan routinely times out or gets most ports
filtered, so `open_ports` came back empty even though whatweb/dig clearly
proved the site was live - cascading into "No web-capable port available"
(scanner) then "No payload selected" (exploit), with the graph still
reaching `status: completed` and reporting all-zero results. Nothing
crashed; it failed logically and silently, exactly as observed.

Fixed with two independent, defense-in-depth layers:
- `app/tools/recon.py::recon_suite()`: if the primary `-sV --top-ports 100`
  scan times out, errors, or reports the host down/0 hosts up, automatically
  retries with `nmap -Pn -T4 --top-ports 20` - `-Pn` skips the ICMP/TCP
  host-discovery ping that WAFs/CDNs like Cloudflare often drop (the actual
  reason nmap gives up against such targets), and dropping `-sV` avoids the
  slow per-port version-probing that was timing out.
- `app/core/agent/nodes/recon.py`: if even that retry can't confirm a port
  but whatweb got a real HTTP(S) response, infers the target URL's scheme
  port (443/80) as a last-resort fallback, explicitly tagged
  `ports_inferred` (never silently presented as an nmap-confirmed result).
- `app/core/agent/nodes/scanner.py`: no longer hard-blocks when
  `open_ports` is empty - if the target itself is an `http(s)://` URL it
  scans that scheme's port directly regardless of what port-scanning could
  confirm, and persists that port back into `state["open_ports"]` so
  `exploit_node` (which independently re-derives its port) doesn't
  redundantly fail right after scanner just used it.

Validated live against the exact target/scenario described
(`https://example.com`, Cloudflare-fronted): the primary nmap scan needed
the `-Pn` retry (`raw_recon.ports_scan_degraded: true` in the run's
final_state), which then returned real confirmed ports `[80, 443, 8080]`
(everything else correctly `filtered` by Cloudflare's edge). Scanner found
19 real findings (explicit Cloudflare detection, missing security headers).
Exploit ran three real probes through the reflective retry loop
(generic_probe -> sqli -> path_traversal); `exploit_success: false` is now
an honest, verified negative rather than a structural inability to test
anything. `pytest`: 163/163 passing (excluding one pre-existing,
network-dependent, unrelated failure in test_smart_web_search.py).

## Fixed: GUI performance + non-functional buttons + empty results (2026-07-07)
Full root-cause writeup with before/after evidence in
`specs/011-gui-enhancement/tasks.md`'s "Post-Implementation Bug Fixes"
section. Summary: Dashboard's 4 Quick Action buttons set a session_state flag
nothing read (fixed by setting `nav_radio`, the sidebar's actual widget key);
`status_bar.py`'s Blackboard readout called `.get()` on a JSON *string*
(`ArgusMemory.get_blackboard_summary()`), always raising `AttributeError`,
silently shown as permanent "N/A" - added a real `get_blackboard_counts()`;
Knowledge Graph's `build_graph_data()` was a stub returning an always-empty
graph - now built from real `targets`/`findings` rows; Dashboard "Recent
Activity" and Reports "Generate Report" both read `session_state.jobs`, which
nothing ever appended to - now read the real `logs/agent_runs/*.json` state
files; the Agent tab's `for _ in range(60): time.sleep(1)` polling loop froze
Streamlit's entire single-threaded session (every button, every tab) for up
to 60 seconds at a stretch - replaced with `st.fragment(run_every="2s")` so
only the feed refreshes on a timer while the rest of the page stays
interactive. `pytest tests/test_gui tests/test_tools tests/test_memory.py`:
79/79 passing.

## Correction (2026-07-07)
Prior audit passes in this changelog stated live Ollama/WSL/SSH were
"unavailable in this sandboxed environment." That was incorrect - they are
genuinely installed and reachable here; the passes never actually attempted
live invocation and defaulted to a cautious assumption instead of testing it.
Corrected by direct verification: WSL boots and runs real commands, Ollama
(with `WhiteRabbitNeo-V3-7B` already pulled) answers real inference requests,
and SSH into Kali works via the project's own `paramiko`-based bridge with
the default `kali`/`kali` credentials. `LAUNCH_STUDIO.bat` was run for real
(non-interactively) and completed cleanly: Ollama check passed, SSH
self-heal (`wsl -d kali-linux -u root -- mkdir -p /run/sshd && sshd`)
started the dormant daemon, and the Streamlit dashboard came up and served
real HTTP 200 content on the configured port. No code or script change was
needed to make this work - the only "fix" was actually testing instead of
assuming. One genuine, minor, previously-undiscovered bug was found and
fixed along the way: `app/tools/self_heal.py`'s `_check_wsl()` decoded
`wsl.exe`'s UTF-16LE stdout/stderr with `text=True` (the platform default
encoding), producing an unreadable, null-byte-interleaved diagnostic message
in the failure path. This never affected the actual pass/fail result (that
was always `returncode`-based and correct) - purely cosmetic, now decoded
explicitly as `utf-16-le`.

## Fixed: dashboard stuck at "Starting reconnaissance..." (2026-07-07)
Root cause was in execution flow, not infrastructure (Ollama/SSH/WSL were all
already online). Three confirmed, independent bugs, found by reading the
actual node/runner code and reproduced live end-to-end against
`scanme.nmap.org` (Nmap Project's public scan-authorized test host):

1. **`app/tools/command_runner.py`'s `_run_ssh()` had no timeout at all** on
   `client.exec_command()`/`stdout.read()` - a hung remote command could
   block forever. `_run_direct_wsl()` had a single hardcoded 600s cap shared
   across every call, with no way for a caller to request a tighter bound.
2. **`scripts/run_agent.py`'s outer graph timeout (`DEFAULT_TIMEOUT_SECONDS
   = 120`) was shorter than a single real recon pass.** `recon_node`
   (`app/core/agent/nodes/recon.py`) runs `ReconService.recon_suite()`
   (`app/tools/recon.py`), which calls `whatweb --aggression 3`, then
   `nmap -sV -T4 --top-ports 100`, then `dig` **sequentially, synchronously**.
   Live reproduction confirmed `nmap -sV` alone routinely takes over 120
   seconds against a real, responsive host. Since `graph.invoke()` runs on a
   `daemon=True` thread joined with `worker.join(timeout_seconds)`, the
   120s outer timeout fired mid-recon on essentially every real (non-demo)
   run, before `recon_node` could ever return - so the graph never reached
   scanner/exploit, and the timeout branch never populates `final_state`,
   which is why Blackboard/Final Results showed nothing.
3. **Duplicate "Starting reconnaissance..." log**: `run_agent.py`'s `main()`
   pre-emptively called `record_state_event()` with the exact same message
   text that `recon_node()` independently writes moments later when the
   graph thread actually starts - two genuinely separate writes to the same
   state file producing the same line, not a retry/loop bug.
4. **`app/tools/evasion.py`'s `EvasionService.advanced_vuln_probe()`**
   (called from `exploit_node`) runs 6 sequential `curl` probes via
   `stealth_run()`, each with a random 1-3s stealth delay and, like the SSH
   path above, no explicit timeout - inheriting whatever generic default
   `CommandRunner.run()` had, sized for full tool scans, not single curl
   requests. Found via a second live repro that got past the (by-then-fixed)
   recon/scanner phases and still hit the outer timeout, this time during
   `exploit_node`.

Fix: added a `timeout` parameter threaded through
`CommandRunner.run()`/`_run_direct_wsl()`/`_run_ssh()` (default 180s, real
`socket.timeout` handling added to the SSH path); `recon_suite()` now passes
explicit per-tool bounds (whatweb 90s, nmap 180s, dig 20s) so recon has a
predictable ~290s worst case; raised `run_agent.py`'s
`DEFAULT_TIMEOUT_SECONDS` to 900s to give the full recon->scanner->exploit
pipeline (whose per-node worst cases stack up across three nodes' worth of
sequential external tool calls) a realistic budget; removed the redundant
pre-emptive event write. `stealth_run()` now defaults to a 20s timeout (curl
probes, not full scans) and each curl call adds `--max-time 15
--connect-timeout 5` so curl enforces its own bound rather than relying only
on the outer process being killed. Also fixed a related latent race:
`app/GUI/utils/agent_controller.py`'s `start()` wrote the run snapshot once
before spawning `run_agent.py` and once again immediately after, both
non-atomic read-modify-write cycles against the same file with no locking,
racing the child process's own writes - consolidated into a single
pre-spawn write. Separately, `app/GUI/tabs/agent.py`'s polling loop only
actively refreshed the feed for a bounded 60 seconds per script run and
never re-triggered itself, so any run taking longer looked "frozen" even
when the backend was healthy - added an `st.rerun()` when the loop's 60s
window elapses while the run is still active.

Validated live across three successive end-to-end reproductions against
`scanme.nmap.org`: run 1 (2m11s, recon timed out gracefully, scanner/exploit
still executed, exactly one recon-start event instead of two); run 2 (recon
succeeded with real open ports `[22, 80, 8008]`, scanner found 15 real
findings, exploit then hit the still-too-tight 600s outer budget - which is
what surfaced bug #4 above); run 3 (with the evasion-probe fix and 900s
budget) confirms full completion. Full `pytest` suite (`tests/test_gui`,
`tests/test_tools`, plus the graph/controller-targeted subset) passes
unchanged, 74/74.

## [Unreleased]
- Initial structure proposals applied.
- Closed the last two documented test gaps in `specs/010-langgraph-agent/tasks.md`
  (T027, T029), evaluated as the one safe, purely-additive improvement available
  after a conservative options review. `tests/test_modules/test_tactical_graph_termination.py`
  (7 tests) exercises `app/core/agent/graph.py`'s `should_continue()` directly:
  exploit-success termination, dependency-error retry routing, retry-budget
  exhaustion, missing-payload termination, and a config-driven retry bound.
  Extracted the stale-running reconciliation check in `app/GUI/tabs/agent.py`
  into a pure `_reconcile_agent_running_state()` function (behavior-preserving)
  and added `tests/test_gui/test_agent_tab_status.py` (5 tests) proving a
  failed/completed run is never displayed as still running.
- Full install-to-runtime audit pass: re-verified installer PowerShell syntax,
  project compilation, and the import-time-execution sweep (no new issues
  found beyond what earlier passes already fixed). Added genuinely new
  verification depth: `tests/test_gui/test_dashboard_apptest.py` uses
  Streamlit's `AppTest` harness to actually *run* `dashboard.py` and all 6
  tabs in a simulated session (not just import), catching runtime errors an
  import check cannot - zero exceptions found. This also satisfies Cleanup
  Manifest C3's "Streamlit smoke test of dashboard passes" precondition for
  the first time with real evidence. Confirmed `scripts/run_argus_cli.py --help`
  runs cleanly. Explicitly documented what remains unverifiable in this
  sandboxed environment (live WSL/Kali provisioning, live Ollama inference,
  live SSH bridge, full end-to-end recon->exploit runs) rather than assumed
  away - see `docs/ARCHITECTURE_AUDIT_REPORT.md` section 12.
- Completed the pending merge of `fix/setup-script-update` (all conflicts had been
  resolved in the working tree but never committed); fixed a missing `langgraph`
  dependency in `scripts/Setup/requirements.txt` surfaced during review.
- Consolidated Brain/Factory/Workflow per specs/012-spec-reconciliation T025-T030:
  removed dead RAG forwarder shims (`engine.py`/`processor.py`/`vectorstore.py`);
  merged `ArgusBrainV2`/`agent_factory_v2` into `app/core/agent/{brain,agent_factory}.py`
  and deleted the `_v2` shadow files; migrated `app/core/workflow/` into
  `app/core/agent/{react_workflow,react_state,react_prompts}.py` (dropping the
  already-dead `hooks.py`); wired `EmbeddingManifest` into `VectorStore`/`RAGEngine`
  so a stale or provider-mismatched FAISS index is never silently queried; added
  Ollama `format=json` structured Action decoding as the primary parse path, with
  the existing regex parser retained as fallback.
- Fixed two latent bugs found via mypy/testing: `RAGEngine.retrieve()` (and thus
  `format_context()`/`format_combined_context()`, used on every live RAG-enriched
  query) never applied the configured similarity threshold; `llm_factory.build_llm()`
  passed `timeout=3600` as a bare `OllamaLLM` kwarg, which that class silently drops
  (moved to `client_kwargs`, the correct channel).
- Added a `llm=` injection seam to `ArgusBrain.__init__` and new unit tests
  (brain dispatch/ask, agent factory, RAG threshold/manifest wiring) that run
  against `langchain_core`'s `FakeListLLM` and mocked FAISS/embeddings, with no
  live Ollama/FAISS server required.
- Translated the 8 Arabic `specs/*/converge.md` files to English (constitution VI).
- Expanded CI mypy coverage to the consolidated agent/RAG modules; hardened
  `installer.yml`'s Pester job (pinned checkout, explicit Pester module install,
  soft-skip when the test file is absent instead of hard-failing).
- Repository hygiene pass (Cleanup Manifest C2/C3/C4/C6/C7 from
  `docs/ARCHITECTURE_AUDIT_REPORT.md`): untracked generated/runtime artifacts
  (`logs/agent_runs/*.json`, `artifacts/*.zip`). Root-caused *why* they were
  tracked despite looking gitignored: 3 `.gitignore` rules used inline trailing
  comments (`pattern  # comment`) - git does not strip these, so the whole
  comment was part of the literal pattern and the rules matched nothing. Fixed
  by moving all 3 comments onto their own line; verified with `git check-ignore`.
  Moved 13 root-level incident notes into
  `docs/history/`, relocated the misnamed `Plan md/` folder, and retired the
  superseded `INSTALL_EVERYTHING.bat`/`.ps1` installer path (the `scripts/README.md`
  had already documented it as removed). Cleaned 9 pure-scratch files out of
  `workspace/`.
- GUI consolidation (C3): renamed `app/GUI/argus_studio.py` to `app/GUI/dashboard.py`
  per specs/011's naming. Along the way, found and fixed a real misconfiguration:
  `config.yaml`'s `gui_entry` and `app/core/config.py`'s `PathSettings` default were
  both pointing at `gui_app.py` (a crude single-target demo script), not the actual
  modular dashboard - `app/core/agent/contracts.py`'s own
  `STREAMLIT_DASHBOARD_ENTRYPOINT` constant already correctly named `argus_studio.py`
  as canonical. Fixed both config paths plus the two launcher scripts that each
  pointed at a different (and different from each other) GUI file. Added
  deprecation banners to the remaining legacy GUI entrypoints, matching the pattern
  already used by `app.py`.
- Reconciled `specs/010-langgraph-agent/tasks.md` (previously showed 0/33 complete
  despite the tactical agent graph being fully built) and updated
  `specs/013-langgraph-workflow`'s status from "Partially Superseded" to "Fully
  Superseded" now that its migration into `app/core/agent/` is complete. Confirmed
  Manifest C5 (missing `002`/`003-sqlite` spec artifacts) was already done.
- Deleted `app/GUI/gui_app.py` and `app/GUI/gui_root.py`: both executed
  `brain.ask()` unconditionally at import time (no button gate), crashing with
  `'NoneType' object has no attribute 'update'` when Ollama/WSL aren't reachable
  and Streamlit runs in bare mode. Verified 98% identical to each other and fully
  superseded by `app/GUI/dashboard.py`'s `AgentController`-based Agent tab.
  Updated `docs/ARGUS_FRAMEWORK_ARCHITECTURE_v2.md`, `IMPLEMENTATION_GUIDE.md`,
  and `specs/012-spec-reconciliation/tasks.md` (T033) to match.
- Fixed a misleading status claim in `app/GUI/argus_gui.py`: it displayed
  "WSL Bridge: ACTIVE" unconditionally regardless of actual reachability; now
  reuses `status_bar.py`'s existing `check_ssh_status()` instead of duplicating
  the check.
- Repo-wide sweep for import-time side effects beyond the GUI package (per
  specs/012's "deterministic imports" principle) found two real, if low-severity,
  cases: `app/core/agent/blackboard.py` created the SQLite schema unconditionally
  on import (moved to lazy init on first `get_connection()` call); `app/core/agent/graph.py`
  read `config.yaml` via `ArgusConfig.load()` at import to set `MAX_RETRIES`
  (moved into a `_get_max_retries()` function called from `should_continue()`).
  Neither depended on Ollama/WSL, so neither could crash in a bare environment -
  both were hygiene fixes, not crash fixes. `app/tools/wsl_bridge.py`'s
  `load_dotenv()` at import and `scripts/run_argus_cli.py`'s pre-`__main__`
  `load_dotenv()`/`ArgusConfig.load()` were reviewed and left as-is: standard,
  low-risk bootstrap patterns for a `.env`-driven module and a CLI entrypoint
  script respectively, not accidental side effects.

## [0.1.0] - 2026-06-22
- Added CONTRIBUTING guidelines.
- Added CI workflow for linting and testing.
- Added pre-commit configuration.
- Added security notes directory and sample note.
- Added logging configuration.
- Added requirements.txt and env.example.
- Added plugins directory with PluginBase stub.
- Updated .gitignore for additional patterns.
