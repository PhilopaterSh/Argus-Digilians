# CSRF — qwen_cve

- source: qwen_cve
- class: csrf
- cwe: CWE-352
- cve: ['CVE-2021-25011']
- severity: medium
- quality_score: 10

## Scenario

Break down CVE-2021-25011 in plain terms.

## Analysis / Response

CVE-2021-25011 describes a Cross-Site Request Forgery (CSRF) flaw affecting Wpgooglemap Wp Google Map. The NVD entry for CVE-2021-25011 reads: The Maps Plugin using Google Maps for WordPress plugin before 1.8.1 does not have proper authorisation and CSRF in most of its AJAX actions, which could allow any authenticated users, such as subscriber to delete arbitrary posts and update the plugin's settings. CSRF does not let the attacker read responses; it lets them make the victim perform actions. The weakness recorded for CVE-2021-25011 is CWE-352, CWE-862.
