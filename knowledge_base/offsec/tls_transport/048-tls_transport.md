# TLS_TRANSPORT — h1

- source: h1
- class: tls_transport
- cwe: CWE-319
- cve: ['CVE-2023-23914']
- severity: low
- program: curl
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CVE-2023-23914: curl HSTS ignored on multiple requests
**Affected Asset:** https://github.com/curl/curl

**Vulnerability Description:**
## Summary:
curl tool HSTS doesn't work correctly when performing multiple requests within a single invocation.

## Steps To Reproduce:

  1. `curl --hsts "" https://hsts.example.com http://hsts.example.com`

The second request will be performed over HTTP regardless if correct HSTS header is returned by the first request.

## Impact

Request performed over insecure channels unexpectedly and loss of confidentiality and integrity.

**Steps to Reproduce:**
1. `curl --hsts "" https://hsts.example.com http://hsts.example.com`

The second request will be performed over HTTP regardless if correct HSTS header is returned by the first request.

## Analysis / Response

**Vulnerability Class:** tls_transport
**CWE:** CWE-319
**Weakness:** Cleartext Transmission of Sensitive Information
**Severity:** low
**Endpoint Pattern:** https://hsts.example.com

**Impact Assessment:**
Request performed over insecure channels unexpectedly and loss of confidentiality and integrity.

**Remediation:**
Enforce TLS 1.2+ for all connections. Enable HSTS. Disable weak cipher suites. Use certificate pinning for mobile applications.
