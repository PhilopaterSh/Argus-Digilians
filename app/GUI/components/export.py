import json
import os
import re
from datetime import datetime, timezone

# Event `detail` strings are free text produced by the ReAct loop
# (app/core/agent/react_callback.py). These prefixes are how a step is
# classified for the trace section - matching the format app/core/prompts.py
# requires the model to emit.
_STEP_PREFIXES = ("Thought:", "Action:", "Observation:", "Reflection:",
                  "Action Input:", "Final Answer:")
_ACTION_NAME_RE = re.compile(r'"name"\s*:\s*"([A-Za-z_0-9]+)"')


def _format_duration(started_at, updated_at):
    """Human-readable elapsed time between two ISO timestamps.

    Args:
        started_at (str): ISO start timestamp.
        updated_at (str): ISO end timestamp.

    Returns:
        str: e.g. "11m 33s", or "unknown" if either value is missing or
        unparseable (never raises - a report must render regardless).
    """
    try:
        start = datetime.fromisoformat(str(started_at).replace("Z", "+00:00"))
        end = datetime.fromisoformat(str(updated_at).replace("Z", "+00:00"))
        seconds = int((end - start).total_seconds())
        if seconds < 0:
            return "unknown"
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes}m {seconds}s" if minutes else f"{seconds}s"
    except Exception:
        return "unknown"


def _tools_invoked(events):
    """Extract the ordered list of tool names the agent actually called.

    Args:
        events (list[dict]): Run events with a `detail` string.

    Returns:
        list[str]: Tool names in call order, duplicates preserved so a
        repeated call is visible rather than silently collapsed.
    """
    names = []
    for event in events or []:
        for match in _ACTION_NAME_RE.finditer(str(event.get("detail", ""))):
            names.append(match.group(1))
    return names


def generate_run_report_markdown(run_state, log_tail=""):
    """Render the complete assessment record for one agent run as Markdown.

    This is the downloadable companion to the GUI's on-screen summary
    (`app/GUI/tabs/agent.py`): the screen shows findings and risk, while
    everything needed to audit or reproduce the run - every tool call, every
    observation, the raw process log - lives here instead of being dumped
    into expanders as raw JSON.

    Args:
        run_state (dict): A run snapshot as written by
            `app/core/agent/contracts.py` and polled by `AgentController` -
            `run_id`/`target`/`mode`/`status`/`started_at`/`updated_at`/
            `events`/`final_state`.
        log_tail (str): The agent subprocess's captured stdout/stderr, from
            `AgentController.get_log_tail()`. Optional.

    Returns:
        str: A Markdown document. Sections absent from `run_state` are
        skipped rather than rendered empty, and nothing is invented -
        an empty run yields a short report saying so.
    """
    state = run_state or {}
    final = state.get("final_state") or {}
    findings = final.get("findings") or []
    events = state.get("events") or []
    target = state.get("target") or final.get("target") or "unknown"

    lines = [
        "# Argus Security Assessment",
        "",
        f"**Target**: {target}  ",
        f"**Run ID**: `{state.get('run_id', 'n/a')}`  ",
        f"**Mode**: {state.get('mode', 'n/a')}  ",
        f"**Status**: {state.get('status', 'n/a')}  ",
        f"**Started**: {state.get('started_at', 'n/a')}  ",
        f"**Finished**: {state.get('updated_at', 'n/a')}  ",
        f"**Duration**: {_format_duration(state.get('started_at'), state.get('updated_at'))}  ",
        f"**Report generated**: {datetime.now(timezone.utc).isoformat()}",
        "",
        "---",
        "",
    ]

    section = [0]

    def heading(title):
        """Next section heading, numbered so gaps can't appear.

        Args:
            title (str): Section title.

        Returns:
            str: e.g. "## 3. Findings".
        """
        section[0] += 1
        return f"## {section[0]}. {title}"

    lines += [heading("Executive Summary"), ""]

    risk = final.get("overall_risk_score")
    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Overall risk score | {risk if risk is not None else 'N/A'} / 10 |")
    lines.append(f"| Confirmed findings | {len(findings)} |")
    lines.append(f"| Tool calls made | {len(_tools_invoked(events))} |")
    lines.append("")

    if final.get("summary"):
        lines += [final["summary"], ""]
    if final.get("attack_surface_stats"):
        lines += [f"**Attack surface**: {final['attack_surface_stats']}", ""]
    if final.get("parse_warning"):
        lines += [f"> **Warning**: {final['parse_warning']}", ""]

    lines += ["---", "", heading("Findings"), ""]
    if findings:
        for index, finding in enumerate(findings, 1):
            lines += [
                f"### {index}. [{finding.get('severity', '?')}] "
                f"{finding.get('issue', 'Unknown issue')}",
                "",
                f"- **Affected endpoint**: `{finding.get('target', 'n/a')}`",
                f"- **Detected by**: `{finding.get('tool_source') or 'n/a'}`",
                f"- **Proof-of-concept payload**: `{finding.get('suggested_payload') or 'n/a'}`",
                "",
                finding.get("description", "") or "_No description recorded._",
                "",
            ]
            if finding.get("remediation"):
                lines += [f"**Remediation**: {finding['remediation']}", ""]
    else:
        lines += ["No vulnerabilities were confirmed during this run.", ""]

    lines += ["---", "", heading("Assessment Trace"), ""]
    tools = _tools_invoked(events)
    if tools:
        lines += ["**Tools executed, in order:**", ""]
        for position, name in enumerate(tools, 1):
            lines.append(f"{position}. `{name}`")
        lines.append("")
    if events:
        lines += ["<details>", "<summary>Full step-by-step trace "
                  f"({len(events)} events)</summary>", ""]
        for event in events:
            detail = str(event.get("detail", "")).strip()
            timestamp = event.get("timestamp", "")
            status = event.get("status", "")
            label = next(
                (p.rstrip(":") for p in _STEP_PREFIXES if detail.startswith(p)),
                "Step",
            )
            lines += [
                f"#### {label} - `{timestamp}` ({status})",
                "",
                "```",
                detail or "(no detail recorded)",
                "```",
                "",
            ]
        lines += ["</details>", ""]
    else:
        lines += ["_No events were recorded for this run._", ""]

    if final.get("output"):
        lines += ["---", "", heading("Model's Full Report"), "",
                  str(final["output"]), ""]

    if log_tail and log_tail.strip():
        lines += ["---", "", heading("Process Log (stdout/stderr)"), "",
                  "```", log_tail.strip(), "```", ""]

    lines += ["---", "", heading("Conclusion"), ""]
    if findings:
        severities = ", ".join(
            sorted({str(f.get("severity", "?")) for f in findings})
        )
        lines.append(
            f"The assessment confirmed **{len(findings)} finding(s)** "
            f"(severity: {severities}) against `{target}`. Each finding above "
            f"includes the exact payload that reproduced it."
        )
    else:
        lines.append(
            f"No vulnerabilities were confirmed against `{target}` by the tools "
            f"run in this assessment. This is not proof the target is secure - "
            f"it reflects only what the tools above actually tested."
        )
    lines.append("")
    for step in final.get("next_steps") or []:
        lines.append(f"- {step}")
    lines += ["", "---", "", "*Generated by Argus Security Framework*"]

    return "\n".join(lines)


