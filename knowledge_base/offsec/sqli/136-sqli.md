# SQLI — qwen_cve

- source: qwen_cve
- class: sqli
- cwe: CWE-89
- cve: ['CVE-2021-27315']
- severity: high
- quality_score: 13

## Scenario

What request and response pattern identifies CVE-2021-27315?

## Analysis / Response

Checking for CVE-2021-27315 on Doctor Appointment System:

1) Inventory: find every Doctor Appointment System instance and record its version, then compare against the affected range in the advisory.

3) Log and traffic indicators: look for requests to the affected endpoint with quotes, UNION SELECT, SLEEP(, WAITFOR DELAY or boolean tautologies.

Only run active checks for CVE-2021-27315 against systems you own or are authorized to test.

**Security Impact:** Successful SQL injection allows an attacker to read, modify, or delete database contents, bypass authentication, and in some cases execute operating system commands, leading to complete data breach.

**Remediation:** Use parameterized queries (prepared statements) for all database interactions. Implement an ORM with built-in query safety. Apply input validation with allowlists. Enforce least-privilege database accounts. Deploy WAF rules for SQL injection patterns.
