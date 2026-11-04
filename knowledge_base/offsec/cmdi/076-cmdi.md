# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-78
- cve: ['CVE-2021-25281']
- severity: critical
- quality_score: 12

## Scenario

Assess the risk of CVE-2021-25281 in SaltStack Salt.

## Analysis / Response

Unauthenticated attackers can remotely execute any wheel modules on the Salt master by bypassing eauth credentials, leading to complete infrastructure compromise and control over all managed systems.

An attacker can reach SaltStack Salt for this over the network, without any account, with no user interaction, per the CVSS vector.

In CIA terms for CVE-2021-25281, confidentiality impact is high, integrity impact is high and availability impact is high.

Scored 9.8 under CVSS v3, CVE-2021-25281 sits in the critical band.

Treat CVE-2021-25281 as an emergency patch if SaltStack Salt is internet-facing.
