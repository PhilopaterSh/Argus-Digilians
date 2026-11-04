# ACCESS_CONTROL — qwen_cve

- source: qwen_cve
- class: access_control
- cwe: CWE-200
- severity: medium
- quality_score: 9

## Scenario

What OWASP ASVS or Top 10 items cover information disclosure?

## Analysis / Response

Here is how information disclosure is classified. Information disclosure maps to CWE-200 (Exposure of Sensitive Information), with children CWE-209 (error messages), CWE-532 (log files) and CWE-538/552 (files accessible to external parties). OWASP 2021 covers it under A01 Broken Access Control and A05 Security Misconfiguration. Disclosure often enables more severe follow-up attacks. Repository history retains secrets after deletion.

**Remediation:** Implement role-based access control (RBAC) with server-side enforcement. Deny by default. Validate authorization on every request. Use indirect object references. Implement proper ownership checks. Log access control failures.
