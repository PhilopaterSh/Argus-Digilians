"""Benchmark runner: SR/SCR/TTE scoring + multi-configuration ablation (specs/025 T002/T003).

`run_fixture()` drives one fixture through the real `ArgusBrain` + real
`build_argus_tools()` (fixing the 2-tool subset gap in the migrated
`tests/manual/ai_benchmark.py`) and computes:
- SR (Success Rate): the fixture's ground-truth flag found in the final output.
- SCR (Subtask Completion Rate): fraction of the fixture's named subtasks
  whose detector_regex matches a completed tool-call step in the run trace.
- TTE (Time-to-Exploit): the 1-based index of the first completed tool-call
  step containing the flag, or None if unsolved.

`run_suite()` runs a fixture set under one or more named configurations
(e.g. `enable_inter_reflection` on/off) and writes a comparison report -
this is what makes an ablation study (specs/025 FR-004) possible. Pass
`trials > 1` to repeat each (fixture, configuration) pair and aggregate
(mean + population stddev) via `AggregatedResult`/`_aggregate_trials()` -
a single trial per configuration is not reliable evidence: two one-trial
ablations of `enable_inter_reflection` in this project's own history gave
different verdicts (0.33 vs 0.25 mean SCR, then 0.33 vs 0.33).
"""
import json
import os
import re
import statistics
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.agent.brain import ArgusBrain  # noqa: E402
from app.core.agent.brain_tools import build_argus_tools  # noqa: E402
from app.core.config import ArgusConfig  # noqa: E402
from app.tools.tool_registry import WSLBridgeTools  # noqa: E402
from benchmarks.fixture_base import Fixture  # noqa: E402


@dataclass
class FixtureResult:
    fixture_name: str
    config_name: str
    sr: bool
    scr: float
    subtask_results: dict[str, bool]
    tte: Optional[int]
    duration_s: float
    error: Optional[str]


@dataclass
class AggregatedResult:
    """SR/SCR/TTE aggregated across `trials` repeated runs of one fixture+config.

    A single run's result can be noise (see the module-level "why trials
    exist" note on `run_suite()`); this is what a multi-trial comparison
    should actually be read from, not any one `FixtureResult`.
    """

    fixture_name: str
    config_name: str
    trials: int
    solved_count: int
    sr_rate: float
    mean_scr: float
    stddev_scr: float
    mean_tte: Optional[float]
    error_count: int
    subtask_match_rates: dict[str, float]


@dataclass
class SuiteReport:
    timestamp: str
    configs: dict[str, dict]
    trials: int = 1
    results: dict[str, list[AggregatedResult]] = field(default_factory=dict)


class TraceCaptureCallback:
    """Accumulates `ArgusBrain.ask()`'s per-step run trace.

    `ArgusBrain.ask()` does not return `tool_call_history` - the only
    externally-visible per-step trace is this `on_graph_event` seam
    (matching `app/core/agent/react_callback.py::LiveFeedCallbackHandler`'s
    existing pattern). `status` is one of `"reflecting"`/`"completed"`/
    `"running"`, derived by `ArgusBrain._emit_graph_step()` from the message
    content prefix; `"completed"` entries are actual tool-result
    (`Observation:`) content, which is what SCR/TTE score against.
    """

    def __init__(self) -> None:
        """Init."""
        self.steps: list[tuple[str, str]] = []

    def on_graph_event(self, status: str, detail: str) -> None:
        """Record one graph step.

        Args:
            status (str): `"reflecting"` / `"completed"` / `"running"`.
            detail (str): The raw step content.
        """
        self.steps.append((status, detail))


def _apply_config_overrides(overrides: Optional[dict]) -> None:
    """Reset the `ArgusConfig` singleton, reload it, then apply overrides.

    `ArgusConfig` caches itself in a classvar (`ArgusConfig.load()` returns
    the same instance on every call within a process); an ablation runner
    that runs several configurations in one process must force a reload
    before each run or later configurations silently reuse the first one's
    state.

    Args:
        overrides (dict | None): Flat `{field_name: value}` pairs applied via
            `setattr` after reloading, e.g. `{"enable_inter_reflection": False}`.
    """
    ArgusConfig.reset()
    cfg = ArgusConfig.load()
    for key, value in (overrides or {}).items():
        setattr(cfg, key, value)


