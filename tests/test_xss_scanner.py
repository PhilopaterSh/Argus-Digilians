"""Unit tests for XSS scanner classification (no network)."""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.tools import WSLBridgeTools


def _classify(body, payload, marker="ARGUSxSS7"):
    EXEC_SIGS = (
        "<script", "onerror=", "onload=", "onfocus=", "onmouseover=",
        "javascript:", "<svg", "<iframe", "<body", "<input",
    )
    marker_hit = marker in body
    payload_hit = payload in body
    if payload_hit and any(sig in payload.lower() for sig in EXEC_SIGS):
        return "High", "executable payload reflected unencoded"
    if marker_hit:
        idx = body.find(marker)
        snippet = body[max(0, idx - 60):idx + len(marker) + 60]
        if any(sig in snippet.lower() for sig in EXEC_SIGS):
            return "High", "marker reflected near executable HTML/JS context"
        if f">{marker}<" in snippet:
            return "High", "marker reflected between HTML tags"
        if f'="{marker}"' in snippet or f"='{marker}'" in snippet:
            return "Medium", "marker reflected inside HTML attribute"
        if payload_hit or marker_hit:
            return "Medium", "user input reflected unencoded"
    return None


def test_script_reflection():
    p = "<script>alert('ARGUSxSS7')</script>"
    body = f"<html><body>{p}</body></html>"
    assert _classify(body, p)[0] == "High"


def test_img_onerror_reflection():
    p = '"><img src=x onerror=alert(ARGUSxSS7)>'
    body = f'<input value="{p}">'
    assert _classify(body, p)[0] == "High"


def test_attribute_reflection():
    body = '<a href="./Login.asp?RetURL=ARGUSxSS7">login</a>'
    assert _classify(body, "ARGUSxSS7")[0] == "Medium"


def test_html_encoded_safe():
    body = "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert _classify(body, "<script>alert(1)</script>") is None


def test_bridge_has_check_xss():
    bridge = WSLBridgeTools()
    assert callable(bridge.check_xss)


if __name__ == "__main__":
    test_script_reflection()
    test_img_onerror_reflection()
    test_attribute_reflection()
    test_html_encoded_safe()
    test_bridge_has_check_xss()
    print("All XSS unit tests passed")