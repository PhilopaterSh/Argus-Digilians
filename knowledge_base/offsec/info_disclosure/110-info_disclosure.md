# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2018-16671']
- severity: critical
- quality_score: 13

## Scenario

Describe the attack consequences of CVE-2018-16671 for CirCarLife.

## Analysis / Response

Successful exploitation of this vulnerability can lead to unauthorized access to sensitive data, compromising the confidentiality and integrity of the system.

Preconditions from the CVSS vector of CVE-2018-16671: the attack works over the network, without any account, with no user interaction.

For CirCarLife, the vector says confidentiality impact is low, integrity impact is none and availability impact is none.

Scored 5.3 under CVSS v3, CVE-2018-16671 sits in the medium band.

Patch CirCarLife in the normal cycle, prioritising instances reachable from untrusted networks.
