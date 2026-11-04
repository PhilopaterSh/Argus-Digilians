# ACCESS_CONTROL — qwen_cve

- source: qwen_cve
- class: access_control
- cwe: CWE-285
- cve: ['CVE-2024-34257']
- severity: critical
- quality_score: 13

## Scenario

Can you give me an overview of CVE-2024-34257?

## Analysis / Response

In short, CVE-2024-34257 is a broken access control issue in TOTOLINK EX1800T TOTOLINK EX.

TOTOLINK EX1800T V9.1.0cu.2112_B20220316 has a vulnerability in the apcliEncrypType parameter that allows unauthorized execution of arbitrary commands, allowing an attacker to obtain device administrator privileges. It maps to CWE-285.

Root cause: TOTOLINK EX1800T TOTOLINK EX does not check that the caller is authorized for the object or function requested.

TOTOLINK EX1800T TOTOLINK EX issue CVE-2024-34257 scores 9.8 on CVSS v3 (critical).

Impact: Unauthenticated attackers can execute arbitrary commands via the apcliEncrypType parameter, gaining device administrator privileges.

**Remediation:** Implement role-based access control (RBAC) with server-side enforcement. Deny by default. Validate authorization on every request. Use indirect object references. Implement proper ownership checks. Log access control failures.
