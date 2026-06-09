import json
import os
from datetime import datetime


class JSONReportWriter:
    """Responsible only for writing structured reports to disk."""

    def __init__(self, reports_dir: str = "reports"):
        self.reports_dir = reports_dir

    def save_json_report(self, domain: str, data: dict) -> str:
        os.makedirs(self.reports_dir, exist_ok=True)
        filename = f"intel_{domain}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        path = os.path.join(self.reports_dir, filename)

        with open(path, "w", encoding="utf-8") as report_file:
            json.dump(data, report_file, indent=4)

        print(f"[+] Structured intelligence saved to: {path}")
        return path
