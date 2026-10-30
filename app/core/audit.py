"""Durable, append-only command audit trail (pentest finding ARG-09 remediation).

Every Kali command executed through ``CommandRunner`` and every safety-layer
block is appended as one JSON line to ``data/audit_log.jsonl``. Append-only by
design: entries are never edited or removed by the framework, so the file is a
tamper-evident record of what the agent actually did (Constitution V -
Observability; spec 026's durable-logging requirement, minus RBAC).

Best-effort by contract: an audit write failure logs a warning and never
breaks or delays command execution. The file stays local (``data/`` is
gitignored) because it records real engagement commands and targets.
"""
from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone

_lock = threading.Lock()
_DEFAULT_PATH = os.path.join("data", "audit_log.jsonl")

AUDIT_PATH = _DEFAULT_PATH


def log_event(kind: str, operator: str, target: str, command: str,
              status: str, reason: str = "") -> bool:
    """Append one audit event to ``data/audit_log.jsonl``.

    Args:
        kind (str): Event class: "command" | "block" | "target_reject".
        operator (str): What drove the action: "agent" | "gui" | "cli" |
            "self-heal".
        target (str): The target the action relates to ("" when none).
        command (str): The command or probe payload; truncated to 500 chars.
        status (str): "executed" | "blocked" | "rejected" | "error".
        reason (str): Short block/rejection reason ("" when none).

    Returns:
        bool: True when the line was appended, False on any I/O problem
        (the failure is logged, never raised - auditing must not break
        execution).
    """
    entry = {
        "ts": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ"),
        "kind": str(kind),
        "operator": str(operator),
        "target": str(target)[:200],
        "command": str(command)[:500],
        "status": str(status),
        "reason": str(reason)[:200],
    }
    try:
        os.makedirs(os.path.dirname(AUDIT_PATH) or ".", exist_ok=True)
        with _lock:
            with open(AUDIT_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, sort_keys=True) + "\n")
        return True
    except OSError as exc:
        import logging
        logging.getLogger(__name__).warning(
            "[AUDIT] failed to append event (%s): %s", entry["kind"], exc)
        return False


def read_events(limit: int = 200) -> list[dict]:
    """Return the most recent audit events, oldest last.

    Args:
        limit (int): Max number of trailing events to return.

    Returns:
        list[dict]: Parsed events; a missing or corrupt line is skipped.
    """
    if not os.path.isfile(AUDIT_PATH):
        return []
    events: list[dict] = []
    try:
        with open(AUDIT_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    events.append(json.loads(line))
                except ValueError:
                    continue
    except OSError:
        return []
    return events[-max(1, int(limit)):]
