from urllib.parse import urlparse


def _first_web_port(open_ports):
    for port in open_ports:
        if port in {80, 443, 8080, 8000, 8443}:
            return port
    return open_ports[0] if open_ports else None


def _build_target_url(target: str, port: int) -> str:
    """Build a normalized target URL from a host/URL string and a port.

    Parses ``target`` (adding an ``http://`` scheme if none is present), extracts
    the host, and returns a URL whose scheme is derived from ``port`` (``https``
    for 443/8443, otherwise ``http``). If the parsed host already contains a
    ``:port`` suffix, the ``port`` argument is ignored and the existing host is
    used as-is.

    Args:
        target (str): Target host or URL, e.g. ``"example.com"``,
            ``"http://example.com"``, or ``"example.com:8080"``. If it does not
            start with ``"http"``, an ``http://`` scheme is assumed for parsing.
        port (int): Port to append to the URL. Selects the scheme (443 or 8443
            -> ``https``, otherwise ``http``). Ignored when ``target`` already
            includes an explicit port.

    Returns:
        str: A normalized URL in the form ``"{scheme}://{host}:{port}"``, or
        ``"{scheme}://{host}"`` when ``target`` already contains an explicit port.

    Examples:
        >>> _build_target_url("example.com", 443)
        'https://example.com:443'
        >>> _build_target_url("http://example.com", 8080)
        'http://example.com:8080'
        >>> _build_target_url("example.com:9000", 443)
        'https://example.com:9000'
    """
    parsed = urlparse(target if target.startswith("http") else f"http://{target}")
    host = parsed.netloc or parsed.path
    scheme = "https" if port in {443, 8443} else "http"
    return f"{scheme}://{host}:{port}" if ":" not in host else f"{scheme}://{host}"
