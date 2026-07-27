"""Mock vulnerable server for the path_traversal_download fixture (specs/025).

`/download?file=...` naively joins user input onto a "public" directory path
with no normalization or containment check - a real path-traversal
vulnerability, using genuine filesystem reads (no simulated response). A
`secret.txt` file carrying the flag lives one level above the public
directory, reachable via `../secret.txt`. Both directories are created in a
private per-process temp sandbox (cleaned up in `stop()`), so a traversal
payload that escapes the intended directory only ever reaches this
fixture's own throwaway files, not real host files with meaningful content.
"""
import http.server
import os
import shutil
import socketserver
import tempfile
import threading
import urllib.parse
from typing import Callable

FLAG = "flag{path_traversal_outside_public_dir}"

_sandbox_dir: str = ""


class VulnerableDownloadServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Do GET."""
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/download":
            query = urllib.parse.parse_qs(parsed.query)
            filename = query.get("file", ["welcome.txt"])[0]
            # Vulnerable: `filename` is joined onto the public dir with no
            # normalization/containment check against `..` traversal.
            target = os.path.join(_sandbox_dir, "public", filename)
            try:
                with open(target, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
                self.send_response(200)
                body = f"<html><body><pre>{content}</pre></body></html>"
            except (FileNotFoundError, IsADirectoryError, PermissionError, OSError):
                self.send_response(404)
                body = "<html><body>File not found.</body></html>"
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(body.encode())
        elif parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Download files: /download?file=welcome.txt</body></html>")
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Log message."""
        return


def start_server(port: int = 0) -> tuple[str, Callable[[], None]]:
    """Start the mock server on an OS-assigned port unless `port` is given.

    Args:
        port (int): TCP port to bind, or 0 for an OS-assigned ephemeral port.

    Returns:
        tuple[str, Callable[[], None]]: `(base_url, stop_fn)`.
    """
    global _sandbox_dir
    _sandbox_dir = tempfile.mkdtemp(prefix="argus_benchmark_path_traversal_")
    public_dir = os.path.join(_sandbox_dir, "public")
    os.makedirs(public_dir, exist_ok=True)
    with open(os.path.join(public_dir, "welcome.txt"), "w", encoding="utf-8") as f:
        f.write("Welcome! Try downloading other files via /download?file=...\n")
    with open(os.path.join(_sandbox_dir, "secret.txt"), "w", encoding="utf-8") as f:
        f.write(f"CONFIDENTIAL INTERNAL NOTE\n{FLAG}\n")

    # Bound to 0.0.0.0, not 127.0.0.1: Argus's tools execute inside a
    # separate WSL network namespace and cannot reach true Windows-host
    # loopback (confirmed live, see fixture_base.py's _wsl_reachable_host()).
    httpd = socketserver.TCPServer(("0.0.0.0", port), VulnerableDownloadServer)
    actual_port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    def stop() -> None:
        """Stop."""
        httpd.shutdown()
        httpd.server_close()
        shutil.rmtree(_sandbox_dir, ignore_errors=True)

    return f"http://127.0.0.1:{actual_port}", stop