def _compute_sr(flag: str, output_text: str) -> bool:
    """Success Rate: does the final output contain the ground-truth flag?

    Args:
        flag (str): The fixture's ground-truth flag string.
        output_text (str): `str(result["output"])` from `ArgusBrain.ask()`.

    Returns:
        bool: True if `flag` appears (case-insensitive) in `output_text`.
    """
    return flag.lower() in output_text.lower()


def _compute_scr(subtasks: list, completed_steps: list[str]) -> tuple[dict[str, bool], float]:
    """Subtask Completion Rate: fraction of subtasks with matching evidence.

    Args:
        subtasks (list[Subtask]): The fixture's named subtask decomposition.
        completed_steps (list[str]): `"completed"`-status trace entries
            (actual tool-result content), in run order.

    Returns:
        tuple[dict[str, bool], float]: per-subtask hit/miss, and the overall
            fraction matched (0.0 if there are no subtasks).
    """
    subtask_results = {}
    for subtask in subtasks:
        pattern = re.compile(subtask.detector_regex, re.IGNORECASE)
        subtask_results[subtask.name] = any(pattern.search(step) for step in completed_steps)
    scr = sum(subtask_results.values()) / len(subtasks) if subtasks else 0.0
    return subtask_results, scr


def _compute_tte(flag: str, completed_steps: list[str]) -> Optional[int]:
    """Time-to-Exploit: 1-based index of the first step containing the flag.

    Args:
        flag (str): The fixture's ground-truth flag string.
        completed_steps (list[str]): `"completed"`-status trace entries, in
            run order.

    Returns:
        int | None: 1-based step index, or None if the flag never appears
            in any completed step (e.g. it was only in the synthesized
            final report, not a raw tool Observation).
    """
    flag_re = re.compile(re.escape(flag), re.IGNORECASE)
    for idx, step in enumerate(completed_steps, start=1):
        if flag_re.search(step):
            return idx
    return None


def run_fixture(
    fixture_dir: Path,
    config_overrides: Optional[dict] = None,
    config_name: str = "default",
    timeout_s: int = 1800,
    llm: Optional[Any] = None,
    rag_config: Optional[dict] = None,
    resolve_wsl_host: bool = True,
) -> FixtureResult:
    """Run one fixture against a real `ArgusBrain` and score SR/SCR/TTE.

    Args:
        fixture_dir (Path): `benchmarks/fixtures/<name>/`.
        config_overrides (dict | None): Applied to `ArgusConfig` before the
            run via `_apply_config_overrides()` (specs/025 FR-004).
        config_name (str): Label recorded on the returned `FixtureResult`.
        timeout_s (int): Wall-clock budget (specs/025 NFR-002); a run that
            exceeds this is recorded as `error="timeout"`, not a crash.
        llm (Any | None): Test seam - passed straight through to
            `ArgusBrain(..., llm=llm)`. `None` uses the real production LLM.
        rag_config (dict | None): Passed straight through to
            `ArgusBrain(..., rag_config=rag_config)`.
        resolve_wsl_host (bool): Passed straight through to `Fixture.start()`
            - set `False` only when `llm` is a fake that never triggers a
            real tool call (keeps fast unit tests from needing live WSL).

    Returns:
        FixtureResult: SR/SCR/TTE plus per-subtask detail for this run.
    """
    fixture = Fixture.load(fixture_dir)
    _apply_config_overrides(config_overrides)

    base_url, stop_server = fixture.start(resolve_wsl_host=resolve_wsl_host)
    start_time = time.time()
    error: Optional[str] = None
    result_holder: dict[str, Any] = {}

    try:
        bridge = WSLBridgeTools()
        tools = build_argus_tools(bridge)
        model_name = ArgusConfig.load().model_name
        brain = ArgusBrain(model_name, tools, rag_config=rag_config, memory=None, llm=llm)
        trace_cb = TraceCaptureCallback()
        query = fixture.render_query(base_url)

        def _worker() -> None:
            """Worker."""
            result_holder["result"] = brain.ask(query, callbacks=[trace_cb])

        worker = threading.Thread(target=_worker, daemon=True)
        worker.start()
        worker.join(timeout_s)
        if worker.is_alive():
            error = "timeout"
    except Exception as exc:  # noqa: BLE001 - a fixture bug must not crash the whole suite
        error = str(exc)
    finally:
        stop_server()

    duration_s = time.time() - start_time
    subtask_names = {s.name: False for s in fixture.subtasks}

    if error:
        return FixtureResult(fixture.name, config_name, False, 0.0, subtask_names, None, duration_s, error)

    result = result_holder.get("result", {})
    output_text = str(result.get("output", ""))
    sr = _compute_sr(fixture.flag, output_text)

    completed_steps = [detail for status, detail in trace_cb.steps if status == "completed"]
    subtask_results, scr = _compute_scr(fixture.subtasks, completed_steps)
    tte = _compute_tte(fixture.flag, completed_steps) if sr else None

    return FixtureResult(fixture.name, config_name, sr, scr, subtask_results, tte, duration_s, None)


