import re

def clean_ansi_codes(text):
    """Removes ANSI escape codes (colors, bold, etc.) from terminal output."""
    ansi_escape = re.compile(r'(?:\x1B[@-_]|[\x80-\x9F])[0-?]*[ -/]*[@-~]')
    return ansi_escape.sub('', text)
