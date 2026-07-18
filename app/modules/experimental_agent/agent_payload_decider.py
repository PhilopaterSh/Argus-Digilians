"""
core/agent_payload_decider.py

Phase 1 - Agent Payload Decider
================================
Asks WhiteRabbitNeo to select and rank the most relevant payloads
from the SecLists pool for XSS and SQLi scan steps, given the
current target context (detected tech stack, WAF presence, prior
confirmed findings this session).

Selection model - PREPEND
  Agent-selected payloads run first, in the agent's preferred order.
  Remaining SecLists payloads are appended in their original pool
  order up to MAX_TOTAL_PAYLOADS.  Full SecLists coverage is always
  preserved - the agent changes priority, not scope.

Safety guarantees
  - Never raises - every failure path returns the full SecLists pool.
  - The agent selects by INDEX into the SecLists pool.  It cannot
    introduce or fabricate new payloads.
  - Index validation is strict: out-of-range, non-integer, and
    duplicate indices are silently dropped.
  - A minimum of MIN_SELECTIONS valid indices is required; fewer
    valid indices triggers automatic fallback to the full pool.
  - Every decision - and every fallback - is logged with a reason.

Scope (Phase 1)
  Supported steps: "xss", "sqli" only.
  SSRF and file-fuzz selection are deferred to Phase 2.

Security note
  Only use Argus against targets you own or have written
  authorisation to test.  Argus is for authorised security
  assessment only.
"""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Callable, Optional
from app.modules.experimental_agent.payload_encoder import PayloadEncoder

# -- Module-level constants ----------------------------------------------------

SUPPORTED_STEPS: frozenset[str] = frozenset({"xss", "sqli"})

DECIDER_TIMEOUT:    int = 25   # soft timeout guidance (seconds)
MIN_SELECTIONS:     int = 3    # agent must return >= this many valid indices
MAX_SELECTIONS:     int = 12   # agent may select at most this many indices
MAX_TOTAL_PAYLOADS: int = 20   # combined cap: agent picks + SecLists fill
LOW_CONF_THRESHOLD: int = 40   # log warning when agent confidence < this

_STEP_LABELS: dict[str, str] = {
    "xss":  "Cross-Site Scripting (XSS)",
    "sqli": "SQL Injection (SQLi)",
}


# -- Result dataclass ----------------------------------------------------------

@dataclass
class DecisionResult:
    """
    Returned by AgentPayloadDecider.select_payloads().

    Always safe to use - ``payloads`` is never empty when a non-empty
    pool was supplied.
    """

    payloads:          list[str]   # final payload list for the scan step
    source:            str         # "agent" | "fallback"
    reasoning:         str         # agent's one-sentence explanation
    confidence:        int         # 0-100 self-reported confidence
    selected_indices:  list[int]   # agent's raw index choices ([] if fallback)
    fallback_reason:   str         # why fallback triggered ("" if agent succeeded)
    elapsed_ms:        int         # wall-clock time of the LLM call in ms
    encoding_applied:  str = ""    # technique applied to agent payloads ("" = none)

    @property
    def used_agent(self) -> bool:
        """True when the agent's selection is in effect."""
        return self.source == "agent"


# -- Main class ----------------------------------------------------------------

