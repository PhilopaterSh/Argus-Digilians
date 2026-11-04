# CSRF — qwen_cve

- source: qwen_cve
- class: csrf
- cwe: CWE-352
- cve: ['CVE-2021-24780']
- severity: medium
- quality_score: 10

## Scenario

Summarize CVE-2021-24780.

## Analysis / Response

CVE-2021-24780 describes a Cross-Site Request Forgery (CSRF) flaw affecting Single Post Exporter Project Single Post Exporter. The NVD entry for CVE-2021-24780 reads: The Single Post Exporter WordPress plugin through 1.1.1 does not have CSRF checks when saving its settings, which could allow attackers to make a logged in admin change them via a CSRF attack and give access to the export feature to any role such as subscriber. Subscriber users would then be able to export an arbitrary post/page (such as private and password protected) via a direct URL CSRF works because browsers attach cookies automatically to cross-site requests when SameSite protections are absent. The weakness recorded for CVE-2021-24780 is CWE-352.
