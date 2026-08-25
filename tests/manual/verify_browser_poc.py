"""Manual end-to-end verification for the headless-browser evidence capture
(specs/029, app/tools/browser_manager.py::BrowserManager).

The unit suite in tests/test_tools/test_browser_manager.py mocks Playwright
entirely, so it passes even on a machine where Playwright or Chromium is not
installed. This script is the opposite check: it launches a REAL headless
Chromium and writes a REAL .png, so it fails loudly when the runtime setup is
missing.

Everything runs against a throwaway HTTP server bound to 127.0.0.1 on an
ephemeral port. No external host is ever contacted. That local server is
deliberately vulnerable to path traversal (it joins an unsanitised `filename`
query parameter onto a lab directory), and the file it leaks is a fixture this
script creates in a temp directory - never a real system file.

Usage, from the repo root:

    Argus_venv\\Scripts\\python.exe tests\\manual\\verify_browser_poc.py

Exit code 0 means a non-empty PNG was produced.
"""
from __future__ import annotations

import os
import shutil
import sys
import tempfile
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from app.tools.browser_manager import BrowserManager, BrowserManagerError  # noqa: E402

LAB_DIR = Path(tempfile.mkdtemp(prefix="argus_browser_lab_"))
WEBROOT = LAB_DIR / "public"


def _seed_lab() -> None:
    """Create the fake webroot plus the 'sensitive' file the traversal leaks."""
    WEBROOT.mkdir(parents=True, exist_ok=True)
    (WEBROOT / "index.html").write_text(
        "<h1>Argus lab target</h1>", encoding="utf-8"
    )
    secret = LAB_DIR / "etc"
    secret.mkdir(parents=True, exist_ok=True)
    (secret / "passwd").write_text(
        "root:x:0:0:root:/root:/bin/bash\n"
        "daemon:x:1:1:daemon:/usr/sbin:/usr/sbin/nologin\n"
        "argus-lab:x:1000:1000:LOCAL LAB FIXTURE - not a real system file"
        ":/home/argus:/bin/sh\n",
        encoding="utf-8",
    )


LANDING_PAGE = """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Argus Lab Store</title><style>
body { font-family: Arial, Helvetica, sans-serif; margin:0; color:#222; }
header { background:#1f2a44; color:#fff; padding:18px 32px; }
header h1 { margin:0; font-size:20px; }
nav { background:#2c3a5c; padding:10px 32px; color:#cfd6e6; font-size:13px; }
nav span { margin-right:22px; }
main { padding:28px 32px; }
.grid { display:flex; gap:20px; margin-top:18px; }
.card { border:1px solid #ddd; border-radius:6px; width:190px; padding:14px; }
.card .ph { background:#e8ebf2; height:110px; border-radius:4px; }
.card h3 { font-size:14px; margin:12px 0 4px; }
.card p { font-size:12px; color:#666; margin:0; }
footer { border-top:1px solid #ddd; margin-top:28px; padding:14px 32px;
         font-size:11px; color:#888; }
</style></head><body>
<header><h1>Argus Lab Store</h1></header>
<nav><span>Home</span><span>Catalogue</span><span>Offers</span><span>Account</span></nav>
<main>
  <h2>Featured products</h2>
  <p>LOCAL LAB FIXTURE - this site exists only on 127.0.0.1 for testing.</p>
  <div class="grid">
    <div class="card"><div class="ph"></div><h3>Product 1</h3><p>$19.99</p></div>
    <div class="card"><div class="ph"></div><h3>Product 2</h3><p>$24.50</p></div>
    <div class="card"><div class="ph"></div><h3>Product 3</h3><p>$31.00</p></div>
  </div>
</main>
<footer>Argus Security Framework - local verification target</footer>
</body></html>"""