def run_report_filename(run_state):
    """Build a filesystem-safe filename for a run's Markdown report.

    Args:
        run_state (dict): The run snapshot (uses `target` and `run_id`).

    Returns:
        str: e.g. `argus_report_example.com_3b770ffb.md`.
    """
    state = run_state or {}
    target = str(state.get("target") or "target")
    safe = re.sub(r"[^A-Za-z0-9._-]", "_",
                  target.replace("https://", "").replace("http://", "")).strip("_")
    run_id = str(state.get("run_id") or "")[:8] or "run"
    return f"argus_report_{safe or 'target'}_{run_id}.md"


def generate_html_report(findings, target, template=None):
    """Render a self-contained dark-themed HTML security report.

    Args:
        findings (list[dict]): Findings, each with `severity`/`type`/
            `summary` keys (missing keys default to "info"/"?").
        target (str): The scanned target, shown in the report header.
        template: Currently unused by this function's own body - accepted
            for call-site compatibility.

    Returns:
        str: A complete HTML document string (executive summary table,
        per-finding table, and a raw-JSON technical-details section).
    """
    safe_name = target.replace("https://", "").replace("http://", "").replace("/", "_")
    html = [
        "<!DOCTYPE html><html><head><meta charset='utf-8'>",
        "<title>Argus Security Report</title>",
        "<style>",
        "body{background:#0e1117;color:#ccc;font-family:'Courier New',monospace;padding:30px;max-width:960px;margin:auto;}",
        "h1{color:#00ff41;border-bottom:2px solid #00ff41;padding-bottom:10px;}",
        "h2{color:#00ff41;margin-top:30px;}",
        "table{border-collapse:collapse;width:100%;margin:15px 0;}",
        "th,td{padding:10px;text-align:left;border-bottom:1px solid #333;}",
        "th{background:#1a1d24;color:#00ff41;}",
        ".critical{color:#ff4444;font-weight:bold;}",
        ".high{color:#ffaa00;font-weight:bold;}",
        ".medium{color:#ffff00;}",
        ".low{color:#44ff44;}",
        ".info{color:#888;}",
        ".summary-card{background:#1a1d24;padding:20px;border-radius:8px;margin:15px 0;border-left:4px solid #00ff41;}",
        ".footer{text-align:center;color:#555;margin-top:50px;font-size:0.8rem;}",
        "</style></head><body>",
        f"<h1>:shield: Argus Security Report</h1>",
        f"<p><strong>Target:</strong> {target}</p>",
        f"<p><strong>Generated:</strong> {datetime.now(timezone.utc).isoformat()}</p>",
        f"<p><strong>Report ID:</strong> ARGUS-{datetime.now():%Y%m%d-%H%M%S}</p>",
    ]

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info").lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

    html.append("<h2>Executive Summary</h2>")
    html.append(f"<div class='summary-card'>")
    html.append(f"<p>Total Findings: <strong>{len(findings)}</strong></p>")
    html.append(f"<p>Critical: <strong class='critical'>{severity_counts['critical']}</strong> | "
                f"High: <strong class='high'>{severity_counts['high']}</strong> | "
                f"Medium: <strong class='medium'>{severity_counts['medium']}</strong> | "
                f"Low: <strong class='low'>{severity_counts['low']}</strong></p>")
    html.append("</div>")

    html.append("<h2>Findings Detail</h2>")
    if findings:
        html.append("<table><tr><th>Severity</th><th>Type</th><th>Summary</th></tr>")
        for f in findings:
            sev = f.get("severity", "info").lower()
            html.append(
                f"<tr><td class='{sev}'>[{sev.upper()}]</td>"
                f"<td>{f.get('type', '?')}</td>"
                f"<td>{f.get('summary', '?')}</td></tr>"
            )
        html.append("</table>")
    else:
        html.append("<p>No findings recorded.</p>")

    html.append("<h2>Technical Details</h2>")
    html.append(f"<pre style='background:#1a1d24;padding:15px;border-radius:4px;overflow:auto;'>{json.dumps(findings, indent=2, default=str)}</pre>")

    html.append("<div class='footer'>")
    html.append("Generated by Argus Security Framework | Confidential")
    html.append("</div></body></html>")
    return "\n".join(html)


