"""Unit tests for the panel password crypto (app/core/panel_auth.py, ARG-01)."""
from app.core.panel_auth import hash_password, verify_password


def test_hash_and_verify_round_trip():
    """Verify a hashed password verifies and a wrong one does not."""
    stored = hash_password("s3cret-panel!")
    assert stored.startswith("pbkdf2_sha256$")
    assert "s3cret-panel!" not in stored
    assert verify_password("s3cret-panel!", stored) is True
    assert verify_password("wrong-password", stored) is False


def test_verify_rejects_malformed_stored_values():
    """Verify malformed stored hashes fail closed."""
    assert verify_password("x", "") is False
    assert verify_password("x", "garbage") is False
    assert verify_password("x", "md5$1$aa$bb") is False
    assert verify_password("x", "pbkdf2_sha256$notanint$aa$bb") is False


def test_unique_salts_per_hash():
    """Verify two hashes of the same password differ (random salt)."""
    assert hash_password("same") != hash_password("same")
