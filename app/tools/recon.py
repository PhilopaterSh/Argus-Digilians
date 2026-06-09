import re
from concurrent.futures import ThreadPoolExecutor

from tools.utils import clean_target, ensure_url


class ReconService:
    """Responsible only for reconnaissance orchestration."""

    def __init__(self, runner, memory, fuzzer, secret_analyzer, report_writer):
        self.runner = runner
        self.memory = memory
        self.fuzzer = fuzzer
        self.secret_analyzer = secret_analyzer
        self.report_writer = report_writer
        self.last_recon_results = None

    def recon_suite(self, url: str, selected_targets=None) -> str:
        base_target = clean_target(url)
        root_domain = base_target.replace("www.", "")

        print(f"[*] Starting Intelligence Gathering for: {root_domain}")

        subdomain_report = ""
        if not selected_targets:
            subdomain_report = self.enumerate_subdomains(root_domain)
            alive_targets = self._extract_alive_targets(subdomain_report)
            process_targets = self.prioritize_targets(list(set(alive_targets)))[:3]
            if base_target not in process_targets:
                process_targets.append(base_target)
        else:
            process_targets = selected_targets

        intel_data = {}
        final_results = [
            f"--- 🛡️ COMPREHENSIVE ARGUS RECON REPORT: {root_domain} ---",
            f"[+] Focus Area: {', '.join(process_targets)}\n",
        ]

        with ThreadPoolExecutor(max_workers=3) as executor:
            future_results = list(executor.map(self.analyze_single_target, process_targets))
            for target_name, data, text_report in future_results:
                intel_data[target_name] = data
                final_results.append(text_report)

        self.last_recon_results = intel_data
        self.report_writer.save_json_report(root_domain, intel_data)

        full_text_report = "\n".join(final_results)
        if subdomain_report:
            full_text_report += "\n\n=== 📋 COMPLETE SUBDOMAIN INVENTORY ===\n" + subdomain_report

        return full_text_report

    def analyze_single_target(self, target: str):
        target_url = ensure_url(target, default_scheme="https")

        waf_result = self.runner.run(f"wafw00f {target_url}")
        fingerprint_result = self.runner.run(f"whatweb -v --color=never --no-errors {target_url}")
        services_result = self.runner.run(f"nmap -F --open -sV {target}")
        fuzz_result = self.fuzzer.fuzz_sensitive_files(target_url)
        secrets_result = self.secret_analyzer.analyze_secrets(target_url)
        headers_result = self.runner.run(f"curl -sI {target_url}")

        target_intel = {
            "waf": waf_result,
            "fingerprint": fingerprint_result,
            "services": services_result,
            "fuzzing": fuzz_result,
            "secrets": secrets_result,
            "headers": headers_result,
        }

        self._save_target_intelligence(
            target=target,
            waf_result=waf_result,
            fingerprint_result=fingerprint_result,
            services_result=services_result,
            fuzz_result=fuzz_result,
            secrets_result=secrets_result,
            headers_result=headers_result,
        )

        waf_summary = self._extract_waf_summary(waf_result)
        tech_summary = self._extract_tech_summary(fingerprint_result)

        report_section = [f"\n=== 🎯 TARGET: {target} ==="]
        report_section.append(f"\n[*] WAF Analysis...\n{waf_summary}")
        report_section.append(f"\n[*] Deep Fuzzing & Secrets...\n{fuzz_result}\n{secrets_result}")
        report_section.append(f"\n[*] Fingerprinting...\n{tech_summary}")

        return target, target_intel, "\n".join(report_section)

    def enumerate_subdomains(self, domain: str) -> str:
        print(f"[*] Starting deep subdomain enumeration for: {domain}")
        result = self.runner.run(f"argus_recon {domain}")

        if "TOP VERIFIED SUBDOMAINS:" in result:
            try:
                for subdomain in self._extract_alive_targets(result):
                    self.memory.upsert_target(subdomain, parent_domain=domain)
            except Exception as exc:
                print(f"[!] Error parsing/saving subdomains: {exc}")

        return result

    def prioritize_targets(self, targets: list[str]) -> list[str]:
        return sorted(targets, key=len)

    def _extract_alive_targets(self, report: str) -> list[str]:
        targets = []
        capture = False

        for line in report.split("\n"):
            if "TOP VERIFIED SUBDOMAINS:" in line:
                capture = True
                continue
            if capture and "INFRASTRUCTURE POINTERS" in line:
                break
            if capture and line.strip() and not line.startswith("["):
                targets.append(line.strip().replace("https://", "").replace("http://", ""))

        return targets

    def _save_target_intelligence(
        self,
        target: str,
        waf_result: str,
        fingerprint_result: str,
        services_result: str,
        fuzz_result: str,
        secrets_result: str,
        headers_result: str,
    ):
        waf_summary = self._extract_waf_summary(waf_result)
        self.memory.add_finding(target, "wafw00f", "waf", waf_result, waf_summary)

        if "detected" in waf_summary.lower() and "[" in waf_summary:
            waf_match = re.search(r"\[(.*?)\]", waf_summary)
            if waf_match:
                waf_name = waf_match.group(1)
                self.memory.upsert_entity("waf", waf_name)
                self.memory.add_relation(target, waf_name, "PROTECTED_BY")

        tech_summary = self._extract_tech_summary(fingerprint_result)
        self.memory.add_finding(target, "whatweb", "tech", fingerprint_result, tech_summary)

        tech_matches = re.findall(r"\[ (.*?) \]", fingerprint_result)
        if tech_matches:
            for tech_item in tech_matches[0].split(","):
                tech_name = tech_item.strip().split("[")[0].strip()
                if tech_name:
                    self.memory.upsert_entity("tech", tech_name)
                    self.memory.add_relation(target, tech_name, "USES_TECH")

        ports_summary_lines = [
            line for line in services_result.split("\n") if "/tcp" in line and "open" in line
        ]
        ports_summary = ", ".join(ports_summary_lines) if ports_summary_lines else "No open ports found"
        self.memory.add_finding(target, "nmap", "ports", services_result, ports_summary)

        if "FOUND:" in fuzz_result:
            self.memory.add_finding(target, "fuzzer", "leak", fuzz_result, "Sensitive files found!")
            file_matches = re.findall(r"FOUND: (.*?)\s\(", fuzz_result)
            for file_url in file_matches:
                file_name = file_url.split("/")[-1]
                self.memory.upsert_entity("file", file_name, metadata={"url": file_url})
                self.memory.add_relation(target, file_name, "HAS_FILE")

        if "[!]" in secrets_result:
            self.memory.add_finding(target, "analyzer", "secrets", secrets_result, "Secrets leaked in HTML")

        self.memory.add_finding(target, "curl", "headers", headers_result, "HTTP Headers captured")

    def _extract_waf_summary(self, waf_result: str) -> str:
        summary_lines = [line for line in waf_result.split("\n") if "[+]" in line]
        return summary_lines[0] if summary_lines else "Not detected"

    def _extract_tech_summary(self, fingerprint_result: str) -> str:
        summary_lines = [
            line
            for line in fingerprint_result.split("\n")
            if "Summary :" in line or "Detected Plugins:" in line
        ]
        return " ".join(summary_lines[:2]) if summary_lines else "Unknown"
