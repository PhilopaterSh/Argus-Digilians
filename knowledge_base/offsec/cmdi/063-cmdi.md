# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-78
- cve: ['CVE-2023-30258']
- severity: critical
- quality_score: 13

## Scenario

I saw CVE-2023-30258 in a scan report. What is it?

## Analysis / Response

CVE-2023-30258 is a remote code execution vulnerability in MagnusBilling.

Command Injection vulnerability in MagnusSolution magnusbilling 6.x and 7.x allows remote attackers to run arbitrary commands via unauthenticated HTTP request. It maps to CWE-78 and CWE-77.

Root cause: MagnusBilling passes attacker-influenced data into a shell command, interpreter or code-evaluation function.

MagnusBilling issue CVE-2023-30258 scores 9.8 on CVSS v3 (critical).

Impact: Unauthenticated attackers can execute arbitrary OS commands on the MagnusBilling server, leading to complete system compromise and potential access to all billing data and customer information.

**Remediation:** Avoid calling OS commands with user input. Use language-native APIs instead of shell commands. If commands are necessary, use strict allowlists for permitted values. Never concatenate user input into command strings. Implement sandboxing.
