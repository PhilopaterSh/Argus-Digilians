import re

def clean_ansi_codes(text):
    """Removes ANSI escape codes (colors, bold, etc.) from terminal output.

    Args:
        text (str): Raw terminal output that may contain ANSI escape
            sequences.

    Returns:
        str: `text` with every ANSI escape sequence stripped.
    """
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

    Args:
        url (str): A URL, with or without scheme/port (e.g.
            "http://example.com:80/path").

    Returns:
        str: The bare host, with scheme and port stripped (e.g.
        "example.com").
    """
    host = url.replace("https://", "").replace("http://", "").split("/")[0]
    return host.split(":")[0]


# Real content-based proof that an exploitation attempt actually worked, not
# a guess based on HTTP status alone (a "200" or "500" response proves
# nothing about *what* content came back - a WAF challenge page or a normal
# error page can return either). Shared by evasion.py's live attack probes
# (advanced_vuln_probe) and reflective_verification.py's passive output
# analysis (post_execute_verify) so a signature only needs adding once
# (Constitution IX - Single Source of Truth) - previously duplicated
# independently in both files.
SENSITIVE_CONTENT_INDICATORS = {
    "root:x:0:0:": "LFI/Path Traversal Confirmed (/etc/passwd read success)",
    "DB_PASSWORD": "Secret Disclosure Confirmed (Database configuration leaked)",
    "appSettings": "Web Configuration Leak Confirmed (web.config read success)",
    "uid=": "RCE Confirmed (id command executed successfully)",
}
