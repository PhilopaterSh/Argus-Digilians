# ACCESS_CONTROL — qwen_cve

- source: qwen_cve
- class: access_control
- cwe: CWE-862
- cve: ['CVE-2024-13694']
- severity: low
- quality_score: 13

## Scenario

What could an attacker achieve with CVE-2024-13694?

## Analysis / Response

NVD has not published its own score for CVE-2024-13694; the CNA (security@wordfence.com) assigned 7.5 (High) under CVSS 3.1, which is used as the severity here. The vector CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N for CVE-2024-13694 means it is exploitable over the network, with low attack complexity, without any privileges, and with no user interaction; the scope stays within the vulnerable component, with high confidentiality, no integrity and no availability impact. Mass enumeration can produce large data breaches. Teams running Moreconvert Woocommerce Wishlist should treat CVE-2024-13694 as high priority and confirm exposure before scheduling the fix.
