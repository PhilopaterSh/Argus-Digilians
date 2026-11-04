# ACCESS_CONTROL — h1

- source: h1
- class: access_control
- cwe: CWE-284
- severity: informational
- program: fastly-vdp
- quality_score: 12

## Scenario

Analyze the following vulnerability report and provide a structured security assessment.

**Report Title:** Unauthenticated cache purging
**Affected Asset:** *.fanout.io

**Vulnerability Description:**
## Summary:
I found a vulnerability in https://fanout.io/ page known  as unauthenticated cache purging vulnerability. This vulnerability arises when cache purging requests are available to the unauthenticated users. 

## Steps To Reproduce:

  1. Go to any terminal of an OS which has curl installed in it.
  2. Type in the following command `curl --head https://fanout.io/` and hit enter. You will see that there are these following HTTP headers available
```http
via: 1.1 varnish
age: 7
x-served-by: cache-qpg1234-QPG
x-cache: HIT
x-cache-hits: 1
```
  3. This means that the page is caching the requests. So to reproduce the bug or to exploit it, type `curl -X PURGE https://fanout.io/` and in the response you'll see `{ "status": "ok", "id": "[REDACTED_PHONE]" }` (the id can be changed in your case)
This response proves that this endpoint is vulnerable to unauthenticated cache purging.

## Supporting Material/References:
F2235408

## Impact

In general, cache purging vulnerabilities can have a high severity level because they can allow an attacker to manipulate the cache of a web application, which can lead to various types of attacks such as website defacement, unauthorized access to sensitive data, or denial of service (DoS) attacks.

**Steps to Reproduce:**
1. Go to any terminal of an OS which has curl installed in it.
  2. Type in the following command `curl --head https://fanout.io/` and hit enter. You will see that there are these following HTTP headers available
```http
via: 1.1 varnish
age: 7
x-served-by: cache-qpg1234-QPG
x-cache: HIT
x-cache-hits: 1
```
  3. This means that the page is caching the requests. So to reproduce the bug or to exploit it, type `curl -X PURGE https://fanout.io/` and in the response you'll see `{ "status": "ok", "id": "[REDACTED_PHONE]" }` (the id can be changed in your case)
This response proves that this endpoint is vulnerable to unauthenticated cache purging.

## Supporting Material/References:
F2235408

**Proof of Concept:**
```http
via: 1.1 varnish
age: 7
x-served-by: cache-qpg1234-QPG
x-cache: HIT
x-cache-hits: 1
```

## Analysis / Response

**Vulnerability Class:** access_control
**CWE:** CWE-284
**Weakness:** Improper Access Control - Generic
**Severity:** informational
**Endpoint Pattern:** https://fanout.io/

**Impact Assessment:**
In general, cache purging vulnerabilities can have a high severity level because they can allow an attacker to manipulate the cache of a web application, which can lead to various types of attacks such as website defacement, unauthorized access to sensitive data, or denial of service (DoS) attacks.

**Remediation:**
Implement server-side authorization checks on every request. Use role-based access control. Deny by default. Never rely on client-side access control.
