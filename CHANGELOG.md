# CHANGELOG

All notable changes to this project will be documented in this file.

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
