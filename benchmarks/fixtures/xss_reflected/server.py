"""Mock vulnerable server for the xss_reflected fixture (specs/025 T006).

`/search?q=...` reflects `q` verbatim into the HTML response with no
escaping - a real (if minimal) reflected-XSS vulnerability. The flag is only
included once a payload that actually breaks HTML context (contains `<`) is
submitted, so retrieving it requires demonstrating the vulnerability, not
just browsing the page.
"""
import http.server
import socketserver
import threading
import urllib.parse
from typing import Callable

FLAG = "flag{xss_reflected_unescaped_search}"


class VulnerableSearchServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Do GET."""
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/search":
            query = urllib.parse.parse_qs(parsed.query)
            q = query.get("q", [""])[0]
            # Vulnerable: `q` is embedded into the HTML body with no escaping.
            body = f"<html><body><div>Results for: {q}</div>"
            if "<" in q:
                body += f"<!-- admin note: {FLAG} -->"
            body += "</body></html>"
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(body.encode())
        elif parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Try our search: /search?q=...</body></html>")
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
    # Bound to 0.0.0.0, not 127.0.0.1: Argus's tools execute inside a
    # separate WSL network namespace and cannot reach true Windows-host
    # loopback (confirmed live, see fixture_base.py's _wsl_reachable_host()).
    httpd = socketserver.TCPServer(("0.0.0.0", port), VulnerableSearchServer)
    actual_port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    def stop() -> None:
        """Stop."""
        httpd.shutdown()
        httpd.server_close()

    return f"http://127.0.0.1:{actual_port}", stop
