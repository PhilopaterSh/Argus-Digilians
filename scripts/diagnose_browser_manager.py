"""Standalone diagnostic for specs/029's BrowserManager/VulnerabilityReportWriter.

Answers one concrete question: "is the headless browser actually working, and
why am I not getting an evidence report?" - without needing a live target,
Ollama, or the WSL/Kali SSH bridge. Runs four independent checks and prints a
clear PASS/FAIL per step plus an actionable next step on the first failure,
since `EvasionService.advanced_vuln_probe()` deliberately swallows a capture
failure to protect the underlying text finding (specs/029 FR-005) - which
means a broken Playwright install can silently look identical to "target
genuinely not vulnerable, nothing to report."

Usage:
    Argus_venv\\Scripts\\python.exe scripts\\diagnose_browser_manager.py
    Argus_venv\\Scripts\\python.exe scripts\\diagnose_browser_manager.py --url https://example.com
"""
import argparse
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.tools.browser_manager import BrowserManager, BrowserManagerError
from app.tools.vuln_report_writer import VulnerabilityReportWriter


def _step(n, title):
    print(f"\n[{n}] {title}")
    print("-" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Diagnose whether BrowserManager/VulnerabilityReportWriter (specs/029) are actually working."
    )
    parser.add_argument(
        "--url", default=None,
        help="Optional real URL to navigate to instead of a local test fixture (no network needed if omitted).",
    )
    args = parser.parse_args()

    failures = []

    # 1. Is the `playwright` package importable at all?
    _step(1, "Checking `playwright` package import")
    try:
        import playwright.sync_api  # noqa: F401
        print("[OK] `playwright` package is installed.")
    except ImportError as e:
        print(f"[FAIL] `playwright` is NOT installed: {e}")
        print("       Fix: Argus_venv\\Scripts\\python.exe -m pip install playwright")
        failures.append("playwright package missing")
        _summary(failures)
        return 1

    # 2. Can Chromium actually launch? (separate from step 1 - `pip install
    #    playwright` alone does NOT download the browser binary; this is the
    #    single most common reason capture silently fails)
    _step(2, "Launching headless Chromium via BrowserManager")
    bm = BrowserManager()
    try:
        bm.start("diagnostic")
        print("[OK] Chromium launched successfully.")
    except BrowserManagerError as e:
        print(f"[FAIL] Chromium failed to launch: {e}")
        print("       Fix: Argus_venv\\Scripts\\python.exe -m playwright install chromium")
        failures.append("chromium launch failed")
        _summary(failures)
        return 1

    # 3. Full capture_vulnerability() round-trip - against either the given
    #    --url or a local, offline HTML fixture that mimics a CONFIRMED
    #    path-traversal response (so this step needs no network/target at
    #    all when --url isn't passed).
    _step(3, "Capturing a screenshot (capture_vulnerability())")
    target_url = args.url
    tmp_html = None
    if target_url is None:
        tmp_html = tempfile.NamedTemporaryFile(
            mode="w", suffix=".html", delete=False, encoding="utf-8",
        )
        tmp_html.write(
            "<html><body><pre>root:x:0:0:root:/root:/bin/bash</pre>"
            "<p>Simulated confirmed path-traversal response - diagnose_browser_manager.py fixture</p>"
            "</body></html>"
        )
        tmp_html.close()
        target_url = "file://" + tmp_html.name.replace("\\", "/")
        print(f"[*] No --url given - using local offline fixture: {target_url}")

    evidence = None
    try:
        evidence = bm.capture_vulnerability(
            "path_traversal", target_url, payload="diagnostic", note="diagnose_browser_manager.py",
        )
        shot_path = evidence["screenshot_path"]
        exists = os.path.isfile(shot_path)
        size = os.path.getsize(shot_path) if exists else 0
        if exists and size > 0:
            print(f"[OK] Screenshot written: {shot_path} ({size} bytes)")
        else:
            print(f"[FAIL] capture_vulnerability() returned a path that doesn't exist on disk: {shot_path}")
            failures.append("screenshot file not written")
    except BrowserManagerError as e:
        print(f"[FAIL] Screenshot capture raised: {e}")
        print("       This is the exact failure advanced_vuln_probe() catches and downgrades")
        print("       to a one-line warning in its output - which is why a report never appeared.")
        failures.append("capture_vulnerability() raised")
    finally:
        bm.close()
        if tmp_html is not None:
            try:
                os.unlink(tmp_html.name)
            except OSError:
                pass

    if evidence is None:
        _summary(failures)
        return 1

    # 4. JSON report round-trip (VulnerabilityReportWriter)
    _step(4, "Writing + re-reading the JSON evidence report")
    try:
        report_path = VulnerabilityReportWriter().save_report(
            "diagnose_browser_manager", "path_traversal", [evidence],
        )
        with open(report_path, "r", encoding="utf-8") as f:
            report = json.load(f)
        assert report["total_findings"] == 1
        print(f"[OK] Report written and re-read successfully: {report_path}")
    except Exception as e:
        print(f"[FAIL] Report write/read failed: {e}")
        failures.append("report write/read failed")

    return _summary(failures)


def _summary(failures):
    print("\n" + "=" * 60)
    if not failures:
        print("ALL CHECKS PASSED - BrowserManager and the evidence report pipeline both work.")
        print("If advanced_vuln_probe() still isn't producing a report on a real run, the")
        print("most likely cause is that the target simply wasn't confirmed vulnerable")
        print("(no SENSITIVE_CONTENT_INDICATORS match) - by design, no screenshot is taken")
        print("unless a real finding is first recorded.")
        return 0
    print(f"FAILED at: {', '.join(failures)}")
    print("Fix the first failure above and re-run this script before assuming the target")
    print("itself is the problem.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
