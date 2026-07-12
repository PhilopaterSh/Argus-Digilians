"""
ArgusBrain (AI-DRIVEN) — LLM decides every step instead of a fixed pipeline.

Drop-in replacement for the old sequential ArgusBrain. Same public interface:
    brain = ArgusBrain(model_name, tools_list)
    result = brain.ask("scan example.com")     # -> dict (same keys as before)

How it works
------------
Instead of running hard-coded phases in a fixed order, the LLM is the
controller. Each round it sees:
  - the goal and the target,
  - the catalog of available tools (name + description),
  - a running digest of every action already taken and what it returned
    (including AI-generated evidence notes, e.g. "which subdomains look
    worth deep-scanning"),
and it chooses the NEXT tool to run (or decides to finish). The tools still do
the real work — the AI is the brain that directs them; it never invents a
result. This is an evidence-conditioned decision LOOP (a small state
machine), not a numbered script: the model can skip, reorder, or repeat
phases based on what it actually finds.

Only ONE step is forced outside the AI's control: Check_Reachability always
runs first. That is a deterministic guardrail (cheap, prevents wasting a
decision round — or real scan traffic — on a target that is not even up),
not a "which vulnerability class to test" decision. Generate_Report is
likewise always executed once, inside `finalize()`, regardless of exactly
when the model asks for it, so report parsing stays consistent.

Prompts
-------
The persona/rules (ARGUS_SYSTEM_PROMPT), the per-round decision prompt
(DECISION_PROMPT), and the end-of-scan synthesis prompt (FINAL_ANALYSIS_PROMPT)
all live in `core/prompts.py` — the single source of truth for every Argus
LLM prompt. This module no longer duplicates that text inline.

Safety / anti-hallucination
----------------------------
  - The tools are the ONLY source of findings. The LLM never invents results;
    it only decides what to run and, at the end, summarises real tool output.
  - Deterministic guardrails: reachability is always checked first, a tool is
    not re-run with the same input more than twice, there is a hard step cap,
    and Generate_Report is always called before returning.
  - `core/safety.py` (the SafetyLayer) and `core/tools.py` (the actual
    scanners/detection logic) are untouched by this controller — the AI only
    ever chooses WHICH already-vetted tool to call next, never HOW a tool
    detects a vulnerability.
  - If the model returns unparseable JSON, a heuristic fallback picks the next
    sensible un-run tool so the scan still completes.
"""
import os
import re
import json as _json
from datetime import datetime

from langchain_ollama import OllamaLLM
from core.schemas import SecurityReport
from langchain_core.output_parsers import PydanticOutputParser
from core.prompts import DECISION_PROMPT, FINAL_ANALYSIS_PROMPT, get_system_prompt


_RECOMMENDED_ORDER = [
    "Check_Reachability",
    "Subdomain_Enumeration",
    "Get_Priority_Targets",
    "Recon_Suite",
    "Query_Scenario_KB",
    "Run_Nikto",
    "Path_Traversal_Check",
    "XSS_Check",
    "SQLi_Check",
    "Smart_Web_Search",
    "Query_Memory",
    "Query_Knowledge_Graph",
    "Generate_Report",
]

MAX_STEPS = 16
OBS_TRUNC = 900
_MAX_SAME_REPEAT = 2

# Guardrails against "stuck in recon forever" (observed: a flaky crt.sh kept
# getting retried via Recon_Suite/Subdomain_Enumeration and the scan reached
# Generate_Report having NEVER run a vulnerability check). These are
# code-enforced, not just prompt text, so they hold even on a weaker/smaller
# local model that doesn't reliably follow the "don't retry a dead tool" rule.
_VULN_TOOLS = ("Path_Traversal_Check", "XSS_Check", "SQLi_Check", "Run_Nikto")
_RECON_NUDGE_AT = 4    # steps with zero vuln-tool calls -> inject an urgent reminder
_RECON_FORCE_AT = 7    # steps with zero vuln-tool calls -> deterministically force one

