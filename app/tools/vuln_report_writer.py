"""JSON evidence-report writer for screenshot-backed vulnerability findings
(specs/029-vulnerability-screenshot-evidence).

Mirrors `app/tools/reachability.py::JSONReportWriter.save_json_report()`'s
exact convention (same `reports/` directory, same target-sanitization regex,
same `%Y%m%d_%H%M%S` timestamp format) rather than inventing a second
convention for what is functionally the same kind of artifact.
"""
import json
import os
import re
from datetime import datetime, timezone


class VulnerabilityReportWriter:
    """Persists `BrowserManager.capture_vulnerability()` evidence dicts to a
    single JSON report file per probe run."""

    def save_report(self, target: str, vulnerability_type: str, evidence: list) -> str:
        """Write a JSON evidence report to `reports/`.

        Args:
            target (str): Target domain/URL; sanitized (non-word characters
                replaced with `_`) and used in the output filename.
            vulnerability_type (str): The vulnerability class this report
                covers, e.g. `"path_traversal"`.
            evidence (list[dict]): Evidence dicts as returned by
                `BrowserManager.capture_vulnerability()` - each already
                JSON-serializable.

        Returns:
            str: The path of the written report file, in the form
            `reports/vulnerability_report_{safe_target}_{timestamp}.json`.
        """
        os.makedirs("reports", exist_ok=True)
        safe_target = re.sub(r"[^\w\.-]", "_", target)
        timestamp = datetime.now()
        path = (
            f"reports/vulnerability_report_{safe_target}_"
            f"{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        )

        report = {
            "target": target,
            "vulnerability_type": vulnerability_type,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "total_findings": len(evidence),
            "evidence": evidence,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, default=str)

        print(f"[+] Vulnerability evidence report saved to: {path}")
        return path
