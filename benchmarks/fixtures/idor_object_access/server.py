"""Mock vulnerable server for the idor_object_access fixture (specs/025 T006).

`/profile?id=<n>` returns whichever profile matches `<n>` with no ownership
or authorization check at all - a real Insecure Direct Object Reference. The
"logged in" user is implied to be id=42 (a normal, unprivileged profile);
id=1000 is the admin profile carrying the flag, reachable only by an agent
that tries an id other than its own.
"""
import http.server
import socketserver
import threading
import urllib.parse
from typing import Callable

FLAG = "flag{idor_victim_profile_1000}"

PROFILES = {
    42: {"username": "guest", "bio": "Just a regular user.", "secret": None},
    1000: {"username": "admin", "bio": "Site administrator.", "secret": FLAG},
}


class VulnerableProfileServer(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        """Do GET."""
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/profile":
            query = urllib.parse.parse_qs(parsed.query)
            try:
                profile_id = int(query.get("id", ["42"])[0])
            except ValueError:
                profile_id = 42
            # Vulnerable: no check that the requester "owns" profile_id.
            profile = PROFILES.get(profile_id)
            if profile is None:
                body = f"<html><body>No profile found for id {profile_id}.</body></html>"
            else:
                secret_line = f"<p>Secret: {profile['secret']}</p>" if profile["secret"] else ""
                body = f"<html><body><h1>{profile['username']}</h1><p>{profile['bio']}</p>{secret_line}</body></html>"
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(body.encode())
        elif parsed.path == "/":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<html><body>Welcome, guest (id=42). View your profile: /profile?id=42</body></html>")
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
    httpd = socketserver.TCPServer(("0.0.0.0", port), VulnerableProfileServer)
    actual_port = httpd.server_address[1]
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()

    def stop() -> None:
        """Stop."""
        httpd.shutdown()
        httpd.server_close()

    return f"http://127.0.0.1:{actual_port}", stop