def _aggregate_trials(trial_results: list[FixtureResult]) -> AggregatedResult:
    """Aggregate N repeated `run_fixture()` results into one `AggregatedResult`.

    Args:
        trial_results (list[FixtureResult]): One or more runs of the same
            fixture under the same configuration.

    Returns:
        AggregatedResult: solved-rate, mean+population-stddev SCR, mean TTE
            over solved trials only (None if none solved), and error count.
            `statistics.pstdev` (population, not sample) is used so a single
            trial still yields a defined `0.0` rather than raising - trials=1
            is the documented default, not an edge case to special-case.
    """
    first = trial_results[0]
    trials = len(trial_results)
    solved_count = sum(1 for r in trial_results if r.sr)
    scrs = [r.scr for r in trial_results]
    ttes = [r.tte for r in trial_results if r.tte is not None]
    error_count = sum(1 for r in trial_results if r.error)

    subtask_names = first.subtask_results.keys()
    subtask_match_rates = {
        name: sum(1 for r in trial_results if r.subtask_results.get(name)) / trials
        for name in subtask_names
    }

    return AggregatedResult(
        fixture_name=first.fixture_name,
        config_name=first.config_name,
        trials=trials,
        solved_count=solved_count,
        sr_rate=solved_count / trials,
        mean_scr=statistics.fmean(scrs),
        stddev_scr=statistics.pstdev(scrs),
        mean_tte=statistics.fmean(ttes) if ttes else None,
        error_count=error_count,
        subtask_match_rates=subtask_match_rates,
    )


def run_suite(
    fixture_dirs: list[Path],
    configs: dict[str, dict],
    results_dir: Path = Path("benchmarks/results"),
    timeout_s: int = 1800,
    trials: int = 1,
) -> SuiteReport:
    """Run every fixture under every named configuration and write a report.

    A single run of a fixture is noisy - this project's own ablation history
    is the evidence: two one-trial-per-configuration runs of the same
    `enable_inter_reflection` ablation gave different verdicts (0.33 vs 0.25,
    then 0.33 vs 0.33). `trials > 1` re-runs each `(fixture, config)` pair N
    times and reports a solved-rate/mean+stddev instead of a single point
    value, which is what makes a comparison actually trustworthy - `trials=1`
    stays the default so a quick single-fixture check doesn't silently get
    N times slower.

    Args:
        fixture_dirs (list[Path]): Fixtures to run.
        configs (dict[str, dict]): `{config_name: overrides}` - e.g.
            `{"baseline": {}, "no_inter_reflection": {"enable_inter_reflection": False}}`.
        results_dir (Path): Directory for the timestamped report (specs/025 FR-005).
        timeout_s (int): Per-fixture wall-clock budget, passed to `run_fixture()`.
        trials (int): Repeated runs per `(fixture, config)` pair (default 1,
            today's behavior). Total live runs = `len(fixture_dirs) *
            len(configs) * trials` - each is a full live agent run when `llm`
            is not overridden, so raise this deliberately, not by default.

    Returns:
        SuiteReport: aggregate + per-fixture results, already written to disk.
    """
    results: dict[str, list[AggregatedResult]] = {}
    for config_name, overrides in configs.items():
        config_results = []
        for fixture_dir in fixture_dirs:
            trial_results = [
                run_fixture(fixture_dir, config_overrides=overrides, config_name=config_name, timeout_s=timeout_s)
                for _ in range(trials)
            ]
            config_results.append(_aggregate_trials(trial_results))
        results[config_name] = config_results
        ArgusConfig.reset()  # belt-and-suspenders: don't leak this config batch into the next

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report = SuiteReport(timestamp=timestamp, configs=configs, trials=trials, results=results)

    results_dir.mkdir(parents=True, exist_ok=True)
    (results_dir / f"{timestamp}_report.md").write_text(render_report(report), encoding="utf-8")
    return report


