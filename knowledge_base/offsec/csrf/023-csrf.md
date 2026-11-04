# CSRF — qwen_cve

- source: qwen_cve
- class: csrf
- cwe: CWE-352
- cve: ['CVE-2010-2114']
- severity: low
- quality_score: 12

## Scenario

Which weakness type is behind CVE-2010-2114?

## Analysis / Response

CVE-2010-2114 is classified as Cross-Site Request Forgery (CSRF), based on CWE-352. The CWE-352 mapping for CVE-2010-2114 comes from NVD weakness data rather than keyword guessing. In a vulnerability tracker, CVE-2010-2114 would be filed under Cross-Site Request Forgery (CSRF) with severity Low.

**Security Impact:** Cross-site request forgery allows an attacker to trick authenticated users into performing unintended actions such as changing passwords, transferring funds, or modifying account settings.

**Remediation:** Implement anti-CSRF tokens (synchronizer pattern or double-submit cookies). Use SameSite=Strict cookie attribute. Verify Origin/Referer headers. Require re-authentication for sensitive actions.
