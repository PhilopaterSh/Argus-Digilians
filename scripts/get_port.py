"""Read the Streamlit port from config.yaml and print it to stdout.

Fail-safe: if config.yaml is missing, unreadable, or lacks streamlit.port,
print the canonical default port (12199) instead of crashing.
Canonical port per specs/012-spec-reconciliation (section 2.6) / Architecture ADR-16.
The fail-safe default MUST equal the configured default so no drift is possible.
"""
import os

CANONICAL_DEFAULT_PORT = 12199


def get_port() -> int:
    """Read the configured Streamlit port, falling back to the canonical default.

    Returns:
        int: The port from config.yaml's `streamlit.port` key, or
        `CANONICAL_DEFAULT_PORT` (12199) if the file is missing, unreadable,
        or does not define that key.
    """
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.yaml")
    try:
        import yaml  # imported lazily so a missing dep still yields the default
        with open(config_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        port = cfg.get("streamlit", {}).get("port", CANONICAL_DEFAULT_PORT)
        return int(port)
    except Exception:
        return CANONICAL_DEFAULT_PORT


if __name__ == "__main__":
    print(get_port())
