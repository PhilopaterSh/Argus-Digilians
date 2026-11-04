# AUTH — qwen_cve

- source: qwen_cve
- class: auth
- cwe: CWE-287
- cve: ['CVE-2021-30049']
- severity: medium
- quality_score: 13

## Scenario

Rate the severity of CVE-2021-30049 and explain why.

## Analysis / Response

Successful exploitation of this vulnerability could allow an attacker to execute malicious scripts in the context of the victim's browser, potentially leading to session hijacking, defacement, or theft of sensitive information.

According to its vector, CVE-2021-30049 can be exploited over the network, without any account, only if a user is tricked into an action.

In CIA terms for CVE-2021-30049, confidentiality impact is low, integrity impact is low and availability impact is none.

For CVE-2021-30049, CVSS v3 gives a base score of 6.1 (medium).

Patch SysAid Technologies 20.3.64 b in the normal cycle, prioritising instances reachable from untrusted networks.
