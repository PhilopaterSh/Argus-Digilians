import re
from urllib.parse import urlparse
from typing import List, Optional, Tuple

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


def shell_quote(value: str) -> str:
    """Render `value` inert as a single `sh -c` argument.

    Every live probe in this package is a curl command string executed through
    a shell (`CommandRunner.run` hands it to `bash -c` via WSL/SSH), and the
    values spliced into those strings are hostile by nature:

      * Attack payloads are metacharacter-dense by construction. Both the
        hardcoded `1'/**/OR/**/1=1/**/--` SQLi string and the quote-bearing
        entries in PayloadsAllTheThings' dotdotpwn.txt contain single quotes,
        which terminated the surrounding quoted argument and left the command
        syntactically invalid - bash aborted with "unexpected EOF" and curl
        never ran, so those payloads were silently never tested.
      * URLs and parameter names can be attacker-*controlled*: they are mined
        from crawler links persisted in memory, and `app/tools/crawler.py`'s
        extractor (`grep -oE 'href="[^"]+"' | cut -d'"' -f2`) only excludes
        double quotes, so a hostile target page can plant shell metacharacters
        that reach the command line verbatim - a confirmed remote code
        execution against the operator's own host.

    Prefer this over `shlex.quote()`: shlex leaves already-safe strings
    unquoted, so the emitted command shape would vary with the payload and
    make probes harder to reason about and assert on. This always wraps in
    single quotes, which POSIX sh treats as fully literal; the only character
    needing care is the single quote itself, closed and reopened via the
    standard `'"'"'` idiom.

    Args:
        value (str): Raw, possibly hostile string to pass as one argument.

    Returns:
        str: `value` wrapped in single quotes and safe to interpolate into a
        shell command string.
    """
    return "'" + value.replace("'", "'\"'\"'") + "'"


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
    # Windows/IIS traversal targets: win.ini's canonical section header and
    # boot.ini's loader block prove a genuine read on Windows hosts where
    # /etc/passwd never exists (dedicated PathTraversalScanner probes both).
    "; for 16-bit app support": "Path Traversal Confirmed (win.ini read success)",
    "[boot loader]": "Path Traversal Confirmed (boot.ini read success)",
    # /etc/shadow: only readable via a privileged/misconfigured sink - a
    # higher-severity confirmation than /etc/passwd.
    "root:$": "LFI/Path Traversal Confirmed (/etc/shadow read success - privileged)",
}


# ----------------------------------------------------------------------
# Knowledge-graph (entities/relations) parsing helpers.
#
# Single source of truth (Constitution IX) for the tool-output parsing that
# feeds ArgusMemory's entities/relations tables (the Query_Knowledge_Graph
# tool's data source) - `app/core/agent/brain.py`'s deterministic recon
# pipeline (`run_deterministic_recon`) and `app/core/agent/react_workflow.py`'s
# live ReAct execute_node both call these identically instead of each
# maintaining their own copy. brain.py's own `_to_bare_hostname`/
# `_parse_subdomains`/`_parse_tech`/`_clean_tech_string` methods delegate
# here rather than duplicating the logic.
# ----------------------------------------------------------------------
_TECH_BLOCK_RE = re.compile(r"Tech:\s*(.+?)(?:\nPorts:|\Z)", re.DOTALL)
_TECH_NOISE_KEYS = {"Cookies", "Country", "IP", "Title"}
_TECH_TOKEN_RE = re.compile(r"[A-Za-z][\w\-\.]*(?:\[[^\]]*\])?")


def to_bare_hostname(target: str) -> str:
    """Reduce a URL or bare host to just its hostname.

    http://testasp.vulnweb.com/some/path?x=1  ->  testasp.vulnweb.com
    testasp.vulnweb.com                        ->  testasp.vulnweb.com

    Args:
        target (str): A URL or bare host; a missing scheme is treated
            as `http://`.

    Returns:
        str: The bare hostname, or `target` unchanged if it has no
        parseable hostname.
    """
    parsed = urlparse(target if "://" in target else f"http://{target}")
    return parsed.hostname or target


