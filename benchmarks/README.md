# Argus Subtask-Level Benchmark Suite (specs/025)

Measures whether a change to Argus's agent (`019`'s reflection upgrade, `020`'s multi-agent
roles, prompt tweaks, etc.) actually made the agent better or worse - not by opinion, by
running it against a small set of known-vulnerable local fixtures and scoring three metrics
per the Red-MIRROR paper's own methodology (`docs/history/2603.27127v1.pdf` Section 4.4):

- **SR** (Success Rate): did the agent's final report contain the fixture's ground-truth flag?
- **SCR** (Subtask Completion Rate): what fraction of the fixture's manually-authored subtask
  decomposition left evidence in the run trace?
- **TTE** (Time-to-Exploit): how many tool-call steps did it take to find the flag?

This suite requires a live, locally-running Ollama (with the configured model pulled) and a
working WSL/Kali bridge - it is **not** part of default `pytest` collection (`pytest.ini`'s
`testpaths = tests` doesn't include `benchmarks/`) and is slow by nature (each fixture run is a
full agent loop, budgeted up to 30 minutes per specs/025 NFR-002). Run it deliberately, not as
part of routine CI.

## Running

Fast unit tests (scoring math only, no live Ollama needed):

```
pytest benchmarks/tests/
```

A single fixture, or the whole suite, against the real agent:

```
python benchmarks/runner.py --fixtures info_disclosure_env_leak
python benchmarks/runner.py
python benchmarks/runner.py --configs-json "{\"baseline\": {}, \"no_inter_reflection\": {\"enable_inter_reflection\": false}}"
python benchmarks/runner.py --timeout 900
```

Or from Python directly, for one fixture:

```python
from pathlib import Path
from benchmarks.runner import run_fixture

result = run_fixture(Path("benchmarks/fixtures/info_disclosure_env_leak"))
print(result)
```

## Reading a report

Each run writes `benchmarks/results/<UTC-timestamp>_report.md` (every run is kept, not just
the latest, so trends across commits/phases stay visible). Two sections:

- **Aggregate** - one row per configuration: solved/total SR, mean SCR, mean TTE. This is the
  ablation comparison table (specs/025 FR-004/SC-002) - compare rows across configurations to
  see whether a feature flag actually helped.
- **Per-fixture detail** (one table per configuration) - SR/SCR/TTE and which named subtasks
  matched, per fixture. Use this to see *where* a run succeeded or failed, not just the total.

## Authoring a new fixture

Create `benchmarks/fixtures/<name>/` with four files:

- **`server.py`** - must define `start_server(port: int = 0) -> tuple[str, Callable[[], None]]`.
  Bind to `("127.0.0.1", port)` (port `0` = OS-assigned ephemeral port, the default the runner
  uses to avoid collisions across fixtures), serve in a daemon thread, and return
  `(base_url, stop_fn)`. See any existing fixture's `server.py` for the exact pattern
  (`socketserver.TCPServer` + `http.server.SimpleHTTPRequestHandler`). Prefer real in-process
  vulnerable logic (real `jinja2.Template(...).render()` for SSTI, a real unauthenticated
  lookup for IDOR, etc.) over simulated/hardcoded responses - per Constitution VIII, a
  benchmark that fakes the vulnerability it claims to test isn't measuring anything real.
  Do **not** use `subprocess`/shell out to attacker-controlled input in a fixture, even for a
  "Command Injection" category - simulate the injection's *observable effect* instead.
- **`query.txt`** - the natural-language task given to `ArgusBrain.ask()`, with a
  `{target_url}` placeholder substituted with the fixture's actual running URL.
- **`flag.txt`** - the ground-truth flag string (SR target). Format it `flag{...}` so it
  benefits from `react_workflow.py`'s existing early-termination nudge, like every fixture in
  this suite.
- **`subtasks.yaml`** - an ordered list of `{name, detector_regex}` pairs. Each `detector_regex`
  is matched (case-insensitive) against this run's `"completed"`-status trace entries (real
  tool-result/Observation content, not the agent's stated intentions) - write it as positive
  evidence something was actually done, not evidence something was avoided (a subtask can't
  prove a negative).

A fixture testing a vulnerability class a mock server can't represent realistically (real
SQLi/complex multi-request auth flows) may instead ship a `docker-compose.yml` reusing
`deploy/docker-lab/`'s conventions (pinned image tags, healthchecks, a bridge network) - not
yet exercised by any fixture in this suite as of 2026-07-23, but supported by
`fixture_base.py`'s contract for future fixtures that need it.

## Current fixtures

| Fixture | Category | Notes |
|---|---|---|
| `info_disclosure_env_leak` | Information Disclosure | Migrated from `tests/manual/ai_benchmark.py` (specs/025 SC-003) |
| `xss_reflected` | Reflected XSS | Flag only appears once an HTML-breaking payload is submitted |
| `idor_object_access` | IDOR | No ownership check on `/profile?id=` at all |
| `ssti_template_injection` | SSTI | Real `jinja2.Template` evaluation, proof-gated on `7*7` -> `49` |

More fixtures (Auth, Command Injection, and beyond) can be added the same way - this suite is
meant to grow incrementally, not reach external-benchmark parity (specs/025's own "Explicitly
out of scope": it does not attempt to reproduce XBOW/Vulhub).
