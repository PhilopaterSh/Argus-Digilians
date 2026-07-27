"""Ported XSS classification tests from momen (no network required).

Exercises the real production classifier (app/tools/xss_classifier.py),
not a local reimplementation - see that module's docstring for what was
and wasn't ported from momen:core/tools.py's check_xss().
"""

import pytest

from app.tools.xss_classifier import classify_xss_reflection as _classify

pytestmark = pytest.mark.unit


def test_script_reflection():
    """Verify Script reflection."""
    p = "<script>alert('ARGUSxSS7')</script>"
    body = f"<html><body>{p}</body></html>"
    sev, _ = _classify(body, p)
    assert sev == "High"


def test_img_onerror_reflection():
    """Verify Img onerror reflection."""
    p = '"><img src=x onerror=alert(ARGUSxSS7)>'
    body = f'<input value="{p}">'
    sev, _ = _classify(body, p)
    assert sev == "High"


def test_attribute_reflection():
    """Verify Attribute reflection."""
    body = '<a href="./Login.asp?RetURL=ARGUSxSS7">login</a>'
    sev, _ = _classify(body, "ARGUSxSS7")
    assert sev == "Medium"


def test_html_encoded_safe():
    """Verify Html encoded safe."""
    body = "&lt;script&gt;alert(1)&lt;/script&gt;"
    assert _classify(body, "<script>alert(1)</script>") is None


def test_html_encoded_event_handler_marker_safe():
    """Verify Html encoded event handler marker safe."""
    # Regression test: an HTML-entity-encoded non-<script> tag (e.g. <img onerror=...>)
    # near the marker must not be misclassified as executable - the encoding means
    # no real <img> tag was ever created, so onerror= is inert text, not a live handler.
    p = '"><img src=x onerror=alert(ARGUSxSS7)>'
    body = f"&lt;img src=x onerror=alert(ARGUSxSS7)&gt;"
    assert _classify(body, p) is None


def test_marker_between_tags():
    """Verify Marker between tags."""
    body = f"<div>some text ARGUSxSS7 more text</div>"
    sev, _ = _classify(body, "ARGUSxSS7")
    assert sev == "Medium"


def test_onfocus_attribute():
    """Verify Onfocus attribute."""
    p = '" onfocus=alert(ARGUSxSS7) autofocus="'
    body = f'<input value={p}>'
    sev, _ = _classify(body, p)
    assert sev == "High"


def test_no_reflection_returns_none():
    """Verify No reflection returns none."""
    body = "<html><body>clean page</body></html>"
    assert _classify(body, "<script>alert(1)</script>") is None


def test_marker_collision_with_unrelated_page_content_is_a_known_false_positive():
    """Documents a known, currently-unfixed false-positive class: MARKER
    ("ARGUSxSS7") is a fixed module-level constant, not generated per scan
    session. If a page already contains that literal text for reasons
    completely unrelated to the injected payload (e.g. a product code, a
    prior scan's leftover artifact), classify_xss_reflection() has no way
    to tell that apart from a genuine reflection - it reports a finding
    even though `payload` itself never appears anywhere in `body`.

    This is a locked-in regression guard on CURRENT behavior, not a claim
    that the behavior is correct - see this module's docstring history
    (specs/001-merge-branches/tasks.md's Open Follow-Ups) for the real
    fix: a live scanning loop must generate a fresh random marker per scan
    session instead of reusing this shared constant. If that fix ships,
    this test's expected result should flip to `None` and this docstring
    should be updated to say so, not silently deleted.
    """
    body = "<p>Our internal product reference code is ARGUSxSS7 for this SKU, nothing to do with your search.</p>"
    payload = "this-payload-never-appears-anywhere"

    sev, reason = _classify(body, payload)

    assert sev == "Medium"
    assert reason == "user input reflected unencoded in response"