def generate_markdown_report(findings, target):
    """Render a Markdown security report.

    Args:
        findings (list[dict]): Findings, each with `severity`/`type`/
            `summary` keys (missing keys default to "info"/"?").
        target (str): The scanned target, shown in the report header.

    Returns:
        str: A Markdown document (summary table, per-severity counts,
        and a bulleted findings list).
    """
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
    for f in findings:
        sev = f.get("severity", "info").lower()
        if sev in severity_counts:
            severity_counts[sev] += 1

    lines = [
        f"# Argus Security Report",
        f"",
        f"**Target**: {target}",
        f"**Generated**: {datetime.now(timezone.utc).isoformat()}",
        f"",
        f"## Executive Summary",
        f"",
        f"| Severity | Count |",
        f"|----------|-------|",
    ]
    for sev in ["critical", "high", "medium", "low", "info"]:
        if severity_counts[sev] > 0:
            lines.append(f"| {sev.title()} | {severity_counts[sev]} |")
    lines.extend([
        f"",
        f"**Total Findings**: {len(findings)}",
        f"",
        f"## Findings",
        f"",
    ])
    for f in findings:
        sev = f.get("severity", "info").upper()
        ftype = f.get("type", "?")
        summary = f.get("summary", "?")
        lines.append(f"- **[{sev}]** {ftype}: {summary}")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"*Generated by Argus Security Framework*")
    return "\n".join(lines)


def generate_json_report(findings, target):
    """Render a machine-readable JSON security report.

    Args:
        findings (list[dict]): Findings included verbatim under the
            report's `findings` key.
        target (str): The scanned target.

    Returns:
        str: A pretty-printed JSON string with `report_type`, `target`,
        `generated_at`, `findings_count`, `findings`, and `metadata` keys.
    """
    report = {
        "report_type": "Argus Security Assessment",
        "target": target,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "findings_count": len(findings),
        "findings": findings,
        "metadata": {
            "framework": "Argus Security Framework",
            "version": "2.0.0",
        },
    }
    return json.dumps(report, indent=2, default=str)


def get_available_templates():
    """List available HTML report template filenames.

    Returns:
        list[str]: `.html` filenames under `app/GUI/templates/reports/`,
        or `["default.html"]` if that directory doesn't exist.
    """
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates", "reports")
    if os.path.exists(templates_dir):
        return [f for f in os.listdir(templates_dir) if f.endswith(".html")]
    return ["default.html"]
