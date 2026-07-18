"""
Argus Safety Layer - Blocks destructive payloads, sanitizes inputs (port from momen).
All scanning must be controlled, logged, and non-destructive.
"""
import re
import ipaddress
from urllib.parse import urlparse

# Patterns that are always blocked regardless of scan mode
DESTRUCTIVE_PATTERNS = [
    r'rm\s+-rf', r'format\s+[a-zA-Z]:', r'mkfs\.', r'dd\s+if=',
    r'DROP\s+TABLE', r'DROP\s+DATABASE', r'TRUNCATE\s+TABLE',
    r'shutdown\s+-', r'halt', r'poweroff', r'reboot',
    r'>\s*/dev/sda', r':\(\)\{.*\}', r'fork\s*bomb',
    r'wget.*\|.*sh', r'curl.*\|.*bash', r'chmod\s+777\s+/',
    r'passwd\s+root', r'/etc/shadow',
]

# Private/internal IP ranges - blocked in passive mode
PRIVATE_RANGES = [
    ipaddress.ip_network('10.0.0.0/8'),
    ipaddress.ip_network('172.16.0.0/12'),
    ipaddress.ip_network('192.168.0.0/16'),
    ipaddress.ip_network('127.0.0.0/8'),
    ipaddress.ip_network('::1/128'),
]


class SafetyLayer:
    """Central safety enforcement for all Argus operations."""

    def __init__(self, allow_internal: bool = False):
        self.allow_internal = allow_internal
        self._blocked_count = 0
        self._audit_log = []

    def sanitize_input(self, text: str) -> str:
        """Removes shell injection characters and normalizes input."""
        if not isinstance(text, str):
            return str(text)
        text = text.replace('\x00', '')
        dangerous_chars = ['`', '$(']
        for char in dangerous_chars:
            text = text.replace(char, '')
        return text.strip()

    def is_destructive_payload(self, payload: str) -> bool:
        """Returns True if the payload matches any destructive pattern."""
        payload_lower = payload.lower()
        for pattern in DESTRUCTIVE_PATTERNS:
            if re.search(pattern, payload_lower, re.IGNORECASE):
                self._log_block("destructive_payload", payload[:100])
                return True
        return False

    def validate_target(self, url: str, mode: str = "passive") -> tuple:
        """
        Validates a target URL.
        Returns (is_valid: bool, reason: str)
        """
        if not url or not isinstance(url, str):
            return False, "Target URL is empty or invalid."

        url = url.strip()
        if not url.startswith(('http://', 'https://', 'ftp://')):
            url = 'https://' + url

        try:
            parsed = urlparse(url)
            host = parsed.hostname
            if not host:
                return False, "Could not parse hostname from URL."

            try:
                ip = ipaddress.ip_address(host)
                if not self.allow_internal:
                    for private_range in PRIVATE_RANGES:
                        if ip in private_range:
                            self._log_block("private_ip", host)
                            return False, f"Target IP {host} is in a private range."
            except ValueError:
                pass

            return True, "Target validated."
        except Exception as e:
            return False, f"Validation error: {str(e)}"

    def guard_command(self, command: str) -> tuple:
        """
        Guards a WSL command before execution.
        Returns (is_safe: bool, reason: str)
        """
        if self.is_destructive_payload(command):
            return False, f"BLOCKED: Command contains destructive pattern."
        return True, "Command is safe."

    def _log_block(self, block_type: str, content: str):
        """Logs a blocked action to the audit trail."""
        import datetime
        self._blocked_count += 1
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "type": block_type,
            "content_preview": content[:200]
        }
        self._audit_log.append(entry)

    def get_audit_log(self) -> list:
        """Returns the full audit log of blocked actions."""
        return self._audit_log

    def get_stats(self) -> dict:
        """Returns safety statistics."""
        return {
            "total_blocked": self._blocked_count,
            "audit_entries": len(self._audit_log)
        }
