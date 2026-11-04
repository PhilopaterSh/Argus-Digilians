# REDIRECT — qwen_cve

- source: qwen_cve
- class: redirect
- cwe: CWE-601
- cve: ['CVE-2023-6275']
- severity: medium
- quality_score: 13

## Scenario

How do I check whether my TOTVS Fluig Platform is vulnerable to CVE-2023-6275?

## Analysis / Response

Detection approach for CVE-2023-6275 in TOTVS Fluig Platform:

1) Inventory: start from asset inventory, since a version match for TOTVS Fluig Platform is the safest first signal.

2) Request-level test for TOTVS Fluig Platform (authorized targets only):
 1. Send a GET request to /mobileredir/openApp.jsp?redirectUrl=%22%3E%3Cscript%3Ealert(document.domain)%3C/script%3E on the target; a positive result is when the response body contains ""><script>alert(document.domain)</script>" and "fluig://" and the content type contains "text/html" and the HTTP status is 200.

3) Log and traffic indicators: look for query strings or form fields sent to GET /mobileredir/openApp.jsp?redirectUrl=%22%3E%3Cscript%3Ealert(document.domain)%3C/script%3E that contain HTML tags or event-handler attributes.

For TOTVS Fluig Platform, any HTTP client can replay these requests; a Nuclei template is optional.

**Security Impact:** Open redirect vulnerabilities facilitate phishing attacks by allowing attackers to redirect users from a trusted domain to a malicious site, enabling credential theft and malware distribution.

**Remediation:** Validate redirect targets against an allowlist of permitted URLs/domains. Use indirect references (mapping IDs) instead of direct URLs. Always display a warning page before redirecting to external domains.
