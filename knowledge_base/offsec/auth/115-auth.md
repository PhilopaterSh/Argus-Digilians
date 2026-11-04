# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-287
- cve: ['CVE-2022-3578']
- severity: medium
- quality_score: 13

## Scenario

Assess the risk of CVE-2022-3578 in the WordPress plugin ProfileGrid.

## Analysis / Response

Successful exploitation of this vulnerability could allow an attacker to inject malicious scripts into web pages viewed by users, leading to potential data theft, session hijacking, or defacement.

According to its vector, CVE-2022-3578 can be exploited over the network, without any account, only if a user is tricked into an action.

CIA breakdown of CVE-2022-3578: confidentiality impact is low, integrity impact is low and availability impact is none.

CVE-2022-3578 has a CVSS v3 base score of 6.1 (medium).

Patch the WordPress plugin ProfileGrid in the normal cycle, prioritising instances reachable from untrusted networks.