# Observed: a weaker/local model kept re-choosing an already-maxed-out tool
# (e.g. Recon_Suite) 3 times in a row after each was skipped, burning the
# rest of the step budget instead of picking something new. After this many
# consecutive skips, stop asking and wrap up with whatever evidence exists.
_CONSECUTIVE_SKIP_LIMIT = 2


class ArgusBrain:
    def __init__(self, model_name: str, tools_list: list):
        self.llm = OllamaLLM(
            model=model_name,
            timeout=3600,
            temperature=0.1,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        )
        self.tools = tools_list
        self.tool_map = {t.name: t.func for t in tools_list}
        self.tool_desc = {t.name: getattr(t, "description", "") for t in tools_list}
        self.output_parser = PydanticOutputParser(pydantic_object=SecurityReport)

    def _parse_scan_pattern(self, raw: str):
        raw = raw.strip()
        raw = re.sub(r'^[a-zA-Z][a-zA-Z0-9+.\-]*://', '', raw)
        sub_mode = raw.startswith("*.")
        slash_stars = raw.count("/*")
        dir_mode = slash_stars > 0
        depth = max(slash_stars, 1) if dir_mode else 0
        d = raw
        if sub_mode:
            d = d[2:]
        # Domain END boundary: cut at the first '/', ':' (port), '?' (query
        # string), or '#' (fragment) — whichever comes first — so anything
        # that isn't part of the hostname is dropped.
        for sep in ("/", ":", "?", "#"):
            d = d.split(sep)[0]
        if d.lower().startswith("www."):
            d = d[4:]
        return d, sub_mode, dir_mode, depth

    _MULTI_URL_PREFIX = "__MULTI_URL_PASTE__"

    def _extract_target(self, query: str) -> str:
        q = query.strip()
        first_tok = q.split()[0] if q else q
        if first_tok.startswith("*.") or "/*" in first_tok:
            return first_tok

        # Domain START boundary guard: catch a common paste mistake where two
        # full URLs end up stuck together with no separator, e.g. a leftover
        # placeholder "https://example.com" immediately followed by the real
        # target "https://lab-id.web-security-academy.net/". A naive greedy
        # regex would silently merge both into a garbage hostname (observed:
        # "example.comhttps") and the whole scan would run against nothing.
        # Detect 2+ scheme occurrences BEFORE any hostname extraction and
        # fail loudly instead of guessing which URL was intended.
        scheme_hits = list(re.finditer(r"https?://", q))
        if len(scheme_hits) >= 2:
            bounds = [h.start() for h in scheme_hits] + [len(q)]
            urls = [q[bounds[i]:bounds[i + 1]].strip().rstrip(",") for i in range(len(scheme_hits))]
            return self._MULTI_URL_PREFIX + "|".join(urls)

        m = re.search(r"https?://[^\s,]+", q)
        if m:
            return m.group(0).rstrip("/")
        m = re.search(
            r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}",
            q,
        )
        if m:
            return m.group(0)
        return q.split()[0] if q else q

    def _call(self, tool_name: str, tool_input: str) -> str:
        fn = self.tool_map.get(tool_name)
        if not fn:
            return f"[SKIP] Tool '{tool_name}' not registered."
        try:
            return fn(tool_input) or "(no output)"
        except Exception as e:
            return f"[ERROR] {tool_name}: {e}"

    def _tool_catalog(self) -> str:
        return "\n".join(
            f"  - {name}: {self.tool_desc.get(name, '')}" for name in self.tool_map
        )

    @staticmethod
    def _normalize_for_repeat(value: str) -> str:
        """Normalize a tool input for repeat-detection so 'https://x.net/',
        'x.net', and ' X.NET ' are recognised as the SAME call. Exact-string
        comparison was letting the model re-run the same target with slightly
        different formatting each time, defeating the anti-loop guard."""
        v = (value or "").strip().lower()
        v = re.sub(r'^[a-zA-Z][a-zA-Z0-9+.\-]*://', '', v)
        return v.rstrip('/')

    def _history_digest(self, history: list) -> str:
        if not history:
            return "  (nothing run yet)"
        out = []
        for i, (tool, inp, obs) in enumerate(history, 1):
            snippet = obs.strip().replace("\n", " ")[:220]
            out.append(f"  {i}. {tool}({inp}) -> {snippet}")
        return "\n".join(out)

    def _decide_next(self, target: str, history: list, mode_note: str = "") -> dict:
        done = [h[0] for h in history]
        tool_names = ", ".join(self.tool_map.keys())
        digest = self._history_digest(history)
        if mode_note:
            digest = f"{digest}\n\n{mode_note}"
        task_prompt = DECISION_PROMPT.format(
            target=target,
            tool_catalog=self._tool_catalog(),
            history=digest,
        )
        prompt = get_system_prompt(tool_names) + "\n\n" + task_prompt
        try:
            raw = self.llm.invoke(prompt)
            m = re.search(r"\{.*\}", raw, re.DOTALL)
            if m:
                obj = _json.loads(m.group(0))
                tool = str(obj.get("tool", "")).strip()
                if tool:
                    return {
                        "tool": tool,
                        "input": str(obj.get("input", target)).strip() or target,
                        "reason": str(obj.get("reason", "")).strip(),
                    }
        except Exception:
            pass
        for t in _RECOMMENDED_ORDER:
            if t in self.tool_map and t not in done:
                return {"tool": t, "input": target,
                        "reason": "fallback: next recommended step (LLM output unparseable)"}
        return {"tool": "FINISH", "input": target, "reason": "fallback: nothing left"}

    @staticmethod
    def _is_confirmed_obs(tool: str, obs: str) -> bool:
        return tool in _VULN_TOOLS and any(
            marker in obs for marker in ("[CONFIRMED]", "[HIGH]", "[CRITICAL]")
        )

    # ── Deterministic PoC extraction ────────────────────────────────────────
    # The LLM narrative (_final_analysis) has been observed TWICE reporting
    # "No confirmed vulnerabilities" even when a vuln tool clearly returned a
    # [CONFIRMED]/[HIGH] result a few steps earlier — a reliability ceiling of
    # the local/small model, not a prompt-wording problem (Fix 5, placing the
    # evidence first in the prompt, did not fully solve it on a repeat run).
    # These regexes parse the EXACT fixed-format strings that check_xss(),
    # check_sqli() and check_path_traversal() in core/tools.py already return
    # for a confirmed hit (see the `summary.append(...)` blocks there). This
    # is regex over OUR OWN code's deterministic output — not LLM output — so
    # it is 100% reliable and needs no model cooperation at all.
    _XSS_HIT_RE = re.compile(
        r"\[(HIGH|MEDIUM)\]\s*Reflected XSS \w+\s*\n"
        r"\s*Method\s*:\s*(?P<method>.+?)\s*\n"
        r"\s*Page\s*:\s*(?P<page>.+?)\s*\n"
        r"\s*Param\s*:\s*(?P<param>.+?)\s*\n"
        r"\s*Payload\s*:\s*(?P<payload>.+?)\s*\n"
        r"\s*URL\s*:\s*(?P<url>.+?)\s*\n"
        r"\s*Reason\s*:\s*(?P<reason>.+?)\s*\n"
        r"\s*Proof\s*:\s*(?P<proof>.+?)\s*(?:\n|$)"
    )
    _SQLI_HIT_RE = re.compile(
        r"URL\s*:\s*(?P<url>.+?)\s*\n"
        r"\s*Param\s*:\s*(?P<param>.+?)\s*\n"
        r"\s*Payload:\s*(?P<payload>.+?)\s*\n"
        r"\s*Error\s*:\s*(?P<error>.+?)\s*\n"
        r"\s*Proof\s*:\s*(?P<proof>.+?)\s*(?:\n|$)"
    )
    _TRAVERSAL_HIT_RE = re.compile(
        r"URI\s*:\s*(?P<uri>.+?)\s*\n"
        r"\s*Payload\s*:\s*(?P<payload>.+?)\s*\n"
        r"\s*Matched\s*:\s*'(?P<matched>.+?)'\s*\n"
        r"\s*Evidence:\s*\n(?P<evidence>.*?)(?=\n\n\s*URI\s*:|\Z)",
        re.DOTALL,
    )

    @classmethod
    def _extract_poc(cls, tool: str, obs: str) -> list:
        """Deterministically parse a confirmed vuln-tool observation into
        structured PoC dicts. Returns [] if the format doesn't match (never
        raises) — worst case the deterministic section just has less detail,
        it never crashes the scan."""
        out = []
        try:
            if tool == "XSS_Check":
                for m in cls._XSS_HIT_RE.finditer(obs):
                    out.append({
                        "type": "Reflected XSS", "severity": m.group(1).title(),
                        "method": m.group("method").strip(), "target": m.group("url").strip(),
                        "param": m.group("param").strip(), "payload": m.group("payload").strip(),
                        "evidence": m.group("proof").strip(), "extra": m.group("reason").strip(),
                    })
            elif tool == "SQLi_Check":
                for m in cls._SQLI_HIT_RE.finditer(obs):
                    out.append({
                        "type": "SQL Injection", "severity": "Critical",
                        "method": "GET", "target": m.group("url").strip(),
                        "param": m.group("param").strip(), "payload": m.group("payload").strip(),
                        "evidence": m.group("proof").strip(), "extra": m.group("error").strip(),
                    })
            elif tool == "Path_Traversal_Check":
                for m in cls._TRAVERSAL_HIT_RE.finditer(obs):
                    out.append({
                        "type": "Path Traversal", "severity": "Critical",
                        "method": "GET", "target": m.group("uri").strip(),
                        "param": "(path)", "payload": m.group("payload").strip(),
                        "evidence": m.group("evidence").strip()[:400],
                        "extra": f"matched signature '{m.group('matched').strip()}'",
                    })
        except Exception:
            pass
        return out

    @staticmethod
    def _repro_steps(finding: dict) -> list:
        t = finding["type"]
        if t == "Reflected XSS":
            return [
                f"Send a {finding['method']} request to: {finding['target']}",
                f"This injects the payload `{finding['payload']}` into parameter '{finding['param']}'.",
                "View the HTTP response body (or View Page Source / Ctrl+U in a browser) and search "
                "for the payload text.",
                "If it appears verbatim/unencoded (not as &lt;...&gt;) and executes (e.g. as a JS "
                f"alert or inside a live HTML tag) — {finding['extra']} — the XSS is confirmed.",
                "Evidence captured by Argus at scan time (context around the reflection):\n"
                f"    ...{finding['evidence']}...",
            ]
        if t == "SQL Injection":
            return [
                f"Send a {finding['method']} request to: {finding['target']}",
                f"This injects the payload `{finding['payload']}` into parameter '{finding['param']}'.",
                f"The response body contains a database error signature: \"{finding['extra']}\" — "
                "this proves unsanitised input reached the SQL query.",
                "Evidence captured by Argus at scan time:\n"
                f"    ...{finding['evidence']}...",
            ]
        if t == "Path Traversal":
            return [
                f"Send a GET request to: {finding['target']}",
                f"This appends the traversal payload `{finding['payload']}` to the path.",
                f"The response body contains {finding['extra']} — this proves the application read a "
                "file outside its intended web root.",
                "Evidence captured by Argus at scan time:\n"
                f"    {finding['evidence']}",
            ]
        return ["(no reproduction template for this finding type)"]

    def _build_verified_findings_section(self, history: list) -> str:
        """Deterministic (non-LLM) ground-truth section: what was ACTUALLY
        confirmed, with PoC + reproduction steps, built purely from tool
        output. Placed ahead of the AI narrative so the user never has to
        take the model's word for whether a vulnerability exists."""
        findings = []
        for tool, _inp, obs in history:
            if not self._is_confirmed_obs(tool, obs):
                continue
            findings.extend(self._extract_poc(tool, obs))

        # de-dupe by (type, target, param)
        seen, unique = set(), []
        for f in findings:
            key = (f["type"], f["target"], f["param"])
            if key in seen:
                continue
            seen.add(key)
            unique.append(f)

        lines = [
            "This section is built directly from tool output by code — not by the AI narrative "
            "below — so it is accurate even if the free-text analysis underneath disagrees with it.",
            "",
        ]
        if not unique:
            lines.append(
                "[RESULT] No vulnerability-testing tool (Path_Traversal_Check / XSS_Check / "
                "SQLi_Check / Run_Nikto) returned a [CONFIRMED]/[HIGH]/[CRITICAL] result this scan."
            )
            ran = sorted({t for t, _, _ in history if t in _VULN_TOOLS})
            lines.append(
                f"Vulnerability tools that ran: {', '.join(ran) if ran else '(none ran this scan)'}."
            )
            return "\n".join(lines)

        lines.append(f"{len(unique)} CONFIRMED finding(s):\n")
        for i, f in enumerate(unique, 1):
            lines.append(f"── Finding #{i}: {f['type']} — {f['severity']} ──")
            lines.append(f"  Target URL / URI : {f['target']}")
            lines.append(f"  Method           : {f['method']}")
            lines.append(f"  Parameter        : {f['param']}")
            lines.append(f"  Payload used     : {f['payload']}")
            lines.append("  Reproduction steps:")
            for step_i, step in enumerate(self._repro_steps(f), 1):
                lines.append(f"    {step_i}. {step}")
            lines.append("")
        return "\n".join(lines)

    def _final_analysis(self, target: str, history: list) -> str:
        """Build the evidence block for FINAL_ANALYSIS_PROMPT.

        A long, noisy, purely-chronological evidence dump (16 steps of
        history, including repeated Recon_Suite runs and irrelevant
        Smart_Web_Search noise) was observed burying a real CONFIRMED
        finding — the final report wrote "No data from this scan" for
        Vulnerability Findings despite a HIGH-severity reflected XSS having
        been confirmed a few steps earlier. Root cause: on a smaller/local
        model, a single important line surrounded by thousands of characters
        of lower-value text is easy to miss ("lost in the middle").

        Fix: pull every CONFIRMED vulnerability result out and place it in
        its own clearly-labelled section FIRST, then dedupe the rest
        (exact-repeat tool+input calls, and [SKIP] noise add nothing)."""
        confirmed, other, seen = [], [], set()
        for tool, inp, obs in history:
            if tool == "_note":
                continue
            obs_stripped = obs.strip()
            if obs_stripped.startswith("[SKIP]"):
                continue  # anti-loop noise — no evidence value
            if self._is_confirmed_obs(tool, obs):
                confirmed.append((tool, inp, obs_stripped))
                continue
            key = (tool, self._normalize_for_repeat(inp))
            if key in seen:
                continue  # drop exact-duplicate recon/search/memory calls
            seen.add(key)
            other.append((tool, inp, obs_stripped))

        parts = []
        if confirmed:
            parts.append(
                "=== CONFIRMED VULNERABILITY FINDINGS (read these FIRST — the scan DID find "
                "something; do not write 'No data' for Vulnerability Findings or Risk "
                "Assessment below) ==="
            )
            parts.extend(f"### {tool}({inp}) — CONFIRMED\n{obs[:1500]}" for tool, inp, obs in confirmed)
        if other:
            parts.append("=== OTHER EVIDENCE (recon, intelligence, clean/negative results) ===")
            parts.extend(f"### {tool}({inp})\n{obs[:800]}" for tool, inp, obs in other)
        evidence = "\n\n".join(parts) if parts else "(no tool evidence was gathered this scan)"

        task_prompt = FINAL_ANALYSIS_PROMPT.format(target=target, evidence=evidence)
        prompt = get_system_prompt(", ".join(self.tool_map.keys())) + "\n\n" + task_prompt
        try:
            return self.llm.invoke(prompt).strip()
        except Exception as e:
            return f"[WARN] final analysis failed: {e}"

    def _select_interesting_targets(self, blackboard_json: str, cap: int = 8) -> list:
        try:
            bb = _json.loads(blackboard_json)
        except Exception:
            return []
        scored = []
        for dom, tools in (bb.items() if isinstance(bb, dict) else []):
            if not isinstance(tools, dict) or " " in dom or "." not in dom:
                continue
            score = 0
            for ttype, data in tools.items():
                if not isinstance(data, dict):
                    continue
                sev = data.get("severity", "Info")
                summ = data.get("summary", "")
                if ttype in ("leak", "secrets"):
                    score += 3
                if sev in ("High", "Critical"):
                    score += 2
                if "Open ports:" in summ and "No open ports" not in summ:
                    score += 1
            if score > 0:
                scored.append((score, dom))
        scored.sort(reverse=True)
        return [d for _, d in scored[:cap]]

    @staticmethod
    def _one_line_verdict(tool: str, obs: str) -> str:
        o = obs or ""
        if "[CONFIRMED]" in o or "CONFIRMED]" in o or "[HIGH] Reflected XSS" in o or "[CRITICAL]" in o:
            m = re.search(r"\[CONFIRMED\][^\n]*|\[HIGH\][^\n]*|\[CRITICAL\][^\n]*", o)
            return "VULNERABLE — " + (m.group(0).strip()[:120] if m else "confirmed finding")
        if "No SQL injection confirmed" in o or "No reflected XSS" in o or "No confirmed path traversal" in o \
           or "not a finding" in o or "No confirmed" in o:
            return "clean (no confirmed finding)"
        if "[ERROR]" in o or "could not fetch" in o.lower() or "getaddrinfo failed" in o.lower():
            return "not tested (target unreachable / error)"
        return (o.strip().replace("\n", " ")[:100] or "no output")

    def ask(self, query: str, callbacks=None, cancel_event=None) -> dict:
        raw_target = self._extract_target(query)

        if raw_target.startswith(self._MULTI_URL_PREFIX):
            urls = raw_target[len(self._MULTI_URL_PREFIX):].split("|")
            listed = "\n".join(f"  {i+1}. {u}" for i, u in enumerate(urls))
            msg = (
                "[INPUT ERROR] Detected two (or more) URLs pasted together with no space/comma "
                "between them:\n" + listed +
                "\nThis usually happens when a placeholder like 'https://example.com' wasn't "
                "cleared before pasting the real target. Re-run with exactly ONE target URL."
            )
            return {"output": msg, "output_str": msg, "raw": msg, "risk_score": 1,
                    "findings_count": 0, "report_data": {}, "json_path": "", "md_path": ""}

        domain, sub_mode, dir_mode, dir_depth = self._parse_scan_pattern(raw_target)
        target = domain

        _is_ip = bool(re.match(r'^\d{1,3}(\.\d{1,3}){3}$', target))
        _is_host = bool(re.search(r'[A-Za-z0-9]\.[A-Za-z]{2,}', target))
        if not (_is_ip or _is_host):
            msg = (f"[INPUT ERROR] '{target}' is not a valid domain or IP. "
                   f"Provide something like 'example.com' or 'https://example.com'.")
            return {"output": msg, "output_str": msg, "raw": msg, "risk_score": 1,
                    "findings_count": 0, "report_data": {}, "json_path": "", "md_path": ""}

        if sub_mode and dir_mode:
            mode_label = "SUBDOMAIN + DIRECTORY (AI-decided)"
        elif sub_mode:
            mode_label = "SUBDOMAIN (AI-decided)"
        elif dir_mode:
            mode_label = f"DIRECTORY hint (depth {dir_depth}, AI-decided)"
        else:
            mode_label = "DIRECT TARGET (AI-decided)"

        mode_note = (
            f"SCAN SCOPE HINT: the operator's pattern was '{raw_target}'. "
            + ("This is a SUBDOMAIN-WILDCARD scope — consider Subdomain_Enumeration "
               "and Get_Priority_Targets before deep vulnerability testing so you "
               "scan the highest-value hosts, not just the base domain. "
               if sub_mode else "")
            + (f"This includes a DIRECTORY-WILDCARD hint (depth {dir_depth}) — the "
               "vuln scanners already crawl/discover paths internally. "
               if dir_mode else "")
            + "This is guidance only: choose the actual next tool based on evidence."
        )

        bar = "=" * 60
        log = [bar,
               f"  ARGUS SCAN  |  Target: {target}",
               f"  Mode: {mode_label}",
               bar]

        try:
            from core.memory import ArgusMemory
            ArgusMemory().purge_bad_entities()
        except Exception:
            pass

        history = []

        def _cancelled():
            return cancel_event is not None and cancel_event.is_set()

        def finalize(stopped=False):
            if stopped:
                log.append("\n[STOPPED] Scan cancelled by user — building a PARTIAL "
                           "report from the evidence gathered so far.")
            log.append("\n── REPORT ──")
            _report_out = ""
            if "Generate_Report" in self.tool_map:
                _report_out = self._call("Generate_Report", target)
                history.append(("Generate_Report", target, _report_out))
                log.append("  " + _report_out.strip().replace("\n", "\n  "))

            log.append("\n" + bar + "\n  VERIFIED FINDINGS — PROOF OF CONCEPT (deterministic)\n" + bar)
            log.append(self._build_verified_findings_section(history))

            log.append("\n" + bar + "\n  ARGUS AI THREAT ANALYSIS (narrative synthesis)\n" + bar)
            analysis = self._final_analysis(target, history)
            log.append(analysis)

            full_log = "\n".join(log)
            risk_score, findings_count, report_data = 1, 0, {}
            json_path = md_path = ""
            jm = re.search(r"JSON:\s*(.+\.json)", _report_out)
            mm = re.search(r"Markdown:\s*(.+\.md)", _report_out)
            if jm:
                json_path = jm.group(1).strip()
                try:
                    with open(json_path, encoding="utf-8") as f:
                        report_data = _json.load(f)
                    risk_score = report_data.get("meta", {}).get("risk_score", 1)
                    findings_count = len(report_data.get("findings", []))
                except Exception as e:
                    print(f"[!] Could not read JSON report: {e}")
            if mm:
                md_path = mm.group(1).strip()
            return {
                "output": full_log, "output_str": full_log, "raw": full_log,
                "risk_score": risk_score, "findings_count": findings_count,
                "report_data": report_data, "json_path": json_path,
                "md_path": md_path, "stopped": stopped,
            }

        log.append("\n── STEP 0: Reachability (deterministic guardrail) ──")
        if "Check_Reachability" in self.tool_map:
            obs = self._call("Check_Reachability", target)
            history.append(("Check_Reachability", target, obs))
            log.append("  " + obs.strip().replace("\n", "\n  ")[:500])
        if _cancelled():
            return finalize(stopped=True)

        log.append(f"\n  [i] {mode_note}")

        step_num = 1
        consecutive_skips = 0  # see _CONSECUTIVE_SKIP_LIMIT below
        while step_num <= MAX_STEPS:
            if _cancelled():
                return finalize(stopped=True)

            vuln_done = any(h[0] in _VULN_TOOLS for h in history)
            recon_only_steps = step_num - 1  # completed decision rounds so far

            # Hard guardrail: too many rounds with zero vulnerability testing
            # (e.g. stuck retrying a flaky crt.sh via Recon_Suite) -> stop
            # asking and force real testing so the scan can't quietly end
            # with no vulnerability coverage at all.
            if not vuln_done and recon_only_steps >= _RECON_FORCE_AT:
                forced_tool = next((t for t in _VULN_TOOLS if t in self.tool_map), None)
                if forced_tool:
                    log.append(f"\n  ── Step {step_num}: {forced_tool}({target}) [FORCED] ──")
                    log.append(f"      reason: {recon_only_steps} steps passed with no vulnerability "
                               f"test run yet — forcing {forced_tool} on the base target.")
                    obs = self._call(forced_tool, target)
                    history.append((forced_tool, target, obs))
                    log.append("      " + self._one_line_verdict(forced_tool, obs))
                    step_num += 1
                    continue

            nudge = ""
            if not vuln_done and recon_only_steps >= _RECON_NUDGE_AT:
                nudge = (
                    f"\n\n[URGENT] {recon_only_steps} steps have passed with NO vulnerability test "
                    "run yet (no Path_Traversal_Check / XSS_Check / SQLi_Check / Run_Nikto). Recon "
                    "is not the deliverable. Run one of those NOW on the base target unless "
                    "Check_Reachability actually failed."
                )

            decision = self._decide_next(target, history, mode_note=mode_note + nudge)
            tool = decision["tool"]
            reason = decision.get("reason", "")
            tool_input = decision.get("input", target)

            if tool == "FINISH":
                log.append(f"\n  [AI] Step {step_num}: FINISH — {reason or 'sufficient evidence gathered'}")
                break

            if tool == "Generate_Report":
                log.append(f"\n  [AI] Step {step_num}: model requests Generate_Report — {reason}")
                break

            log.append(f"\n  ── Step {step_num}: {tool}({tool_input}) ──")
            if reason:
                log.append(f"      reason: {reason}")

            if tool not in self.tool_map:
                log.append(f"      [SKIP] '{tool}' is not a registered tool.")
                history.append((tool, tool_input, f"[SKIP] '{tool}' not registered."))
                step_num += 1
                consecutive_skips += 1
                if consecutive_skips >= _CONSECUTIVE_SKIP_LIMIT:
                    log.append(f"\n  [i] {consecutive_skips} skipped/invalid decisions in a row — "
                               "stopping the decision loop early and proceeding to report.")
                    break
                continue

            already_same = sum(
                1 for h in history
                if h[0] == tool and self._normalize_for_repeat(h[1]) == self._normalize_for_repeat(tool_input)
            )
            if already_same >= _MAX_SAME_REPEAT:
                log.append(f"      [SKIP] '{tool}' already run {already_same}x with an equivalent input.")
                history.append((tool, tool_input,
                                 f"[SKIP] repeat limit ({_MAX_SAME_REPEAT}) reached for this input."))
                step_num += 1
                consecutive_skips += 1
                # The model is clearly stuck re-choosing an already-maxed-out
                # tool (observed: 3 back-to-back Recon_Suite skips burning the
                # rest of the step budget). Stop asking and wrap up instead.
                if consecutive_skips >= _CONSECUTIVE_SKIP_LIMIT:
                    log.append(f"\n  [i] {consecutive_skips} skipped/repeated decisions in a row — "
                               "stopping the decision loop early and proceeding to report.")
                    break
                continue

            consecutive_skips = 0
            obs = self._call(tool, tool_input)
            history.append((tool, tool_input, obs))
            if tool in ("Path_Traversal_Check", "XSS_Check", "SQLi_Check"):
                log.append("      " + self._one_line_verdict(tool, obs))
            else:
                log.append("      " + obs.strip().replace("\n", "\n      ")[:400])

            if tool == "Query_Memory":
                interesting = self._select_interesting_targets(obs)
                if interesting:
                    note = "[EVIDENCE] Hosts with open ports / confirmed leaks worth deep vulnerability scanning: " + ", ".join(interesting)
                    history.append(("_note", "", note))
                    log.append("      " + note)

            step_num += 1
        else:
            log.append(f"\n  [i] Reached the {MAX_STEPS}-step AI decision cap; proceeding to report.")

        return finalize(stopped=False)

    def simple_ask(self, prompt: str) -> dict:
        return {"output": self.llm.invoke(prompt)}
