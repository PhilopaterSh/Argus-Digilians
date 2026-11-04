# RESOURCE — qwen_cve

- source: qwen_cve
- class: resource
- cwe: CWE-400
- cve: ['CVE-2018-0171']
- severity: critical
- quality_score: 13

## Scenario

Assess the risk of CVE-2018-0171 in Cisco Smart Install.

## Analysis / Response

Unauthenticated attackers can trigger device reloads causing denial of service or execute arbitrary code by exploiting improper packet validation in the Smart Install feature.

Exploiting CVE-2018-0171 requires access over the network, without any account, with no user interaction.

In CIA terms for CVE-2018-0171, confidentiality impact is high, integrity impact is high and availability impact is high.

CVE-2018-0171 has a CVSS v3 base score of 9.8 (critical).

Treat CVE-2018-0171 as an emergency patch if Cisco Smart Install is internet-facing.
