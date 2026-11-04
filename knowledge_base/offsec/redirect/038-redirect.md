# REDIRECT — qwen_cve

- source: qwen_cve
- class: redirect
- cwe: CWE-601
- cve: ['CVE-2018-13384']
- severity: informational
- quality_score: 13

## Scenario

What privileges or interaction does CVE-2018-13384 require?

## Analysis / Response

NVD scores CVE-2018-13384 at 6.1 (Medium) using CVSS 3.0. The vector CVSS:3.0/AV:N/AC:L/PR:N/UI:R/S:C/C:L/I:L/A:N for CVE-2018-13384 means it is exploitable over the network, with low attack complexity, without any privileges, and it requires user interaction; the scope changes beyond the vulnerable component, with low confidentiality, low integrity and no availability impact. Open redirects help attackers evade URL reputation filters. Teams running Fortinet Fortios should treat CVE-2018-13384 as medium priority and confirm exposure before scheduling the fix.
