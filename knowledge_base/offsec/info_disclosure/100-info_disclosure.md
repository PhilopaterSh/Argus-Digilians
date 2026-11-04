# INFO_DISCLOSURE — h1

- source: h1
- class: info_disclosure
- cwe: CWE-922
- cve: ['CVE-2018-11409']
- severity: medium
- program: deptofdefense
- quality_score: 10

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Splunk Sensitive Information Disclosure @████████

**Vulnerability Description:**
Hi Team,

Hope you are doing great.
I got a domain that contains Splunk Sensitive Information Disclosure @██████████
PoC:
https://███████/en-US/splunkd/__raw/services/server/info/server-info?output_mode=json
█████████

Splunk through 7.0.1 allows information disclosure by appending __raw/services/server/info/server-info?output_mode=json to a query, as demonstrated by discovering a license key.

Reference:
    - https://nvd.nist.gov/vuln/detail/CVE-[REDACTED_PHONE]
    - https://github.com/kofa2002/splunk
    - https://www.exploit-db.com/exploits/44865/
    - http://web.archive.org/web/[REDACTED_PHONE]/https://securitytracker.com/id/1041148

## Impact

Splunk Sensitive Information Disclosure

## System Host(s)
██████

## Affected Product(s) and Version(s)


## CVE Numbers


## Steps to Reproduce
Open this link:
https://█████████/en-US/splunkd/__raw/services/server/info/server-info?output_mode=json

## Suggested Mitigation/Remediation Actions




**Steps to Reproduce:**
Open this link:
https://█████████/en-US/splunkd/__raw/services/server/info/server-info?output_mode=json

## Suggested Mitigation/Remediation Actions

**Proof of Concept:**
https://███████/en-US/splunkd/__raw/services/server/info/server-info?output_mode=json
█████████

Splunk through 7.0.1 allows information disclosure by appending __raw/services/server/info/server-info?output_mode=json to a query, as demonstrated by discovering a license key.

Reference:
    - https://nvd.nist.gov/vuln/detail/CVE-[REDACTED_PHONE]
    - https://github.com/kofa2002/splunk
    - https://www.exploit-db.com/exploits/44865/
    - http://web.archive.org/web/[REDACTED_PHONE]/https://securitytracker.com/id/1041148

## Analysis / Response

**Vulnerability Class:** info_disclosure
**CWE:** CWE-922
**Weakness:** Insecure Storage of Sensitive Information
**Severity:** medium
**Endpoint Pattern:** https://███████/en-US/splunkd/__raw/services/server/info/server-info?output_mode=json

**Impact Assessment:**
Splunk Sensitive Information Disclosure

## System Host(s)
██████

## Affected Product(s) and Version(s)


## CVE Numbers

**Remediation:**
Remove sensitive data from error messages, headers, and responses. Implement proper access controls. Disable debug modes in production.