def render_report(report: SuiteReport) -> str:
    """Render a `SuiteReport` as Markdown (aggregate + per-fixture tables).

    Args:
        report (SuiteReport): The suite's results.

    Returns:
        str: Markdown report text.
    """
    lines = [f"# Benchmark Suite Report - {report.timestamp}", "", f"Trials per (fixture, configuration): {report.trials}", "", "## Aggregate", ""]
    lines.append("| Configuration | SR (solved/total trials) | Mean SCR (+/- stddev) | Mean TTE (solved only) |")
    lines.append("|---|---|---|---|")
    for config_name, agg_results in report.results.items():
        total_trials = sum(r.trials for r in agg_results)
        total_solved = sum(r.solved_count for r in agg_results)
        mean_scr = statistics.fmean(r.mean_scr for r in agg_results) if agg_results else 0.0
        mean_stddev = statistics.fmean(r.stddev_scr for r in agg_results) if agg_results else 0.0
        fixture_ttes = [r.mean_tte for r in agg_results if r.mean_tte is not None]
        mean_tte_str = f"{statistics.fmean(fixture_ttes):.1f}" if fixture_ttes else "N/A"
        lines.append(f"| {config_name} | {total_solved}/{total_trials} | {mean_scr:.2f} (+/- {mean_stddev:.2f}) | {mean_tte_str} |")
    lines.append("")

    for config_name, agg_results in report.results.items():
        lines.append(f"## Per-fixture detail - {config_name}")
        lines.append("")
        lines.append("| Fixture | SR rate | Mean SCR (+/- stddev) | Mean TTE | Subtask match rates | Errors |")
        lines.append("|---|---|---|---|---|---|")
        for r in agg_results:
            tte_str = f"{r.mean_tte:.1f}" if r.mean_tte is not None else "N/A"
            subtasks_str = ", ".join(f"{name}: {rate:.0%}" for name, rate in r.subtask_match_rates.items()) or "(none)"
            lines.append(
                f"| {r.fixture_name} | {r.solved_count}/{r.trials} | {r.mean_scr:.2f} (+/- {r.stddev_scr:.2f}) | "
                f"{tte_str} | {subtasks_str} | {r.error_count}/{r.trials} |"
            )
        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the Argus subtask-level benchmark suite (specs/025).")
    parser.add_argument(
        "--fixtures", nargs="+", default=None,
        help="Fixture directory names under benchmarks/fixtures/ to run (default: all)."
    )
    parser.add_argument(
        "--configs-json", default=None,
        help='JSON dict of {config_name: overrides}, e.g. '
             '\'{"baseline": {}, "no_inter_reflection": {"enable_inter_reflection": false}}\'. '
             'Default: {"baseline": {}}.'
    )
    parser.add_argument("--timeout", type=int, default=1800, help="Per-fixture wall-clock timeout in seconds.")
    parser.add_argument(
        "--trials", type=int, default=1,
        help="Repeated runs per (fixture, configuration) pair, aggregated with a mean+stddev "
             "(default 1). Raise for a trustworthy ablation comparison - each additional trial "
             "multiplies total live-run time."
    )
    args = parser.parse_args()

    fixtures_root = Path(__file__).parent / "fixtures"
    if args.fixtures:
        selected_dirs = [fixtures_root / name for name in args.fixtures]
    else:
        selected_dirs = sorted(p for p in fixtures_root.iterdir() if p.is_dir() and (p / "server.py").exists())

    selected_configs = json.loads(args.configs_json) if args.configs_json else {"baseline": {}}

    suite_report = run_suite(selected_dirs, selected_configs, timeout_s=args.timeout, trials=args.trials)
    print(render_report(suite_report))
