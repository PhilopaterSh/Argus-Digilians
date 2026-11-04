# REDIRECT — qwen_cve

- source: qwen_cve
- class: redirect
- cwe: CWE-93
- cve: ['CVE-2017-8791']
- severity: medium
- quality_score: 13

## Scenario

Walk me through CVE-2017-8791.

## Analysis / Response

CVE-2017-8791 was published to NVD on 2017-05-05 and is classified as CRLF Injection / Response Splitting. NVD describes CVE-2017-8791 as follows: An issue was discovered on Accellion FTA devices before FTA_9_12_180. There is a home/seos/courier/login.html auth_params CRLF attack vector. CRLF injection often occurs in redirect Location headers built from input. The weakness recorded for CVE-2017-8791 is CWE-93.

**Security Impact:** Open redirect vulnerabilities facilitate phishing attacks by allowing attackers to redirect users from a trusted domain to a malicious site, enabling credential theft and malware distribution.

**Remediation:** Validate redirect targets against an allowlist of permitted URLs/domains. Use indirect references (mapping IDs) instead of direct URLs. Always display a warning page before redirecting to external domains.
