# SQLI — qwen_cve

- source: qwen_cve
- class: sqli
- cwe: CWE-89
- cve: ['CVE-2022-0439']
- severity: critical
- quality_score: 15

## Scenario

Tell me about CVE-2022-0439 in Email Subscribers & Newsletters.

## Analysis / Response

In short, CVE-2022-0439 is an SQL injection issue in Email Subscribers & Newsletters.

The Email Subscribers & Newsletters WordPress plugin before 5.3.2 does not correctly escape the `order` and `orderby` parameters to the `ajax_fetch_report_list` action, making it vulnerable to blind SQL injection attacks by users with roles as low as Subscriber. Further, it does not have any CSRF protection in place for the action, allowing an attacker to trick any logged in user to perform the action by clicking a link. It maps to CWE-89 and CWE-352.

Root cause: Email Subscribers & Newsletters concatenates request input into an SQL statement instead of binding it as a parameter.

The CVSS v3 base score for CVE-2022-0439 is 8.8, which rates as high.

Impact: Attackers can execute arbitrary SQL commands and access sensitive data, potentially leading to data breach or data tampering.
