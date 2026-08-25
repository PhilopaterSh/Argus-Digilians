import re
import json
import urllib.parse
from app.core.memory.memory_service import ArgusMemory
from app.tools.utils import normalize_domain_for_memory, find_sensitive_content_match

MAX_HISTORY = 10
LOOP_THRESHOLD = 3


class ReflectiveVerificationService:
    """
    Implements Reflective Verification and Task Difficulty Assessment (TDA)
    based on the Red-MIRROR and PentestGPT v2 architectures.
    """

    def __init__(self, runner, memory: ArgusMemory):
        """Store collaborators and initialize the recent-command history
        used for infinite-loop detection.

        Args:
            runner: Object with a `run(command)` method (shared
                CommandRunner) - not called directly by this class, kept
                for interface consistency with sibling tool services.
            memory (ArgusMemory): Used to look up the blackboard summary
                and to upsert target priority scores.
        """
        self.runner = runner
        self.memory = memory
        self._command_history: list[str] = []

    def pre_execute_verify(self, command: str) -> str:
        """
        [Phase 1 Reflection] Checks command inputs for syntax validity, parameter structure,
        and dangerous/malformed arguments before execution.

        Args:
            command (str): The shell command about to be executed.

        Returns:
            str: A human-readable verification message - "SUCCESS: ..." if
            the command passes all checks, or a "Verification
            Warning/Blocked: ..." message naming the specific problem
            (empty command, blacklisted pattern, missing target/URL, or a
            repeated-command loop).
        """
        print(f"[*] [Reflector-Phase1] Verifying command: {command}")
        
        # 1. Reject empty commands
        if not command or not command.strip():
            return "Verification Warning: Command is empty."

        # 2. Syntax/Blacklist validation for dangerous characters (prevent command injection on Host)
        forbidden_patterns = [r";\s*rm\s+-rf", r"\|\|\s*rm\s+", r"&\s*rm\s+"]
        for pattern in forbidden_patterns:
            if re.search(pattern, command, re.IGNORECASE):
                return "Verification Blocked: Command contains blacklisted patterns or dangerous sequences."

        # 3. Parameter checks (e.g., matching common tools with known syntax requirements)
        # Nmap host validation
        if command.startswith("nmap"):
            # Check if there is a target
            parts = command.split()
            if len(parts) < 2:
                return "Verification Warning: Nmap command is missing targets or arguments."
        
        # Curl checks
        if "curl" in command:
            # Check if url starts with http/https
            urls = re.findall(r'https?://[^\s\'"]+', command)
            if not urls:
                return "Verification Warning: Curl command is missing a valid HTTP/HTTPS target URL."

        # 4. Infinite Loop Prevention: detect 3+ identical consecutive commands
        self._command_history.append(command)
        if len(self._command_history) > MAX_HISTORY:
            self._command_history.pop(0)
        if len(self._command_history) >= LOOP_THRESHOLD:
            recent = self._command_history[-LOOP_THRESHOLD:]
            if all(c == command for c in recent):
                return "Verification Blocked: Command repeated 3+ times (possible infinite loop)."

        print(f"[+] [Reflector-Phase1] Command successfully verified.")
        return "SUCCESS: Command syntax and parameters validated."

    def post_execute_verify(self, url: str, command: str, raw_output: str) -> str:
        """
        [Phase 2 Reflection] Introspects command outputs to identify False Positives, WAF redirects,
        honeypot patterns, and verify actual impact.

        Args:
            url (str): The target URL the command was run against - used
                to key any recorded finding.
            command (str): The command that was executed, recorded
                alongside a confirmed finding.
            raw_output (str): The command's raw output to analyze.

        Returns:
            str: A human-readable analysis message - an "ALERT: ..."
            message for a WAF block or a suspected false positive, a
            "SUCCESS: ..." message (and a recorded finding) for a
            confirmed high-severity signature, or a generic
            "no immediate false positives or exploit signatures detected"
            message otherwise.
        """
        print(f"[*] [Reflector-Phase2] Analyzing output for {url}...")
        
        if not raw_output or not raw_output.strip():
            return "Analysis: Output is empty. Target might have timed out."

        clean_target = normalize_domain_for_memory(url)

        # 1. Confirmed-impact verification FIRST.
        # A real sensitive-content signature (an actual /etc/passwd body, a
        # leaked DB_PASSWORD, win.ini's section header) is positive proof that
        # content came back, and it outranks every heuristic below. This check
        # used to run last, after the WAF scan - so a genuine traversal read on
        # a Cloudflare-fronted target was discarded as "BLOCKED" the moment the
        # word "cloudflare" appeared anywhere in the captured output (a Server
        # header is enough), silently downgrading a real compromise to a
        # non-finding. Heuristics may never veto hard evidence.
        for indicator, summary in SENSITIVE_CONTENT_INDICATORS.items():
            if indicator in raw_output:
                # Document finding directly in memory
                self.memory.add_finding(clean_target, "reflective_verification", "high_severity_vulnerability", command, f"VERIFIED: {summary}")
                return f"SUCCESS: High-severity finding verified. {summary}"

        # 2. WAF Block Page Verification
        waf_indicators = [
            "cloudflare", "sucuri", "incapsula", "akamai", "mod_security",
            "access denied", "blocked by waf", "request blocked", "403 forbidden"
        ]
        for ind in waf_indicators:
            if ind.lower() in raw_output.lower():
                return f"ALERT: Target responded with a WAF block/challenge page. Action should be marked as BLOCKED."

        # 3. Redirect/Honeypot/False Positive Verification (e.g., 200 OK with login page or size 0)
        # Check if HTTP status codes are printed
        http_code_match = re.search(r'\b(200|301|302|404|500)\b', raw_output)
        if http_code_match:
            code = http_code_match.group(1)
            # If it's a redirect to homepage or content length is 0
            if code in ["301", "302"] and ("location: / " in raw_output.lower() or "location: http" in raw_output.lower()):
                return "ALERT: Possible False Positive. Tool reported status 200/302, but it's a redirect to the homepage."
            
            # Content Length Verification
            content_length_match = re.search(r'content-length:\s*(\d+)', raw_output, re.IGNORECASE)
            if content_length_match:
                length = int(content_length_match.group(1))
                if length == 0:
                    return "ALERT: False Positive. Target returned status 200 OK, but Content-Length is 0."

        # 3. Analyze output for actual indicators of success (e.g. Web.config contents, /etc/passwd contents)
        summary = find_sensitive_content_match(raw_output)
        if summary:
            # Document finding directly in memory
            self.memory.add_finding(clean_target, "reflective_verification", "high_severity_vulnerability", command, f"VERIFIED: {summary}")
            return f"SUCCESS: High-severity finding verified. {summary}"


        return "Analysis: Command executed successfully. No immediate false positives or exploit signatures detected."

    def task_difficulty_assessment(self, targets: str) -> str:
        """
        Computes a Task Difficulty Assessment (TDA) score (0.0 to 10.0) for target selection
        based on open ports, version confidence, complexity, and expected path length.

        Args:
            targets (str): A comma-separated list of target hosts.

        Returns:
            str: A multi-target TDA report (one block per target with its
            path-length/confidence/WAF scores, computed TDA score, and a
            recommended action), or "Error: No targets provided." if
            `targets` has no non-empty entries.
        """
        target_list = [t.strip() for t in targets.split(",") if t.strip()]
        if not target_list:
            return "Error: No targets provided."

        assessment_report = ["=== TASK DIFFICULTY ASSESSMENT (TDA) REPORT ==="]
        
        for target in target_list:
            clean_target = normalize_domain_for_memory(target)
            
            # Gather intelligence details from memory to compute metrics
            # 1. Path length (e.g., number of open ports / services)
            # 2. Version confidence (fingerprinted exact versions)
            # 3. Attack surface size
            
            # Simple simulation of TDA metric scoring:
            # - More open services = more paths (Higher Path Length, Lower Difficulty)
            # - Exact version fingerprinted = Higher Confidence (Lower Difficulty)
            # - Heavy WAF presence = Higher Difficulty
            
            # Query memory to see if we have scan info
            findings_summary = self.memory.get_blackboard_summary()
            target_data = {}
            try:
                state_data = json.loads(findings_summary)
                target_data = state_data.get(clean_target, {})
            except Exception:
                pass
            
            ports_count = 0
            has_versions = False
            has_waf = False
            
            if "ports" in target_data:
                ports_count = len(re.findall(r'\b\d+/tcp\b', target_data["ports"]))
            if "tech" in target_data:
                has_versions = any(char.isdigit() for char in target_data["tech"])
                has_waf = "waf" in target_data["tech"].lower() or "blocked" in target_data["tech"].lower()

            # TDA Quantitative Metrics Scoring:
            base_score = 5.0 # Start in the middle
            
            # 1. Path Length Factor (Expected steps)
            # If we have many ports, we have more surface to explore
            path_length_score = max(1, 10 - ports_count)
            
            # 2. Confidence Score (Evidence quality)
            confidence_score = 8.0 if has_versions else 3.0
            
            # 3. Defense Evasion Difficulty
            defense_penalty = 3.0 if has_waf else 0.0
            
            # Calculate final TDA score
            tda_score = round((path_length_score * 0.4) + ((10 - confidence_score) * 0.3) + (defense_penalty * 0.3), 2)
            
            # Suggest Action
            if tda_score < 4.0:
                action = "RECOMMENDED: Low difficulty target with highly defined attack path. Target immediately."
            elif tda_score < 7.0:
                action = "MODERATE: Target requires standard enumeration and tool scanning."
            else:
                action = "HIGH DIFFICULTY: Target defended by WAF or has minimal attack surface. Recommend advanced evasion probes."

            assessment_report.append(
                f"\nTarget: {clean_target}\n"
                f"  - Path Length Score (Lower is better): {path_length_score}/10\n"
                f"  - Version Confidence Score (Higher is better): {confidence_score}/10\n"
                f"  - WAF Presence: {'Yes' if has_waf else 'No'}\n"
                f"  - Calculated TDA Score: {tda_score}/10\n"
                f"  - {action}"
            )
            
            # Update target priority in memory
            priority_val = int((10.0 - tda_score) * 10)
            self.memory.upsert_target(clean_target, priority=priority_val)

        return "\n".join(assessment_report)
