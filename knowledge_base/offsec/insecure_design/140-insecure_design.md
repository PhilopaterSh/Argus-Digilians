# INSECURE_DESIGN — h1

- source: h1
- class: insecure_design
- cwe: CWE-657
- severity: low
- program: coalition
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Non-Cloudflare IPs allowed to access origin servers
**Affected Asset:** platform.thecoalition.com

**Vulnerability Description:**
Hello Security Team,

**Summary:** Like report #255978 It is possible to access origin servers served by nginx and not cloudflare. 

**Description:** Even though these IP's don't serve a functional version of the app it is possible to enable DDoS attacks by bypassing cloudflare protections.

## Steps To Reproduce:

  [REDACTED_PHONE]
  [REDACTED_PHONE]
  [REDACTED_PHONE]
 
There are more IP's but I think these are enough as a proof of concept.

## Impact

Response header from one of origin IP's :
`Connection:keep-alive
Content-Encoding:gzip
Content-Length:4774
Content-Type:text/html; charset=utf-8
Date:Wed, 14 Feb 2018 01:28:15 GMT
Request-Id:542a2e[REDACTED_PHONE]e8-bfba-c90bcfe9a4b2
Server:nginx/1.12.1
Strict-Transport-Security:max-age=16070400
Vary:Accept-Encoding
X-Content-Type-Options:nosniff
X-Download-Options:noopen
X-Frame-Options:deny
X-XSS-Protection:1; mode=block`

and the regular website:

`cf-ray:3ecc3592fd2a7e21-DTW
content-encoding:br
content-type:text/html; charset=utf-8
date:Wed, 14 Feb 2018 01:21:12 GMT
expect-ct:max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"
request-id:57feab[REDACTED_PHONE]e8-a7fe-31e9cef0afb4
server:cloudflare
status:200
strict-transport-security:max-age=2592000; includeSubDomains
vary:Accept-Encoding
x-content-type-options:nosniff
x-download-options:noopen
x-frame-options:deny
x-xss-protection:1; mode=block`

Also http://[REDACTED_PHONE]/login serves an insecure login page.

**Steps to Reproduce:**
[REDACTED_PHONE]
  [REDACTED_PHONE]
  [REDACTED_PHONE]
 
There are more IP's but I think these are enough as a proof of concept.

## Analysis / Response

**Vulnerability Class:** insecure_design
**CWE:** CWE-657
**Weakness:** Violation of Secure Design Principles
**Severity:** low
**Endpoint Pattern:** https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct

**Impact Assessment:**
Response header from one of origin IP's :
`Connection:keep-alive
Content-Encoding:gzip
Content-Length:4774
Content-Type:text/html; charset=utf-8
Date:Wed, 14 Feb 2018 01:28:15 GMT
Request-Id:542a2e[REDACTED_PHONE]e8-bfba-c90bcfe9a4b2
Server:nginx/1.12.1
Strict-Transport-Security:max-age=16070400
Vary:Accept-Encoding
X-Content-Type-Options:nosniff
X-Download-Options:noopen
X-Frame-Options:deny
X-XSS-Protection:1; mode=block`

and the regular website:

`cf-ray:3ecc3592fd2a7e21-DTW
content-encoding:br
content-type:text/html; charset=utf-8
date:Wed, 14 Feb 2018 01:21:12 GMT
expect-ct:max-age=604800, report-uri="https://report-uri.cloudflare.com/cdn-cgi/beacon/expect-ct"
request-id:57feab[REDACTED_PHONE]e8-a7fe-31e9cef0afb4
server:cloudflare
status:200
strict-transport-security:max-age=2592000; includeSubDomains
vary:Accept-Encoding
x-content-type-options:nosniff
x-download-options:noopen
x-frame-options:deny
x-xss-protection:1; mode=block`

Also http://[REDACTED_PHONE]/login serves an insecure login page.

**Remediation:**
Conduct threat modeling during design phase. Apply defense-in-depth principles. Follow secure design patterns and reference architectures.
