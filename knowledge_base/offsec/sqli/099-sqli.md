# SQLI — qwen_cve

- source: qwen_cve
- class: sqli
- cwe: CWE-89
- cve: ['CVE-2024-24112']
- severity: critical
- quality_score: 12

## Scenario

Tell me about CVE-2024-24112 in Exrick XMall.

## Analysis / Response

CVE-2024-24112 affects Exrick XMall and is classed as SQL injection.

xmall v1.1 was discovered to contain a SQL injection vulnerability via the orderDir parameter. It maps to CWE-89.

Root cause: Exrick XMall trusts a request parameter inside a query, so SQL syntax supplied by the attacker changes the query logic.

Exrick XMall issue CVE-2024-24112 scores 9.8 on CVSS v3 (critical).

Impact: Unauthenticated attackers can extract sensitive database information via SQL injection in the orderDir parameter.

**Remediation:** Use parameterized queries (prepared statements) for all database interactions. Implement an ORM with built-in query safety. Apply input validation with allowlists. Enforce least-privilege database accounts. Deploy WAF rules for SQL injection patterns.
