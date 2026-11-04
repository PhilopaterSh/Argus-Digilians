# SSRF — qwen_cve

- source: qwen_cve
- class: ssrf
- cwe: CWE-918
- cve: ['CVE-2021-40438']
- severity: critical
- quality_score: 12

## Scenario

Break down the CVSS impact of CVE-2021-40438.

## Analysis / Response

Attackers can perform SSRF attacks via mod_proxy to access internal resources and forward requests to arbitrary origin servers, potentially exposing internal services and data.

Preconditions from the CVSS vector of CVE-2021-40438: the attack works over the network, without any account, with no user interaction.

For Apache <= 2.4.48 Mod_Proxy, the vector says confidentiality impact is high, integrity impact is high and availability impact is high.

Scored 9.0 under CVSS v3, CVE-2021-40438 sits in the critical band.

Treat CVE-2021-40438 as an emergency patch if Apache <= 2.4.48 Mod_Proxy is internet-facing.
