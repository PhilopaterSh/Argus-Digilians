"""specs/020 T006/T007: head-to-head wall-clock comparison between the
production single-loop graph (_build_custom_workflow) and the experimental
multi-role graph (_build_multi_role_workflow), on an equivalent-effort
scenario (exactly 2 real tool calls: one recon-class, one exploit-class,
then a final report) - per NFR-001, this must be measured before the
multi-role path is considered for anything beyond an experiment.

Uses a mocked, fixed per-call latency for both the LLM and the tools
(SIMULATED_LLM_LATENCY_SECONDS / SIMULATED_TOOL_LATENCY_SECONDS below) so
the comparison isolates each topology's own orchestration overhead (how
many LLM decision calls it takes to accomplish the same real work) from
unrelated noise (actual network/Ollama inference variance) - this is a
structural, not an absolute, measurement. Real absolute run time depends on
the actual model's inference speed, which this harness deliberately does
not simulate realistically (0.05s here vs. several real seconds for
WhiteRabbitNeo-V3-7B on this project's target hardware) - what matters is
the CALL-COUNT ratio, which is latency-independent and directly informs
NFR-001's threshold decision.

Not a pytest test (no fixed pass/fail threshold to assert - NFR-001
explicitly requires human/team judgment on the measured numbers, not an
automatic gate) - run directly: `python tests/manual/specs020_wallclock_comparison.py`
"""
import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from langchain_core.messages import AIMessage, HumanMessage
from app.core.agent.react_workflow import _build_custom_workflow, _build_multi_role_workflow

SIMULATED_LLM_LATENCY_SECONDS = 0.05
SIMULATED_TOOL_LATENCY_SECONDS = 0.02


class TimedMockLLM:
    """Cycles through fixed responses like the test suite's MockLLM, but
    sleeps SIMULATED_LLM_LATENCY_SECONDS per call to give wall-clock
    comparison something non-zero and consistent to measure."""

    def __init__(self, responses: list[str]):
        self.responses = responses
        self.call_count = 0

    def invoke(self, messages, **kwargs):
        time.sleep(SIMULATED_LLM_LATENCY_SECONDS)
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return AIMessage(content=response)


def timed_recon(target: str) -> str:
    time.sleep(SIMULATED_TOOL_LATENCY_SECONDS)
    return "Subdomains: admin.test.com, api.test.com."


def Run_Nikto(target: str) -> str:
    """Same name as the real tool so EXPLOITATION_TOOLS/PHASE_5_6_TOOLS
    allowlists recognise it, matching the test suite's own convention."""
    time.sleep(SIMULATED_TOOL_LATENCY_SECONDS)
    return "Nikto scan complete: found /admin/ directory listing enabled."


BASE_STATE = {
    "messages": [HumanMessage(content="Scan https://test.com")],
    "target": "https://test.com",
    "phase": "recon",
    "blackboard_summary": "",
    "iteration_count": 0,
    "max_iterations": 15,
    "tool_name": None,
    "tool_input": None,
    "tool_result": None,
    "tool_error": None,
    "tool_call_history": [],
    "reflection_notes": [],
    "phase56_nudged": False,
    "current_role": "",
    "role_history": [],
    "remaining_steps": 15,
}


def run_single_loop() -> tuple[float, int]:
    llm = TimedMockLLM([
        'Thought: recon.\nAction: {"name": "timed_recon", "input": "https://test.com"}',
        'Thought: scan.\nAction: {"name": "Run_Nikto", "input": "https://test.com"}',
        "Final Answer: comprehensive report",
    ])
    graph = _build_custom_workflow(llm, [timed_recon, Run_Nikto], enable_inter_reflection=False)
    start = time.time()
    graph.invoke(dict(BASE_STATE))
    elapsed = time.time() - start
    return elapsed, llm.call_count


def run_multi_role() -> tuple[float, int]:
    llm = TimedMockLLM([
        "Start with collector to map the attack surface.",
        'Thought: recon.\nAction: {"name": "timed_recon", "input": "https://test.com"}',
        "Recon is done, send this to the exploiter for vulnerability testing.",
        'Thought: scan.\nAction: {"name": "Run_Nikto", "input": "https://test.com"}',
        "Both steps done, time to summarize.",
        "Final Answer: comprehensive report",
    ])
    graph = _build_multi_role_workflow(
        llm, {"collector": [timed_recon], "exploiter": [Run_Nikto]},
        enable_inter_reflection=False,
    )
    start = time.time()
    graph.invoke(dict(BASE_STATE))
    elapsed = time.time() - start
    return elapsed, llm.call_count


def main():
    single_time, single_calls = run_single_loop()
    multi_time, multi_calls = run_multi_role()

    print("=" * 60)
    print("specs/020 NFR-001: wall-clock comparison (mocked latency)")
    print("=" * 60)
    print(f"Single-loop graph:  {single_time:.4f}s wall-clock, {single_calls} LLM calls")
    print(f"Multi-role graph:   {multi_time:.4f}s wall-clock, {multi_calls} LLM calls")
    print("-" * 60)
    call_ratio = multi_calls / single_calls
    time_ratio = multi_time / single_time
    print(f"LLM call-count ratio (multi-role / single-loop): {call_ratio:.2f}x")
    print(f"Wall-clock ratio (mocked latency):                {time_ratio:.2f}x")
    print("=" * 60)
    print(
        "NOTE: call-count ratio is the latency-independent, structurally "
        "meaningful number - it directly scales to real inference time "
        "(each extra LLM call costs several real seconds against "
        "WhiteRabbitNeo-V3-7B on this project's hardware, not the 0.05s "
        "simulated here)."
    )


if __name__ == "__main__":
    main()
