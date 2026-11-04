# TLS_TRANSPORT — h1

- source: h1
- class: tls_transport
- cwe: CWE-319
- cve: ['CVE-2023-23915']
- severity: low
- program: curl
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** CVE-2023-23915: HSTS amnesia with --parallel
**Affected Asset:** https://github.com/curl/curl

**Vulnerability Description:**
## Summary:
curl overwrites HSTS cache entries if requests are performed in parallel.

## Steps To Reproduce:

  1. `curl --parallel --hsts hsts.txt https://site1.tld  https://site2.tld https://site3.tld`

Only one of the sites contacted will have entry in `hsts.txt` afterwards. Non-TLS connection to the other sites will not protected by TLS.

## Impact

Request performed over insecure channels unexpectedly and loss of confidentiality and integrity.

**Steps to Reproduce:**
1. `curl --parallel --hsts hsts.txt https://site1.tld  https://site2.tld https://site3.tld`

Only one of the sites contacted will have entry in `hsts.txt` afterwards. Non-TLS connection to the other sites will not protected by TLS.

## Analysis / Response

**Vulnerability Class:** tls_transport
**CWE:** CWE-319
**Weakness:** Cleartext Transmission of Sensitive Information
**Severity:** low
**Endpoint Pattern:** https://site1.tld

**Impact Assessment:**
Request performed over insecure channels unexpectedly and loss of confidentiality and integrity.

**Remediation:**
Enforce TLS 1.2+ for all connections. Enable HSTS. Disable weak cipher suites. Use certificate pinning for mobile applications.
