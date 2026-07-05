"""
Argus Report Engine - Generates JSON and Markdown reports with severity scoring.
"""
import json
from datetime import datetime
from pathlib import Path


SEVERITY_WEIGHTS = {
    "Critical": 10,
    "High": 7,
    "Medium": 4,
    "Low": 2,
    "Info": 0
}


class ReportEngine:
    def __init__(self, memory, reports_dir: Path):
        self.memory = memory
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def severity_score(self, findings: list) -> int:
        """
        Risk score 1-10 driven by worst finding severity, with a bonus for finding count.
        Old formula averaged over all findings, so Info/Low diluted everything to 1/10.
        New formula:
          - Base  = weight of the single worst finding (0-10)
          - Bonus = min(2, total_weight // 8)  → at most +2 for many serious findings
        Examples:
          1 Critical (10) + 4 Info (0) → base=10, bonus=min(2,10//8)=1 → 10 (capped)
          1 High (7) + 5 Info (0)      → base=7,  bonus=min(2,7//8)=0  → 7
          2 High (14) + 1 Medium (4)   → base=7,  bonus=min(2,18//8)=2 → 9
          6 Info (0)                   → base=0,  bonus=0              → max(1,0)=1
        """
        if not findings:
            return 1
        weights   = [SEVERITY_WEIGHTS.get(f.get('severity', 'Info'), 0) for f in findings]
        max_w     = max(weights)
        total_w   = sum(weights)
        bonus     = min(2, total_w // 8)
        score     = max_w + bonus
        return max(1, min(10, score))

    def generate(self, target: str, scan_mode: str = "passive") -> tuple:
        """Generates both JSON and Markdown reports. Returns (json_path, md_path, score)."""
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        clean_target = target.replace('https://', '').replace('http://', '').split('/')[0]
        safe_name = "".join(c if c.isalnum() or c in '.-_' else '_' for c in clean_target)

        # Get data from memory
        blackboard_raw = self.memory.get_blackboard_summary()
        try:
            blackboard = json.loads(blackboard_raw)
        except Exception:
            blackboard = {}

        graph = self.memory.get_graph_insights()

        # Build findings list — skip entries whose key is not a valid domain.
        # A domain key that contains spaces is a full query string that leaked in
        # due to the _extract_target() bug; entries longer than 253 chars are also invalid.
        def _is_valid_domain_key(key: str) -> bool:
            if not key or ' ' in key or len(key) > 253:
                return False
            # Must contain at least one dot and no control characters
            return '.' in key and all(c.isprintable() for c in key)

        findings = []
        for domain, tools in blackboard.items():
            if not _is_valid_domain_key(domain):
                continue
            for tool_type, data in tools.items():
                sev = data.get('severity', 'Info')
                summary = data.get('summary', '')
                findings.append({
                    "target": domain,
                    "tool": tool_type,
                    "severity": sev,
                    "summary": summary
                })

        score = self.severity_score(findings)

        # Build report dict
        report = {
            "meta": {
                "target": clean_target,
                "scan_mode": scan_mode,
                "generated_at": datetime.now().isoformat(),
                "tool": "Argus Security Framework v2.0",
                "risk_score": score
            },
            "summary": {
                "total_findings": len(findings),
                "severity_breakdown": self._severity_breakdown(findings),
                "knowledge_graph": graph
            },
            "findings": findings
        }

        # Write JSON
        json_path = self.reports_dir / f"argus_{safe_name}_{ts}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        # Write Markdown
        md_path = self.reports_dir / f"argus_{safe_name}_{ts}.md"
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(self._to_markdown(report))

        print(f"[+] JSON Report: {json_path}")
        print(f"[+] Markdown Report: {md_path}")
        return str(json_path), str(md_path), score

    def _severity_breakdown(self, findings: list) -> dict:
        breakdown = {k: 0 for k in SEVERITY_WEIGHTS}
        for f in findings:
            sev = f.get('severity', 'Info')
            if sev in breakdown:
                breakdown[sev] += 1
        return breakdown

    def _to_markdown(self, report: dict) -> str:
        meta = report['meta']
        summary = report['summary']
        findings = report['findings']

        lines = [
            f"# Argus Security Report",
            f"**Target:** {meta['target']}",
            f"**Scan Mode:** {meta['scan_mode']}",
            f"**Generated:** {meta['generated_at']}",
            f"**Risk Score:** {meta['risk_score']}/10",
            f"",
            f"## Summary",
            f"- Total Findings: {summary['total_findings']}",
        ]
        for sev, count in summary['severity_breakdown'].items():
            if count > 0:
                lines.append(f"- {sev}: {count}")

        lines.extend(["", "## Knowledge Graph Relationships", ""])
        graph = summary.get("knowledge_graph", "")

        if graph:
            lines.append(graph)
        else:
            lines.append("_No graph relationships recorded._")

        lines.extend(["", "## Findings", ""])
        if findings:
            for f in findings:
                lines.append(
                    f"### [{f.get('severity', 'Info')}] "
                    f"{f.get('tool', 'unknown')} — {f.get('target', '')}"
                )
                lines.append(f"- **Summary:** {f.get('summary', '')}")
                lines.append("")
        else:
            lines.append("_No findings recorded._")

        return "\n".join(lines)
