# ACCESS_CONTROL — qwen_cve

- source: qwen_cve
- class: access_control
- cwe: CWE-284
- cve: ['CVE-2021-36888']
- severity: critical
- quality_score: 15

## Scenario

Quick rundown of CVE-2021-36888, please.

## Analysis / Response

the WordPress plugin Image Hover Ultimate is affected by CVE-2021-36888, a broken access control flaw.

Unauthenticated Arbitrary Options Update vulnerability leading to full website compromise discovered in Image Hover Effects Ultimate (versions <= 9.6.1) WordPress plugin. It maps to CWE-284 and CWE-306.

Root cause: the WordPress plugin Image Hover Ultimate does not check that the caller is authorized for the object or function requested.

CVE-2021-36888 has a CVSS v3 base score of 9.8 (critical).

Impact: Attackers can fully compromise the website, leading to complete control and potential data theft or defacement.
