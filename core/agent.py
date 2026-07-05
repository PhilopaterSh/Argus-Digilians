"""
ArgusBrain - Sequential pipeline agent with LLM threat reasoning and RAG.

13-step pipeline:
  1  Check_Reachability
  2  Subdomain_Enumeration
  3  Get_Priority_Targets
  4  Recon_Suite           (WAF + tech + ports + file fuzzing + secrets)
  5  Run_Nikto
  6  Path_Traversal_Check
  7  XSS_Check
  8  SQLi_Check            <- NEW
  9  Smart_Web_Search
  10 LLM_Threat_Analysis   <- NEW  (RAG-enhanced reasoning)
  11 Query_Memory
  12 Query_Knowledge_Graph
  13 Generate_Report
"""
import os
import re
import json as _json
from datetime import datetime

from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import PydanticOutputParser
from core.schemas import SecurityReport


class ArgusBrain:
    def __init__(self, model_name: str, tools_list: list):
        self.llm = OllamaLLM(
            model=model_name,
            timeout=3600,
            temperature=0.1,
            base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434")
        )
        self.tools = tools_list
        self.tool_map = {t.name: t.func for t in tools_list}
        self.output_parser = PydanticOutputParser(pydantic_object=SecurityReport)

    # -- helpers -----------------------------------------------------------------

    def _parse_scan_pattern(self, raw: str):
        """Detect wildcard scan modes and extract clean domain.

        Pattern syntax (user types this as the scan target):
          *.example.com          -> subdomain enumeration only
          example.com/*/*/*      -> directory/path enumeration only (depth = wildcard count)
          *.example.com/*/*/*    -> both combined
          example.com            -> full vulnerability scan (all 13 steps)

        Returns: (domain, sub_mode, dir_mode, depth)
        """
        raw = raw.strip()
        sub_mode = raw.startswith('*.')
        slash_stars = raw.count('/*')
        dir_mode = slash_stars > 0
        depth = max(slash_stars, 1) if dir_mode else 0

        d = raw
        if sub_mode:
            d = d[2:]           # strip '*.'
        d = d.split('/')[0]     # strip path / wildcards
        d = d.split(':')[0]     # strip port
        if d.lower().startswith('www.'):
            d = d[4:]
        return d, sub_mode, dir_mode, depth

    def _extract_target(self, query: str) -> str:
        """Extract the target URL/domain from a natural-language query.

        Priority:
          0. Wildcard scan pattern    (*.example.com, example.com/*/*/*)
          1. Explicit URL with scheme (https://example.com)
          2. Bare domain / IP        (example.com, sub.domain.co.uk)
          3. Last resort: first token (avoids injecting the full prompt into tools)
        """
        # 0. Wildcard patterns — first token, pass to _parse_scan_pattern as-is
        first_tok = query.strip().split()[0] if query.strip() else query
        if first_tok.startswith('*.') or '/*' in first_tok:
            return first_tok
        # 1. Full URL with scheme
        m = re.search(r'https?://[^\s,]+', query)
        if m:
            return m.group(0).rstrip('/')
        # 2. Bare domain (e.g. sketchfab.com, sub.domain.co.uk)
        m = re.search(
            r'(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}',
            query
        )
        if m:
            return m.group(0)
        # 3. Last resort -- return first whitespace token (better than the whole prompt)
        return query.split()[0]
    def _call(self, tool_name: str, tool_input: str) -> str:
        fn = self.tool_map.get(tool_name)
        if not fn:
            return f"[SKIP] Tool '{tool_name}' not registered."
        try:
            return fn(tool_input) or "(no output)"
        except Exception as e:
            return f"[ERROR] {tool_name}: {e}"

    # -- LLM reasoning with RAG --------------------------------------------------

    def _llm_threat_analysis(self, domain: str, tech_str: str, open_ports: str,
                              reach: str, recon: str, traversal: str,
                              xss: str, sqli: str, search: str) -> str:
        """
        RAG-enriched LLM prompt. Feeds all scan evidence + knowledge base context
        into WhiteRabbitNeo and returns structured threat assessment.

        Skipped when: tech stack is unknown AND no vulnerability was confirmed,
        to avoid hallucinated findings in the report.
        """
        # Early exit -- skip LLM inference when there is nothing concrete to reason about
        has_confirmed = (
            "[CONFIRMED]" in traversal or "[CRITICAL]" in traversal
            or "[HIGH] Reflected XSS" in xss or "XSS CONFIRMED" in xss
            or "[MEDIUM] Reflected XSS" in xss
            or "[CONFIRMED]" in sqli or "[CRITICAL] SQL" in sqli
            or bool(re.findall(r'\[!\] CONFIRMED:', recon))
        )
        if not has_confirmed:
            return (
                "\n[INFO] LLM Threat Analysis: no confirmed vulnerabilities detected "
                "-- AI inference skipped to prevent speculative / hallucinated findings.\n"
                f"  Tech detected: {tech_str} | Ports: {open_ports}\n"
            )

        try:
            from core.rag_kb import get_tech_context, analyze_timeout_pattern

            # -- RAG retrieval ---------------------------------------------------
            rag  = get_tech_context(tech_str)
            rag_cves_str = "\n".join(
                f"  [{c['severity']}] {c['id']}: {c['desc']}  |  Test: {c['test_hint']}"
                for c in rag["cves"][:6]
            ) or "  (none matched)"
            rag_hints_str = "\n".join(
                f"  - {h}" for h in rag["hints"][:6]
            ) or "  (none)"

            # -- Timeout pattern analysis ----------------------------------------
            timeout_count = traversal.count("[ TIMEOUT ]")
            total_probes  = len(re.findall(r'\[ (?:TIMEOUT|SAFE|CRITICAL) \]', traversal))
            baseline_ok   = "HTTP 200" in reach or "is reachable" in reach
            pattern       = analyze_timeout_pattern(timeout_count, max(total_probes, 1), baseline_ok)

            # -- Confirmed findings -----------------------------------------------
            confirmed = []
            if "[CONFIRMED]" in traversal or "[CRITICAL]" in traversal:
                confirmed.append("Path Traversal / LFI")
            if ("[HIGH] Reflected XSS" in xss or "XSS CONFIRMED" in xss
                    or "[MEDIUM] Reflected XSS" in xss or "REFLECTED XSS FINDING" in xss):
                confirmed.append("Reflected XSS")
            if "[CONFIRMED]" in sqli or "[CRITICAL] SQL" in sqli:
                params = re.findall(r'Param\s+:\s*([^\n]+)', sqli)
                confirmed.append(f"SQL Injection on params: {', '.join(set(params[:3]))}")
            fuzz_in_recon = re.findall(r'\[!\] CONFIRMED: ([^\n]+)', recon)
            if fuzz_in_recon:
                confirmed.append(f"Exposed files: {', '.join(fuzz_in_recon[:3])}")
            evidence_str = (
                "\n".join(f"  confirmed: {c}" for c in confirmed)
                if confirmed else "  (none confirmed yet)"
            )

            # -- CVEs from web search --------------------------------------------
            web_cves = list(set(re.findall(r'CVE-\d{4}-\d+', search)))[:5]
            web_cves_str = ", ".join(web_cves) if web_cves else "none found"

            # -- Reasoning prompt ------------------------------------------------
            prompt = (
                f"You are a senior penetration tester reviewing an automated scan.\n\n"
                f"TARGET: {domain}\n"
                f"TECH STACK: {tech_str}\n"
                f"OPEN PORTS: {open_ports}\n\n"
                f"=== CONFIRMED FINDINGS ===\n{evidence_str}\n\n"
                f"=== PATH TRAVERSAL PATTERN ===\n"
                f"{timeout_count} of {total_probes} probes timed out "
                f"(baseline responded normally: {baseline_ok}).\n"
                f"Interpretation: {pattern.get('analysis', '')}\n\n"
                f"=== RAG KNOWLEDGE BASE: CVEs for {tech_str} ===\n{rag_cves_str}\n\n"
                f"=== ATTACK SURFACE HINTS ===\n{rag_hints_str}\n\n"
                f"=== CVEs FROM WEB SEARCH ===\n{web_cves_str}\n\n"
                f"Answer these 5 questions. Be specific. Under 400 words total.\n\n"
                f"1. CONFIRMED/SUSPECTED VULNERABILITIES: What is present and what is suspected?\n"
                f"2. TIMEOUT MEANING: What does the {timeout_count}/{total_probes} pattern indicate specifically for IIS/ASP.NET?\n"
                f"3. TOP CVE: Which CVE above is most likely exploitable on this target and why?\n"
                f"4. NEXT 3 TESTS: Exact URLs or payloads the pentester should try immediately.\n"
                f"5. RISK: Critical / High / Medium / Low and one-sentence justification."
            )

            llm_response = self.llm.invoke(prompt)

            # -- Format section --------------------------------------------------
            bypass_payloads = pattern.get("bypass_payloads", [])
            bypass_str = ""
            if bypass_payloads:
                bypass_str = (
                    "\n\n  [WAF BYPASS PAYLOADS -- try for path traversal]\n"
                    + "\n".join(f"    {p}" for p in bypass_payloads)
                )

            return (
                "\n" + "=" * 60 + "\n"
                "  ARGUS AI THREAT ANALYSIS  (RAG + LLM)\n"
                + "=" * 60 + "\n"
                f"  Tech Stack      : {tech_str}\n"
                f"  Timeout Pattern : [{pattern.get('confidence','?')}] {pattern.get('label','')}\n"
                f"  RAG CVEs loaded : {len(rag['cves'])}\n"
                f"  Web CVEs found  : {web_cves_str}\n"
                + "=" * 60 + "\n\n"
                + "\n".join(f"  {line}" for line in llm_response.strip().split("\n"))
                + bypass_str
                + "\n" + "=" * 60
            )

        except Exception as e:
            return f"\n[WARN] LLM threat analysis failed: {e}"

    # -- main entry point --------------------------------------------------------

    def ask(self, query: str, callbacks=None) -> dict:
        raw_target              = self._extract_target(query)
        domain, sub_mode, dir_mode, dir_depth = self._parse_scan_pattern(raw_target)
        target                  = domain   # clean domain used by all tools

        # Determine what this scan run does
        full_mode   = not sub_mode and not dir_mode
        run_subs    = sub_mode or full_mode          # steps 2-3
        run_vulns   = full_mode                       # steps 5-8 (Nikto, traversal, XSS, SQLi)
        run_llm     = full_mode                       # step 10
        run_dirscan = dir_mode or full_mode           # FFUF / recon fuzz

        if sub_mode and dir_mode:
            scan_label = "SUBDOMAIN + DIRECTORY ENUMERATION"
        elif sub_mode:
            scan_label = "SUBDOMAIN ENUMERATION"
        elif dir_mode:
            scan_label = f"DIRECTORY ENUMERATION (depth {dir_depth})"
        else:
            scan_label = "FULL VULNERABILITY SCAN"

        log_lines = [f"[*] Argus pipeline started | Mode: {scan_label} | Target: {target}"]

        # Purge stale WSL error strings
        try:
            from core.memory import ArgusMemory
            ArgusMemory().purge_bad_entities()
        except Exception:
            pass

        # -- 1: Reachability ----------------------------------------------------
        log_lines.append("\n[1/13] Check_Reachability")
        reach = self._call("Check_Reachability", target)
        log_lines.append(reach[:400])

        # -- 2: Subdomain enumeration (skipped in dir-only mode) ---------------
        subs = ""
        if run_subs:
            log_lines.append("\n[2/13] Subdomain_Enumeration")
            subs = self._call("Subdomain_Enumeration", target)
            log_lines.append(subs[:500])
        else:
            log_lines.append("\n[2/13] Subdomain_Enumeration — SKIPPED (directory scan mode)")

        # -- 3: Priority targets (skipped in dir-only mode) ---------------------
        priority = ""
        if run_subs:
            log_lines.append("\n[3/13] Get_Priority_Targets")
            priority = self._call("Get_Priority_Targets", "")
            log_lines.append(priority[:300])
        else:
            log_lines.append("\n[3/13] Get_Priority_Targets — SKIPPED")

        # -- 4: Recon suite (WAF+tech+ports+fuzzing+secrets) --------------------
        log_lines.append("\n[4/13] Recon_Suite")
        recon = self._call("Recon_Suite", target)
        log_lines.append(recon[:800])

        # -- 5-8: Vuln scanners (skipped in subdomain/directory-only modes) ----
        nikto = traversal = xss = sqli = ""
        if run_vulns:
            log_lines.append("\n[5/13] Run_Nikto")
            nikto = self._call("Run_Nikto", target)
            log_lines.append(nikto[:600])

            log_lines.append("\n[6/13] Path_Traversal_Check")
            traversal = self._call("Path_Traversal_Check", target)
            log_lines.append(traversal)

            log_lines.append("\n[7/13] XSS_Check")
            xss = self._call("XSS_Check", target)
            log_lines.append(xss)

            log_lines.append("\n[8/13] SQLi_Check")
            sqli = self._call("SQLi_Check", target)
            log_lines.append(sqli)
        else:
            log_lines.append(
                f"\n[5-8/13] Nikto / Path Traversal / XSS / SQLi — SKIPPED ({scan_label})"
            )

        # -- 9: Web search for CVEs ---------------------------------------------
        log_lines.append("\n[9/13] Smart_Web_Search")
        search = self._call("Smart_Web_Search", f"CVE vulnerabilities exploit {domain}")
        log_lines.append(search[:500])

        # -- 10: LLM threat reasoning (skipped in subdomain/dir-only modes) ----
        tech_match   = re.search(r'Tech:\s*([^\n\r]+)', reach + recon)
        tech_str     = tech_match.group(1).strip() if tech_match else "Unknown"
        port_match   = re.search(r'Open ports:\s*([^\n]+)', recon)
        open_ports   = port_match.group(1).strip() if port_match else "Unknown"
        llm_analysis = ""
        if run_llm:
            log_lines.append("\n[10/13] LLM_Threat_Analysis")
            llm_analysis = self._llm_threat_analysis(
                domain, tech_str, open_ports,
                reach, recon, traversal, xss, sqli, search
            )
            log_lines.append(llm_analysis)
        else:
            log_lines.append(
                f"\n[10/13] LLM_Threat_Analysis — SKIPPED ({scan_label})"
            )

        # -- 11: Memory consolidation -------------------------------------------
        log_lines.append("\n[11/13] Query_Memory")
        memory_out = self._call("Query_Memory", "")
        log_lines.append(memory_out[:500])

        # -- 12: Knowledge graph ------------------------------------------------
        log_lines.append("\n[12/13] Query_Knowledge_Graph")
        graph = self._call("Query_Knowledge_Graph", "")
        log_lines.append(graph[:300])

        # -- 13: Generate report ------------------------------------------------
        log_lines.append("\n[13/13] Generate_Report")
        report_out = self._call("Generate_Report", target)
        log_lines.append(report_out)

        # -- Scan Brief ---------------------------------------------------------
        brief_lines = [
            "\n" + "=" * 60,
            "  ARGUS SCAN BRIEF",
            "=" * 60,
        ]
        brief_lines.append(f"  Mode       : {scan_label}")
        brief_lines.append(f"  Target     : {target}")
        brief_lines.append(f"  Technology : {tech_str}")
        brief_lines.append(f"  Open Ports : {open_ports}")

        # Sensitive files (from recon output)
        conf_files = re.findall(r'\[!\] CONFIRMED: ([^\n]+)', recon)
        if conf_files:
            brief_lines.append(f"  Exposed Files ({len(conf_files)}):")
            for f in conf_files[:5]:
                brief_lines.append(f"    - {f.strip()}")
        else:
            brief_lines.append("  Exposed Files : None confirmed")

        # Path traversal
        if "[CONFIRMED]" in traversal or "[CRITICAL]" in traversal:
            hits = re.findall(r'URI\s+:\s*([^\n]+)', traversal)
            brief_lines.append(f"  Path Traversal : CONFIRMED ({len(hits)} endpoint(s))")
            for h in hits[:3]:
                brief_lines.append(f"    - {h.strip()}")
        elif "[ TIMEOUT ]" in traversal:
            t_cnt = traversal.count("[ TIMEOUT ]")
            t_tot = len(re.findall(r'\[ (?:TIMEOUT|SAFE|CRITICAL) \]', traversal))
            # If ALL probes timed out on a non-ASP.NET stack, those .asp endpoints
            # simply do not exist on this target -- not a real finding.
            all_timed_out = (t_cnt == t_tot)
            is_asp_stack = any(kw in tech_str.lower() for kw in ("iis", "asp", "windows"))
            if all_timed_out and not is_asp_stack:
                brief_lines.append(
                    f"  Path Traversal : {t_cnt}/{t_tot} probes timed out -- "
                    f"ASP.NET endpoints not present on this tech stack (not a finding)"
                )
            else:
                brief_lines.append(
                    f"  Path Traversal : {t_cnt}/{t_tot} timed out "
                    f"-- possible WAF/IIS filter (see AI analysis)"
                )
        else:
            brief_lines.append("  Path Traversal : Not detected")

        # XSS
        if "[HIGH] Reflected XSS" in xss or "XSS CONFIRMED" in xss:
            xss_urls = re.findall(r'URL\s+:\s*([^\n]+)', xss)
            brief_lines.append(f"  XSS            : CONFIRMED ({len(xss_urls)} URL(s))")
        elif "[MEDIUM] Reflected XSS" in xss or "REFLECTED XSS FINDING" in xss:
            xss_params = list(set(re.findall(r'Param\s+:\s*([^\n]+)', xss)))
            brief_lines.append(
                f"  XSS            : SUSPECTED -- params: {', '.join(xss_params[:4])}"
            )
        else:
            brief_lines.append("  XSS            : Not detected")

        # SQLi
        if "[CONFIRMED]" in sqli or "[CRITICAL] SQL" in sqli:
            sqli_params = list(set(re.findall(r'Param\s+:\s*([^\n]+)', sqli)))
            brief_lines.append(
                f"  SQL Injection  : CONFIRMED -- params: {', '.join(sqli_params[:4])}"
            )
        else:
            brief_lines.append("  SQL Injection  : Not detected")

        # CVEs
        all_cves = list(set(re.findall(r'CVE-\d{4}-\d+', search + llm_analysis)))
        if all_cves:
            brief_lines.append(f"  CVEs (found)   : {', '.join(all_cves[:5])}")

        # RAG CVEs for this stack
        try:
            from core.rag_kb import get_tech_context
            rag_r = get_tech_context(tech_str)
            if rag_r["cves"]:
                brief_lines.append(
                    "  RAG CVEs       : " +
                    ", ".join(
                        f"{c['id']} ({c['severity']})" for c in rag_r["cves"][:4]
                    )
                )
        except Exception:
            pass

        brief_lines.append("=" * 60)
        log_lines.append("\n".join(brief_lines))

        full_log = "\n".join(log_lines)

        # Parse risk score and findings from JSON report
        risk_score     = 1
        findings_count = 0
        report_data    = {}
        json_match = re.search(r'JSON:\s*(.+\.json)', report_out)
        md_match   = re.search(r'Markdown:\s*(.+\.md)', report_out)
        json_path  = ""
        md_path    = ""

        if json_match:
            json_path = json_match.group(1).strip()
            try:
                with open(json_path, encoding='utf-8') as f:
                    report_data = _json.load(f)
                risk_score     = report_data.get('meta', {}).get('risk_score', 1)
                findings_count = len(report_data.get('findings', []))
            except Exception as e:
                print(f"[!] Could not read JSON report: {e}")

        if md_match:
            md_path = md_match.group(1).strip()

        return {
            "output":         full_log,
            "output_str":     full_log,
            "raw":            full_log,
            "risk_score":     risk_score,
            "findings_count": findings_count,
            "report_data":    report_data,
            "json_path":      json_path,
            "md_path":        md_path,
        }

    def _dict_to_markdown(self, report: dict) -> str:
        lines = [
            f"# Argus Security Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Target:** {report.get('scan_target', 'N/A')}",
            f"**Mode:** {report.get('scan_mode', 'passive')}",
            f"**Risk Score:** {report.get('overall_risk_score', 'N/A')}/10",
            "\n## Findings\n"
        ]
        for f in report.get("findings", []):
            lines.append(f"### [{f.get('severity', 'Info')}] {f.get('issue', '')}")
            lines.append(f"- **Target:** {f.get('target', '')}")
            lines.append(f"- **Description:** {f.get('description', '')}")
            if f.get("suggested_payload"):
                lines.append(f"- **Payload:** `{f.get('suggested_payload')}`")
            lines.append(f"- **Remediation:** {f.get('remediation', '')}\n")
        lines.append("\n## Recommended Next Steps\n")
        for step in report.get("next_steps", []):
            lines.append(f"- {step}")
        return "\n".join(lines)

    def simple_ask(self, prompt: str) -> dict:
        response = self.llm.invoke(prompt)
        return {"output": response}
