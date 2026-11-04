# CMDI — qwen_cve

- source: qwen_cve
- class: cmdi
- cwe: CWE-78
- cve: ['CVE-2023-51467']
- severity: critical
- quality_score: 12

## Scenario

Assess the risk of CVE-2023-51467 in Apache OFBiz.

## Analysis / Response

Unauthenticated attackers can bypass authentication and execute arbitrary Groovy code, leading to remote code execution and complete system compromise.

Preconditions from the CVSS vector of CVE-2023-51467: the attack works over the network, without any account, with no user interaction.

CIA breakdown of CVE-2023-51467: confidentiality impact is high, integrity impact is high and availability impact is high.

CVE-2023-51467 has a CVSS v3 base score of 9.8 (critical).

Treat CVE-2023-51467 as an emergency patch if Apache OFBiz is internet-facing.
