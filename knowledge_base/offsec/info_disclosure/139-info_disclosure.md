# INFO_DISCLOSURE — qwen_cve

- source: qwen_cve
- class: info_disclosure
- cwe: CWE-200
- cve: ['CVE-2010-0759']
- severity: high
- quality_score: 13

## Scenario

What preconditions does CVE-2010-0759 need, and what is the damage?

## Analysis / Response

Successful exploitation of this vulnerability could allow an attacker to read sensitive files on the server, leading to unauthorized access or information disclosure.

An attacker can reach Joomla! Plugin Core Design Scriptegrator for this over the network, without authentication, per the CVSS vector.

In CIA terms for CVE-2010-0759, confidentiality, integrity and availability impact are partial, partial and partial respectively.

CVE-2010-0759 has a CVSS v2 base score of 7.5 (high). Because CVE-2010-0759 only has a v2 vector, compare it to v3-scored issues with care.

Schedule the Joomla! Plugin Core Design Scriptegrator fix in the current patch cycle, sooner if it is exposed to the internet.
