# PATHTRAVER — qwen_cve

- source: qwen_cve
- class: pathtraver
- cwe: CWE-22
- cve: ['CVE-2024-1483']
- severity: critical
- quality_score: 14

## Scenario

What does CVE-2024-1483 (Mlflow < 2.9.2 - Path Traversal) involve?

## Analysis / Response

Mlflow is affected by CVE-2024-1483, a path traversal flaw.

A path traversal vulnerability exists in mlflow/mlflow version 2.9.2, allowing attackers to access arbitrary files on the server. By crafting a series of HTTP POST requests with specially crafted 'artifact_location' and 'source' parameters, using a local URI with '#' instead of '?', an attacker can traverse the server's directory structure. The issue occurs due to insufficient validation of user-supplied input in the server's handlers. It maps to CWE-22 and CWE-29.

Root cause: file-handling code in Mlflow trusts a user-supplied file name or path segment.

The CVSS v3 base score for CVE-2024-1483 is 7.5, which rates as high.

Impact: Successful exploitation could be lead to disclose of sensitive information such as SSH Keys or Internal configurations.

**Remediation:** Canonicalize and validate all file paths. Use a chroot jail or sandboxed directory. Implement path allowlists. Strip or reject sequences like ../ and null bytes. Use framework-provided secure file access APIs.
