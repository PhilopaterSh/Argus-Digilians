# SQLI — qwen_cve

- source: qwen_cve
- class: sqli
- cwe: CWE-89
- cve: ['CVE-2024-8625']
- severity: high
- quality_score: 11

## Scenario

Shorten CVE-2024-8625 into a change-management blurb.

## Analysis / Response

Verified brief for CVE-2024-8625:
- Title: WordPress TS Poll < 2.4.0 - SQL Injection
- Affected: total-soft ts poll
- Severity/CVSS: HIGH / 7.2
- CWE: CWE-89
- Class: SQL Injection

The TS Poll WordPress plugin before 2.4.0 does not sanitize and escape a parameter before using it in a SQL statement, allowing admins to perform SQL injection attacks

Defenders should confirm the vendor advisory and apply the fixed build. Cross-check metrics at NVD before changing SLAs.