class _VulnerableHandler(BaseHTTPRequestHandler):
    """Path-traversal-vulnerable static file server. LOCAL LAB FIXTURE ONLY."""

    def do_GET(self):  # noqa: N802 - BaseHTTPRequestHandler's required name
        parsed = urllib.parse.urlparse(self.path)
        filename = urllib.parse.parse_qs(parsed.query).get("filename", [""])[0]

        if not filename:
            # The landing page. `BrowserManager.capture_site_context()`
            # photographs this, so it is deliberately styled like a real
            # site rather than one bare line of text.
            self._send(200, LANDING_PAGE)
            return

        # Deliberately unsanitised join - this IS the vulnerability under test.
        target = os.path.join(str(WEBROOT), filename)
        try:
            with open(target, "r", encoding="utf-8", errors="replace") as fh:
                content = fh.read()
        except OSError as exc:
            self._send(404, f"<pre>not found: {exc}</pre>")
            return

        # /image mirrors PortSwigger's lab endpoint: it keeps claiming to be
        # a JPEG even when the traversal makes it return a text file. That is
        # the case that used to produce a blank broken-image screenshot.
        # /view is the plain text/html variant.
        if parsed.path == "/image":
            self._send(200, content, content_type="image/jpeg")
        else:
            self._send(200, f"<pre>{content}</pre>")

    def _send(self, code: int, body: str, content_type: str = "text/html; charset=utf-8") -> None:
        raw = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def log_message(self, *_args) -> None:  # keep the console clean
        pass


def main() -> int:
    _seed_lab()

    server = ThreadingHTTPServer(("127.0.0.1", 0), _VulnerableHandler)
    port = server.server_address[1]
    threading.Thread(target=server.serve_forever, daemon=True).start()

    payload = "../etc/passwd"
    out_dir = REPO_ROOT / "artifacts" / "screenshots"
    note = (
        "LOCAL LAB: unsanitised 'filename' parameter served a file outside "
        "the webroot"
    )

    # Two shapes of the same finding. The second one - the response that
    # claims to be a JPEG - is the one that used to yield a blank
    # broken-image screenshot.
    cases = [
        ("renderable text/html response", f"http://127.0.0.1:{port}/view?filename={payload}", "page"),
        ("response mislabelled as image/jpeg", f"http://127.0.0.1:{port}/image?filename={payload}", "view_source"),
    ]

    print(f"[*] lab webroot : {WEBROOT}")
    print(f"[*] output dir  : {out_dir}")

    results = []
    try:
        with BrowserManager(screenshot_dir=str(out_dir)) as bm:
            for label, url, expected_mode in cases:
                print(f"\n[*] case: {label}")
                print(f"    url : {url}")
                evidence = bm.capture_vulnerability(
                    "path_traversal", url, payload=payload, note=note
                )
                results.append((label, expected_mode, evidence))
    except BrowserManagerError as exc:
        print(f"[X] FAILED: {exc}")
        return 1
    finally:
        server.shutdown()
        server.server_close()
        shutil.rmtree(LAB_DIR, ignore_errors=True)

    failures = []
    for label, expected_mode, evidence in results:
        print(f"\n[+] evidence dict ({label}):")
        for key, value in evidence.items():
            printable = value if key != "response_excerpt" else repr(value)[:120]
            print(f"      {key}: {printable}")

        shots = [Path(p) for p in evidence["screenshots"]]
        if len(shots) != 3:
            failures.append(f"{label}: expected 3 screenshots, got {len(shots)}")
            continue
        if not evidence.get("site_screenshot_path"):
            failures.append(f"{label}: no screenshot of the website itself")
            continue
        missing = [s for s in shots if not s.is_file() or s.stat().st_size == 0]
        if missing:
            failures.append(f"{label}: unusable screenshot(s): {missing}")
            continue
        for step in evidence["steps"]:
            size = Path(step["screenshot"]).stat().st_size
            print(f"      step {step['step']}: {step['action']}")
            print(f"              {Path(step['screenshot']).name} ({size} bytes)")

        if evidence["capture_mode"] != expected_mode:
            failures.append(
                f"{label}: capture_mode is {evidence['capture_mode']!r}, "
                f"expected {expected_mode!r}"
            )
        if "root:x:0:0" not in (evidence.get("response_excerpt") or ""):
            failures.append(f"{label}: leaked file content missing from evidence")

    print()
    if failures:
        for line in failures:
            print(f"[X] {line}")
        return 1

    site_shots = {e["site_screenshot_path"] for _l, _m, e in results}
    if len(site_shots) != 1:
        print(f"[X] site context was captured {len(site_shots)} times, expected once")
        return 1

    print(
        "[+] PASS - the headless browser walked all three steps and "
        "photographed each one. Every PNG is Chromium rendering a real "
        "server response; nothing was drawn by Argus."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
