import re


def clean_ansi_codes(text: str) -> str:
    """Remove ANSI escape codes from terminal output."""
    ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
    return ansi_escape.sub("", text or "")


def clean_host(value: str) -> str:
    """Convert URL-like input into a hostname."""
    return (
        value.replace("https://", "")
        .replace("http://", "")
        .split("/")[0]
        .split(":")[0]
    )


def clean_target(value: str) -> str:
    """Convert URL-like input into host/path target without scheme."""
    return value.replace("https://", "").replace("http://", "").split("/")[0]


def ensure_url(value: str, default_scheme: str = "https") -> str:
    """Ensure the value has an HTTP scheme."""
    if value.startswith(("http://", "https://")):
        return value
    return f"{default_scheme}://{value}"
