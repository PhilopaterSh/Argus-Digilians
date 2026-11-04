# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-209
- cve: ['CVE-2022-0660']
- severity: critical
- quality_score: 14

## Scenario

I saw CVE-2022-0660 in a scan report. What is it?

## Analysis / Response

CVE-2022-0660 affects Microweber and is classed as information disclosure.

Generation of Error Message Containing Sensitive Information in Packagist microweber/microweber prior to 1.2.11. It maps to CWE-209.

Root cause: Microweber returns sensitive data such as configuration, credentials, versions or internal paths to unauthenticated callers.

Microweber issue CVE-2022-0660 scores 9.4 on CVSS v3 (critical). Note that the Nuclei template rates CVE-2022-0660 at 7.5, but NVD's primary score is 9.4, which this answer uses.

Impact: An attacker can exploit this vulnerability to gain unauthorized access to sensitive information.

**Remediation:** Remove detailed error messages in production. Disable debug modes and directory listings. Sanitize API responses to exclude internal details. Implement proper access controls on sensitive files. Review HTTP response headers.
