"""Reflected-XSS severity classification.

Ported from momen:core/tools.py's WSLBridgeTools.check_xss() (the nested
_classify() closure only - the surrounding live HTTP scanning loop,
endpoint list, and finding-recording logic were not ported; see
specs/001-merge-branches/tasks.md T012 for that gap).
"""
import re

MARKER = "ARGUSxSS7"
EXEC_SIGS = (
    "<script", "onerror=", "onload=", "onfocus=", "onmouseover=",
    "javascript:", "<svg", "<iframe", "<body", "<input",
)


def _snippet(body: str, needle: str) -> str:
    """Extract a small window of text around the first occurrence of `needle`.

    Args:
        body (str): The full text to search.
        needle (str): The substring to locate.

    Returns:
        str: Up to 60 characters of context on each side of `needle`
        (newlines collapsed to spaces), or "" if `needle` isn't found.
    """
    idx = body.find(needle)
    if idx < 0:
        return ""
    return body[max(0, idx - 60):idx + len(needle) + 60].replace("\n", " ").strip()


def classify_xss_reflection(body: str, payload: str, content_type: str = "") -> tuple[str, str] | None:
    """Return (severity, reason) if `body` shows a reflected-XSS signature for
    `payload`, else None. `content_type` filters out non-HTML responses
    (CSS/JSON/JS/font/image) where a text reflection can't execute as XSS.

    Args:
        body (str): The HTTP response body to inspect for a reflection.
        payload (str): The XSS payload that was sent.
        content_type (str): The response's Content-Type header, if known
            - used only to short-circuit obviously non-HTML responses.

    Returns:
        tuple[str, str] | None: `(severity, reason)` where severity is
        "High" or "Medium", or `None` if no exploitable reflection was
        found.
    """
    if not body or not isinstance(body, str):
        return None

    ct = (content_type or "").lower()
    if ct and not any(h in ct for h in ("text/html", "application/xhtml")):
        if any(x in ct for x in (
            "text/css", "application/json", "text/javascript",
            "application/javascript", "font", "image/", "text/plain",
        )):
            return None

    marker_hit = MARKER in body
    payload_hit = payload in body

    if payload_hit and any(sig in payload.lower() for sig in EXEC_SIGS):
        return "High", "executable payload reflected unencoded"

    if marker_hit:
        snippet = _snippet(body, MARKER)
        snippet_lower = snippet.lower()
        # If the reflection's immediate context is HTML-entity-escaped (&lt;/&gt;)
        # with no raw angle bracket nearby, no tag/attribute the payload didn't
        # already control was actually created - EXEC_SIGS text (e.g. "onerror=")
        # appearing as inert escaped text is not exploitable.
        looks_escaped = "&lt;" in snippet_lower or "&gt;" in snippet_lower
        has_raw_angle_bracket = "<" in snippet or ">" in snippet
        if looks_escaped and not has_raw_angle_bracket:
            return None

        if any(sig in snippet_lower for sig in EXEC_SIGS):
            return "High", "marker reflected near executable HTML/JS context"

        if re.search(rf'>\s*{re.escape(MARKER)}\s*<', snippet, re.I):
            return "High", "marker reflected between HTML tags (unencoded)"

        if re.search(rf'=\s*["\']?[^"\'>\s]*{re.escape(MARKER)}', snippet, re.I):
            return "Medium", "marker reflected inside HTML attribute (potential breakout XSS)"

        if payload_hit or marker_hit:
            return "Medium", "user input reflected unencoded in response"

    return None
