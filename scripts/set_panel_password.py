"""Set or rotate the Argus Security Studio panel password (ARG-01).

Prompts for a password on the host, stores only its PBKDF2 hash in the
repo-root `.env` as `ARGUS_PANEL_PASSWORD_HASH`, and never writes the
plaintext anywhere. Run once before exposing the Studio:

    python scripts/set_panel_password.py
"""
import getpass
import io
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.panel_auth import hash_password  # noqa: E402

ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
KEY = "ARGUS_PANEL_PASSWORD_HASH"


def main():
    """Prompt twice for a password and persist its PBKDF2 hash into `.env`."""
    print("Argus Security Studio - panel password setup")
    password = getpass.getpass("New panel password: ")
    confirm = getpass.getpass("Confirm password: ")
    if not password:
        print("ERROR: empty password refused.")
        sys.exit(1)
    if password != confirm:
        print("ERROR: passwords do not match.")
        sys.exit(1)
    stored = hash_password(password)
    lines = []
    if os.path.isfile(ENV_PATH):
        with io.open(ENV_PATH, encoding="utf-8") as f:
            lines = [line for line in f.read().splitlines() if not line.startswith(KEY + "=")]
    lines.append(f"{KEY}={stored}")
    with io.open(ENV_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"Wrote {KEY} to {ENV_PATH}")
    print("Restart the Studio (scripts/LAUNCH_STUDIO.bat) and sign in.")


if __name__ == "__main__":
    main()
