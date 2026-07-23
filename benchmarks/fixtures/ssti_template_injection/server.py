"""Mock vulnerable server for the ssti_template_injection fixture (specs/025 T006).

`/greet?name=...` builds a Jinja2 template STRING from user input before
rendering it (`Template(f"Hello, {name}!").render()`) - the classic
beginner SSTI mistake, using a real `jinja2.Template` (not a faked/simulated
render), no filesystem/subprocess access involved. A payload like
`{{7*7}}` gets genuinely evaluated server-side; the response only carries
the flag when the rendered output proves real evaluation happened (`49`
present and no literal `{{` left over), not merely that the payload text was
echoed back unrendered.
"""
import http.server
import socketserver
import threading
import urllib.parse
from typing import Callable

from jinja2 import Template

FLAG = "flag{ssti_jinja2_template_injection}"


class VulnerableGreetServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Do GET."""
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/greet":
            query = urllib.parse.parse_qs(parsed.query)
            name = query.get("name", ["Guest"])[0]
            # Vulnerable: user input becomes part of the TEMPLATE SOURCE,
            # not a passed-in variable - real Jinja2 SSTI.
            template_source = f"Hello, {name}! Welcome to our site."
            try:
                rendered = Template(template_source).render()
            except Exception:
                rendered = template_source
            body = f"<html><body>{rendered}"
            if "49" in rendered and "{{" not in rendered:
                body += f"<!-- {FLAG} -->"
            body += "</body></html>"
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(body.encode())
        elif parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Try our greeting page: /greet?name=...</body></html>")
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
    httpd = socketserver.TCPServer(("0.0.0.0", port), VulnerableGreetServer)
    actual_port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    def stop() -> None:
        """Stop."""
        httpd.shutdown()
        httpd.server_close()

    return f"http://127.0.0.1:{actual_port}", stop
