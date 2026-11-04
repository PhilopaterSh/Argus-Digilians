# SQLI — qwen_cve

- source: qwen_cve
- class: sqli
- cwe: CWE-862
- cve: ['CVE-2023-22478']
- severity: high
- quality_score: 12

## Scenario

Which vulnerability class best describes CVE-2023-22478 (KubePi <= v1.6.4 LoginLogsSearch - Unauthorized Access)?
A) broken access control
B) privilege escalation
C) SQL injection
D) SSRF

## Analysis / Response

Answer: A) broken access control.

Why: KubePi is a modern Kubernetes panel. The API interfaces with unauthorized entities and may leak sensitive information. This issue has been patched in version 1.6.4. There are currently no known workarounds. CVE-2023-22478 is recorded as CWE-862.

**Security Impact:** Successful SQL injection allows an attacker to read, modify, or delete database contents, bypass authentication, and in some cases execute operating system commands, leading to complete data breach.