class AgentPayloadDecider:
    """
    Lightweight agentic layer that asks WhiteRabbitNeo to prioritise
    payloads for a scan step before the step executes.

    Instantiation
    -------------
        decider = AgentPayloadDecider(llm=engine, log_cb=self._log)

    Usage in a scan step
    ---------------------
        result   = decider.select_payloads(context)
        payloads = result.payloads   # always a non-empty list - safe to iterate
    """

    def __init__(
        self,
        llm,                                    # OllamaEngine instance
        log_cb: Optional[Callable] = None,      # agent.py's self._log signature
    ) -> None:
        self.llm     = llm
        self._log    = log_cb or (lambda msg, level="info": None)
        self._encoder = PayloadEncoder()

    # -- Public API ------------------------------------------------------------

    def select_payloads(self, context: dict) -> DecisionResult:
        """
        Main entry point.  Always returns a DecisionResult with a
        non-empty ``payloads`` list.  Never raises.

        Expected keys in ``context`` (built by _build_decider_context):
            step               str         "xss" | "sqli"
            target_url         str
            host               str
            tech_stack         list[str]   e.g. ["Django", "Nginx"]
            waf_detected       str|None    WAF name or None
            findings_so_far    list[dict]  confirmed findings this session
            available_payloads list[str]   the SecLists pool for this step
        """
        step = context.get("step", "")
        pool = context.get("available_payloads", [])

        # -- Guards: immediate fallback, no LLM call -----------------------
        if step not in SUPPORTED_STEPS:
            return self._fallback(
                step, pool, 0,
                f"step '{step}' not in supported set {set(SUPPORTED_STEPS)}",
            )
        if not pool:
            return self._fallback(step, pool, 0, "payload pool is empty")

        # -- Build prompt --------------------------------------------------
        prompt = self._build_prompt(context)

        # -- LLM call ------------------------------------------------------
        t0 = time.monotonic()
        try:
            raw, err = self.llm.generate(
                prompt,
                temperature=0.1,
                max_tokens=300,
            )
        except Exception as exc:
            elapsed = int((time.monotonic() - t0) * 1000)
            return self._fallback(step, pool, elapsed, f"LLM exception: {exc}")

        elapsed_ms = int((time.monotonic() - t0) * 1000)

        if err:
            return self._fallback(step, pool, elapsed_ms, f"LLM error: {err}")
        if not raw or not raw.strip():
            return self._fallback(step, pool, elapsed_ms, "LLM returned empty response")

        # -- Validate response ---------------------------------------------
        indices, reasoning, confidence, fail_reason, encoding = self._validate(raw, len(pool))
        if indices is None:
            return self._fallback(step, pool, elapsed_ms, fail_reason)

        # -- Low-confidence warning (honour selection, just warn) ----------
        if confidence < LOW_CONF_THRESHOLD:
            self._log(
                f"[AgentDecider:{step.upper()}] [!] Low confidence "
                f"({confidence}/100) - agent selection applied with warning",
                "warn",
            )

        # -- Build final payload list (prepend model) ----------------------
        payloads = self._build_prepend_list(indices, pool)

        # -- Apply agent-requested encoding to agent-selected payloads only --
        if encoding:
            encoded_picks = [
                self._encoder.encode(p, encoding)
                for p in payloads[:len(indices)]
            ]
            payloads = encoded_picks + payloads[len(indices):]
            self._log(
                f"[AgentDecider:{step.upper()}] Encoding '{encoding}' applied "
                f"to {len(indices)} agent-selected payload(s)",
                "step",
            )

        # -- Log the decision (visible in Streamlit) -----------------------
        fill_count = len(payloads) - len(indices)
        self._log(
            f"[AgentDecider:{step.upper()}] Agent selected {len(indices)}/{len(pool)} "
            f"payloads (conf={confidence}/100, {elapsed_ms} ms) - \"{reasoning}\"",
            "step",
        )
        self._log(
            f"[AgentDecider:{step.upper()}] -> {len(payloads)} total "
            f"({len(indices)} agent-ranked + {fill_count} SecLists fill, "
            f"cap={MAX_TOTAL_PAYLOADS})",
            "step",
        )

        return DecisionResult(
            payloads=payloads,
            source="agent",
            reasoning=reasoning,
            confidence=confidence,
            selected_indices=indices,
            fallback_reason="",
            elapsed_ms=elapsed_ms,
            encoding_applied=encoding,
        )

    # -- Prompt builder --------------------------------------------------------

    def _build_prompt(self, context: dict) -> str:
        """
        Constructs the constrained index-selection prompt for WhiteRabbitNeo.

        Keeps the prompt small and deterministic so the 7B model stays
        on task.  Payload text is truncated to 120 chars each to avoid
        a context overflow.
        """
        step     = context["step"]
        host     = context.get("host", "unknown")
        tech     = context.get("tech_stack", [])
        waf      = context.get("waf_detected")
        findings = context.get("findings_so_far", [])
        pool     = context.get("available_payloads", [])

        step_label = _STEP_LABELS.get(step, step.upper())
        tech_str   = ", ".join(tech) if tech else "not detected"
        waf_str    = waf if waf else "none detected"

        # Compact findings summary - type + severity only, no raw data
        if findings:
            parts = [
                f"{f.get('data_type', '?')}:{f.get('severity', '?')}"
                for f in findings[:10]   # cap to control prompt size
            ]
            findings_str = f"{len(findings)} confirmed - {', '.join(parts)}"
        else:
            findings_str = "none yet"

        # Numbered payload list - truncate long entries to keep prompt compact
        payload_lines = "\n".join(
            f"[{i}] {p[:120]}"
            for i, p in enumerate(pool)
        )

        # WAF escalation hint - always prefer evasion, WAF makes it more aggressive
        waf_hint = (
            "\nWARNING: WAF detected. Be maximally aggressive with evasion - "
            "strongly prefer deeply encoded, obfuscated, or multi-layer bypass "
            "variants. Deprioritise any plaintext payloads."
            if waf else
            "\nNOTE: Even without a confirmed WAF, always prefer evasion-style, "
            "obfuscated, or encoded payloads over obvious plaintext ones. "
            "Modern defences often operate silently."
        )

        return (
            f"You are a security payload selector for an automated web scanner.\n"
            f"Choose which payloads from the numbered list are most likely to\n"
            f"succeed against this target. Do NOT invent new payloads.\n"
            f"\n"
            f"SCAN CONTEXT:\n"
            f"  Target host   : {host}\n"
            f"  Scan step     : {step_label}\n"
            f"  Tech stack    : {tech_str}\n"
            f"  WAF           : {waf_str}\n"
            f"  Prior findings: {findings_str}\n"
            f"{waf_hint}\n"
            f"\n"
            f"SELECTION PRIORITIES (apply in order):\n"
            f"  1. Evasion-style, obfuscated, or encoded variants - always preferred.\n"
            f"  2. Payloads that match the detected tech stack.\n"
            f"  3. Context-breaking or polyglot payloads over single-context ones.\n"
            f"  4. Plaintext / obvious payloads only if no evasion variants exist.\n"
            f"\n"
            f"AVAILABLE PAYLOADS (select by index):\n"
            f"{payload_lines}\n"
            f"\n"
            f"TASK:\n"
            f"Select between {MIN_SELECTIONS} and {MAX_SELECTIONS} indices from the list.\n"
            f"If uncertain, lean toward evasive payloads - select [0,1,2,3,4] "
            f"with confidence=35 rather than defaulting to obvious ones.\n"
            f"\n"
            f"OPTIONAL - ENCODING:\n"
            f"You may include an \"encoding\" field naming ONE technique to apply to your\n"
            f"selected payloads before injection.  Choose based on the WAF / target context.\n"
            f"\n"
            f"SQLi techniques (most evasive first):\n"
            f"  mysql_version_comment  - /*!50000 UNION*/ - MySQL executes, WAFs skip (Cloudflare/ModSec)\n"
            f"  char_encode            - CHAR(79,82,...) - defeats quote-based blacklists entirely\n"
            f"  concat_bypass          - CONCAT(0x4f,0x52,...) - breaks exact-string WAF matching\n"
            f"  base64_wrapper         - FROM_BASE64(...) - bypasses WAFs that ignore base64\n"
            f"  hex_encode             - 0x4f52... - bypasses quote filters (MySQL/MSSQL)\n"
            f"  sql_comment_obfuscation - UN/**/ION - splits keywords mid-word (all DBs)\n"
            f"  space_to_comment       - OR/**/1=1 - reliable whitespace bypass (all DBs)\n"
            f"  newline_bypass         - OR%0a1=1 - evades Cloudflare space tokenisers\n"
            f"  tab_bypass             - OR%091=1 - evades Akamai space tokenisers\n"
            f"  scientific_notation    - 1e0=1e0 - integer literals WAFs miss\n"
            f"  double_url_encode      - %253C - bypasses WAFs that decode once before matching\n"
            f"  case_randomization     - sElEcT - defeats case-sensitive pattern matching\n"
            f"\n"
            f"XSS techniques:\n"
            f"  unicode_encode         - JS \\u003c escapes - JS string context bypass\n"
            f"  html_entity_encode     - &#60;script&#62; - HTML attribute/element context (Akamai)\n"
            f"  double_url_encode      - also effective for XSS in URL params\n"
            f"\n"
            f"WAF quick-pick:\n"
            f"  Cloudflare   -> mysql_version_comment or newline_bypass\n"
            f"  Akamai       -> html_entity_encode or tab_bypass\n"
            f"  ModSecurity  -> mysql_version_comment or space_to_comment\n"
            f"  Unknown WAF  -> sql_comment_obfuscation or char_encode\n"
            f"\n"
            f"If no WAF is confirmed, still pick a technique - modern defences often\n"
            f"operate silently.  Omit \"encoding\" only if the payload is already heavily\n"
            f"obfuscated in the SecLists pool itself.\n"
            f"\n"
            f"OUTPUT FORMAT - CRITICAL:\n"
            f"- Your ENTIRE response must be one raw JSON object.\n"
            f"- Start with {{ and end with }}.\n"
            f"- NO markdown, NO code fences, NO explanation, NO text outside the JSON.\n"
            f"- The \"encoding\" field is OPTIONAL - include only if evasion is needed.\n"
            f"\n"
            f"Example (copy this format exactly):\n"
            f'{{"selected_indices": [0, 3, 7], "reasoning": "one sentence", "confidence": 75}}\n'
            f"\n"
            f"BEGIN JSON NOW:"
        )

    # -- Validation ------------------------------------------------------------

    def _validate(
        self,
        raw: str,
        pool_size: int,
    ) -> tuple[list[int] | None, str, int, str, str]:
        """
        Parse and strictly validate the LLM response.

        Returns
        -------
        (valid_indices, reasoning, confidence, fail_reason, encoding)

        On success  : valid_indices is a list[int], fail_reason is "", encoding may be "".
        On failure  : valid_indices is None, encoding is "".
        """
        # 1. Extract the outermost JSON object using three strategies in order.
        #
        #    Strategy A - strip markdown fences, then brace-depth matching.
        #      Finds the FIRST complete balanced {...} block, ignoring any text
        #      or braces that appear AFTER the JSON object closes.  This is the
        #      correct fix for WhiteRabbitNeo appending commentary like
        #      "Here's why I chose {these indices}:" after the JSON.
        #
        #    Strategy B - regex for flat (non-nested) objects as a last resort.
        #
        #    On total failure - log the raw response (truncated) so future
        #    issues can be diagnosed from the Streamlit log.

        # Strip markdown code fences before any extraction attempt
        cleaned = re.sub(r"```(?:json)?\s*", "", raw, flags=re.IGNORECASE)
        cleaned = cleaned.replace("```", "").strip()

        data = None

        # Strategy A: brace-depth walk - finds the first balanced { } block
        _start = cleaned.find("{")
        if _start != -1:
            _depth = 0
            for _i, _ch in enumerate(cleaned[_start:], start=_start):
                if _ch == "{":
                    _depth += 1
                elif _ch == "}":
                    _depth -= 1
                    if _depth == 0:
                        try:
                            data = json.loads(cleaned[_start : _i + 1])
                        except json.JSONDecodeError:
                            pass   # fall through to Strategy B
                        break

        # Strategy B: regex for flat objects (no nested braces in values)
        if data is None:
            _m = re.search(r"\{[^{}]*\}", cleaned)
            if _m:
                try:
                    data = json.loads(_m.group(0))
                except json.JSONDecodeError:
                    pass

        if data is None:
            # Log a truncated snapshot of the raw response for debugging
            _preview = repr(raw[:200]) + ("..." if len(raw) > 200 else "")
            self._log(
                f"[AgentDecider] JSON parse failed - raw LLM response: {_preview}",
                "warn",
            )
            return None, "", 0, "could not extract valid JSON from LLM response", ""

        # 2. selected_indices must be present and a list
        raw_indices = data.get("selected_indices")
        if not isinstance(raw_indices, list):
            return (
                None, "", 0,
                f"selected_indices is {type(raw_indices).__name__}, expected list",
                "",
            )

        # 3. Filter: integers only, in-range [0, pool_size), deduplicated,
        #    order preserved (agent's ranking matters for the prepend model)
        seen:  set[int] = set()
        valid: list[int] = []
        for item in raw_indices:
            if not isinstance(item, int):
                continue
            if item < 0 or item >= pool_size:
                continue
            if item in seen:
                continue
            seen.add(item)
            valid.append(item)

        # 4. Minimum floor - too few valid indices means the model is confused
        if len(valid) < MIN_SELECTIONS:
            return (
                None, "", 0,
                f"only {len(valid)} valid indices after filtering "
                f"(need >= {MIN_SELECTIONS}; pool_size={pool_size})",
                "",
            )

        # 5. Apply ceiling - discard excess beyond MAX_SELECTIONS
        valid = valid[:MAX_SELECTIONS]

        # 6. Extract optional metadata with safe defaults
        reasoning  = str(data.get("reasoning", "")).strip()[:300]
        confidence = data.get("confidence", 50)
        if not isinstance(confidence, int):
            try:
                confidence = int(confidence)
            except Exception:
                confidence = 50
        confidence = max(0, min(100, confidence))

        # Optional encoding technique requested by the agent
        encoding = str(data.get("encoding", "")).strip().lower()
        from app.modules.experimental_agent.payload_encoder import PayloadEncoder
        _valid_techniques = set(PayloadEncoder().get_available_techniques())
        if encoding not in _valid_techniques:
            encoding = ""   # ignore unknown technique names

        return valid, reasoning, confidence, "", encoding

    # -- Prepend + fill --------------------------------------------------------

    def _build_prepend_list(self, indices: list[int], pool: list[str]) -> list[str]:
        """
        PREPEND model:
          1. Agent-selected payloads first, in the agent's preferred order.
          2. Remaining pool payloads appended in their original order.
          3. Total capped at MAX_TOTAL_PAYLOADS.

        SecLists coverage is always fully preserved within the cap.
        """
        selected_set = set(indices)

        # Agent's picks
        result: list[str] = [pool[i] for i in indices]

        # Fill remainder from non-selected pool entries
        for idx, payload in enumerate(pool):
            if len(result) >= MAX_TOTAL_PAYLOADS:
                break
            if idx not in selected_set:
                result.append(payload)

        return result

    # -- Fallback --------------------------------------------------------------

    def _fallback(
        self,
        step:       str,
        pool:       list[str],
        elapsed_ms: int,
        reason:     str,
    ) -> DecisionResult:
        """
        Return the full SecLists pool unchanged and log the reason.

        This path is guaranteed never to raise.  It is the safety net
        for every possible failure mode.
        """
        tag = f"[AgentDecider:{step.upper()}]" if step else "[AgentDecider]"
        self._log(
            f"{tag} FALLBACK -> {reason} "
            f"(using full SecLists pool, {len(pool)} payloads)",
            "warn",
        )
        return DecisionResult(
            payloads=pool,
                      source="fallback",
            reasoning="",
            confidence=0,
            selected_indices=[],
            fallback_reason=reason,
            elapsed_ms=elapsed_ms,
        )
