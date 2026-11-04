# SQLI — qwen_cve

- source: qwen_cve
- class: sqli
- cwe: CWE-89
- cve: ['CVE-2024-9796']
- severity: critical
- quality_score: 14

## Scenario

Give me the key facts about CVE-2024-9796.

## Analysis / Response

CVE-2024-9796 is an SQL injection vulnerability in the WordPress plugin WP-Advanced-Search.

The WP-Advanced-Search WordPress plugin before 3.3.9.2 does not sanitize and escape the t parameter before using it in a SQL statement, allowing unauthenticated users to perform SQL injection attacks It maps to CWE-89.

Root cause: the WordPress plugin WP-Advanced-Search concatenates request input into an SQL statement instead of binding it as a parameter.

The CVSS v3 base score for CVE-2024-9796 is 9.8, which rates as critical.

Impact: Unauthenticated attackers can exploit SQL injection through the autocompletion endpoint to extract sensitive database information including user credentials, posts, comments, and configuration data.

**Remediation:** Use parameterized queries (prepared statements) for all database interactions. Implement an ORM with built-in query safety. Apply input validation with allowlists. Enforce least-privilege database accounts. Deploy WAF rules for SQL injection patterns.
