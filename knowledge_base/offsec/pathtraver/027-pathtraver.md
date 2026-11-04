# PATHTRAVER — qwen_cve

- source: qwen_cve
- class: pathtraver
- cwe: CWE-552
- cve: ['CVE-2024-6911']
- severity: critical
- quality_score: 14

## Scenario

What kind of vulnerability is CVE-2024-6911?

## Analysis / Response

PerkinElmer ProcessPlus is affected by CVE-2024-6911, an information disclosure flaw.

Files on the Windows system are accessible without authentication to external parties due to a local file inclusion in PerkinElmer ProcessPlus.This issue affects ProcessPlus: through 1.11.6507.0. It maps to CWE-552.

Root cause: PerkinElmer ProcessPlus returns sensitive data such as configuration, credentials, versions or internal paths to unauthenticated callers.

Scored 7.5 under CVSS v3, CVE-2024-6911 sits in the high band.

Impact: Unauthenticated attackers can exploit LFI to read arbitrary files from the Windows system, potentially exposing sensitive configuration files, credentials, and system information.

**Remediation:** Canonicalize and validate all file paths. Use a chroot jail or sandboxed directory. Implement path allowlists. Strip or reject sequences like ../ and null bytes. Use framework-provided secure file access APIs.
