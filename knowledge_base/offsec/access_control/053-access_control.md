# ACCESS_CONTROL — qwen_cve

- source: qwen_cve
- class: access_control
- cwe: CWE-862
- cve: ['CVE-2024-13570']
- severity: medium
- quality_score: 13

## Scenario

Describe the attack consequences of CVE-2024-13570 for the WordPress plugin Stray Random Quotes.

## Analysis / Response

Attackers can execute malicious scripts in the context of high-privilege users, potentially leading to account compromise or data theft.

According to its vector, CVE-2024-13570 can be exploited over the network, without any account, only if a user is tricked into an action.

In CIA terms for CVE-2024-13570, confidentiality impact is low, integrity impact is low and availability impact is none.

CVE-2024-13570 has a CVSS v3 base score of 6.1 (medium).

Patch the WordPress plugin Stray Random Quotes in the normal cycle, prioritising instances reachable from untrusted networks.
