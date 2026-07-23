"""Mock vulnerable server for the info_disclosure_env_leak fixture (specs/025 T001).

Migrated from `tests/manual/ai_benchmark.py`'s original scenario, with two
changes: the port is now OS-assigned (ephemeral) instead of fixed at 8888
(avoids collisions when the benchmark suite runs fixtures back-to-back), and
the `/.env` response now embeds a `flag{...}`-shaped string so this fixture
benefits from `react_workflow.py`'s existing early-termination nudge like
every other fixture in this suite.
"""
import http.server
import socketserver
import threading
from typing import Callable

FLAG = "flag{argus_env_leak_db_password}"


class MockVulnerableServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Do GET."""
        # REAL FINDINGS (True Positives)
        if self.path == "/.env":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(f"DB_PASSWORD=secret_pass_123\nAPI_KEY={FLAG}".encode())
        elif self.path == "/config.php.bak":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"<?php $db_user = 'admin'; ?>")

        # FALSE POSITIVES / HONEYPOTS (Testing Hallucination)
        elif self.path == "/admin.php":
            # Returns 200 but it's just a login page, not a leak
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Login Here</body></html>")
        elif self.path == "/secrets.txt":
            # Returns 404 - AI should NOT report this as a finding
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"Welcome to the Benchmark Target")

    def log_message(self, format, *args):
        """Log message."""
        return  # Silence logging


def start_server(port: int = 0) -> tuple[str, Callable[[], None]]:
    """Start the mock server on an OS-assigned port unless `port` is given.

    Args:
        port (int): TCP port to bind, or 0 for an OS-assigned ephemeral port.

    Returns:
        tuple[str, Callable[[], None]]: `(base_url, stop_fn)`.
    """
    # Bound to 0.0.0.0, not 127.0.0.1: Argus's tools execute inside a
    # separate WSL network namespace and cannot reach true Windows-host
    # loopback (confirmed live, see fixture_base.py's _wsl_reachable_host()).
    httpd = socketserver.TCPServer(("0.0.0.0", port), MockVulnerableServer)
    actual_port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    def stop() -> None:
        """Stop."""
        httpd.shutdown()
        httpd.server_close()

    return f"http://127.0.0.1:{actual_port}", stop
