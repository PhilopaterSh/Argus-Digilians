"""Recon-Assist brief ingestion — host-side bridge to the differential
reconnaissance pipeline (github.com/PhilopaterSh/Recon-Assist, v2.6).

The pipeline writes ``argus_brief.json`` (schema
``recon-assist/argus-brief@v1``) after every scheduled differential run:
new/changed hosts vs the accumulated baseline, takeover candidates, JS
secret indicators, ASN/network-owner attribution, and a deterministic
priority score per lead.

This service (spec 030-recon-assist-integration, Phase 1) is the read-side:
it loads the brief, ingests it into ArgusMemory (targets + findings with
lifecycle tags), and renders LLM-facing summaries and manual-testing
guidance. It is intentionally host-side and stdlib-only - the brief is
written on the Windows host by the pipeline and read here directly; no
WSL/SSH hop is involved (R5).

Guardrails (spec section 3):
- deterministic scores in the brief are authoritative; the agent refines,
  never invents;
- every host in the brief was already scope-guarded by the pipeline;
- JS secret indicators are candidates until manually verified.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List, Optional

TOOL_NAME = "recon_assist"


class ReconAssistBriefService:
    """Read-side bridge: load pipeline briefs, ingest into ArgusMemory,
    and render agent-facing summaries.

    Args:
        memory: ArgusMemory instance (upsert_target/add_finding are used).
            Optional for tests; ``None`` disables memory ingestion.
    """

    def __init__(self, memory: Any = None) -> None:
        self._memory = memory
        self._ingested: set[str] = set()  # brief signatures already ingested (R1)

    # ---------- public API ----------

    def load_brief(self, brief_path: str) -> str:
        """Load a brief file, ingest it, and return an LLM-facing summary.

        Idempotent per (R1): re-loading the same brief re-writes the same
        findings keyed by deterministic titles, and upsert_target dedupes.

        Args:
            brief_path: Path to ``argus_brief.json``. Windows host paths are
                expected (the pipeline writes host-side).

        Returns:
            str: Fenced Markdown summary for the agent loop, or a
            ``[!]``-prefixed error string (R2 - never raises to the caller).
        """
        data = self._read_brief(brief_path)
        if isinstance(data, str):
            return data  # error string

        stats = data.get("stats", {})
        priorities = data.get("priorities", [])
        new_hosts = data.get("new_hosts", [])
        generated = data.get("generated_utc", "unknown")

        if self._memory is not None:
            self._ingest(data)

        lines = [
            "```markdown",
            f"Recon-Assist brief (generated {generated})",
            f"New hosts: {stats.get('new_hosts', len(new_hosts))} | "
            f"Live: {stats.get('live', '?')} | "
            f"Takeover indicators: {stats.get('takeover_indicators', '?')} | "
            f"JS secret indicators: {stats.get('js_secret_indicators', '?')}",
            "",
            "Priority queue (deterministic - agent refines, never invents):",
        ]
        for p in priorities[:15]:
            lines.append(f"  [{p.get('score', 0)}] {p.get('host', '?')}")
            reasons = "; ".join(p.get("reasons", []))
            if reasons:
                lines.append(f"        reasons: {reasons}")
        if not priorities:
            lines.append("  (empty)")
        lines.append("```")
        return "\n".join(lines)

    def new_hosts(self, brief_path: str) -> List[str]:
        """Return the brief's new-host list (R3: tolerates URL lines)."""
        data = self._read_brief(brief_path)
        if isinstance(data, str):
            return []
        return [h for h in data.get("new_hosts", []) if h]

    def differential_guidance(self, brief_path: str) -> str:
        """Deterministic manual-testing guidance ordered by brief priority."""
        data = self._read_brief(brief_path)
        if isinstance(data, str):
            return data
        priorities = data.get("priorities", [])
        if not priorities:
            return "No prioritized leads in this brief."
        lines = ["Manual-testing guidance (highest priority first):"]
        for p in priorities[:20]:
            lines.append(f"[{p.get('score', 0)}] {p.get('host', '?')}")
            lines.append(f"      why: {'; '.join(p.get('reasons', []))}")
            lines.append("      first step: probe with httpx/curl, confirm exposure,")
            lines.append("      then assess within the program's rules.")
        return "\n".join(lines)

    # ---------- ingestion ----------

    def _ingest(self, data: Dict[str, Any]) -> None:
        generated = data.get("generated_utc", "unknown")
        signature = f"{generated}:{len(data.get('new_hosts', []))}:{data.get('stats', {}).get('new_hosts', 0)}"
        if signature in self._ingested:
            return
        self._ingested.add(signature)
        new_hosts = data.get("new_hosts", [])
        for host in new_hosts:
            host = _host_of(host)
            if not host:
                continue
            if self._memory is not None and hasattr(self._memory, "upsert_target"):
                self._memory.upsert_target(host)
        for p in data.get("priorities", []):
            host = _host_of(p.get("host", ""))
            if not host:
                continue
            if self._memory is not None and hasattr(self._memory, "add_finding"):
                self._memory.add_finding(
                    domain=host,
                    tool_name=TOOL_NAME,
                    data_type="priority_lead",
                    raw_data=json.dumps(p, ensure_ascii=False),
                    summary=f"score {p.get('score', 0)}: {'; '.join(p.get('reasons', []))}",
                    severity=_severity_of(p.get("score", 0)),
                )
        for indicator in data.get("takeover_indicators", []):
            host = _host_of(indicator)
            if self._memory is not None and hasattr(self._memory, "add_finding"):
                self._memory.add_finding(
                    domain=host or "(takeover)",
                    tool_name=TOOL_NAME,
                    data_type="takeover_indicator",
                    raw_data=indicator,
                    summary="takeover indicator from pipeline",
                    severity="High" if indicator.startswith("[CONFIRMED") else "Medium",
                )

    # ---------- internals ----------

    def _read_brief(self, brief_path: str) -> Any:
        """Load+validate the brief JSON. Returns dict or error string (R2)."""
        if not brief_path or not os.path.isfile(brief_path):
            return f"[!] Brief file not found: {brief_path}"
        try:
            with open(brief_path, encoding="utf-8") as fh:
                data = json.load(fh)
        except json.JSONDecodeError as exc:
            return f"[!] Brief is not valid JSON: {exc}"
        except OSError as exc:
            return f"[!] Brief unreadable: {exc}"
        if not isinstance(data, dict) or "schema" not in data:
            return "[!] Brief missing 'schema' marker - not a recon-assist brief."
        if not str(data["schema"]).startswith("recon-assist/argus-brief"):
            return f"[!] Unsupported brief schema: {data['schema']}"
        return data


def _host_of(line: str) -> str:
    """Extract a hostname from a bare host, URL, or httpx/takeover line."""
    line = line.strip()
    m = re.match(r"https?://([^/\s]+)", line)
    if m:
        return m.group(1)
    m = re.search(r"\]\s*(\S+)\s*->", line)
    if m:
        return m.group(1)
    return line.split()[0] if line.split() else ""


def _severity_of(score: int) -> str:
    if score >= 90:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"
