import re

def clean_ansi_codes(text):
    """Remove ANSI escape sequences and sanitize terminal output for Windows consoles.

    - Strips ANSI color/formatting codes.
    - Replaces common Unicode box-drawing characters with ASCII equivalents.
    - Removes non-printable/control characters and falls back to ASCII.
    This prevents UnicodeEncodeError when the Streamlit/StdOut callbacks print WSL output
    that contains colored or box-drawing characters not supported by the host code page.
    """
    import unicodedata

    # Remove common ANSI CSI sequences like \x1b[31m, \x1b[0m, etc.
    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    cleaned = ansi_escape.sub('', text or '')

    # Map common box-drawing / line characters to ASCII equivalents
    replacements = {
        '┌': '+', '└': '+', '┐': '+', '─': '-', '│': '|', '┴': '+', '┬': '+',
        '├': '+', '┤': '+', '┼': '+', '╭': '+', '╮': '+', '╯': '+', '╰': '+'
    }
    for k, v in replacements.items():
        cleaned = cleaned.replace(k, v)

    # Normalize unicode (decompose) and drop non-printable characters
    cleaned = unicodedata.normalize('NFKD', cleaned)
    cleaned = ''.join(ch for ch in cleaned if (ch.isprintable() or ch in '\r\n\t'))

    # Finally, ensure ASCII-only output to be safe for any terminal encoding
    try:
        ascii_clean = cleaned.encode('ascii', 'ignore').decode('ascii')
    except Exception:
        # Fallback: return the best-effort cleaned string
        ascii_clean = ''.join(c for c in cleaned if ord(c) < 0x110000)

    return ascii_clean
