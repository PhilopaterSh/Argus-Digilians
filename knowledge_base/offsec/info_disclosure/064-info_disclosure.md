# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2017-14849']
- severity: high
- quality_score: 13

## Scenario

How urgent is patching CVE-2017-14849?

## Analysis / Response

An attacker can read sensitive files on the server, potentially leading to unauthorized access or information disclosure.

Exploiting CVE-2017-14849 requires access over the network, without any account, with no user interaction.

CIA breakdown of CVE-2017-14849: confidentiality impact is high, integrity impact is none and availability impact is none.

For CVE-2017-14849, CVSS v3 gives a base score of 7.5 (high).

Schedule the Node.js fix in the current patch cycle, sooner if it is exposed to the internet.