def parse_subdomains(observation: str, exclude_hostname: str) -> List[str]:
    """Pulls plausible hostnames out of Subdomain_Enumeration's raw
    (possibly fenced) line-per-subdomain output, excluding the root
    host we already scanned and de-duping while preserving order.

    Args:
        observation (str): Raw Subdomain_Enumeration tool output.
        exclude_hostname (str): The already-scanned root host to
            exclude from the results.

    Returns:
        List[str]: Candidate subdomains, in first-seen order, with
        `exclude_hostname` and any line containing a space or slash
        (or lacking a `.`) filtered out.
    """
    candidates = []
    for line in observation.splitlines():
        line = line.strip().strip("`")
        if not line or " " in line or "/" in line or "." not in line:
            continue
        if line == exclude_hostname:
            continue
        candidates.append(line)
    seen = set()
    out = []
    for c in candidates:
        if c not in seen:
            seen.add(c)
            out.append(c)
    return out


def parse_tech_block(observation: str) -> str:
    """Pulls the raw 'Tech: ...' line out of Recon_Suite's output.
    This is the noisy WhatWeb-style line (cookies, IP, title and all) -
    use `clean_tech_string()` before using it as a search query or graph
    entity value.

    Args:
        observation (str): Raw Recon_Suite tool output.

    Returns:
        str: The raw `Tech:` block's text (up to 500 chars), or `""`
        if no `Tech:` block is found.
    """
    match = _TECH_BLOCK_RE.search(observation)
    if not match:
        return ""
    return match.group(1).strip()[:500]


def clean_tech_string(raw_tech: str) -> str:
    """
    Strips a WhatWeb-style tech line down to just the useful
    identifiers. Raw input looks like:
      "http://x.com/ [200 OK] ASP_NET, Cookies[...], Country[US],
       HTTPServer[Microsoft-IIS/8.5], IP[1.2.3.4], Title[...], ..."
    Searching that whole line returns nothing - no one has ever
    written that as a search query. This keeps only tokens whose key
    isn't in `_TECH_NOISE_KEYS`, and prefers the bracket VALUE (e.g.
    "Microsoft-IIS/8.5") over the raw token when there is one.

    Args:
        raw_tech (str): The raw `Tech:` line text (as returned by
            `parse_tech_block`).

    Returns:
        str: A space-joined, deduplicated string of useful tech
        tokens (up to 200 chars); `""` if `raw_tech` is empty, or
        `raw_tech[:200]` unchanged if no tokens survive filtering.
    """
    if not raw_tech:
        return ""
    text = raw_tech
    if "] " in text:
        # drop the "http://.../ [200 OK] " prefix if present
        text = text.split("] ", 1)[1]

    values = []
    for tok in _TECH_TOKEN_RE.findall(text):
        if "[" in tok:
            key, _, rest = tok.partition("[")
            if key in _TECH_NOISE_KEYS:
                continue
            value = rest.rstrip("]").strip()
            values.append(value if value else key)
        elif tok not in _TECH_NOISE_KEYS and not re.fullmatch(r"[A-Z]{1,3}", tok):
            # Skip short all-caps remnants like a leftover "US" from
            # "Country[UNITED STATES][US]" - a stray bracket fragment,
            # not a real technology token.
            values.append(tok)

    deduped = list(dict.fromkeys(values))
    cleaned = " ".join(deduped)
    return cleaned[:200] if cleaned else raw_tech[:200]


def record_graph_edge(
    memory,
    entity: Tuple[str, str],
    source_val: str,
    target_val: str,
    rel_type: str,
) -> None:
    """Persist a single knowledge-graph edge so Query_Knowledge_Graph has
    real data to return. No-op (and never fatal) when `memory` is `None`
    or a write fails.

    Args:
        memory: An `ArgusMemory`-like object exposing `upsert_entity`/
            `add_relation`, or `None` to skip silently.
        entity (Tuple[str, str]): `(entity_type, entity_value)` for the
            new node this edge introduces.
        source_val (str): The relation's source node value.
        target_val (str): The relation's target node value.
        rel_type (str): The relation type (e.g. "USES_TECH").

    Returns:
        None
    """
    entity_type, entity_value = entity
    if memory is None:
        return
    value = (entity_value or "").strip()
    if not value:
        return
    try:
        memory.upsert_entity(entity_type, value)
        memory.add_relation(source_val, target_val, rel_type)
    except Exception as e:
        print(f"[GRAPH] graph edge write skipped ({rel_type}): {e}")
