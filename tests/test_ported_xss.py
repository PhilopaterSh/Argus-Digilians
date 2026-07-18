"""Ported XSS classification tests from momen (no network required).

Exercises the real production classifier (app/tools/xss_classifier.py),
not a local reimplementation - see that module's docstring for what was
and wasn't ported from momen:core/tools.py's check_xss().
"""

from app.tools.xss_classifier import classify_xss_reflection as _classify


def test_script_reflection():
    p = "<script>alert('ARGUSxSS7')</script>"
    body = f"<html><body>{p}</body></html>"
    sev, _ = _classify(body, p)
    assert sev == "High"


def test_img_onerror_reflection():
    p = '"><img src=x onerror=alert(ARGUSxSS7)>'
    body = f'<input value="{p}">'
    sev, _ = _classify(body, p)
    assert sev == "High"


def test_attribute_reflection():
    body = '<a href="./Login.asp?RetURL=ARGUSxSS7">login</a>'
    sev, _ = _classify(body, "ARGUSxSS7")
    assert sev == "Medium"


def test_html_encoded_safe():
    body = "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert _classify(body, "<script>alert(1)</script>") is None


def test_html_encoded_event_handler_marker_safe():
    # Regression test: an HTML-entity-encoded non-<script> tag (e.g. <img onerror=...>)
    # near the marker must not be misclassified as executable - the encoding means
    # no real <img> tag was ever created, so onerror= is inert text, not a live handler.
    p = '"><img src=x onerror=alert(ARGUSxSS7)>'
    body = f"&lt;img src=x onerror=alert(ARGUSxSS7)&gt;"
    assert _classify(body, p) is None


def test_marker_between_tags():
    body = f"<div>some text ARGUSxSS7 more text</div>"
    sev, _ = _classify(body, "ARGUSxSS7")
    assert sev == "Medium"


def test_onfocus_attribute():
    p = '" onfocus=alert(ARGUSxSS7) autofocus="'
    body = f'<input value={p}>'
    sev, _ = _classify(body, p)
    assert sev == "High"


def test_no_reflection_returns_none():
    body = "<html><body>clean page</body></html>"
    assert _classify(body, "<script>alert(1)</script>") is None
