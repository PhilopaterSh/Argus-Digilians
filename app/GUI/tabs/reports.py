import glob
import json
import os
from datetime import datetime, timezone

import streamlit as st

_AGENT_RUNS_DIR = os.path.join("logs", "agent_runs")


def _latest_run_for_target(target_url):
    """Finds the most recent agent run file for this target on disk.

    Previously this tab read st.session_state.jobs for findings - a list
    initialized to [] in dashboard.py that nothing ever appends to, so
    "Generate Report" always produced a report with 0 findings even right
    after a fully successful agent run. Reports now pull real results from
    the same run state files scripts/run_agent.py writes.
    """
    paths = glob.glob(os.path.join(_AGENT_RUNS_DIR, "agent_*.json"))
    paths.sort(key=os.path.getmtime, reverse=True)
    for path in paths:
        try:
            with open(path, "r", encoding="utf-8") as handle:
                run = json.load(handle)
        except (OSError, json.JSONDecodeError):
            continue
        if run.get("target") == target_url:
            return run
    return None


def render_reports():
    st.title(":page_facing_up: Report Generation")
    st.markdown("---")

    targets = st.session_state.get("targets", [])

    if not targets:
        st.warning("No targets available. Add targets and run the agent first.")
        return

    target_urls = [t["url"] for t in targets]
    selected_target = st.selectbox("Select Target", target_urls)

    target_obj = next((t for t in targets if t["url"] == selected_target), None)

    col1, col2 = st.columns(2)
    with col1:
        report_format = st.selectbox("Report Format", ["HTML", "Markdown", "JSON"])
    with col2:
        include_raw = st.checkbox("Include Raw Data", value=False)

    st.markdown("---")
    st.subheader(":hammer_and_wrench: Generate")

    if st.button(":gear: Generate Report", type="primary"):
        run = _latest_run_for_target(selected_target)
        if not run:
            st.warning(f"No agent run found yet for {selected_target}. Run the agent first to generate a real report.")
            return

        final_state = run.get("final_state", {})
        exploit_success = final_state.get("exploit_success", False)
        # Real vulnerability findings (app/core/agent/nodes/scanner.py) carry
        # {tool, port, summary, url} - no "severity"/"type" keys, which is
        # what this report renderer expects further down. Map them here
        # instead of silently rendering every real finding as "?"/info.
        findings = [
            {
                "type": f.get("tool", "?"),
                "summary": f.get("summary", "?"),
                "severity": "critical" if exploit_success else "medium",
            }
            for f in final_state.get("vulnerabilities", [])
        ]

        report_data = {
            "title": f"Argus Security Report - {selected_target}",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "target": selected_target,
            "target_type": target_obj.get("type", "url") if target_obj else "url",
            "summary": {
                "total_findings": len(findings),
                "critical": len([f for f in findings if f.get("severity") == "critical"]),
                "high": len([f for f in findings if f.get("severity") == "high"]),
                "medium": len([f for f in findings if f.get("severity") == "medium"]),
                "low": len([f for f in findings if f.get("severity") == "low"]),
            },
            "findings": findings if include_raw else [
                {"type": f.get("type", "?"), "summary": f.get("summary", "?"), "severity": f.get("severity", "info")}
                for f in findings
            ],
        }

        if report_format == "JSON":
            report_str = json.dumps(report_data, indent=2, default=str)
            mime = "application/json"
            ext = "json"
        elif report_format == "Markdown":
            md_lines = [
                f"# {report_data['title']}",
                f"",
                f"**Generated**: {report_data['generated_at']}",
                f"**Target**: {report_data['target']}",
                f"",
                f"## Summary",
                f"",
                f"| Severity | Count |",
                f"|----------|-------|",
                f"| Critical | {report_data['summary']['critical']} |",
                f"| High     | {report_data['summary']['high']} |",
                f"| Medium   | {report_data['summary']['medium']} |",
                f"| Low      | {report_data['summary']['low']} |",
                f"",
                f"## Findings",
                f"",
            ]
            for f in report_data["findings"]:
                md_lines.append(f"- **[{f.get('severity', 'info').upper()}]** {f.get('type', '?')}: {f.get('summary', '?')}")
            report_str = "\n".join(md_lines)
            mime = "text/markdown"
            ext = "md"
        else:
            html_lines = [
                "<!DOCTYPE html><html><head><meta charset='utf-8'>",
                "<title>Argus Security Report</title>",
                "<style>body{background:#0e1117;color:#ccc;font-family:monospace;padding:20px;}",
                "h1{color:#00ff41;}h2{color:#00ff41;}table{border-collapse:collapse;width:100%;}",
                "th,td{padding:8px;text-align:left;border-bottom:1px solid #333;}",
                ".critical{color:#ff4444;}.high{color:#ffaa00;}.medium{color:#ffff00;}.low{color:#44ff44;}</style></head><body>",
                f"<h1>{report_data['title']}</h1>",
                f"<p>Generated: {report_data['generated_at']}</p>",
                f"<p>Target: <strong>{report_data['target']}</strong></p>",
                "<h2>Summary</h2><table><tr><th>Severity</th><th>Count</th></tr>",
                f"<tr><td class='critical'>Critical</td><td>{report_data['summary']['critical']}</td></tr>",
                f"<tr><td class='high'>High</td><td>{report_data['summary']['high']}</td></tr>",
                f"<tr><td class='medium'>Medium</td><td>{report_data['summary']['medium']}</td></tr>",
                f"<tr><td class='low'>Low</td><td>{report_data['summary']['low']}</td></tr>",
                "</table><h2>Findings</h2><ul>",
            ]
            for f in report_data["findings"]:
                sev = f.get("severity", "info")
                html_lines.append(f"<li class='{sev}'><strong>[{sev.upper()}]</strong> {f.get('type', '?')}: {f.get('summary', '?')}</li>")
            html_lines.append("</ul></body></html>")
            report_str = "\n".join(html_lines)
            mime = "text/html"
            ext = "html"

        safe_name = selected_target.replace("https://", "").replace("http://", "").replace("/", "_").replace(":", "_")
        filename = f"Argus_Report_{safe_name}.{ext}"

        st.download_button(
            label=f":inbox_tray: Download {report_format} Report",
            data=report_str,
            file_name=filename,
            mime=mime,
        )
        st.success(f"Report generated: {filename}")
