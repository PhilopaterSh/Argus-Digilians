# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-287
- cve: ['CVE-2021-42565']
- severity: critical
- quality_score: 13

## Scenario

Rate the severity of CVE-2021-42565 and explain why.

## Analysis / Response

Successful exploitation of this vulnerability could allow an attacker to execute malicious scripts in the context of a user's browser, potentially leading to session hijacking, defacement, or theft of sensitive information.

According to its vector, CVE-2021-42565 can be exploited over the network, without any account, only if a user is tricked into an action.

In CIA terms for CVE-2021-42565, confidentiality impact is low, integrity impact is low and availability impact is none.

The CVSS v3 base score for CVE-2021-42565 is 6.1, which rates as medium.

Patch myfactory FMS in the normal cycle, prioritising instances reachable from untrusted networks.
