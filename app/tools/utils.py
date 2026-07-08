import re

def clean_ansi_codes(text):
    """Removes ANSI escape codes (colors, bold, etc.) from terminal output."""
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)


def normalize_domain_for_memory(url: str) -> str:
    """Strip scheme and port so the same real site maps to one Blackboard
    target regardless of which port-qualified variant a caller scanned.

    Multiple tool modules independently stripped the scheme but not the
    port (`url.replace("https://", "").replace("http://", "").split("/")[0]`),
    so a call made with "http://example.com:80" (typical for tools that
    operate on a specific port) wrote to a different Blackboard target than
    app/tools/recon.py's recon_suite(), which is called with the bare
    original URL - splitting one real site into two separate "targets" and
    fragmenting the Knowledge Graph. This is the single canonical form;
    every add_finding()/upsert_target() call site should derive its domain
    key through this function (Constitution IX - Single Source of Truth).
    """
    host = url.replace("https://", "").replace("http://", "").split("/")[0]
    return host.split(":")[0]
