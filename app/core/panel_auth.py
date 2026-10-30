"""Panel authentication crypto for the Argus Security Studio (ARG-01).

Pure standard library: PBKDF2-HMAC-SHA256 with a per-password random salt,
stored in `.env` as ``ARGUS_PANEL_PASSWORD_HASH`` in the format
``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``. Deliberately NOT a
plaintext password and NOT streamlit-dependent, so it is unit-testable
without a GUI runtime.
"""
from __future__ import annotations

import hashlib
import hmac
import os

_ITERATIONS = 200_000
_PREFIX = "pbkdf2_sha256"


def hash_password(password: str, iterations: int = _ITERATIONS) -> str:
    """Hash a panel password into the storable `.env` format.

    Args:
        password (str): The plaintext password chosen by the operator.
        iterations (int): PBKDF2 iteration count.

    Returns:
        str: ``pbkdf2_sha256$<iterations>$<salt_hex>$<hash_hex>``.
    """
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)
    return f"{_PREFIX}${iterations}${salt.hex()}${digest.hex()}"


def verify_password(password: str, stored: str) -> bool:
    """Verify a password against a stored hash in constant time.

    Args:
        password (str): The plaintext attempt.
        stored (str): The `hash_password` output read from the environment.

    Returns:
        bool: True when the attempt matches; False for any malformed,
        missing, or mismatching stored value.
    """
    try:
        prefix, iterations_s, salt_hex, hash_hex = str(stored).split("$")
        if prefix != _PREFIX:
            return False
        digest = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), int(iterations_s)
        )
        return hmac.compare_digest(digest.hex(), hash_hex)
    except (ValueError, AttributeError):
        return False


def get_stored_hash() -> str | None:
    """Return the configured panel password hash from `.env`, if any.

    Returns:
        str | None: The ``ARGUS_PANEL_PASSWORD_HASH`` value, or `None` when
        unset/empty (the panel then renders setup instructions and stays
        locked - fail-closed).
    """
    try:
        from dotenv import load_dotenv

        load_dotenv()
    except ImportError:
        pass
    value = os.getenv("ARGUS_PANEL_PASSWORD_HASH", "").strip()
    return value or None
