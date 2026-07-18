"""Reflected-XSS severity classification.

Ported from momen:core/tools.py's WSLBridgeTools.check_xss() (the nested
_classify() closure only — the surrounding live HTTP scanning loop,
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
    idx = body.find(needle)
    if idx < 0:
        return ""
    return body[max(0, idx - 60):idx + len(needle) + 60].replace("\n", " ").strip()


def classify_xss_reflection(body: str, payload: str, content_type: str = "") -> tuple[str, str] | None:
    """Return (severity, reason) if `body` shows a reflected-XSS signature for
    `payload`, else None. `content_type` filters out non-HTML responses
    (CSS/JSON/JS/font/image) where a text reflection can't execute as XSS.
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
        encoded_only = (
            "&lt;script" in body.lower()
            and "<script" not in body.lower()
            and "onerror=" not in body.lower()
        )
        if encoded_only and MARKER in body:
            return None

        if any(sig in snippet.lower() for sig in EXEC_SIGS):
            return "High", "marker reflected near executable HTML/JS context"

        if re.search(rf'>\s*{re.escape(MARKER)}\s*<', snippet, re.I):
            return "High", "marker reflected between HTML tags (unencoded)"

        if re.search(rf'=\s*["\']?[^"\'>\s]*{re.escape(MARKER)}', snippet, re.I):
            return "Medium", "marker reflected inside HTML attribute (potential breakout XSS)"

        if payload_hit or marker_hit:
            return "Medium", "user input reflected unencoded in response"

    return None
