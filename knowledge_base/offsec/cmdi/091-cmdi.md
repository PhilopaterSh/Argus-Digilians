# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-94
- severity: critical
- quality_score: 10

## Scenario

How is code injection / remote code execution classified in vulnerability taxonomies?

## Analysis / Response

Taxonomy mapping for code injection / remote code execution: Code injection is CWE-94 (Improper Control of Generation of Code), with CWE-95 for eval injection and CWE-917 for expression language injection; template injection is CWE-1336. It falls under OWASP A03:2021 Injection. Internet-facing RCE CVEs are often exploited within days of disclosure. Asset inventory and fast patching are key for third-party RCE bugs.

**Security Impact:** Command injection enables arbitrary command execution on the server, potentially leading to complete system compromise, data exfiltration, lateral movement, and persistent backdoor installation.
